# SPDX-License-Identifier: GPL-3.0-or-later
"""CLI do dumper: detect, dump, save-read, save-write, info, ports."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from . import protocol as P
from .client import Client, TimeoutError_
from .verify import verify_rom
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


def cmd_info(args) -> int:
    _c, t, info = connect(args)
    print(f"protocolo {info['proto']}  firmware {info['firmware']}  MOCK={'sim' if info['mock'] else 'não'}"
          f"  Si5351={'sim' if info['si5351'] else 'não'}  sistemas: {', '.join(info['systems']) or '-'}  payload máx. {info['max_payload']}")
    t.close()
    return 0


def cmd_detect(args) -> int:
    c, t, _ = connect(args)
    r = c.detect(system_id(args.system))
    status = {0: "cartucho detectado", 1: "nenhum cartucho", 2: "não suportado", 3: "erro de hardware"}
    print(f"{P.SYSTEM_BY_ID.get(r['system'], r['system'])}: {status.get(r['status'], r['status'])}")
    if r["status"] == 0:
        print(f"  título: {r['name'] or '(desconhecido)'}  ROM: {r['rom_size']} bytes  save: {r['save_size']} bytes")
    t.close()
    return 0 if r["status"] == 0 else 2


def _save_result(args, res: P.Frame | object, ext: str, default: str) -> int:
    path = out_path(args, ext, default)
    path.write_bytes(res.data)
    print(f"{path}  {len(res.data)} bytes  CRC32 {res.crc32:08X}")
    return 0


def cmd_dump(args) -> int:
    c, t, _ = connect(args)
    sid = system_id(args.system)
    res = c.dump_rom(sid, args.block, _progress("ROM"), args.mapper, args.prg, args.chr)
    t.close()
    rc = _save_result(args, res, P.SYSTEMS[args.system][1], f"rom_{args.system}")
    chk = verify_rom(sid, res.data)
    if chk.status != "na":
        print(("aviso: " if chk.status == "mismatch" else "") + str(chk))
    return rc


def cmd_save_read(args) -> int:
    c, t, _ = connect(args)
    res = c.read_save(system_id(args.system), args.block, _progress("save"), args.mapper)
    t.close()
    return _save_result(args, res, ".sav", f"save_{args.system}")


def cmd_save_write(args) -> int:
    data = Path(args.input).read_bytes()
    c, t, _ = connect(args)
    crc = c.write_save(system_id(args.system), data, args.block or P.DEFAULT_BLOCK, _progress("gravando"), args.mapper)
    t.close()
    print(f"save gravado: {len(data)} bytes  CRC32 {crc:08X}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="dumper", description="Dumper de cartuchos oscr_minimal")
    ap.add_argument("--version", action="version", version=f"dumper {__version__} (protocolo {P.PROTO_VERSION})")
    ap.add_argument("-p", "--port", help="porta serial (padrão: primeira ttyUSB/ttyACM/COM)")
    ap.add_argument("-b", "--baud", type=int, help="baud (padrão: 1000000, depois 115200)")
    ap.add_argument("--simulate", action="store_true", help="usa o simulador em memória (sem hardware)")
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
    dp.add_argument("--mapper", type=int, default=0, help="NES/Famicom: número do mapper (0, 1, 2, 3, 4, 7)")
    dp.add_argument("--prg", type=int, default=0, help="NES/Famicom: tamanho da PRG em KB (múltiplo de 16); Mega Drive: tamanho da ROM em KB (0 = pelo cabeçalho)")
    dp.add_argument("--chr", type=int, default=0, help="NES/Famicom: tamanho da CHR em KB (múltiplo de 8; 0 = CHR-RAM)")
    for sp in (add("save-read", cmd_save_read, "lê o save", out=True), add("save-write", cmd_save_write, "grava o save", inp=True)):
        sp.add_argument("--mapper", type=int, default=0, help="NES/Famicom: mapper do cartucho (1 ou 4 têm save com bateria)")
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
