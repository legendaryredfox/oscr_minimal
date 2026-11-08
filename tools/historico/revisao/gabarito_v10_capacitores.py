#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gabarito 1:1 (A4 paisagem) para soldar capacitores de 100 nF no slot Mega Drive da 16_bits v1.0 ja encomendada:
vista de BAIXO (lado das soldas) da placa, com os pares A1-A2 e A31-A32 (GND e 5V do slot) e zoom 6:1 de cada par.
Os furos vem de hardware-v1.0/dumper.kicad_pcb (identicos aos do dumper-v1.0-jlcpcb.zip encomendado: conferido no .drl).
Uso (Python do venv do KiCad MCP): gabarito_v10_capacitores.py   -> docs/gabarito-v1.0-capacitores.{svg,pdf,png}"""
import subprocess
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[3]
PCB = ROOT / "boards/16_bits/hardware-v1.0/dumper.kicad_pcb"
OUT = ROOT / "boards/16_bits/docs"
mm = pcbnew.ToMM
b = pcbnew.LoadBoard(str(PCB))
bb = b.GetBoardEdgesBoundingBox()
X0, Y0, X1, Y1 = mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())
pads = []
for f in b.GetFootprints():
    for p in f.Pads():
        pads.append((f.GetReference(), p.GetNumber(), mm(p.GetX()), mm(p.GetY()), mm(p.GetSizeX()), mm(p.GetDrillSize().x), p.GetNetname()))
holes = [(mm(p.GetX()), mm(p.GetY()), mm(p.GetDrillSize().x)) for f in b.GetFootprints() for p in f.Pads() if p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH]
md = {n: (x, y) for r, n, x, y, s, d, net in pads if r == "MD1"}
ALVO = {"A1": "GND", "A2": "5V", "A31": "5V", "A32": "GND"}
COR = {"GND": "#111", "5V": "#d62828"}

W, H = 297, 210
S = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" viewBox="0 0 {W} {H}" font-family="DejaVu Sans, sans-serif">',
     '<rect width="297" height="210" fill="#fff"/>']
T = lambda x, y, t, s=3.2, w="normal", a="start", c="#111": f'<text x="{x}" y="{y}" font-size="{s}" font-weight="{w}" text-anchor="{a}" fill="{c}">{t}</text>'
S.append(T(10, 12, "Gabarito: 2 capacitores de 100 nF no slot Mega Drive (placa 16_bits v1.0)", 5.2, "bold"))
S.append(T(10, 18.5, "Imprima a 100% (sem ajustar à página): a régua abaixo tem que medir 50 mm. Vista de BAIXO, lado das soldas (espelhada em relação à vista de cima).", 2.8))

# ---------------------------------------------------------------- vista de baixo 1:1
OX, OY = 10, 28       # canto da placa na folha
def bx(x): return OX + (X1 - x)           # espelha: vista de baixo
def by(y): return OY + (y - Y0)
S.append(f'<rect x="{OX}" y="{OY}" width="{X1 - X0}" height="{Y1 - Y0}" fill="#e8f1e2" stroke="#222" stroke-width="0.4"/>')
for hx, hy, hd in holes:
    S.append(f'<circle cx="{bx(hx)}" cy="{by(hy)}" r="{hd / 2}" fill="#fff" stroke="#222" stroke-width="0.25"/>')
for r, n, x, y, s, d, net in pads:
    if r == "A1" and False:
        continue
    key = n if r == "MD1" else None
    if r == "MD1" and n in ALVO:
        continue
    S.append(f'<circle cx="{bx(x)}" cy="{by(y)}" r="{s / 2}" fill="#c9b458" stroke="#8a7a2a" stroke-width="0.12" opacity="0.75"/>')
    S.append(f'<circle cx="{bx(x)}" cy="{by(y)}" r="{d / 2}" fill="#fff"/>')
for n, k in ALVO.items():
    x, y = md[n]
    S.append(f'<circle cx="{bx(x)}" cy="{by(y)}" r="2.3" fill="none" stroke="{COR[k]}" stroke-width="0.6"/>')
    S.append(f'<circle cx="{bx(x)}" cy="{by(y)}" r="0.76" fill="#fff" stroke="{COR[k]}" stroke-width="0.3"/>')
# rotulos: um por par
S.append(T(bx(70), by(71), "vista de baixo (lado das soldas)", 2.8, "normal", "middle", "#777"))
for (n1, n2), nome in ((("A1", "A2"), "PAR 1 (A1+A2)"), (("A31", "A32"), "PAR 2 (A31+A32)")):
    xm = (bx(md[n1][0]) + bx(md[n2][0])) / 2
    ym = by(md[n1][1])
    S.append(f'<line x1="{xm}" y1="{ym - 2.6}" x2="{xm}" y2="{ym - 9}" stroke="#d62828" stroke-width="0.4"/>')
    S.append(T(xm, ym - 10.5, nome, 3.0, "bold", "middle", "#d62828"))
# regua de 50 mm
S.append(f'<line x1="{OX}" y1="{OY + 92}" x2="{OX + 50}" y2="{OY + 92}" stroke="#111" stroke-width="0.5"/>')
for k in range(0, 51, 10):
    S.append(f'<line x1="{OX + k}" y1="{OY + 91}" x2="{OX + k}" y2="{OY + 93}" stroke="#111" stroke-width="0.4"/>')
S.append(T(OX + 25, OY + 97, "régua: 50 mm", 2.6, "normal", "middle"))

# ---------------------------------------------------------------- zoom 6:1
Z = 6.0
def painel(px, py, w, h, cx, cy, titulo, par, flip=True):
    """painel w x h (mm na folha) centrado no ponto (cx, cy) da placa; escala Z; vista de baixo."""
    S.append(f'<rect x="{px}" y="{py}" width="{w}" height="{h}" fill="#fff" stroke="#222" stroke-width="0.3"/>')
    S.append(f'<clipPath id="c{px}"><rect x="{px}" y="{py}" width="{w}" height="{h}"/></clipPath><g clip-path="url(#c{px})">')
    def zx(x): return px + w / 2 + (cx - x) * Z
    def zy(y): return py + h / 2 + (y - cy) * Z
    S.append(f'<rect x="{px}" y="{py}" width="{w}" height="{h}" fill="#e8f1e2"/>')
    for n, (x, y) in md.items():
        k = ALVO.get(n)
        S.append(f'<circle cx="{zx(x)}" cy="{zy(y)}" r="{0.76 * Z}" fill="#c9b458" stroke="#8a7a2a" stroke-width="0.3" opacity="0.85"/>')
        S.append(f'<circle cx="{zx(x)}" cy="{zy(y)}" r="{0.38 * Z}" fill="#fff"/>')
        if k:
            S.append(f'<circle cx="{zx(x)}" cy="{zy(y)}" r="{0.76 * Z + 1}" fill="none" stroke="{COR[k]}" stroke-width="0.8"/>')
        S.append(T(zx(x), zy(y) + 1.0 * Z + 4.5 if y > 119 else zy(y) - 1.0 * Z - 2.2, n, 3.6, "bold" if k else "normal", "middle", COR[k] if k else "#666"))
    # capacitor SMD 1206 (3,2 x 1,6) deitado entre os pares, no lado das soldas
    (xa, ya), (xb, yb) = md[par[0]], md[par[1]]
    mx, my = (zx(xa) + zx(xb)) / 2, zy(ya)
    S.append(f'<rect x="{mx - 1.6 * Z}" y="{my - 0.8 * Z}" width="{3.2 * Z}" height="{1.6 * Z}" rx="0.6" fill="#b8742a" fill-opacity="0.78" stroke="#5a3510" stroke-width="0.5"/>')
    for sgn in (-1, 1):
        S.append(f'<rect x="{mx + sgn * 1.6 * Z - (0.5 * Z if sgn > 0 else 0)}" y="{my - 0.8 * Z}" width="{0.5 * Z}" height="{1.6 * Z}" fill="#cfcfcf" stroke="#555" stroke-width="0.3"/>')
    S.append(T(mx, my + 0.3, "100 nF", 3.4, "bold", "middle", "#fff"))
    S.append('</g>')
    S.append(T(px + 2, py - 2, titulo, 3.4, "bold"))

painel(125, 40, 78, 46, (md["A1"][0] + md["A2"][0]) / 2, 118.0, "Par 1: A1 (GND) + A2 (5V)", ("A1", "A2"))
painel(209, 40, 78, 46, (md["A31"][0] + md["A32"][0]) / 2, 118.0, "Par 2: A31 (5V) + A32 (GND)", ("A31", "A32"))
S.append(T(125, 93, "Escala 6:1, vista de baixo. Os pinos marcados são os da fileira A (a mais perto do meio da placa).", 2.6, "normal", "start", "#555"))
S.append(T(125, 97.5, "Visto de cima, o par 1 fica no extremo ESQUERDO do slot (onde está o \"A1\" do silk) e o par 2 no extremo direito.", 2.6, "normal", "start", "#555"))
txt = [
    ("Como fazer (cada par):", True),
    ("1. Capacitor cerâmico de 100 nF: SMD 1206 ou 0805, ou radial com as pernas", False),
    ("   cortadas curtas e dobradas.", False),
    ("2. Deite-o entre os dois pinos vizinhos, pelo lado das soldas (o de baixo).", False),
    ("3. Solde cada ponta na solda do pino do slot (ou no anel de cobre dele).", False),
    ("4. Cerâmico não tem polaridade: vale qualquer sentido.", False),
    ("5. Sem alimentar a placa, multímetro em continuidade: A2 e A31 apitam com", False),
    ("   o 5V dos headers do Mega; A1 e A32 com o GND. Entre A1 e A2 NÃO pode", False),
    ("   apitar (seria curto). Idem entre A31 e A32.", False),
    ("6. Corte as sobras rentes: sob o shield ficam o Mega e os headers.", False),
]
for i, (l, bold) in enumerate(txt):
    S.append(T(125, 106 + 5.0 * i, l, 3.0, "bold" if bold else "normal"))
S.append(T(125, 165, "O que isto compensa: na v1.0 o C3 fica a 10,7 mm do A2 e a 83 mm do A31; na v1.2 o C5 fica a", 2.7, "normal", "start", "#333"))
S.append(T(125, 169.5, "8,4 mm do A31 e o C6 a 5,5 mm do A2. Não é defeito medido: é reforço de desacoplamento (HW-MD-5).", 2.7, "normal", "start", "#333"))
S.append(T(125, 174, "Compare o CRC32 de 3 leituras do mesmo cartucho antes e depois; se já saem iguais, pode deixar sem.", 2.7, "normal", "start", "#333"))
S.append(T(10, 205, "Gerado por tools/historico/revisao/gabarito_v10_capacitores.py a partir de boards/16_bits/hardware-v1.0 (coordenadas conferidas no dumper-v1.0-jlcpcb.zip).", 2.2, "normal", "start", "#777"))
S.append("</svg>")
svg = OUT / "gabarito-v1.0-capacitores.svg"
svg.write_text("\n".join(S))
html = OUT / "_gabarito.html"
html.write_text(f'<!doctype html><meta charset="utf-8"><style>@page{{size:297mm 210mm;margin:0}}html,body{{margin:0}}img{{display:block;width:297mm;height:210mm}}</style><img src="{svg.name}">')
subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={OUT / 'gabarito-v1.0-capacitores.pdf'}", html.as_uri()], capture_output=True, timeout=120)
subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", f"--screenshot={OUT / 'gabarito-v1.0-capacitores.png'}", "--window-size=1123,794", svg.as_uri()], capture_output=True, timeout=120)
html.unlink()
print("ok")
