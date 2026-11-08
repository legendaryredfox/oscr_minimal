#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gera boards/n64/docs/pinmap.md cruzando as 3 fontes do OSCR HW5 para o slot N64:
  1. pinout.ods            (colunas "N64 ROM" e "N64 EEP")
  2. esquemáticos KiCad    (n64_adapter e six_slot_adapter, ref. N64)
  3. firmware              (legacy/Cart_Reader/N64.ino)
Reaproveita as funções de tools/gen_pinmap.py. Uso: python3 tools/boards/n64/gen_pinmap.py (precisa de kicad-cli)
"""
import sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import gen_pinmap as g

OUT = ROOT / "boards/n64/docs/pinmap.md"
EEP_PINS = {"19", "21"}   # EEPROM_CLK e EEPROM_DATA usam a coluna "N64 EEP" do ods


def main():
    ods, col = g.load_ods()
    with tempfile.TemporaryDirectory() as tmp:
        six = g.nets_of(g.netlist(g.HW / "six_slot_adapter/six_slot_adapter.kicad_sch", tmp))
        ad = g.nets_of(g.netlist(g.HW / "n64_adapter/n64_adapter.kicad_sch", tmp))
    used = g.fw_ports("N64.ino")
    a_h = g.hdr_of(ad, "J1", ("J2", "J3"))
    s_h = g.hdr_of(six, "N64", ("J3", "J4"))
    hmap = {"J2": "J3", "J3": "J4"}   # adaptador -> six-slot

    rows, divs = [], []
    for net, nodes in ad.items():
        for r, p, fn in nodes:
            if r == "J1":
                rows.append((p, fn, net))
    rows.sort(key=lambda x: g.natkey(x[0]))

    L = []
    w = L.append
    w("# Mapa de pinos — slot N64 → pino do Arduino Mega 2560\n")
    w("**FONTE DA VERDADE.** Gerado por `tools/boards/n64/gen_pinmap.py` (não edite à mão). Mesmas fontes e convenções de `boards/16_and_8_bits/docs/pinmap.md`:\n")
    w("- `ods` = `pinout.ods` (colunas `N64 ROM` e `N64 EEP`)")
    w("- `sch` = `hardware/n64_adapter` (ref. `J1`)")
    w("- `six` = `hardware/six_slot_adapter` (ref. `N64`; mesma net no mesmo pino do header)")
    w("- `fw`  = porta/bit AVR usado em `legacy/Cart_Reader/N64.ino`\n")
    w("Marcas: `-` = fonte não cobre; `!` = fonte discorda. `fw` é checado só no nível da porta/bit.\n")
    w("**Tensão:** o cartucho N64 é de 3,3 V. Os pinos `VCC` (9, 17, 34, 42) vão a 3,3 V; o Mega continua com sinais de 5 V, como o OSCR HW5 faz no modo 3V e como esta família já faz no slot GBA (D3, D22). Nenhuma decisão nova de tensão foi tomada: **aguarda aprovação** (ver `README.md`).\n")
    w("Pinos `12V` (13 e 38): o adaptador do OSCR os deixa sem ligação (o six-slot liga ao +12V do HW5, que não existe aqui). Ficam sem ligação.\n")
    w("## N64 (ref. `J1` em `n64_adapter`, %d pinos)\n" % len(rows))
    w("| pino do slot | sinal | net / pino Arduino | porta/bit AVR | fonte |")
    w("|---|---|---|---|---|")
    for p, fn, net in rows:
        src = ["sch"]
        ard, avr = net, ""
        ocol = "N64 EEP" if p in EEP_PINS else "N64 ROM"
        if g.ARD_RE.match(net) and net in g.ARD2AVR:
            pt, bt = g.ARD2AVR[net]
            avr = f"P{pt}{bt}"
            o = ods.get(net, [""] * 99)[col[ocol]].strip()
            src.append("ods" if o else "!ods")
            if not o:
                divs.append((p, fn, net, f"ods sem sinal em '{ocol}'"))
            src.append("fw" if g.fw_hit(used, net) else "-fw")
        elif net.startswith("CLK"):
            o = ods.get(net, [""] * 99)[col[ocol]].strip()
            avr = "(Si5351)"
            ard = f"{net} (Si5351)"
            src.append("ods" if o else "-ods")
        elif net == "+3V3":
            ard, avr = "3V3 (regulador)", "-"
        elif net == "GND":
            avr = "-"
        elif net.startswith("unconnected"):
            ard, avr = "NC (sem ligação)", "-"
            w(f"| {p} | {fn} | {ard} | {avr} | sch |")
            continue
        if net in ("+3V3", "GND") or net.startswith("CLK") or g.ARD_RE.match(net):
            tr = {(hmap[r2], q) for r2, q in a_h.get(p, set())}
            sx = s_h.get(p, set())
            if net == "+3V3":   # six-slot chama de VCC; compara só presença
                sx_ok = True
            else:
                sx_ok = tr == sx
            src.append("six" if sx_ok else "!six")
            if not sx_ok:
                divs.append((p, fn, net, f"six-slot: header {sorted(sx)} vs adaptador {sorted(tr)}"))
        w(f"| {p} | {fn} | {ard} | {avr} | {' '.join(src)} |")

    w("\n## Fora do slot\n")
    w("| item | pino Arduino | fonte |\n|---|---|---|")
    w("| Si5351 CLK1 → EEPROM_CLK (pino 19) | CLK1 (2 MHz, `set_freq(200000000, CLK1)`) | sch + fw `N64.cpp` (`ENABLE_CLOCKGEN`) |")
    w("| EEPROM_DATA (pino 21) | D7 (PH4), pull-up de 1 kΩ para o 3,3 V (R1 do adaptador) | sch + ods |")
    w("| Si5351 SDA / SCL | D20 / D21 | igual às outras placas |")
    w("| Sem Si5351 no firmware | `PH1` (D16) vira saída em nível alto; o adaptador não leva D16 ao slot, então o EEPROM não é lido | fw `N64.cpp` |\n")
    w("Pinos do slot sem ligação no OSCR (mantidos): 12V (13, 38), NC (14, 39), CIC_to_PIF (18), L_AUDIO (24), PIF_to_CIC (43), R4300_CLK (44), NMI (45), Video_CLK (46), R_AUDIO (49).\n")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(L) + "\n")
    print(f"escrito {OUT}; divergências automáticas: {len(divs)}")
    for d in divs:
        print("  ", d)


main()
