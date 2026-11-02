#!/usr/bin/env python3
"""Calcula o posicionamento (fase 4) e imprime JSON para batch_move_components.
Quadro 'Mega': x_m para a direita, y_m para cima, origem no canto inferior esquerdo do Mega.
PCB: pcb_x = OX + x_m ; pcb_y = OY + (YTOP - y_m)."""
import json, math, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
PRETTY = ROOT / "hardware/lib/dumper.pretty"
OX, OY = 20.0, 20.0
YMIN, YMAX = -17.0, 91.0            # bordas da placa no quadro Mega
XMIN, XMAX = 0.0, 144.0
YTOP = YMAX
def P(xm, ym): return (round(OX + xm, 3), round(OY + (YTOP - ym), 3))

def pads(fp):
    s = (PRETTY / f"{fp}.kicad_mod").read_text()
    out = {}
    for m in re.finditer(r'\(pad "([^"]+)" thru_hole \w+\s*\(at ([-\d.]+) ([-\d.]+)', s):
        out[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    return out

SLOTS = {  # ref: (footprint, centro x_m, centro y_m)
    "MD1": ("MD_Slot", 51.0, -8.0),
    "FC1": ("FC_Slot", 48.0, 21.6),
    "NES1": ("NES_Slot", 51.0, 61.0),
    "SNES1": ("SNES_Slot", 53.0, 82.0),
}
moves, plan = {}, {}
# Mega: footprint com origem no canto inferior esquerdo (y local negativo = para cima)
moves["A1"] = {"x": P(0, 0)[0], "y": P(0, 0)[1], "rotation": 0}
slotpads = {}
for ref, (fp, cx, cy) in SLOTS.items():
    pd = pads(fp)
    xs = [v[0] for v in pd.values()]; ys = [v[1] for v in pd.values()]
    pxm, pym = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    # rot 90 (CCW na tela): (px,py) -> (py, -px)
    cxp, cyp = P(cx, cy)
    pos = (round(cxp - pym, 3), round(cyp + pxm, 3))
    moves[ref] = {"x": pos[0], "y": pos[1], "rotation": 90}
    slotpads[ref] = {n: (pos[0] + py, pos[1] - px) for n, (px, py) in pd.items()}
    plan[ref] = dict(center=(cx, cy), x_range=(round(cx + min(ys) - pym - 4, 2), round(cx + max(ys) - pym + 4, 2)))

def to_m(px, py):  # pcb -> quadro Mega
    return px - OX, YTOP - (py - OY)

# Capacitores de 100nF junto ao VCC de cada slot (pino 1 = +5V, pino 2 = GND, passo 5 mm em x)
VCC = {"SNES1": "27", "NES1": "36", "FC1": "30", "MD1": "A2"}
CAPS = {"C2": "SNES1", "C3": "NES1", "C4": "FC1", "C5": "MD1"}
# posição (x_m do pino 1, y_m) escolhida à mão: fora do corpo do slot, longe dos furos do Mega e das bordas
CAP_POS = {"C2": (80.5, 73.4), "C3": (6.0, 52.4), "C4": (84.83, 30.2), "C5": (5.0, 0.0)}
for c, s_ in CAPS.items():
    px, py = slotpads[s_][VCC[s_]]
    xm0, _ = to_m(px, py)
    xm, ym = CAP_POS[c]
    cp = P(xm, ym)
    moves[c] = {"x": cp[0], "y": cp[1], "rotation": 0}
    plan[c] = dict(near=f"{s_}.{VCC[s_]}", pad_x_m=round(xm0, 2), cap_x_m=xm, cap_y_m=ym)

# Faixa direita (x_m 102..144)
def put(ref, xm, ym, rot=0):
    p = P(xm, ym); moves[ref] = {"x": p[0], "y": p[1], "rotation": rot}
put("GBA1", 122.0, 19.0)       # slot GBA (SMD): pads em x_m 114.5..119.5, corpo até 137, blindagem até 141
put("U1", 104.5, 81.6)         # header Si5351 (centro em y_m 74); pino 1 (VIN) em cima; módulo ~23 x 33 mm à direita, y_m 57.5..90.5
put("D1", 102.5, 11.5)
put("C1", 103.0, 3.5)
put("R1", 102.5, 16.0, 90)     # resistores em pé (rot 90): pino 2 fica 10,16 mm acima do pino 1
put("R2", 106.5, 16.0, 90)
put("C6", 102.5, 29.5)
put("U2", 102.5, 42.0)         # soquete DIP-8
put("C9", 107.0, 46.5)         # 100 nF perto do VCC do GBA
put("U3", 102.5, 50.0)         # regulador 3,3 V (TO-92)
put("C7", 102.5, 54.0)         # entrada 1 uF
put("C8", 110.0, 54.0)         # saída 1 uF
json.dump({"moves": moves}, sys.stdout, separators=(",", ":"))
print(json.dumps(plan, indent=1), file=sys.stderr)
