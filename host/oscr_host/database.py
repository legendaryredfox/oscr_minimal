# SPDX-License-Identifier: GPL-3.0-or-later
"""Identificação do jogo no PC por CRC32 (decisão do usuário, 2026-11-03; docs/fork-oscr.md seção 3.2).

O firmware não carrega base de dados. O PC lê arquivos que o usuário traz:
  - No-Intro / Redump (Logiqx XML, extensão .dat ou .xml): <game name=...><rom name size crc .../></game>;
  - NES 2.0 XML Database (nes20db.xml): além do nome, traz mapper, submapper e os tamanhos de PRG, CHR e RAM,
    que servem para escolher as opções de `dump` no NES/Famicom (`--game`).
A base binária CRDB do OSCR não é lida (formato sem amostra para testar; o diretório databases/ do clone vem vazio).
"""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

NES_SYSTEMS = (2, 3)


@dataclass
class Entry:
    name: str
    crc: int                          # CRC32 do que a base descreve (arquivo sem cabeçalho no No-Intro; arquivo com cabeçalho no NES 2.0)
    size: int = 0
    source: str = ""                  # nome do arquivo da base
    kind: str = "logiqx"              # "logiqx" ou "nes20"
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


def parse_file(path: Path) -> list[Entry]:
    """Lê um .dat/.xml (Logiqx ou NES 2.0). Levanta ValueError se o arquivo não for XML válido."""
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
        """Carrega um arquivo, ou todos os .dat e .xml de uma pasta (recursivo). Devolve quantas entradas entraram."""
        p = Path(path).expanduser()
        if not p.exists():
            raise ValueError(f"base de dados não encontrada: {p}")
        files = sorted(f for f in p.rglob("*") if f.suffix.lower() in (".dat", ".xml")) if p.is_dir() else [p]
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


def load_databases(paths: Iterable[str | os.PathLike]) -> Database:
    db = Database()
    for p in paths:
        db.load(p)
    return db


def paths_from_env() -> list[str]:
    """Caminhos da variável OSCR_DB (separados por ':' no Linux e macOS, ';' no Windows)."""
    return [p for p in os.environ.get("OSCR_DB", "").split(os.pathsep) if p]
