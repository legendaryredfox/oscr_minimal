#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Mapa dos pinos do slot SNES na 16_bits v1.0 encomendada (gerbers de 2026-11-03), vista de cima e vista de baixo.

Lê as fontes da placa encomendada direto do git (commit 7c38c77, boards/16_bits/hardware/dumper.kicad_pcb; cobre e
furos idênticos aos da placa física, que saiu do zip do commit 52e2f6d e só difere na serigrafia dos capacitores, D237)
e desenha cada pino do SNES com o número, mais as peças para orientação, com os nomes da serigrafia da placa física.
Orientação igual à das fotos do usuário: slots na vertical, PIC em cima à esquerda, Mega Drive à direita.
Pinos destacados com --destacar (padrão: os do autoteste da D236).

Uso (Python com pcbnew, por exemplo /usr/bin/python3), da raiz do repositório:
  python3 tools/boards/16_bits/mapa_pinos_snes_v10.py [--destacar 5,6,28,29,30,59,60,61] [-o saida.png]
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import pcbnew
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
COMMIT = "7c38c77"
CAMINHO = "boards/16_bits/hardware/dumper.kicad_pcb"
FONTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONTE_N = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
S = 14            # pixels por mm
MARGEM = 40
SILK_FISICA = {"C2": "C3", "C3": "C5", "C4": "C6"}   # serigrafia da placa física (52e2f6d) x fontes (7c38c77)
CORES = ["#d62828", "#f77f00", "#1d70b8", "#2a9d8f", "#7b2cbf"]


def carregar():
    with tempfile.TemporaryDirectory() as d:
        pcb = Path(d) / "dumper.kicad_pcb"
        pcb.write_bytes(subprocess.run(["git", "-C", str(ROOT), "show", f"{COMMIT}:{CAMINHO}"], check=True, capture_output=True).stdout)
        return pcbnew.LoadBoard(str(pcb))


def grupos(destacar):
    """Agrupa os pinos destacados em pares/trios vizinhos (mesma fileira, números seguidos) para dar uma cor a cada grupo."""
    out, atual = [], []
    for n in sorted(destacar):
        if atual and n == atual[-1] + 1 and (n <= 31) == (atual[-1] <= 31):
            atual.append(n)
        else:
            if atual:
                out.append(atual)
            atual = [n]
    if atual:
        out.append(atual)
    return {n: CORES[i % len(CORES)] for i, g in enumerate(out) for n in g}


