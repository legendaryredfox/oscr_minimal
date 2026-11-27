#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Orçamento de flash e RAM do firmware (F-0a e F-0e, docs/planos/pendencias.md).

  flash_budget.py check [--env SerialASCII ...] [--flash-max 95] [--ram-max 80]
      Compila cada ambiente (pio run) e falha se o flash passar de --flash-max % ou a RAM de --ram-max %
      (a pilha precisa de folga). Sem --env confere todos os ambientes do shield.
  flash_budget.py measure [--env SerialASCII] [--write arquivo.md]
      Quanto cada origem ocupa na imagem, somando o tamanho dos símbolos do firmware.elf (avr-nm -S -C) por namespace
      (núcleos do OSCR, infraestrutura, camada do dumper). Código que o compilador embutiu (LTO) conta no chamador, então o
      número de um núcleo é um piso. (Desligar um núcleo por vez no user.ini não serve: a camada src/dumper/ chama todos
      sem `#if`; o mapa do linker também não, porque o LTO apaga a origem por arquivo.)

O `pio` é procurado em ~/.platformio/penv/bin/pio. Sai com 1 se um limite foi passado.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FW = ROOT / "firmware/oscr"
PIO = Path.home() / ".platformio/penv/bin/pio"
USER_INI = FW / "user.ini"
ENVS = ("SerialASCII", "SerialASCII_Volt")
FLASH_RE = re.compile(r"Flash:.*\(used (\d+) bytes from (\d+) bytes\)")
RAM_RE = re.compile(r"RAM:.*\(used (\d+) bytes from (\d+) bytes\)")


def build(env: str):
    """-> (flash_usado, flash_total, ram_usada, ram_total) ou levanta RuntimeError com o fim da saída do pio."""
    r = subprocess.run([str(PIO), "run", "-e", env], cwd=FW, capture_output=True, text=True)
    out = r.stdout + r.stderr
    f, m = FLASH_RE.search(out), RAM_RE.search(out)
    if r.returncode != 0 or not f or not m:
        raise RuntimeError(f"pio run -e {env} falhou:\n" + "\n".join(out.splitlines()[-15:]))
    return int(f.group(1)), int(f.group(2)), int(m.group(1)), int(m.group(2))


def cmd_check(a) -> int:
    bad = 0
    for env in a.env or ENVS:
        fu, ft, ru, rt = build(env)
        fp, rp = 100 * fu / ft, 100 * ru / rt
        ok = fp <= a.flash_max and rp <= a.ram_max
        print(f"{'ok  ' if ok else 'ERRO'} {env}: flash {fu} B ({fp:.1f} %, limite {a.flash_max:g} %), "
              f"RAM {ru} B ({rp:.1f} %, limite {a.ram_max:g} %); sobram {ft - fu} B de flash")
        bad += not ok
    return 1 if bad else 0


NM = FW / "toolchain/avr-gcc/bin/avr-nm"
FLASH_TYPES = set("TtRrDdWwVv")     # código, constantes e .data (que também ocupa flash, copiado para a RAM no boot)
RAM_TYPES = set("BbDdCc")


def grupo(name: str) -> str:
    """Agrupa um símbolo (demangled) pela origem, usando o namespace: núcleo do OSCR, camada do dumper, infraestrutura do OSCR ou resto."""
    m = re.match(r"OSCR::Cores::(\w+)::", name)
    if m:
        return f"núcleo {m.group(1)}"
    m = re.match(r"OSCR::(\w+)::", name)
    if m:
        return f"OSCR::{m.group(1)}"
    if name.startswith("oscr::") or name.startswith("(anonymous namespace)::") or name.startswith("Dumper"):
        return "camada dumper (src/dumper)"
    return "libc, Arduino e outros"


def cmd_measure(a) -> int:
    f, m = None, None
    r = subprocess.run([str(PIO), "run", "-e", a.env], cwd=FW, capture_output=True, text=True)
    out = r.stdout + r.stderr
    f, m = FLASH_RE.search(out), RAM_RE.search(out)
    elf = FW / ".pio/build" / a.env / "firmware.elf"
    if r.returncode != 0 or not f or not m or not elf.exists():
        print("\n".join(out.splitlines()[-15:]), file=sys.stderr)
        return 1
    nm = subprocess.run([str(NM), "-S", "-C", str(elf)], capture_output=True, text=True)
    if nm.returncode != 0:
        print(nm.stderr, file=sys.stderr)
        return 1
    soma: dict[str, list[int]] = {}
    for ln in nm.stdout.splitlines():
        p = ln.split(" ", 3)
        if len(p) < 4:
            continue
        _, size, typ, name = p
        sz = int(size, 16)
        g = soma.setdefault(grupo(name), [0, 0])
        if typ in FLASH_TYPES:
            g[0] += sz
        if typ in RAM_TYPES:
            g[1] += sz
    tot_f, tot_r, flash_total, ram_total = int(f.group(1)), int(m.group(1)), int(f.group(2)), int(m.group(2))
    linhas = sorted(soma.items(), key=lambda kv: -kv[1][0])
    md = ["| Origem (namespace do símbolo) | Flash (B) | % do flash do Mega | RAM (B) |", "|---|---|---|---|"]
    for g, (fl, rm) in linhas:
        md.append(f"| {g} | {fl} | {100 * fl / flash_total:.1f} % | {rm} |")
    md.append(f"| soma dos símbolos | {sum(v[0] for v in soma.values())} | | {sum(v[1] for v in soma.values())} |")
    md.append(f"| **medido pelo `pio` ({a.env})** | **{tot_f}** | **{100 * tot_f / flash_total:.1f} %** | **{tot_r}** |")
    md.append(f"| total do Mega (flash sem bootloader; RAM) | {flash_total} | | {ram_total} |")
    print("\n".join(md))
    if a.write:
        Path(a.write).write_text("\n".join(md) + "\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("--env", action="append")
    c.add_argument("--flash-max", type=float, default=95.0)
    c.add_argument("--ram-max", type=float, default=80.0)
    m = sub.add_parser("measure")
    m.add_argument("--env", default="SerialASCII")
    m.add_argument("--write")
    a = ap.parse_args()
    if not PIO.exists():
        print(f"pio não encontrado em {PIO}", file=sys.stderr)
        return 2
    try:
        return cmd_check(a) if a.cmd == "check" else cmd_measure(a)
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
