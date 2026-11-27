#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Confere as tabelas dos adaptadores do Atari 5200 e do Atari 7800 (docs/planos/adaptadores.md#adaptador-a5200 e docs/planos/adaptadores.md#adaptador-a7800, D209) contra
1. o quadro "Cartridge Pinout" no começo de firmware/oscr/src/cores/Atari5200.cpp e Atari7800.cpp (pino do conector -> sinal);
2. o pinmap do slot SNES (pino do slot -> porta AVR);
3. as portas que o núcleo usa (A0-A7 PF, A8-A15 PK0-PK7, D0-D7 PC e os controles de cada sistema).
Sai com 1 se algo divergir."""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from adaptadores_doc import secao_doc  # noqa: E402
from check_adaptador_ngp import snes_pins  # noqa: E402

SYSTEMS = {
    "5200": dict(doc="a5200", core="firmware/oscr/src/cores/Atari5200.cpp", n_pins=36,
                 control={"/4000": "PH5", "/8000": "PH6"}, fixed={26: "+5V", 12: "GND", 13: "GND", 14: "GND", 23: "GND", 24: "GND", 25: "GND"},
                 free={11: "N/C", 28: "N/C", 18: "INTERLOCK", 36: "INTERLOCK", 30: "AUD"}, addr_bits=14),
    "7800": dict(doc="a7800", core="firmware/oscr/src/cores/Atari7800.cpp", n_pins=32,
                 control={"R/W": "PH6", "HALT": "PH0", "CLK": "-"}, fixed={13: "+5V", 14: "GND", 30: "GND"},
                 free={31: "IRQ", 18: "AUD"}, addr_bits=16),
}


def core_pinout(path: Path) -> dict[int, str]:
    """Lê as linhas `NOME -| nn mm |- NOME` do quadro: pino nn (esquerda) e mm (direita)."""
    out: dict[int, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[:60]:
        m = re.match(r"^\s*//(.*?)-\|\s*(\d+)\s+(\d+)\s*\|-\s*(\S+)", line)
        if not m:
            continue
        left, a, b, right = m.groups()
        left = left.strip()
        if left.endswith("4000-7FFF"):
            name = "/4000"
        elif left.endswith("8000-BFFF"):
            name = "/8000"
        else:
            name = left.split()[-1]
        out[int(a)] = name
        out[int(b)] = right
    return out


def expected_port(sig: str, control: dict[str, str]) -> str | None:
    if sig in control:
        return control[sig]
    m = re.fullmatch(r"A(\d+)", sig)
    if m:
        n = int(m.group(1))
        return f"PF{n}" if n < 8 else f"PK{n - 8}"
    m = re.fullmatch(r"D(\d)", sig)
    return f"PC{m.group(1)}" if m else None


def check(tag: str, cfg: dict) -> list[str]:
    errs: list[str] = []
    pins = snes_pins()
    cp = core_pinout(ROOT / cfg["core"])
    if len(cp) != cfg["n_pins"]:
        errs.append(f"{tag}: quadro do núcleo com {len(cp)} pinos (esperado {cfg['n_pins']})")
    rows = []
    for line in secao_doc(cfg["doc"]).read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\| ([AD]\d+|/4000|/8000|R/W|HALT|CLK) \| (\d+) \| (P[A-Z]\d|-) \| (\d+) \|$", line)
        if m:
            rows.append(m.groups())
    want_rows = (cfg["addr_bits"] + 8 + len(cfg["control"]))
    if len(rows) != want_rows:
        errs.append(f"{tag}: tabela com {len(rows)} linhas (esperado {want_rows})")
    used: list[int] = []
    sigs = set()
    for sig, slot, port, conn in rows:
        c = int(conn)
        used.append(c)
        sigs.add(sig)
        if cp.get(c) != sig:
            errs.append(f"{tag} {sig}: pino {c} do conector é '{cp.get(c)}' no quadro do núcleo")
        if expected_port(sig, cfg["control"]) != port:
            errs.append(f"{tag} {sig}: tabela diz {port}, o núcleo usa {expected_port(sig, cfg['control'])}")
        if port == "-":
            if int(slot) != 57:
                errs.append(f"{tag} {sig}: a saída CLK1 do Si5351 é o pino 57 do slot SNES (tabela diz {slot})")
        else:
            got = pins.get(int(slot), ("?", "?"))[1]
            if got != port:
                errs.append(f"{tag} {sig}: pino {slot} do slot SNES é {got} no pinmap (tabela diz {port})")
    for c, want in {**cfg["fixed"], **cfg["free"]}.items():
        used.append(c)
        if cp.get(c) != want and not (want == "+5V" and cp.get(c) in ("+5V", "5V")):
            errs.append(f"{tag}: pino {c} do conector é '{cp.get(c)}' no quadro (esperado '{want}')")
    if sorted(used) != list(range(1, cfg["n_pins"] + 1)):
        errs.append(f"{tag}: os {cfg['n_pins']} pinos do conector não aparecem todos uma vez (tabela mais pinos fixos e sem ligação): {sorted(set(range(1, cfg['n_pins'] + 1)) ^ set(used))}")
    for p, want in ((5, "GND"), (36, "GND"), (27, "5V (fixo)"), (58, "5V (fixo)")):
        if pins.get(p, ("?", "?"))[0] != want:
            errs.append(f"{tag}: pino {p} do slot SNES não é '{want}' no pinmap")
    n = cfg["addr_bits"]
    for i in range(n):
        if f"A{i}" not in sigs:
            errs.append(f"{tag}: falta A{i} na tabela")
    print(f"adaptador Atari {tag}:", "divergências" if errs else f"ok ({len(rows)} linhas, {len(cfg['fixed'])} pinos fixos e {len(cfg['free'])} sem ligação conferidos)")
    return errs


def main() -> int:
    errs: list[str] = []
    for tag, cfg in SYSTEMS.items():
        errs += check(tag, cfg)
    for e in errs:
        print("ERRO", e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
