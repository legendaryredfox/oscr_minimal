# SPDX-License-Identifier: GPL-3.0-or-later
"""CLI do dumper: detect, dump, save-read, save-write, identify, search, info, ports, systems, errors.

Feita para pessoas e para agentes de IA: --json (saída e erros), código de saída estável, progresso em JSON lines,
nenhum prompt fora de um terminal. Referência: docs/cli.md."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import zlib
from pathlib import Path

from . import __version__
from . import protocol as P
from .client import Client, TimeoutError_
from . import database as DB
from .planned import PLANNED
from . import romimage as RI
from .verify import eeprom_is_4k, gba_save_hint, verify_rom
from .transport import SerialTransport, Transport

BAUDS = (1_000_000, 115_200)

# Códigos de saída (estáveis; docs/cli.md)
EXIT_OK, EXIT_ERROR, EXIT_NO_CART, EXIT_NO_DEVICE, EXIT_REFUSED, EXIT_USAGE, EXIT_INTERRUPTED = 0, 1, 2, 3, 4, 64, 130

CLI_EXIT_CODES = {
    EXIT_OK: "sucesso", EXIT_ERROR: "erro do dispositivo, do protocolo, de timeout ou de arquivo",
    EXIT_NO_CART: "nenhum cartucho (detect) ou o dispositivo respondeu 'nenhum cartucho'",
    EXIT_NO_DEVICE: "porta serial não encontrada ou dispositivo sem resposta",
    EXIT_REFUSED: "operação recusada: falta --yes fora de um terminal", EXIT_USAGE: "argumentos inválidos",
    EXIT_INTERRUPTED: "interrompido (Ctrl+C)",
}


class CliError(Exception):
    """Erro com tipo estável (`kind`) e código de saída; vira JSON com --json."""

    def __init__(self, kind: str, message: str, exit_code: int = EXIT_ERROR, hint: str | None = None, **extra):
        super().__init__(message)
        self.kind, self.message, self.exit_code, self.hint, self.extra = kind, message, exit_code, hint, extra


def _progress(label: str, mode: str = "auto"):
    """mode: auto (barra se stderr for terminal), none, jsonl (uma linha JSON por 1% em stderr)."""
    state = {"last": -1}

    def cb(done: int, total: int) -> None:
        if mode == "none" or total == 0:
            return
        if mode == "jsonl":
            pct = done * 100 // total
            if pct != state["last"]:
                state["last"] = pct
                print(json.dumps({"event": "progress", "label": label, "done": done, "total": total, "percent": pct}),
                      file=sys.stderr, flush=True)
            return
        if not sys.stderr.isatty():
            return
        pct = done * 100 // total
        if pct != state["last"]:
            state["last"] = pct
            print(f"\r{label}: {pct:3d}%  ({done}/{total} bytes)", end="", file=sys.stderr, flush=True)
            if done >= total:
                print(file=sys.stderr)

    return cb


def list_ports() -> list[str]:
    from serial.tools import list_ports as lp

    return [p.device for p in lp.comports()]


def auto_port() -> str:
    ports = [p for p in list_ports() if any(k in p for k in ("ttyUSB", "ttyACM", "cu.usb", "COM"))]
    if not ports:
        raise CliError("no_port", "nenhuma porta serial encontrada", EXIT_NO_DEVICE,
                       "conecte o dispositivo, use --port, ou --simulate sem hardware (no Linux: grupo dialout)")
    return ports[0]


def connect(args) -> tuple[Client, Transport, dict]:
    """Abre a porta (ou o simulador) e faz INFO, com fallback de baud."""
    if args.simulate:
        from . import sim

        t, _dev, _stop, _th = sim.start()
        c = Client(t, timeout=0.5, long_timeout=5.0)
        return c, t, c.info()
    port = args.port or auto_port()
    bauds = (args.baud,) if args.baud else BAUDS
    last: Exception | None = None
    for b in bauds:
        try:
            t = SerialTransport(port, b)
        except OSError as e:                              # porta ocupada, sem permissão (grupo dialout), cabo solto
            raise CliError("open_port", f"não foi possível abrir {port}: {e}", EXIT_NO_DEVICE,
                           "feche outros programas que usam a porta; no Linux o usuário precisa estar no grupo dialout") from e
        c = Client(t, timeout=0.5)
        try:
            return c, t, c.info()
        except TimeoutError_ as e:
            last = e
            t.close()
    raise CliError("no_response", f"sem resposta do dispositivo em {port} ({', '.join(map(str, bauds))} baud): {last}", EXIT_NO_DEVICE,
                   "confira se o firmware está gravado, a porta e o baud (--baud 115200)")


def system_id(name: str) -> int:
    if name not in P.SYSTEMS:
        raise CliError("usage", f"sistema desconhecido: {name}. Use: {', '.join(P.SYSTEMS)}", EXIT_USAGE)
    return P.SYSTEMS[name][0]


def out_path(args, ext: str, default: str) -> Path:
    p = Path(args.output) if args.output else Path(default)
    if p.suffix == "":
        p = p.with_suffix(ext)
    return p


def cmd_ports(args) -> int:
    ports = list_ports()
    emit(args, {"ports": ports}, ports)
    return 0


# Opções específicas de cada sistema (as de --mapper, --prg, --chr e --ram; o sentido de cada uma está em --help)
SYSTEM_OPTIONS = {"snes": ["prg"], "nes": ["mapper", "prg", "chr", "ram"], "famicom": ["mapper", "prg", "chr", "ram"],
                  "md": ["prg"], "gba": ["mapper"], "gb": [], "mock": []}


def cmd_systems(args) -> int:
    rows = [{"name": n, "id": v[0], "extension": v[1], "options": SYSTEM_OPTIONS.get(n, []), "needs_cartridge": n != "mock"}
            for n, v in P.SYSTEMS.items()]
    planned = [{"name": k, "label": l, "supported": False} for k, l in PLANNED]
    emit(args, {"systems": rows, "planned": planned},
         [f"{r['name']:8} id {r['id']:3}  {r['extension']:5} opções: {', '.join(r['options']) or '-'}" for r in rows]
         + ["", "em breve (outros cartuchos do OSCR, ainda sem hardware, firmware nem id no protocolo):"] + [f"  {p['name']:13} {p['label']}" for p in planned])
    return 0


def cmd_errors(args) -> int:
    dev = [{"code": c, "text": t, "hint": P.ERROR_HINTS.get(c)} for c, t in P.ERRORS.items()]
    cli = [{"exit_code": c, "meaning": m} for c, m in CLI_EXIT_CODES.items()]
    emit(args, {"device_errors": dev, "exit_codes": cli},
         [f"saída {c}: {m}" for c, m in CLI_EXIT_CODES.items()] + [f"erro 0x{d['code']:04X}: {d['text']}" for d in dev])
    return 0


def emit(args, obj: dict, lines: list[str]) -> None:
    """Saída do comando: uma linha de JSON com --json (sempre com "ok"), senão o texto para humanos."""
    if args.json:
        print(json.dumps({"ok": True, **obj} if "ok" not in obj else obj, ensure_ascii=False))
    else:
        for l in lines:
            print(l)


def safe_name(title: str, default: str) -> str:
    n = re.sub(r"[^A-Za-z0-9._ -]+", "_", title or "").strip(" ._")
    return n or default


def load_db(args, required: bool = False) -> DB.Database | None:
    """Base de dados do PC (--db, repetível, ou a variável OSCR_DB). None se nenhuma foi pedida."""
    paths = list(args.db or []) or DB.paths_from_env()
    if not paths:
        if required:
            raise CliError("no_database", "nenhuma base de dados: use --db ARQUIVO_OU_PASTA (No-Intro .dat ou NES 2.0 XML) ou a variável OSCR_DB",
                           EXIT_USAGE)
        return None
    try:
        return DB.load_databases(paths)
    except (ValueError, OSError) as e:
        raise CliError("database", str(e), EXIT_ERROR, "confira o caminho e se o arquivo é um .dat (Logiqx) ou o nes20db.xml") from e


def _game_options(db: DB.Database, query: str) -> DB.Entry:
    """Escolhe a entrada do NES 2.0 XML pelo nome (para preencher mapper, PRG e CHR)."""
    found = [e for e in db.search(query, 200) if e.nes_options()]
    exact = [e for e in found if e.name.lower() == query.lower()]
    found = exact or found
    uniq = {(e.mapper, e.prg_kb, e.chr_kb, e.ram_kb): e for e in found}
    if not uniq:
        raise CliError("game_not_found", f"nenhum jogo com mapper e tamanhos na base para: {query}", EXIT_USAGE,
                       "a base precisa ser o NES 2.0 XML (nes20db.xml); o No-Intro não traz o mapper. Use `dumper search` para procurar")
    if len(uniq) > 1:
        raise CliError("game_ambiguous", f"{len(found)} jogos combinam com '{query}' e têm configurações diferentes", EXIT_USAGE,
                       "seja mais específico. Exemplos: " + "; ".join(f"{e.name} (mapper {e.mapper}, PRG {e.prg_kb} KB, CHR {e.chr_kb} KB)" for e in list(uniq.values())[:5]))
    return next(iter(uniq.values()))


def cmd_info(args) -> int:
    _c, t, info = connect(args)
    if args.json:
        emit(args, info, [])
        t.close()
        return 0
    print(f"protocolo {info['proto']}  firmware {info['firmware']}  MOCK={'sim' if info['mock'] else 'não'}"
          f"  Si5351={'sim' if info['si5351'] else 'não'}  sistemas: {', '.join(info['systems']) or '-'}  payload máx. {info['max_payload']}")
    t.close()
    return 0


def cmd_detect(args) -> int:
    c, t, _ = connect(args)
    r = c.detect(system_id(args.system))
    status = {0: "cartucho detectado", 1: "nenhum cartucho", 2: "não suportado",
              3: "erro de hardware", 4: "cabeçalho inválido (há dados, mas o checksum do cabeçalho não confere: limpe os contatos e encaixe de novo)"}
    lines = [f"{P.SYSTEM_BY_ID.get(r['system'], r['system'])}: {status.get(r['status'], r['status'])}"]
    if r["status"] == 0:
        lines.append(f"  título: {r['name'] or '(desconhecido)'}  ROM: {r['rom_size']} bytes  save: {r['save_size']} bytes")
    emit(args, {"ok": r["status"] == 0, **r, "status_text": status.get(r["status"], str(r["status"]))}, lines)
    t.close()
    return EXIT_OK if r["status"] == 0 else EXIT_NO_CART


def _save_result(args, res: P.Frame | object, ext: str, default: str, extra: dict | None = None, notes: list[str] | None = None) -> int:
    path = out_path(args, ext, default)
    path.write_bytes(res.data)
    obj = {"file": str(path), "bytes": len(res.data), "crc32": f"{res.crc32:08X}"}
    obj.update(extra or {})
    emit(args, obj, [f"{path}  {len(res.data)} bytes  CRC32 {res.crc32:08X}"] + (notes or []))
    return 0


def cmd_dump(args) -> int:
    sid = system_id(args.system)
    db = load_db(args, required=bool(args.game))
    if args.game:
        if sid not in DB.NES_SYSTEMS:
            raise CliError("usage", "--game vale só para NES e Famicom", EXIT_USAGE)
        g = _game_options(db, args.game)
        o = g.nes_options()
        args.mapper = args.mapper or o["mapper"]
        args.prg = args.prg or o["prg"]
        args.chr = args.chr or o["chr"]
        if not args.json:
            print(f"jogo da base: {g.name}  mapper {o['mapper']}  PRG {o['prg']} KB  CHR {o['chr']} KB  ({g.source})", file=sys.stderr)
    c, t, _ = connect(args)
    title = ""
    if not args.output:                                   # sem -o: nome do arquivo pelo título do cartucho
        try:
            title = c.detect(sid).get("name", "")
        except (P.DeviceError, P.ProtocolError, TimeoutError_):
            title = ""
    res = c.dump_rom(sid, args.block, _progress("rom", args.progress), args.mapper, args.prg, args.chr)
    t.close()
    ext = P.SYSTEMS[args.system][1]
    if sid == 6 and len(res.data) > 0x143 and res.data[0x143] & 0x80:
        ext = ".gbc"                                      # cabeçalho com a flag de Game Boy Color
    chk = verify_rom(sid, res.data)
    notes = []
    extra: dict = {"checksum": chk.status}
    if chk.status != "na":
        notes.append(("aviso: " if chk.status == "mismatch" else "") + str(chk))
    if db is not None:
        m = db.identify(sid, res.data)
        extra["game"] = m.to_dict() if m else None
        if m:
            title = m.entry.name
            notes.append(f"jogo: {m.entry.name} ({m.entry.source}, {m.how}" + (f", mais {m.others} idêntica(s)" if m.others else "") + ")")
        else:
            notes.append(f"jogo: não encontrado na base ({len(db)} entradas): dump novo, variante, ou erro de leitura se o CRC32 devia estar lá")
    if sid == 5:
        hint = gba_save_hint(res.data)
        if hint:
            code, label, tag = hint
            extra["gba_save_type"] = code
            more = " (se o save sair repetido a cada 512 bytes, use --mapper 1)" if code == 2 else ""
            notes.append(f"save do GBA: {tag}, {label}: use --mapper {code} em save-read{more}")
        else:
            notes.append("save do GBA: nenhuma cadeia de biblioteca de save na ROM (sem save, ou tipo desconhecido)")
    return _save_result(args, res, ext, safe_name(title, f"rom_{args.system}"), extra, notes)


_EXT_SYSTEM = {".sfc": 1, ".smc": 1, ".nes": 2, ".md": 4, ".gen": 4, ".smd": 4, ".gba": 5, ".gb": 6, ".gbc": 6}


def cmd_identify(args) -> int:
    db = load_db(args, required=True)
    results = []
    for f in args.files:
        data = Path(f).read_bytes()
        sid = P.SYSTEMS[args.system][0] if args.system != "mock" else _EXT_SYSTEM.get(Path(f).suffix.lower(), 0)
        m = db.identify(sid, data)
        results.append({"file": f, "bytes": len(data), "crc32": f"{zlib.crc32(data):08X}", "game": m.to_dict() if m else None})
    lines = [f"{r['file']}  CRC32 {r['crc32']}  " + (f"{r['game']['name']} ({r['game']['source']}, {r['game']['match']})" if r["game"] else "não encontrado na base")
             for r in results]
    emit(args, {"entries_in_database": len(db), "results": results}, lines)
    return EXIT_OK if all(r["game"] for r in results) else EXIT_ERROR


def cmd_search(args) -> int:
    db = load_db(args, required=True)
    found = db.search(args.query, args.limit)
    emit(args, {"entries_in_database": len(db), "results": [e.to_dict() for e in found]},
         [f"{e.crc:08X}  {e.name}" + (f"  [mapper {e.mapper}, PRG {e.prg_kb} KB, CHR {e.chr_kb} KB, RAM {e.ram_kb} KB]" if e.nes_options() else "") for e in found]
         or ["nenhum resultado"])
    return EXIT_OK if found else EXIT_ERROR


def cmd_save_read(args) -> int:
    c, t, _ = connect(args)
    res = c.read_save(system_id(args.system), args.block, _progress("save", args.progress), args.mapper, args.ram)
    t.close()
    notes = []
    if system_id(args.system) == 5 and args.mapper == 2 and eeprom_is_4k(res.data):
        notes.append("aviso: o conteúdo se repete a cada 512 bytes: é uma EEPROM de 512 bytes. Refaça com --mapper 1.")
    return _save_result(args, res, ".sav", f"save_{args.system}", None, notes)


def cmd_save_write(args) -> int:
    data = Path(args.input).read_bytes()
    sid = system_id(args.system)
    if not args.yes:                                      # gravar sobrescreve (ou apaga) a memória do cartucho: sempre confirmar
        if not sys.stdin.isatty():
            raise CliError("refused", "recusado: gravar o save sobrescreve a memória do cartucho. Em modo não interativo confirme com --yes.",
                           EXIT_REFUSED, "repita o comando com --yes (o save atual é salvo em --backup-dir antes, a menos que use --no-backup)")
        ans = input(f"Gravar {len(data)} bytes no save de {args.system}? Isso sobrescreve o save do cartucho. Continuar? [s/N] ")
        if ans.strip().lower() not in ("s", "sim", "y", "yes"):
            print("cancelado")
            return 1
    c, t, _ = connect(args)
    try:
        extra: dict = {}
        if not args.no_backup:                            # backup do save atual antes de gravar
            cur = c.read_save(sid, args.block, _progress("backup", args.progress), args.mapper, args.ram)
            bdir = Path(args.backup_dir).expanduser()
            bdir.mkdir(parents=True, exist_ok=True)
            bpath = bdir / f"{args.system}_{time.strftime('%Y%m%d-%H%M%S')}.sav"
            bpath.write_bytes(cur.data)
            extra["backup"] = str(bpath)
            if not args.json:
                print(f"backup do save atual: {bpath}  CRC32 {cur.crc32:08X}")
        crc = c.write_save(sid, data, args.block or P.DEFAULT_BLOCK, _progress("write", args.progress), args.mapper, args.ram)
    finally:
        t.close()
    extra.update({"bytes": len(data), "crc32": f"{crc:08X}"})
    emit(args, extra, [f"save gravado: {len(data)} bytes  CRC32 {crc:08X}"])
    return 0


def cmd_rom_write(args) -> int:
    """Grava uma ROM em cartucho de flash (WRITE_ROM). Apaga o chip: sempre confirma."""
    if args.system not in ("nes", "famicom", "snes", "md", "mock"):
        raise CliError("usage", "rom-write existe para NES e Famicom (flash NES Maker e A29040B), SNES (flash CFI de 2 ou 4 MB) e Mega Drive (MX29F1610 e S29GL064N); veja docs/funcoes-oscr.md", EXIT_USAGE)
    try:
        data = Path(args.input).read_bytes()
        chip = args.chip
        snes_chip = chip in ("snes-lorom", "snes-hirom")
        if args.system == "snes" or (args.system == "mock" and snes_chip):       # no simulador (mock) o chip decide
            if chip is None:
                raise CliError("usage", "no SNES escolha a fiação do flash com --chip snes-lorom ou --chip snes-hirom (a ROM sozinha não diz como o cartucho foi montado)", EXIT_USAGE)
            if not snes_chip:
                raise CliError("usage", f"o chip {chip} não é de SNES", EXIT_USAGE)
            img = RI.split_snes(data, args.capacity)
        elif args.system == "md" or (args.system == "mock" and chip == "md-flash"):
            if chip not in (None, "md-flash"):
                raise CliError("usage", f"o chip {chip} não é de Mega Drive (use --chip md-flash, ou nada)", EXIT_USAGE)
            chip = "md-flash"
            img = RI.split_md(data)
        elif snes_chip or chip == "md-flash":
            raise CliError("usage", f"o chip {chip} é só para o sistema dele (snes ou md)", EXIT_USAGE)
        else:
            img = RI.split_image(data, chip or "nesmaker")
            if chip is None:
                chip = RI.infer_chip(img)
                if chip is None:
                    raise CliError("usage", "não deu para saber o chip: use --chip nesmaker (mapper 30) ou --chip a29040b (mapper 0)", EXIT_USAGE)
                img = RI.split_image(data, chip)
    except ValueError as e:
        raise CliError("bad_rom", str(e), EXIT_USAGE) from e
    if img.mapper is not None and img.mapper != RI.CHIP_MAPPER[chip] and not args.json:
        print(f"aviso: o arquivo é do mapper {img.mapper}, mas o chip {chip} é de cartucho de mapper {RI.CHIP_MAPPER[chip]}", file=sys.stderr)
    what = (f"{RI.CHIP_LABEL[chip]}: ROM {img.prg_kb} KB em flash de {img.flash_kb} KB ({len(img.body)} bytes)" if img.flash_kb
            else f"{RI.CHIP_LABEL[chip]}: ROM {len(img.body)} bytes" if chip == "md-flash"
            else f"{RI.CHIP_LABEL[chip]}: PRG {img.prg_kb} KB, CHR {img.chr_kb} KB ({len(img.body)} bytes)")
    if not args.yes:
        if not sys.stdin.isatty():
            raise CliError("refused", "recusado: gravar a ROM APAGA o chip de flash do cartucho. Em modo não interativo confirme com --yes.", EXIT_REFUSED,
                           "repita o comando com --yes")
        ans = input(f"Gravar {what}? Isso APAGA a ROM atual do cartucho. Continuar? [s/N] ")
        if ans.strip().lower() not in ("s", "sim", "y", "yes"):
            print("cancelado")
            return 1
    c, t, info = connect(args)
    try:
        if not info.get("write_rom"):
            raise CliError("unsupported_firmware", "este firmware não aceita WRITE_ROM", EXIT_ERROR, "atualize o firmware (docs/funcoes-oscr.md)")
        crc = c.write_rom(system_id(args.system), img.body, RI.CHIPS[chip], img.flash_kb or img.prg_kb, img.chr_kb, args.block or P.DEFAULT_BLOCK,
                          _progress("write-rom", args.progress), args.begin_timeout)
    finally:
        t.close()
    out = {"chip": chip, "prg_kb": img.prg_kb, "chr_kb": img.chr_kb, "bytes": len(img.body), "crc32": f"{crc:08X}"}
    if img.flash_kb:
        out["flash_kb"] = img.flash_kb
    lines = [f"ROM gravada: {what}  CRC32 {crc:08X}"]
    if args.no_verify or args.system == "mock":      # o simulador não guarda a ROM gravada para ler de volta
        out["verify"] = "skipped"
        lines.append("conferência depois de gravar: pulada")
    else:
        c2, t2, _ = connect(args)
        try:
            v = RI.verify_written(c2, system_id(args.system), chip, img, _progress("verify", args.progress))
        finally:
            t2.close()
        out["verify"] = v.to_dict()
        if not v.ok:
            raise CliError("verify_failed", f"a ROM lida de volta NÃO confere com a gravada (primeiro byte diferente no offset {v.first_diff}; lido {v.read_crc32:08X}, esperado {v.expected_crc32:08X})",
                           EXIT_ERROR, "limpe os contatos, confira se o chip é o escolhido e grave de novo; o chip pode estar apagado ou pela metade",
                           written=out, first_diff=v.first_diff)
        lines.append(f"conferência depois de gravar: OK (leu {v.read_bytes} bytes, CRC32 {v.read_crc32:08X})")
    emit(args, out, lines)
    return 0


class _Parser(argparse.ArgumentParser):
    """Erro de uso vira saída 64 (e JSON com --json), não o 2 do argparse, que é 'nenhum cartucho'."""

    json_mode = False

    def error(self, message):
        if _Parser.json_mode:
            print(json.dumps({"ok": False, "error": {"kind": "usage", "message": message}}, ensure_ascii=False))
        else:
            self.print_usage(sys.stderr)
            print(f"{self.prog}: erro: {message}", file=sys.stderr)
        sys.exit(EXIT_USAGE)


def _add_common(p: argparse.ArgumentParser, top: bool) -> None:
    """Opções globais. Valem antes e depois do subcomando (nos subcomandos o padrão é SUPPRESS para não sobrescrever)."""
    d = (lambda v: v) if top else (lambda v: argparse.SUPPRESS)
    p.add_argument("-p", "--port", default=d(None), help="porta serial (padrão: primeira ttyUSB/ttyACM/COM)")
    p.add_argument("-b", "--baud", type=int, default=d(None), help="baud (padrão: 1000000, depois 115200)")
    p.add_argument("--db", action="append", default=d(None), metavar="CAMINHO",
                   help="base de dados para identificar o jogo: arquivo ou pasta de .dat (No-Intro) ou nes20db.xml; pode repetir; também lê a variável OSCR_DB")
    p.add_argument("--simulate", action="store_true", default=d(False), help="usa o simulador em memória (sem hardware)")
    p.add_argument("--json", action="store_true", default=d(False),
                   help='saída em JSON (uma linha em stdout, sempre com "ok"; erros: {"ok":false,"error":{kind,message,hint}})')
    p.add_argument("--progress", choices=("auto", "none", "jsonl"), default=d("auto"),
                   help="progresso em stderr: auto (barra se for terminal), none, jsonl (uma linha JSON por 1%%)")


EPILOG = """códigos de saída: 0 ok | 1 erro | 2 nenhum cartucho | 3 sem porta/dispositivo | 4 recusado (falta --yes) | 64 uso | 130 Ctrl+C
exemplos:
  dumper --json detect -s snes
  dumper dump -s snes -o jogo --json --progress jsonl
  dumper save-write -s snes -i jogo.sav --yes --json
  dumper --simulate --json systems
