#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gera docs/pinmap.md cruzando 3 fontes do OSCR HW5:
  1. pinout.ods            (vendor/oscr/legacy/pinout.ods)
  2. esquemáticos KiCad    (vendor/oscr/legacy/hardware/*)
  3. firmware              (vendor/oscr/legacy/Cart_Reader/*.ino)
Uso: python3 tools/gen_pinmap.py   (precisa de kicad-cli)
"""
import csv, collections, re, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEG = ROOT / "vendor/oscr/legacy"
HW = LEG / "hardware"
FW = LEG / "Cart_Reader"
OUT = ROOT / "docs/pinmap.md"

# --- Mega 2560: pino Arduino -> (porta, bit) -----------------------------------
ARD2AVR = {}
def _reg(port, names):
    for bit, n in enumerate(names):
        if n: ARD2AVR[n] = (port, bit)
_reg("A", [f"D{22+i}" for i in range(8)]); _reg("C", [f"D{37-i}" for i in range(8)])
_reg("F", [f"A{i}" for i in range(8)]);    _reg("K", [f"A{8+i}" for i in range(8)])
_reg("L", [f"D{49-i}" for i in range(8)])
_reg("B", ["D53","D52","D51","D50","D10","D11","D12","D13"])
_reg("D", ["D21","D20","D19","D18",None,None,None,"D38"])
_reg("E", ["D0","D1",None,"D5","D2","D3",None,None])
_reg("G", ["D41","D40","D39",None,None,"D4",None,None])
_reg("H", ["D17","D16",None,"D6","D7","D8","D9",None])
_reg("J", ["D15","D14",None,None,None,None,None,None])
AVR2ARD = {v: k for k, v in ARD2AVR.items()}

# --- fonte 1: ods ------------------------------------------------------------
def load_ods():
    ns = {"t": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
          "x": "urn:oasis:names:tc:opendocument:xmlns:text:1.0"}
    T = "{%s}" % ns["t"]
    root = ET.fromstring(zipfile.ZipFile(LEG / "pinout.ods").read("content.xml"))
    tb = next(root.iter(T + "table"))
    rows = []
    for r in tb.iter(T + "table-row"):
        row = []
        for c in r:
            if c.tag not in (T + "table-cell", T + "covered-table-cell"): continue
            txt = "".join("".join(p.itertext()) for p in c.findall("x:p", ns))
            row += [txt] * min(int(c.get(T + "number-columns-repeated", "1")), 30)
        rows.append(row)
    hi = next(i for i, r in enumerate(rows) if r and r[0] == "Arduino")
    hdr = rows[hi]; col = {h: n for n, h in enumerate(hdr)}
    ods = {}
    for r in rows[hi + 1:]:
        r = r + [""] * (len(hdr) - len(r))
        m = re.match(r"(A\d+|D\d+|CLK\d)\b", r[0])
        if m: ods[m.group(1)] = r
    return ods, col

# --- fonte 2: netlists ---------------------------------------------------------
def netlist(sch, tmp):
    out = Path(tmp) / (Path(sch).stem + ".xml")
    p = subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadxml",
                        "-o", str(out), str(sch)], capture_output=True, text=True)
    if not out.exists():
        sys.exit(f"kicad-cli falhou em {sch}: {p.stderr}")
    return ET.parse(out).getroot()

def nets_of(root):
    d = {}
    for n in root.find("nets"):
        d[n.get("name")] = [(x.get("ref"), x.get("pin"), x.get("pinfunction") or "")
                            for x in n.findall("node")]
    return d

# --- fonte 3: firmware ---------------------------------------------------------
def fw_ports(fname):
    used = collections.defaultdict(set)
    for ln in open(FW / fname, errors="ignore"):
        code = ln.split("//")[0]
        for m in re.finditer(r"\b(PORT|DDR|PIN)([A-L])\b", code):
            p = m.group(2)
            bits = {int(b) for b in re.findall(r"1\s*<<\s*(\d+)", code)}
            if bits: used[p] |= bits
            elif re.search(r"=\s*(0x[0-9A-Fa-f]+|\d+|\w+)", code): used[p].add("whole")
    return used

def fw_hit(used, ard):
    if ard not in ARD2AVR: return False
    p, b = ARD2AVR[ard]
    return "whole" in used[p] or b in used[p]

SYSTEMS = [  # nome, schematic, slot ref, six-slot ref, coluna ods, ino
    ("SNES",     "snes_adapter",     "J3", "SNES1", "SNES",      "SNES.ino"),
    ("NES",      "nes_adapter",      "U1", "NES1",  "NES",       "NES.ino"),
    ("Famicom",  "famicom_adapter",  "U1", "FC1",   "NES",       "NES.ino"),
    ("Mega Drive","megadrive_adapter","U1","MD1",   "Megadrive", "MD.ino"),
    ("GBA",      "main_pcb_hw5",     "J10", "",     "GBA",       "GBA.ino"),   # só existe na placa principal do HW5
]
HDR_MAP = {"J1": "J3", "J2": "J4"}  # adaptador -> placa principal / six-slot
ARD_RE = re.compile(r"^(A\d+|D\d+)$")

def natkey(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]

def hdr_of(nets, slot, hdrs):
    """slot pin -> conjunto de pinos de header (ref,pin) na mesma net"""
    m = collections.defaultdict(set)
    for name, nodes in nets.items():
        hp = {(r, p) for r, p, _ in nodes if r in hdrs}
        for r, p, _ in nodes:
            if r == slot: m[p] |= hp
    return m

def main():
    ods, col = load_ods()
    # confere tabela porta/bit contra a coluna ATMega2560 do ods
    bad = [(k, ods[k][col["ATMega2560"]]) for k in ARD2AVR
           if k in ods and ods[k][col["ATMega2560"]] != f"P{ARD2AVR[k][0]}{ARD2AVR[k][1]}"]
    if bad: sys.exit(f"tabela AVR diverge do ods: {bad}")
    with tempfile.TemporaryDirectory() as tmp:
        six = nets_of(netlist(HW / "six_slot_adapter/six_slot_adapter.kicad_sch", tmp))
        main_n = nets_of(netlist(HW / "main_pcb_hw5/main_pcb_hw5.kicad_sch", tmp))
        pic = nets_of(netlist(HW / "cic_adapter/PIC_adapter.kicad_sch", tmp))
        ad = {s[1]: nets_of(netlist(HW / f"{s[1]}/{s[1]}.kicad_sch", tmp)) for s in SYSTEMS}

    L = []
    w = L.append
    w("# Mapa de pinos — slot do cartucho → pino do Arduino Mega 2560\n")
    w("**FONTE DA VERDADE.** Gerado por `tools/gen_pinmap.py` (não edite à mão; edite o script ou `docs/decisoes.md`).\n")
    w("Cruza três fontes do OSCR HW5 (repositório `sanni/cartreader`, clone em `vendor/oscr/legacy/`):\n")
    w("- `ods` = `pinout.ods` (coluna do sistema; Famicom usa a coluna NES)")
    w("- `sch` = esquemático KiCad do adaptador (`hardware/<sistema>_adapter`) + `main_pcb_hw5`")
    w("- `six` = `hardware/six_slot_adapter` (mesma net no mesmo pino do header; não existe para o GBA)")
    w("- `fw`  = porta/bit AVR usado no `.ino` do sistema (`SNES.ino`, `NES.ino`, `MD.ino`, `GBA.ino`)\n")
    w("Convenção: a coluna **Arduino** é o nome da net no HW5 (`A0..A15`, `D2..D53`, `CLK0..2`). Na placa HW5, "
      "cada net vai do Mega ao header J3/J4 (pino de mesmo número no adaptador) e daí ao slot. "
      "Neste projeto o slot liga direto ao pino do Mega.\n")
    w("`-fw` no Mega Drive para `D2/D3/D5` (/YS, /CAS2, EDCLK): `MD.ino` não toca esses bits (deixa-os como entrada); o HW5 os liga mesmo assim e o `ods` os lista. Mantidos.\n")
    w("Marcas: `ods`/`sch`/`six`/`fw` = fonte concorda; `-` = fonte não cobre (ver nota); "
      "`!` = fonte discorda (ver `docs/decisoes.md`). `fw` é checado só no nível da porta/bit "
      "(o firmware não usa nomes de sinal).\n")
    w("Pinos do Mega **não usados** por nenhum slot: `D0`/`D1` (serial USB; o HW5 leva ao header mas os adaptadores deixam sem ligação), "
      "`D10..D13`, `D18`, `D19`, `D39`, `D50..D53`. `D0`/`D1` nunca podem ir a um slot.\n")

    divs = []
    for name, f, slot, six_ref, ocol, ino in SYSTEMS:
        nets = ad[f]
        used = fw_ports(ino)
        a_h = hdr_of(nets, slot, ("J1", "J2"))
        s_h = hdr_of(six, six_ref, ("J3", "J4")) if six_ref else {}
        rows = []
        for net, nodes in nets.items():
            for r, p, fn in nodes:
                if r != slot: continue
                if name == "GBA":
                    p = {"33": "SHIELD_3", "34": "SHIELD_4"}.get(p, p)
                    if p == "31":      # AUD_IRQ/D7: ver docs/decisoes.md D22 (fica sem ligação)
                        rows.append((p, fn, "unconnected-GBA31")); continue
                    if p == "1": net = "+3V3"
                    if p in ("SHIELD_3", "SHIELD_4"): net = "GND"
                rows.append((p, fn, net))
        rows.sort(key=lambda x: natkey(x[0]))
        w(f"\n## {name} (ref. `{slot}` em `{f}`, {len(rows)} pinos)\n")
        w("| pino do slot | sinal | net / pino Arduino | porta/bit AVR | fonte |")
        w("|---|---|---|---|---|")
        for p, fn, net in rows:
            src = ["sch"]
            ard = net; avr = ""
            if ARD_RE.match(net) and net in ARD2AVR:
                pt, bt = ARD2AVR[net]; avr = f"P{pt}{bt}"
                o = ods.get(net, [""] * 99)[col[ocol]].strip()
                src.append("ods" if o else "!ods")
                if not o: divs.append((name, p, fn, net, "ods sem sinal nesta coluna"))
                src.append("fw" if fw_hit(used, net) else "-fw")
            elif net.startswith("CLK"):
                o = ods.get(net, [""] * 99)[col[ocol]].strip()
                avr = "(Si5351)"
                src.append("ods" if o else "-ods")
                ard = f"{net} (Si5351)"
            elif net == "+3V3":
                ard = "3V3 (regulador U3)"; avr = "-"
            elif net in ("VCC", "+5V"):
                ard = "5V (fixo)"; avr = "-"
            elif net == "GND":
                avr = "-"
            elif net.startswith("CIC"):
                ard = f"{net} → PIC12F629"; avr = "-"
            elif net == "+3V3":
                continue
            elif net.startswith("unconnected"):
                ard = "NC (sem ligação)"; avr = "-"
                w(f"| {p} | {fn} | {ard} | {avr} | sch |")
                continue
            # six-slot
            if six_ref and (net in ("VCC", "+5V", "GND") or net.startswith("CIC") or net.startswith("CLK") or ARD_RE.match(net)):
                tr = {(HDR_MAP[r], q) for r, q in a_h.get(p, set())} - {("J3", "3")}  # J3.3 = 12V só do N64 no six-slot
                src.append("six" if tr == s_h.get(p, set()) else "!six")
                if tr != s_h.get(p, set()):
                    divs.append((name, p, fn, net, f"six-slot: header {sorted(s_h.get(p,set()))} vs adaptador {sorted(tr)}"))
            w(f"| {p} | {fn} | {ard} | {avr} | {' '.join(src)} |")
    w("\n## Placa principal — o que o HW5 liga além dos slots (referência)\n")
    w("| item | pino Arduino | fonte |\n|---|---|---|")
    w("| Si5351 SDA / SCL | D20 (PD1) / D21 (PD0) | sch main J7.3/J7.4 + ods |")
    w("| Si5351 CLK0 / CLK1 / CLK2 | 3 saídas do Si5351 (não vão ao Mega); CLK0→SNES 21.477MHz (pino 1), CLK1→SNES CPU clock (57), CLK2→CIC clock (56) e PIC pino 2 | sch |")
    w("| LED de status (cátodo via 220Ω, ânodo em VCC; **ativo em nível baixo**) | D38 (PD7) | sch main D1/R1 + fw `statusLED()` |")
    w("| Pull-up 1kΩ VCC→D7 (linha /IRQ do SNES) | D7 (PH4) | sch six_slot R1 + ods `D7 (1K Pullup)` |")
    w("| Reset do Mega | RESET → J4.35 (adaptadores não usam) | sch main |\n")
    w("## CIC SNES (PIC12F629 DIP-8) — `cic_adapter/PIC_adapter`\n")
    w("| pino do PIC | net | liga em | fonte |\n|---|---|---|---|")
    pm = {}
    for net, nodes in pic.items():
        for r, p, fn in nodes:
            if r == "PIC12F629": pm[p] = net
    tgt = {"VCC": "5V", "GND": "GND", "CLK2": "Si5351 CLK2 (mesma net do SNES pino 56)",
           "D40": "Mega D40 (PG1) — Reset In", "D41": "Mega D41 (PG0) — Reset Out Host",
           "CIC RESET": "SNES slot pino 25 (CIC_in_data p7)",
           "CIC DATA 1": "SNES slot pino 24 (CIC_out_data p1)",
           "CIC DATA 0": "SNES slot pino 55 (CIC_data_out p2)"}
    for p in sorted(pm, key=int):
        w(f"| {p} | {pm[p]} | {tgt.get(pm[p], '?')} | sch(PIC_adapter + six_slot JCIC1) + ods(snesCIC) + fw SNES.ino (PG0/PG1) |")
    w("\nNota: o PIC12F629 usa a pinagem do `JCIC1` (1=VCC, 2=CLK2, 3=D41, 4=D40, 5=RESET, 6=DATA1, 7=DATA0, 8=GND).\n")
    w("## Pinos do slot sem ligação no OSCR (mantidos sem ligação)\n")
    w("- SNES: pino 31 (Left Audio), pino 62 (Right Audio).")
    w("- NES: `EXP_0..EXP_9` (16-20, 51-55), `Security1..4` (70, 71, 34, 35).")
    w("- Famicom/Mega Drive: ver pinos ausentes na tabela de cada sistema.\n")
    OUT.write_text("\n".join(L) + "\n")
    print(f"escrito {OUT}; divergências automáticas: {len(divs)}")
    for d in divs: print("  ", d)

main()
