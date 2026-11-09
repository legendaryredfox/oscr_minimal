#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""D138: acrescenta ao fab/PEDIDO.md de cada placa a lista dos zips refeitos com F1/J1/seletor (tamanho e SHA-256). Idempotente.
Uso (python do venv do KiCad, que tem pcbnew), da raiz: python tools/troca/pedido138.py [placa ...]"""
import hashlib, json, re, sys
from pathlib import Path
import pcbnew
ROOT = Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT / "tools/troca/boards.json").read_text())
VERS = {"16_bits": ["v1.2", "v1.3"], "16_and_8_bits": ["v1.0"]}
MARK = "## D138 — F1, J1 e seletor de tensão"
for b in (sys.argv[1:] or sorted(CFG)):
    vs = VERS.get(b, ["v1.0", CFG[b]["version"]])
    linhas = []
    for v in vs:
        z = ROOT / "boards" / b / "fab" / f"dumper-{v}-jlcpcb.zip"
        if not z.exists():
            continue
        bb = pcbnew.LoadBoard(str(ROOT / "boards" / b / f"hardware-{v}" / "dumper.kicad_pcb")).GetBoardEdgesBoundingBox()
        tam = f"{bb.GetWidth() / 1e6:.1f} × {bb.GetHeight() / 1e6:.1f} mm".replace(".", ",")
        linhas.append(f"| {v} | `dumper-{v}-jlcpcb.zip` | {tam} | `{hashlib.sha256(z.read_bytes()).hexdigest()}` |")
    p = ROOT / "boards" / b / "fab" / "PEDIDO.md"
    if not p.exists() or not linhas:
        continue
    s = p.read_text()
    if MARK in s:
        s = s[:s.index(MARK)].rstrip("\n") + "\n"
    s += f"""
{MARK} (2026-11-08)

As versões abaixo foram **refeitas** com o PTC F1 (opcional; sem ele, fio ou ponte de solda nos furos) e, nas v1.1 com slot de 5 V, o seletor 3,3 V/5 V, o jumper J1 e os resistores em série (D138). Os tamanhos e SHA-256 mais acima, de antes do D138, **não valem mais**; valem estes (mude de zip só depois de rever o layout no KiCad: roteamento por autoroteador, nada encomendado):

| Versão | Arquivo | Tamanho | SHA-256 |
|---|---|---|---|
""" + "\n".join(linhas) + "\n"
    p.write_text(s)
    print("PEDIDO de", b, len(linhas), "zip(s)")
