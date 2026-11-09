#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gera o fab/PEDIDO.md de cada placa (D138, refeito em D139): como pedir na JLCPCB, tamanho e SHA-256 do zip de cada versão. A `16_bits` tem o
PEDIDO.md escrito à mão (histórico da v1.0 encomendada): aqui só a tabela dela é atualizada. Idempotente.
Uso (python com pcbnew, ex. /usr/bin/python3 -I), da raiz: python tools/troca/pedido138.py [placa ...]"""
import hashlib, json, re, sys
from pathlib import Path
import pcbnew
ROOT = Path(__file__).resolve().parents[2]
BOARDS = ROOT / "boards"
MARK = "## F1, J1 e seletor de tensão (D138)"
for b in (sys.argv[1:] or sorted(d.name for d in BOARDS.iterdir() if (d / "fab").is_dir() and (d / "fab/PEDIDO.md").exists())):
    vs = sorted(v.name.removeprefix("hardware-") for v in (BOARDS / b).glob("hardware-v*") if (BOARDS / b / "fab" / f"dumper-{v.name.removeprefix('hardware-')}-jlcpcb.zip").exists())
    if not vs:
        continue
    linhas, info = [], {}
    for v in vs:
        z = BOARDS / b / "fab" / f"dumper-{v}-jlcpcb.zip"
        brd = pcbnew.LoadBoard(str(BOARDS / b / f"hardware-{v}" / "dumper.kicad_pcb"))
        bb = brd.GetBoardEdgesBoundingBox()
        tam = f"{bb.GetWidth() / 1e6:.1f} × {bb.GetHeight() / 1e6:.1f} mm".replace(".", ",")
        sha = hashlib.sha256(z.read_bytes()).hexdigest()
        info[v] = (tam, sha, sum(1 for f in brd.GetFootprints() if f.GetReference().startswith("MH")))
        linhas.append(f"| {v} | `dumper-{v}-jlcpcb.zip` | {tam} | `{sha}` |")
    tabela = "| Versão | Arquivo | Tamanho | SHA-256 |\n|---|---|---|---|\n" + "\n".join(linhas) + "\n"
    p = BOARDS / b / "fab" / "PEDIDO.md"
    if b == "16_bits":
        s = p.read_text()
        s = re.sub(r"\| Versão \| Arquivo \| Tamanho \| SHA-256 \|\n\|---\|---\|---\|---\|\n(?:\|.*\n?)+", lambda _: tabela, s, count=1)
        p.write_text(s); print("PEDIDO de", b, "(tabela)"); continue
    v = vs[-1]; tam, sha, nholes = info[v]
    p.write_text(f"""# Pedido da placa {b} (JLCPCB)

Envie `dumper-{v}-jlcpcb.zip` (a versão mais nova; gerbers em `gerbers-{v}/`). **Nada encomendado.** O layout foi roteado por autoroteador e **ainda não foi revisado à mão no KiCad**: revise antes de pagar.

Conteúdo do zip (9 arquivos): `dumper-F_Cu.gtl`, `B_Cu.gbl`, `F_Mask.gts`, `B_Mask.gbs`, `F_Silkscreen.gto`, `B_Silkscreen.gbo`, `Edge_Cuts.gm1`, `PTH.drl`, `NPTH.drl`.

| Item | Valor esperado |
|---|---|
| Camadas | 2 |
| Dimensões | {tam} |
| Espessura / acabamento | 1,6 mm, HASL |
| Quantidade | 5 |
| Furos não metalizados | {nholes} (M3 de canto, 3,2 mm) |
| Furo mínimo | 0,3 mm (vias) |
| Demais | trilha/espaço mín. 0,2 mm; sem montagem; sem stencil |

Se a pré-visualização mostrar outra coisa, **não pague**.

{MARK}

O suporte do fusível F1 está em todas as versões (opcional; troca sem solda). O seletor 3,3 V/5 V, o jumper J1 e os resistores em série estão nas placas com slot de 5 V que têm v1.1. O 5V dos slots **não é cortado por software** (D139): troque o cartucho com o USB desligado. Circuito: `docs/referencia/seletor-tensao.md`. Os SHA-256 mudam a cada exportação; confira com `sha256sum`.

{tabela}
Verificação: `python3 tools/check_netlist.py --board {b}` (versão mais nova); ERC e DRC com `tools/troca/verifica.sh {b} {v}`.
""")
    print("PEDIDO de", b, v)
