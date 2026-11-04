# SPDX-License-Identifier: GPL-3.0-or-later
"""Identificação do jogo no PC por CRC32 (decisão do usuário, 2026-11-03; docs/fork-oscr.md seção 3.2).

O firmware não carrega base de dados. O PC lê arquivos que o usuário traz:
  - No-Intro / Redump (Logiqx XML, extensão .dat ou .xml): <game name=...><rom name size crc .../></game>;
  - NES 2.0 XML Database (nes20db.xml): além do nome, traz mapper, submapper e os tamanhos de PRG, CHR e RAM,
    que servem para escolher as opções de `dump` no NES/Famicom (`--game`).
  - base do OSCR legado (.txt: nome, linha de dados, linha em branco; a linha de dados começa pelo CRC32). Vem no
    projeto, em database/oscr/ (ORIGEM.txt diz de onde), e é carregada sozinha; no NES o cabeçalho iNES da linha dá
    mapper e tamanhos.
A base binária CRDB do OSCR não é lida (formato sem amostra para testar; o diretório databases/ do clone vem vazio).
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

NES_SYSTEMS = (2, 3)

# Pasta da base que vem no projeto (database/oscr/ na raiz do repositório) e arquivos .txt que não são base.
BUILTIN_DIR = Path(__file__).resolve().parents[2] / "database" / "oscr"
_NOT_DB = {"origem.txt", "index.txt", "leiame.txt", "readme.txt"}
# Extensão de arquivo que o OSCR deixa no fim do nome ("Jogo (USA).nes"); sai do nome mostrado.
_ROM_EXT = re.compile(r"\.(nes|sfc|smc|gba|gbc|gb|md|gen|gg|sms|pce|sgx|sg|32x|vb|bin)$", re.I)


@dataclass
class Entry:
    name: str
    crc: int                          # CRC32 do que a base descreve (arquivo sem cabeçalho no No-Intro; arquivo com cabeçalho no NES 2.0)
    size: int = 0
    source: str = ""                  # nome do arquivo da base
    kind: str = "logiqx"              # "logiqx", "nes20" ou "oscr"
    # Só no NES 2.0 XML:
    prg_crc: Optional[int] = None
    chr_crc: Optional[int] = None
    mapper: Optional[int] = None
    submapper: Optional[int] = None
    prg_kb: Optional[int] = None
    chr_kb: Optional[int] = None
    ram_kb: Optional[int] = None      # PRG-RAM com bateria (ou, sem bateria, a PRG-RAM)
    battery: bool = False

    def nes_options(self) -> Optional[dict]:
        """Opções de `dump`/`save` do NES/Famicom, ou None se a base não traz mapper e tamanhos."""
        if self.mapper is None or not self.prg_kb:
            return None
        return {"mapper": self.mapper, "prg": self.prg_kb, "chr": self.chr_kb or 0, "ram": self.ram_kb or 0}

    def to_dict(self) -> dict:
        d = {"name": self.name, "crc32": f"{self.crc:08X}", "size": self.size, "source": self.source, "kind": self.kind}
        o = self.nes_options()
        if o:
            d.update({"mapper": o["mapper"], "submapper": self.submapper, "prg_kb": o["prg"], "chr_kb": o["chr"],
                      "ram_kb": o["ram"], "battery": self.battery})
        return d


@dataclass
class Match:
    entry: Entry
    how: str                          # "crc32", "crc32 sem cabeçalho iNES" ou "crc32 da PRG e da CHR"
    others: int = 0                   # outras entradas com o mesmo CRC32 (variantes idênticas)

    def to_dict(self) -> dict:
        return {**self.entry.to_dict(), "match": self.how, "others": self.others}


def _hex(v: Optional[str]) -> Optional[int]:
    try:
        return int(v, 16) if v else None
    except ValueError:
        return None


def _int(v: Optional[str]) -> int:
    try:
        return int(v) if v else 0
    except ValueError:
        return 0


def _kb(el: Optional[ET.Element]) -> int:
    return (_int(el.get("size")) + 1023) // 1024 if el is not None else 0


def _nes20(game: ET.Element, source: str) -> Optional[Entry]:
    pcb, prg, chr_ = game.find("pcb"), game.find("prgrom"), game.find("chrrom")
    if pcb is None or prg is None:
        return None
    rom = game.find("rom")
    name = game.get("name") or (rom.get("name") if rom is not None else None) or ""
    nv, ram = game.find("prgnvram"), game.find("prgram")
    crc = _hex(rom.get("crc32") or rom.get("crc")) if rom is not None else None
    e = Entry(name=name, crc=crc if crc is not None else 0, size=_int(rom.get("size")) if rom is not None else 0, source=source, kind="nes20",
              prg_crc=_hex(prg.get("crc32") or prg.get("crc")), chr_crc=_hex(chr_.get("crc32") or chr_.get("crc")) if chr_ is not None else None,
              mapper=_int(pcb.get("mapper")), submapper=_int(pcb.get("submapper")), prg_kb=_kb(prg), chr_kb=_kb(chr_),
              ram_kb=_kb(nv) or _kb(ram), battery=pcb.get("battery") == "1" or nv is not None)
    if not e.name:
        e.name = f"mapper {e.mapper}, PRG {e.prg_kb} KB, CHR {e.chr_kb} KB ({e.prg_crc:08X})" if e.prg_crc is not None else f"mapper {e.mapper}"
    return e


def _ines(h: bytes) -> Optional[dict]:
    """Mapper e tamanhos do cabeçalho iNES / NES 2.0 de 16 bytes. None se não for um cabeçalho válido ou se o tamanho usa a forma exponencial."""
    if len(h) != 16 or h[:4] != b"NES\x1a":
        return None
    nes2 = (h[7] & 0x0C) == 0x08
    mapper = (h[6] >> 4) | (h[7] & 0xF0)
    sub = 0
    prg, chr_ = h[4], h[5]
    ram = 0
    if nes2:
        mapper |= (h[8] & 0x0F) << 8
        sub = h[8] >> 4
        if (h[9] & 0x0F) == 0x0F or (h[9] >> 4) == 0x0F:
            return None
        prg |= (h[9] & 0x0F) << 8
        chr_ |= (h[9] >> 4) << 8
        nv, vol = h[10] >> 4, h[10] & 0x0F
        ram = ((64 << nv) if nv else (64 << vol) if vol else 0) // 1024
    else:
        ram = h[8] * 8
        if not ram and h[6] & 2:
            ram = 8
    return {"mapper": mapper, "submapper": sub, "prg_kb": prg * 16, "chr_kb": chr_ * 8, "ram_kb": ram, "battery": bool(h[6] & 2)}


def parse_oscr_file(path: Path) -> list[Entry]:
    """Lê uma base .txt do OSCR legado: pares nome + linha de dados (CRC32 primeiro). Linhas que não seguem o formato são ignoradas."""
    source = path.name
    stem = path.stem.lower()
    lines = [l.strip() for l in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    lines = [l for l in lines if l]
    out: list[Entry] = []
    i = 0
    while i + 1 < len(lines):
        name, data = lines[i], lines[i + 1]
        f = data.split(",")
        if not re.fullmatch(r"[0-9A-Fa-f]{8}", f[0]):
            i += 1                                           # nome sem linha de dados: tenta de novo na linha seguinte
            continue
        i += 2
        e = Entry(name=_ROM_EXT.sub("", name), crc=int(f[0], 16), source=source, kind="oscr")
        if stem == "nes" and len(f) >= 3:
            try:
                n = _ines(bytes.fromhex(f[2]))
            except ValueError:
                n = None
            if n:
                e.mapper, e.submapper, e.prg_kb, e.chr_kb, e.ram_kb, e.battery = (n[k] for k in ("mapper", "submapper", "prg_kb", "chr_kb", "ram_kb", "battery"))
                e.size = (e.prg_kb + e.chr_kb) * 1024
        elif stem == "gba" and len(f) >= 3 and f[2].isdigit():
            e.size = int(f[2]) * 1024 * 1024                 # tamanho em MB
        out.append(e)
    return out


def parse_file(path: Path) -> list[Entry]:
    """Lê um .dat/.xml (Logiqx ou NES 2.0). Levanta ValueError se o arquivo não for XML válido."""
    if path.suffix.lower() == ".txt":
        return parse_oscr_file(path)
    out: list[Entry] = []
    source = path.name
    try:
        for _ev, el in ET.iterparse(str(path), events=("end",)):
            if el.tag not in ("game", "machine", "software"):
                continue
            n20 = _nes20(el, source)
            if n20 is not None:
                out.append(n20)
            else:
                for rom in el.findall("rom"):
                    crc = _hex(rom.get("crc") or rom.get("crc32"))
                    if crc is not None:
                        out.append(Entry(name=el.get("name") or rom.get("name") or "", crc=crc, size=_int(rom.get("size")), source=source))
            el.clear()
    except ET.ParseError as e:
        raise ValueError(f"{path}: XML inválido ({e})") from e
    return out


@dataclass
class Database:
    entries: list[Entry] = field(default_factory=list)
    by_crc: dict[int, list[Entry]] = field(default_factory=dict)
    by_prg: dict[int, list[Entry]] = field(default_factory=dict)
    files: list[str] = field(default_factory=list)

    def add(self, e: Entry) -> None:
        self.entries.append(e)
        self.by_crc.setdefault(e.crc, []).append(e)
        if e.prg_crc is not None:
            self.by_prg.setdefault(e.prg_crc, []).append(e)

    def load(self, path: str | os.PathLike) -> int:
        """Carrega um arquivo, ou todos os .dat, .xml e .txt (base do OSCR) de uma pasta (recursivo). Devolve quantas entradas entraram."""
        p = Path(path).expanduser()
        if not p.exists():
            raise ValueError(f"base de dados não encontrada: {p}")
        files = sorted(f for f in p.rglob("*") if f.suffix.lower() in (".dat", ".xml") or (f.suffix.lower() == ".txt" and f.name.lower() not in _NOT_DB)) if p.is_dir() else [p]
        n = 0
        for f in files:
            for e in parse_file(f):
                self.add(e)
                n += 1
            self.files.append(str(f))
        return n

    def __len__(self) -> int:
        return len(self.entries)

    def identify(self, system: int, data: bytes) -> Optional[Match]:
        """Acha o jogo pelo CRC32 do arquivo. No NES/Famicom também tenta o arquivo sem o cabeçalho iNES de 16 bytes
        (o No-Intro "headerless") e os CRC32 da PRG e da CHR (NES 2.0 XML)."""
        hit = self.by_crc.get(zlib.crc32(data))
        if hit:
            return Match(hit[0], "crc32", len(hit) - 1)
        if system in NES_SYSTEMS and data[:4] == b"NES\x1a" and len(data) > 16:
            body = data[16:]
            hit = self.by_crc.get(zlib.crc32(body))
            if hit:
                return Match(hit[0], "crc32 sem cabeçalho iNES", len(hit) - 1)
            prg_len, chr_len = data[4] * 16384, data[5] * 8192
            prg, chr_ = body[:prg_len], body[prg_len:prg_len + chr_len]
            cands = self.by_prg.get(zlib.crc32(prg), []) if prg_len else []
            cc = zlib.crc32(chr_) if chr_len else None
            cands = [e for e in cands if e.chr_crc == cc]
            if cands:
                return Match(cands[0], "crc32 da PRG e da CHR", len(cands) - 1)
        return None

    def search(self, text: str, limit: int = 20) -> list[Entry]:
        """Entradas cujo nome contém todas as palavras de `text` (sem diferenciar maiúsculas)."""
        words = text.lower().split()
        out: list[Entry] = []
        for e in self.entries:
            n = e.name.lower()
            if all(w in n for w in words):
                out.append(e)
                if len(out) >= limit:
                    break
        return out


def load_databases(paths: Iterable[str | os.PathLike], builtin: bool = True) -> Database:
    """Base que vem no projeto (se `builtin` e a pasta existir) mais as do usuário, nesta ordem: a do projeto vem
    primeiro, então vence quando o mesmo CRC32 está nas duas (o nome do jogo muda de uma base para outra)."""
    db = Database()
    if builtin and BUILTIN_DIR.is_dir():
        db.load(BUILTIN_DIR)
    for p in paths:
        db.load(p)
    return db


def paths_from_env() -> list[str]:
    """Caminhos da variável OSCR_DB (separados por ':' no Linux e macOS, ';' no Windows)."""
    return [p for p in os.environ.get("OSCR_DB", "").split(os.pathsep) if p]
