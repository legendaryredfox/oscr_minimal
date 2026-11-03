# SPDX-License-Identifier: GPL-3.0-or-later
"""CLI do dumper: detect, dump, save-read, save-write, info, ports."""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from . import __version__
from . import protocol as P
from .client import Client, TimeoutError_
from .verify import eeprom_is_4k, gba_save_hint, verify_rom
from .transport import SerialTransport, Transport

BAUDS = (1_000_000, 115_200)


def _progress(label: str):
    state = {"last": -1}

    def cb(done: int, total: int) -> None:
        if not sys.stderr.isatty() or total == 0:
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
        raise SystemExit("nenhuma porta serial encontrada; use --port (no Linux: grupo dialout)")
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
        t = SerialTransport(port, b)
        c = Client(t, timeout=0.5)
        try:
            return c, t, c.info()
        except TimeoutError_ as e:
            last = e
            t.close()
    raise SystemExit(f"sem resposta do dispositivo em {port} ({', '.join(map(str, bauds))} baud): {last}")


def system_id(name: str) -> int:
    if name not in P.SYSTEMS:
        raise SystemExit(f"sistema desconhecido: {name}. Use: {', '.join(P.SYSTEMS)}")
    return P.SYSTEMS[name][0]


def out_path(args, ext: str, default: str) -> Path:
    p = Path(args.output) if args.output else Path(default)
    if p.suffix == "":
        p = p.with_suffix(ext)
    return p


def cmd_ports(args) -> int:
    for p in list_ports():
        print(p)
    return 0


def emit(args, obj: dict, lines: list[str]) -> None:
    """Saída do comando: uma linha de JSON com --json, senão o texto para humanos."""
    if args.json:
        print(json.dumps(obj, ensure_ascii=False))
    else:
        for l in lines:
            print(l)


def safe_name(title: str, default: str) -> str:
    n = re.sub(r"[^A-Za-z0-9._ -]+", "_", title or "").strip(" ._")
    return n or default


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
    emit(args, r, lines)
    t.close()
    return 0 if r["status"] == 0 else 2


def _save_result(args, res: P.Frame | object, ext: str, default: str, extra: dict | None = None, notes: list[str] | None = None) -> int:
    path = out_path(args, ext, default)
    path.write_bytes(res.data)
    obj = {"file": str(path), "bytes": len(res.data), "crc32": f"{res.crc32:08X}"}
    obj.update(extra or {})
    emit(args, obj, [f"{path}  {len(res.data)} bytes  CRC32 {res.crc32:08X}"] + (notes or []))
    return 0


def cmd_dump(args) -> int:
    c, t, _ = connect(args)
    sid = system_id(args.system)
    title = ""
    if not args.output:                                   # sem -o: nome do arquivo pelo título do cartucho
        try:
            title = c.detect(sid).get("name", "")
        except (P.DeviceError, P.ProtocolError, TimeoutError_):
            title = ""
    res = c.dump_rom(sid, args.block, _progress("ROM"), args.mapper, args.prg, args.chr)
    t.close()
    ext = P.SYSTEMS[args.system][1]
    if sid == 6 and len(res.data) > 0x143 and res.data[0x143] & 0x80:
        ext = ".gbc"                                      # cabeçalho com a flag de Game Boy Color
    chk = verify_rom(sid, res.data)
    notes = []
    extra: dict = {"checksum": chk.status}
    if chk.status != "na":
        notes.append(("aviso: " if chk.status == "mismatch" else "") + str(chk))
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