Guia completo para agentes: docs/cli.md"""


def build_parser() -> argparse.ArgumentParser:
    ap = _Parser(prog="dumper", description="Dumper de cartuchos oscr_minimal", epilog=EPILOG,
                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", action="version", version=f"dumper {__version__} (protocolo {P.PROTO_VERSION})")
    _add_common(ap, True)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_, system=True, out=False, inp=False):
        sp = sub.add_parser(name, help=help_, description=help_, epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
        sp.set_defaults(fn=fn)
        _add_common(sp, False)
        if system:
            sp.add_argument("-s", "--system", default="mock", choices=sorted(P.SYSTEMS), help="sistema (padrão: mock)")
        if out:
            sp.add_argument("-o", "--output", help="arquivo de saída (a extensão certa é acrescentada; sobrescreve se existir)")
        if inp:
            sp.add_argument("-i", "--input", required=True, help="arquivo para gravar (save, ou ROM no rom-write)")
        if out or inp:
            sp.add_argument("--block", type=int, default=0, help="tamanho do bloco (padrão 512)")
        return sp

    add("ports", cmd_ports, "lista as portas seriais", system=False)
    add("systems", cmd_systems, "lista os sistemas, extensões e opções de cada um (não abre a porta)", system=False)
    add("errors", cmd_errors, "lista os códigos de erro do dispositivo e os códigos de saída da CLI (não abre a porta)", system=False)
    add("info", cmd_info, "versão do firmware e sistemas suportados", system=False)
    add("detect", cmd_detect, "detecta o cartucho")
    ip = add("identify", cmd_identify, "identifica arquivos já salvos pelo CRC32 na base de dados (--db), sem abrir a porta")
    ip.add_argument("files", nargs="+", help="ROMs a identificar")
    sp_ = add("search", cmd_search, "procura jogos pelo nome na base de dados (--db), sem abrir a porta", system=False)
    sp_.add_argument("query", help="palavras do nome (todas precisam aparecer)")
    sp_.add_argument("--limit", type=int, default=20, help="máximo de resultados (padrão 20)")
    dp = add("dump", cmd_dump, "lê a ROM", out=True)
    dp.add_argument("--mapper", type=int, default=0, help="NES/Famicom: número do mapper (0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 30, 33, 34, 48, 66, 67, 68, 69, 70, 71, 72, 73, 75, 78, 79, 86, 87, 92, 93, 94, 118, 140, 152, 180, 184, 206)")
    dp.add_argument("--prg", type=int, default=0, help="NES/Famicom: tamanho da PRG em KB (múltiplo de 16); Mega Drive e SNES ExHiROM: tamanho da ROM em KB (0 = pelo cabeçalho)")
    dp.add_argument("--chr", type=int, default=0, help="NES/Famicom: tamanho da CHR em KB (múltiplo de 8; 0 = CHR-RAM)")
    dp.add_argument("--game", help="NES/Famicom: nome do jogo na base NES 2.0 XML (--db); preenche --mapper, --prg e --chr que ficaram em 0")
    for sp in (add("save-read", cmd_save_read, "lê o save", out=True), add("save-write", cmd_save_write, "grava o save", inp=True)):
        sp.add_argument("--mapper", type=int, default=0, help="NES/Famicom: mapper do cartucho (1, 4, 5 ou 69 têm save com bateria)")
        sp.add_argument("--ram", type=int, default=0, help="NES/Famicom: RAM do save em KB (8, 16 ou 32; 16 e 32 só nos mappers 1 e 5; 0 = 8)")
        if sp.prog.endswith("save-write"):
            sp.add_argument("--yes", action="store_true", help="não pergunta antes de gravar (obrigatório fora de um terminal)")
            sp.add_argument("--no-backup", action="store_true", help="não lê o save atual antes de gravar")
            sp.add_argument("--backup-dir", default="~/oscr_backups", help="pasta do backup (padrão ~/oscr_backups)")
    rp = add("rom-write", cmd_rom_write, "grava a ROM em um cartucho de flash (apaga o chip)", inp=True)
    rp.set_defaults(system="nes")
    rp.add_argument("--chip", choices=sorted(RI.CHIPS), help="chip de flash (NES: padrão pelo mapper do cabeçalho, 30 = nesmaker, 0 = a29040b; SNES: snes-lorom ou snes-hirom, obrigatório)")
    rp.add_argument("--capacity", type=int, choices=RI.SNES_CAPACITIES_KB, help="SNES: capacidade do flash em KB (padrão: a menor em que a ROM cabe)")
    rp.add_argument("--yes", action="store_true", help="não pergunta antes de gravar (obrigatório fora de um terminal)")
    rp.add_argument("--no-verify", action="store_true", help="não lê a ROM de volta para conferir depois de gravar (padrão: confere)")
    rp.add_argument("--begin-timeout", type=float, default=90.0, help="segundos de espera pelo apagamento antes dos dados (padrão 90)")
    return ap


def _fail(args_json: bool, e: CliError) -> int:
    if args_json:
        err = {"kind": e.kind, "message": e.message, **e.extra}
        if e.hint:
            err["hint"] = e.hint
        print(json.dumps({"ok": False, "error": err}, ensure_ascii=False))
    else:
        print(f"erro: {e.message}" + (f". Dica: {e.hint}" if e.hint else ""), file=sys.stderr)
    return e.exit_code


def main(argv: list[str] | None = None) -> int:
    _Parser.json_mode = "--json" in (sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except CliError as e:
        return _fail(args.json, e)
    except P.DeviceError as e:
        kind, code = {3: ("no_cartridge", EXIT_NO_CART), 10: ("no_save", EXIT_ERROR)}.get(e.code, ("device_error", EXIT_ERROR))
        msg = P.ERRORS.get(e.code, "desconhecido") + (f" ({e.text})" if e.text else "")
        return _fail(args.json, CliError(kind, msg, code, P.ERROR_HINTS.get(e.code), device_code=e.code))
    except P.ProtocolError as e:
        return _fail(args.json, CliError("protocol", str(e)))
    except TimeoutError_ as e:
        return _fail(args.json, CliError("timeout", str(e), EXIT_ERROR, "o dispositivo parou de responder; confira o cabo e repita"))
    except OSError as e:                                  # porta que não abre, arquivo inexistente, disco cheio
        return _fail(args.json, CliError("io", str(e)))
    except KeyboardInterrupt:
        return _fail(args.json, CliError("interrupted", "interrompido", EXIT_INTERRUPTED))


if __name__ == "__main__":
    sys.exit(main())
