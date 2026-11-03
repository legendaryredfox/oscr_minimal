#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Lê boards/16_bits/docs/pinmap.md e imprime {ref: {pino: net}} (JSON) e a lista de no-connect.
Usado para alimentar batch_connect do MCP do KiCad na fase 3."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
txt = (ROOT / "boards/16_bits/docs/pinmap.md").read_text()
REF = {"SNES": "SNES1", "NES": "NES1", "Famicom": "FC1", "Mega Drive": "MD1"}
conn, nc = {}, []
sec = None
for ln in txt.splitlines():
    m = re.match(r"## (SNES|NES|Famicom|Mega Drive) \(", ln)
    if m: sec = REF[m.group(1)]; conn[sec] = {}; continue
    if ln.startswith("## "): sec = None; continue
    if not sec or not ln.startswith("| ") or ln.startswith("| pino") or ln.startswith("|---"): continue
    c = [x.strip() for x in ln.strip("|").split("|")]
    pin, net = c[0], c[2]
    if net.startswith("NC"): nc.append((sec, pin)); continue
    if net.startswith("5V"): net = "+5V"
    elif net == "GND": pass
    elif net.startswith("CLK"): net = net.split()[0]
    elif net.startswith("CIC"): net = net.split(" →")[0].replace(" ", "_")
    conn[sec][pin] = net
# Mega
used = {n for s in conn.values() for n in s.values() if re.fullmatch(r"[AD]\d+", n)}
used |= {"D20", "D21", "D38", "D40", "D41", "D7"}
mega = {n: n for n in used}
for p in ("5V1", "5V3", "5V4"): mega[p] = "+5V"
for p in ("GND1", "GND2", "GND3", "GND5", "GND6"): mega[p] = "GND"
conn["A1"] = mega
allmega = [f"A{i}" for i in range(16)] + [f"D{i}" for i in range(54)] + ["5V1","5V3","5V4","GND1","GND2","GND3","GND5","GND6","3V3","VIN","RST1","IORF","AREF","SCL","SDA"]
nc += [("A1", p) for p in allmega if p not in mega]
conn["U1"] = {"1": "+5V", "2": "GND", "3": "D20", "4": "D21", "5": "CLK2", "6": "CLK1", "7": "CLK0"}
conn["U2"] = {"1": "+5V", "8": "GND", "2": "CLK2", "3": "D41", "4": "D40", "5": "CIC_RESET", "6": "CIC_DATA1", "7": "CIC_DATA0"}
conn["D1"] = {"2": "+5V", "1": "LED_K"}
conn["R1"] = {"1": "LED_K", "2": "D38"}
conn["R2"] = {"1": "+5V", "2": "D7"}
conn["C1"] = {"1": "+5V", "2": "GND"}
for c in ("C2", "C3", "C4", "C5", "C6"): conn[c] = {"1": "+5V", "2": "GND"}
conn["FLG1"] = {"1": "+5V"}; conn["FLG2"] = {"1": "GND"}
out = {"connections": conn, "no_connect": [{"componentRef": r, "pinName": p} for r, p in nc]}
json.dump(out, open(sys.argv[1] if len(sys.argv) > 1 else "/dev/stdout", "w"), indent=None, separators=(",", ":"))
print({k: len(v) for k, v in conn.items()}, "nc:", len(nc), file=sys.stderr)