def cmd_save_read(args) -> int:
    c, t, _ = connect(args)
    res = c.read_save(system_id(args.system), args.block, _progress("save"), args.mapper, args.ram)
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
            raise SystemExit("recusado: gravar o save sobrescreve a memória do cartucho. Em modo não interativo confirme com --yes.")
        ans = input(f"Gravar {len(data)} bytes no save de {args.system}? Isso sobrescreve o save do cartucho. Continuar? [s/N] ")
        if ans.strip().lower() not in ("s", "sim", "y", "yes"):
            print("cancelado")
            return 1
    c, t, _ = connect(args)
    try:
        extra: dict = {}
        if not args.no_backup:                            # backup do save atual antes de gravar
            cur = c.read_save(sid, args.block, _progress("backup"), args.mapper, args.ram)
            bdir = Path(args.backup_dir).expanduser()
            bdir.mkdir(parents=True, exist_ok=True)
            bpath = bdir / f"{args.system}_{time.strftime('%Y%m%d-%H%M%S')}.sav"
            bpath.write_bytes(cur.data)
            extra["backup"] = str(bpath)
            if not args.json:
                print(f"backup do save atual: {bpath}  CRC32 {cur.crc32:08X}")
        crc = c.write_save(sid, data, args.block or P.DEFAULT_BLOCK, _progress("gravando"), args.mapper, args.ram)
    finally:
        t.close()
    extra.update({"bytes": len(data), "crc32": f"{crc:08X}"})
    emit(args, extra, [f"save gravado: {len(data)} bytes  CRC32 {crc:08X}"])
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="dumper", description="Dumper de cartuchos oscr_minimal")
    ap.add_argument("--version", action="version", version=f"dumper {__version__} (protocolo {P.PROTO_VERSION})")
    ap.add_argument("-p", "--port", help="porta serial (padrão: primeira ttyUSB/ttyACM/COM)")
    ap.add_argument("-b", "--baud", type=int, help="baud (padrão: 1000000, depois 115200)")
    ap.add_argument("--simulate", action="store_true", help="usa o simulador em memória (sem hardware)")
    ap.add_argument("--json", action="store_true", help="saída em JSON (uma linha), para scripts")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_, system=True, out=False, inp=False):
        sp = sub.add_parser(name, help=help_)
        sp.set_defaults(fn=fn)
        if system:
            sp.add_argument("-s", "--system", default="mock", choices=sorted(P.SYSTEMS), help="sistema (padrão: mock)")
        if out:
            sp.add_argument("-o", "--output", help="arquivo de saída (a extensão certa é acrescentada)")
        if inp:
            sp.add_argument("-i", "--input", required=True, help="arquivo de save para gravar")
        if out or inp:
            sp.add_argument("--block", type=int, default=0, help="tamanho do bloco (padrão 512)")
        return sp

    add("ports", cmd_ports, "lista as portas seriais", system=False)
    add("info", cmd_info, "versão do firmware e sistemas suportados", system=False)
    add("detect", cmd_detect, "detecta o cartucho")
    dp = add("dump", cmd_dump, "lê a ROM", out=True)
    dp.add_argument("--mapper", type=int, default=0, help="NES/Famicom: número do mapper (0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 33, 48, 66, 69, 70, 71, 75, 78, 79, 87, 118, 206)")
    dp.add_argument("--prg", type=int, default=0, help="NES/Famicom: tamanho da PRG em KB (múltiplo de 16); Mega Drive e SNES ExHiROM: tamanho da ROM em KB (0 = pelo cabeçalho)")
    dp.add_argument("--chr", type=int, default=0, help="NES/Famicom: tamanho da CHR em KB (múltiplo de 8; 0 = CHR-RAM)")
    for sp in (add("save-read", cmd_save_read, "lê o save", out=True), add("save-write", cmd_save_write, "grava o save", inp=True)):
        sp.add_argument("--mapper", type=int, default=0, help="NES/Famicom: mapper do cartucho (1, 4, 5 ou 69 têm save com bateria)")
        sp.add_argument("--ram", type=int, default=0, help="NES/Famicom: RAM do save em KB (8, 16 ou 32; 16 e 32 só nos mappers 1 e 5; 0 = 8)")
        if sp.prog.endswith("save-write"):
            sp.add_argument("--yes", action="store_true", help="não pergunta antes de gravar (obrigatório fora de um terminal)")
            sp.add_argument("--no-backup", action="store_true", help="não lê o save atual antes de gravar")
            sp.add_argument("--backup-dir", default="~/oscr_backups", help="pasta do backup (padrão ~/oscr_backups)")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except (P.DeviceError, P.ProtocolError, TimeoutError_) as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
