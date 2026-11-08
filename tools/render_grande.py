#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Renders 3D grandes (renderizados em 4000 px de largura e recortados rente à placa, com margem de 3%), de cima e de baixo, de cada versão de uma placa (D128).
Saída: boards/<placa>/renders/<placa>-<versão>-cima.png e -baixo.png; boards/<placa>/render.png = a versão mais nova, de cima.
Pastas de hardware: hardware-<versão>/ para as congeladas, hardware/ para a mais nova (a última da lista).
Uso (python do venv do KiCad MCP, que tem pcbnew): python tools/render_grande.py <placa> <v1.0> [<v1.2> ...] """
import shutil, subprocess, sys
from PIL import Image
from pathlib import Path
import pcbnew
ROOT = Path(__file__).resolve().parents[1]
placa, versoes = sys.argv[1], sys.argv[2:]
W = 4000
out = ROOT / "boards" / placa / "renders"; out.mkdir(exist_ok=True)
for i, v in enumerate(versoes):
    hw = ROOT / "boards" / placa / ("hardware" if i == len(versoes) - 1 else f"hardware-{v}")
    pcb = str(hw / "dumper.kicad_pcb")
    bb = pcbnew.LoadBoard(pcb).GetBoardEdgesBoundingBox()
    h = int(W * bb.GetHeight() / bb.GetWidth()) + 400
    for lado, nome in (("top", "cima"), ("bottom", "baixo")):
        dst = out / f"{placa}-{v}-{nome}.png"
        subprocess.run(["kicad-cli", "pcb", "render", "--side", lado, "--quality", "high", "--background", "transparent", "--zoom", "1",
                        "--width", str(W), "--height", str(h), "-o", str(dst), pcb], check=True, capture_output=True)
        im = Image.open(dst).convert("RGBA"); box = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
        m = int(0.03 * (box[2] - box[0]))
        box = (max(box[0] - m, 0), max(box[1] - m, 0), min(box[2] + m, im.width), min(box[3] + m, im.height))
        im.crop(box).save(dst, optimize=True)
        print(dst.relative_to(ROOT), im.crop(box).size)
    if i == len(versoes) - 1:
        shutil.copyfile(out / f"{placa}-{v}-cima.png", ROOT / "boards" / placa / "render.png")