def desenhar(b, destacar, espelhar, titulo):
    mm = pcbnew.ToMM
    bb = b.GetBoardEdgesBoundingBox()
    X0, Y0, X1, Y1 = mm(bb.GetX()), mm(bb.GetY()), mm(bb.GetRight()), mm(bb.GetBottom())
    W, H = int((Y1 - Y0) * S) + 2 * MARGEM, int((X1 - X0) * S) + 2 * MARGEM + 50   # girada 90° (como nas fotos)
    img = Image.new("RGB", (W, H), "white")
    g = ImageDraw.Draw(img)
    f_tit, f_ref, f_num, f_peq = (ImageFont.truetype(FONTE_N, 24), ImageFont.truetype(FONTE_N, 15),
                                  ImageFont.truetype(FONTE_N, 15), ImageFont.truetype(FONTE, 11))

    def px(x, y):   # gira 90° anti-horário: x da placa vira a vertical (x pequeno embaixo), y vira a horizontal
        xx = (Y1 - y) if espelhar else (y - Y0)
        return MARGEM + xx * S, MARGEM + 50 + (X1 - x) * S

    g.text((MARGEM, 12), titulo, fill="#111", font=f_tit)
    a, c = px(X0, Y0), px(X1, Y1)
    g.rectangle([min(a[0], c[0]), min(a[1], c[1]), max(a[0], c[0]), max(a[1], c[1])], fill="#e3efdc", outline="#333", width=2)
    cor = grupos(destacar)

    for f in b.GetFootprints():
        ref = f.GetReference()
        if ref.startswith(("FLG", "#")):
            continue
        pads = list(f.Pads())
        for p in pads:
            x, y = px(mm(p.GetX()), mm(p.GetY()))
            r = max(mm(p.GetSizeX()), 1.0) * S / 2
            if ref == "SNES1":
                continue
            g.ellipse([x - r, y - r, x + r, y + r], fill="#c9b458" if ref != "A1" else "#d8d0a8", outline="#8a7a2a")
        if ref not in ("SNES1", "A1", "MH1", "MH2", "MH3", "MH4") and pads:
            xs = [px(mm(p.GetX()), mm(p.GetY())) for p in pads]
            cx, cy = sum(v[0] for v in xs) / len(xs), min(v[1] for v in xs) - 22
            nome = {"MD1": "MEGA DRIVE", "U1": "Si5351", "U2": "PIC"}.get(ref, SILK_FISICA.get(ref, ref))
            g.text((cx, cy), nome, fill="#444", font=f_ref, anchor="mm")

    # header 2x18 do Mega e borda do Mega, para orientar
    a1 = [f for f in b.GetFootprints() if f.GetReference() == "A1"][0]
    d22 = [p for p in a1.Pads() if p.GetNumber() == "D22"][0]
    x, y = px(mm(d22.GetX()), mm(d22.GetY()))
    g.text((x, y - 24), "header 2x18 (D22...)", fill="#555", font=f_ref, anchor="mm")
    xu, yu = px(X0 + 3.0, 72.0)   # USB-B do Mega fica sob R1/R2 (D238)
    g.text((xu, yu + 34), "USB do Mega (embaixo de R1/R2)", fill="#b00", font=f_peq, anchor="mm")

    # pinos do SNES com número
    snes = [f for f in b.GetFootprints() if f.GetReference() == "SNES1"][0]
    for p in snes.Pads():
        n = int(p.GetNumber())
        x, y = px(mm(p.GetX()), mm(p.GetY()))
        net = p.GetNetname().lstrip("/")
        c = cor.get(n)
        r = 9 if c else 7
        fill = c or ("#222" if net == "GND" else "#c1121f" if "5V" in net else "#fff")
        g.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline="#111", width=2 if c else 1)
        fila_32_62 = mm(p.GetY()) < 89.4             # pinos 32-62 (y 86,9) e 1-31 (y 91,9)
        fora = -1 if (fila_32_62 != espelhar) else 1  # o número vai do lado de fora da coluna
        g.text((x + fora * 24, y), str(n), fill=c or "#111", font=f_num, anchor="mm")
        if net in ("GND", "+5V") and not c:
            g.text((x + fora * 58, y), "GND" if net == "GND" else "5V", fill="#555", font=f_peq, anchor="mm")
        if c:
            g.text((x + fora * 62, y), net, fill=c, font=f_peq, anchor="mm")
    xa, ya = px(mm(snes.GetPosition().x) + 42, 89.4)
    g.text((xa, ya), "S\nN\nE\nS", fill="#999", font=f_tit, anchor="mm", align="center")
    return img


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--destacar", default="5,6,28,29,30,59,60,61")
    ap.add_argument("-o", "--saida", default=str(ROOT / "boards/16_bits/docs/pinos-snes-v1.0.png"))
    a = ap.parse_args()
    destacar = [int(v) for v in a.destacar.split(",") if v.strip()]
    b = carregar()
    cima = desenhar(b, destacar, False, "VISTA DE CIMA (lado dos slots)")
    baixo = desenhar(b, destacar, True, "VISTA DE BAIXO (lado das soldas)")
    legenda = Image.new("RGB", (cima.width * 2, 90), "white")
    g = ImageDraw.Draw(legenda)
    f = ImageFont.truetype(FONTE, 16)
    g.text((MARGEM, 10), "Pinos destacados em cor (cada cor = um grupo de vizinhos a medir). Preto = GND, vermelho = 5V.", fill="#111", font=f)
    g.text((MARGEM, 34), "Vista de cima: coluna da esquerda 32 a 62, da direita 1 a 31 (na de baixo, o contrário). O pino n fica ao lado do n+31. Blocos: 1-4 | 5-27 | 28-31.", fill="#111", font=f)
    g.text((MARGEM, 58), f"Fonte: {CAMINHO} ({COMMIT}); cobre e furos iguais aos da placa física, nomes C3/C5/C6 da serigrafia dela (D237).", fill="#555", font=f)
    out = Image.new("RGB", (cima.width * 2, cima.height + legenda.height), "white")
    out.paste(cima, (0, 0))
    out.paste(baixo, (cima.width, 0))
    out.paste(legenda, (0, cima.height))
    out.save(a.saida)
    print(a.saida)


if __name__ == "__main__":
    main()
