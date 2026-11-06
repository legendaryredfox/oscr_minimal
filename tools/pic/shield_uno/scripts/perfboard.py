#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-SA-2.5
"""Layout para placa perfurada (furos a 2,54 mm): verifica as ligacoes e desenha docs/perfboard.svg.

O layout e dado em furos (coluna x, linha y; x e y comecam em 0). Cada fio e uma lista de furos: todos os furos
de um mesmo fio ficam na mesma net; os fios sao isolados, entao um fio pode passar por cima de furos que nao estao
na lista. A verificacao junta pads e fios e compara com a tabela de ligacoes do circuito (a mesma da PCB, sem os pontos
de teste e sem o ICSP): nets certas, nenhum curto entre nets.

Uso: python3 tools/pic/shield_uno/scripts/perfboard.py        (gera docs/perfboard.svg e docs/perfboard.md)
"""
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"

# ---- pecas: ref -> (descricao, {pino: (x, y)})
PECAS = {
    "J3": ("Barra de 6 pinos macho (vai ao Uno por cabos Dupont)",
           {"GND": (4, 0), "D2": (5, 0), "D4": (6, 0), "D7": (7, 0), "A1": (8, 0), "A5": (9, 0)}),
    "J1": ("Borne de parafuso 5,08 mm (entrada de 13 V)", {"1": (1, 2), "2": (3, 2)}),
    "D1": ("1N5819 (faixa = catodo = pino K)", {"A": (1, 4), "K": (1, 8)}),
    "U2": ("Soquete DIP-8 (entalhe para cima = pino 1 em cima a esquerda)",
           {"1": (12, 3), "2": (12, 4), "3": (12, 5), "4": (12, 6), "8": (15, 3), "7": (15, 4), "6": (15, 5), "5": (15, 6)}),
    "C1": ("100 nF", {"1": (10, 3), "2": (10, 5)}),
    "R1": ("10 k", {"1": (5, 8), "2": (9, 8)}),
    "R4": ("1 k", {"1": (5, 10), "2": (9, 10)}),
    "D2": ("LED vermelho (perna curta = catodo = K)", {"A": (11, 10), "K": (12, 10)}),
    "Q1": ("BC547 (C, B, E da esquerda para a direita, lado chato para cima)", {"C": (12, 8), "B": (13, 8), "E": (14, 8)}),
    "R2": ("4,7 k", {"1": (17, 10), "2": (13, 10)}),
    "R3": ("220", {"1": (20, 2), "2": (20, 6)}),
    "D3": ("LED amarelo (perna curta = catodo = K)", {"A": (20, 7), "K": (20, 8)}),
}

# ---- fios (cada um: nome da net, lista de furos)
FIOS = [
    ("GND", [(4, 0), (4, 2), (4, 13)]),                     # J3.GND desce a coluna 5 (x=4) ate o trilho de GND
    ("GND", [(3, 2), (4, 2)]),                              # J1.2
    ("GND", [(4, 13), (10, 13), (12, 13), (14, 13), (18, 13), (20, 13)]),   # trilho de GND (fio nu)
    ("GND", [(10, 5), (10, 13)]),                           # C1.2
    ("GND", [(12, 10), (12, 13)]),                          # D2.K
    ("GND", [(14, 8), (14, 13)]),                           # Q1.E
    ("GND", [(15, 3), (18, 3), (18, 13)]),                  # U2 pino 8
    ("GND", [(20, 8), (20, 13)]),                           # D3.K
    ("VDD", [(5, 0), (5, 3), (10, 3), (12, 3)]),            # D2 do Uno -> U2 pino 1, com C1.1 em (10,3)
    ("CLK", [(6, 0), (6, 2), (17, 2), (17, 5), (15, 5)]),   # D4 -> U2 pino 6
    ("DAT", [(7, 0), (7, 1), (16, 1), (16, 4), (15, 4)]),   # D7 -> U2 pino 7
    ("VPP_CTL", [(8, 0), (8, 11), (17, 11), (17, 10)]),     # A1 -> R2.1
    ("BASE", [(13, 8), (13, 10)]),                          # Q1.B - R2.2
    ("MCLR", [(12, 6), (12, 8)]),                           # U2 pino 4 - Q1.C
    ("MCLR", [(9, 8), (12, 8)]),                            # R1.2
    ("V13_ENT", [(1, 2), (1, 4)]),                          # J1.1 - D1.A
    ("V13", [(1, 8), (5, 8), (5, 10)]),                     # D1.K - R1.1 - R4.1
    ("LED13_A", [(9, 10), (11, 10)]),                       # R4.2 - D2.A
    ("LED_ATIVO", [(9, 0), (20, 0), (20, 2)]),              # A5 -> R3.1
    ("LEDA_A", [(20, 6), (20, 7)]),                         # R3.2 - D3.A
]

# ---- grupos esperados (ref, pino)
ESPERADO = {
    "VDD": [("J3", "D2"), ("U2", "1"), ("C1", "1")],
    "CLK": [("J3", "D4"), ("U2", "6")],
    "DAT": [("J3", "D7"), ("U2", "7")],
    "MCLR": [("U2", "4"), ("R1", "2"), ("Q1", "C")],
    "VPP_CTL": [("J3", "A1"), ("R2", "1")],
    "BASE": [("R2", "2"), ("Q1", "B")],
    "GND": [("J3", "GND"), ("J1", "2"), ("U2", "8"), ("Q1", "E"), ("C1", "2"), ("D2", "K"), ("D3", "K")],
    "V13": [("D1", "K"), ("R1", "1"), ("R4", "1")],
    "V13_ENT": [("J1", "1"), ("D1", "A")],
    "LED13_A": [("R4", "2"), ("D2", "A")],
    "LED_ATIVO": [("J3", "A5"), ("R3", "1")],
    "LEDA_A": [("R3", "2"), ("D3", "A")],
}
LIVRES = [("U2", "2"), ("U2", "3"), ("U2", "5")]
TAM = (22, 14)   # colunas x linhas usadas (x de 0 a 21, y de 0 a 13)


def nome_furo(x, y):
    return f"{chr(65 + y)}{x + 1}"


def verificar():
    pai = {}

    def f(a):
        pai.setdefault(a, a)
        while pai[a] != a:
            pai[a] = pai[pai[a]]
            a = pai[a]
        return a

    def u(a, b):
        pai[f(a)] = f(b)

    pad_em = {}
    for ref, (_, pinos) in PECAS.items():
        for pino, h in pinos.items():
            if h in pad_em:
                return [f"{ref}.{pino} e {pad_em[h]} no mesmo furo {nome_furo(*h)}"]
            pad_em[h] = f"{ref}.{pino}"
            f(h)
    for _, pts in FIOS:
        for a, b in zip(pts, pts[1:]):
            u(a, b)
    erros = []
    grupos = {}
    for h, nome in pad_em.items():
        grupos.setdefault(f(h), []).append(nome)
    achados = {frozenset(v) for v in grupos.values() if len(v) > 1}
    esperados = {frozenset(f"{r}.{p}" for r, p in g) for g in ESPERADO.values()}
    for g in esperados - achados:
        erros.append("falta ligar: " + ", ".join(sorted(g)))
    for g in achados - esperados:
        erros.append("ligacao a mais: " + ", ".join(sorted(g)))
    # pinos livres nao podem estar em fio
    for ref, p in LIVRES:
        h = PECAS[ref][1][p]
        if any(h in pts for _, pts in FIOS):
            erros.append(f"{ref}.{p} devia ficar livre")
    # o nome da net de cada fio tem que bater com o grupo esperado
    for net, pts in FIOS:
        nomes = [pad_em[h] for h in pts if h in pad_em]
        esp = ESPERADO.get(net)
        if esp and nomes and not set(nomes) <= {f"{r}.{p}" for r, p in esp}:
            erros.append(f"fio {net} toca {nomes}")
    # vertices de fio nao podem cair em furo de pad de outra net (ja pego acima) nem sair da placa
    for _, pts in FIOS:
        for x, y in pts:
            if not (0 <= x < TAM[0] and 0 <= y < TAM[1]):
                erros.append(f"furo fora da placa: {nome_furo(x, y)}")
    return erros


CORES = {"GND": "#222222", "VDD": "#d62828", "CLK": "#2a9d8f", "DAT": "#1d4ed8", "VPP_CTL": "#9333ea", "BASE": "#9333ea",
         "MCLR": "#e76f51", "V13": "#c2410c", "V13_ENT": "#c2410c", "LED13_A": "#c2410c", "LED_ATIVO": "#ca8a04", "LEDA_A": "#ca8a04"}


def desenhar():
    P = 28  # pixels por furo
    M = 40
    W, H = TAM[0] * P + 2 * M, TAM[1] * P + 2 * M + 110
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="DejaVu Sans, sans-serif">',
         f'<rect width="{W}" height="{H}" fill="white"/>',
         f'<rect x="{M - 14}" y="{M - 14}" width="{TAM[0] * P + 28 - P + 28}" height="{TAM[1] * P + 28 - P + 28}" rx="6" fill="#d9c27a" stroke="#8a7a3a"/>']
    cx = lambda x: M + x * P
    cy = lambda y: M + y * P
    for x in range(TAM[0]):
        s.append(f'<text x="{cx(x)}" y="{M - 20}" font-size="10" text-anchor="middle" fill="#333">{x + 1}</text>')
        for y in range(TAM[1]):
            s.append(f'<circle cx="{cx(x)}" cy="{cy(y)}" r="3.2" fill="#fff8dc" stroke="#8a7a3a" stroke-width="0.8"/>')
    for y in range(TAM[1]):
        s.append(f'<text x="{M - 26}" y="{cy(y) + 4}" font-size="10" text-anchor="middle" fill="#333">{chr(65 + y)}</text>')
    # pecas (corpos)
    def corpo(a, b, rot, w=10):
        (x1, y1), (x2, y2) = (cx(a[0]), cy(a[1])), (cx(b[0]), cy(b[1]))
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if abs(x1 - x2) >= abs(y1 - y2):
            return f'<rect x="{min(x1, x2) + 6}" y="{my - w / 2}" width="{abs(x2 - x1) - 12}" height="{w}" rx="3" fill="#e9d8a6" stroke="#6b5b2a"/>'
        return f'<rect x="{mx - w / 2}" y="{min(y1, y2) + 6}" width="{w}" height="{abs(y2 - y1) - 12}" rx="3" fill="#e9d8a6" stroke="#6b5b2a"/>'
    for ref in ("R1", "R2", "R3", "R4"):
        p = list(PECAS[ref][1].values())
        s.append(corpo(p[0], p[1], 0))
    d = PECAS["D1"][1]
    s.append(corpo(d["A"], d["K"], 0, 12))
    s.append(f'<rect x="{cx(d["K"][0]) - 6}" y="{cy(d["K"][1]) - 22}" width="12" height="4" fill="#222"/>')
    s.append(corpo(*list(PECAS["C1"][1].values()), 0, 14).replace("#e9d8a6", "#f4a261"))
    for ref, cor in (("D2", "#e63946"), ("D3", "#f4d35e")):
        a, k = PECAS[ref][1]["A"], PECAS[ref][1]["K"]
        s.append(f'<circle cx="{(cx(a[0]) + cx(k[0])) / 2}" cy="{(cy(a[1]) + cy(k[1])) / 2}" r="15" fill="{cor}" fill-opacity="0.55" stroke="#333"/>')
        s.append(f'<text x="{cx(k[0])}" y="{cy(k[1]) + 4}" font-size="9" text-anchor="middle" fill="#000">K</text>')
    q = PECAS["Q1"][1]
    s.append(f'<path d="M{cx(q["C"][0]) - 12} {cy(q["C"][1]) + 9} L{cx(q["E"][0]) + 12} {cy(q["E"][1]) + 9} L{cx(q["E"][0]) + 12} {cy(q["E"][1]) - 4} '
             f'A 30 26 0 0 0 {cx(q["C"][0]) - 12} {cy(q["C"][1]) - 4} Z" fill="#555" fill-opacity="0.35" stroke="#222"/>')
    u2 = PECAS["U2"][1]
    s.append(f'<rect x="{cx(12) - 10}" y="{cy(3) - 11}" width="{3 * P + 20}" height="{3 * P + 22}" rx="3" fill="#bbb" fill-opacity="0.5" stroke="#333"/>')
    s.append(f'<path d="M{cx(13) + 2} {cy(3) - 11} a 10 10 0 0 0 {P - 4} 0" fill="none" stroke="#333"/>')
    j1 = PECAS["J1"][1]
    s.append(f'<rect x="{cx(1) - 14}" y="{cy(2) - 14}" width="{2 * P + 28}" height="28" rx="3" fill="#2a9d8f" fill-opacity="0.55" stroke="#222"/>')
    s.append(f'<rect x="{cx(4) - 12}" y="{cy(0) - 12}" width="{5 * P + 24}" height="24" fill="#222" fill-opacity="0.8"/>')
    # fios
    for net, pts in FIOS:
        path = " ".join(f"{cx(x)},{cy(y)}" for x, y in pts)
        s.append(f'<polyline points="{path}" fill="none" stroke="{CORES[net]}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" stroke-opacity="0.85"'
                 + "/>")
    # pads e rotulos
    for ref, (_, pinos) in PECAS.items():
        for pino, (x, y) in pinos.items():
            s.append(f'<circle cx="{cx(x)}" cy="{cy(y)}" r="5" fill="#c0c0c0" stroke="#222" stroke-width="1.2"/>')
    def rot(txt, x, y, cor="#111", t=11, anchor="middle"):
        s.append(f'<text x="{x}" y="{y}" font-size="{t}" font-weight="bold" text-anchor="{anchor}" fill="{cor}">{txt}</text>')
    rot("J3 (ao Uno)", cx(6.5), cy(0) + 26, "#fff", 9)
    for nome, (x, y) in PECAS["J3"][1].items():
        rot(nome, cx(x), cy(y) - 16 if False else cy(y) + 14, "#fff", 8)
    rot("J1 +", cx(1), cy(2) + 24, "#111", 9)
    rot("J1 GND", cx(3), cy(2) + 24, "#111", 9)
    rot("D1", cx(1) - 14, cy(6), anchor="end")
    rot("U2 DIP-8", cx(13.5), cy(6) + 30)
    for i, (x, y) in enumerate(((12, 3), (12, 4), (12, 5), (12, 6))):
        rot(str(i + 1), cx(x) - 14, cy(y) + 4, "#333", 9)
    for i, (x, y) in enumerate(((15, 6), (15, 5), (15, 4), (15, 3))):
        rot(str(5 + i), cx(x) + 14, cy(y) + 4, "#333", 9)
    rot("C1 100n", cx(10) - 16, cy(4), anchor="end", t=10)
    rot("R1 10k", cx(7), cy(8) - 10, t=10)
    rot("R4 1k", cx(7), cy(10) - 10, t=10)
    rot("R2 4k7", cx(15), cy(10) - 10, t=10)
    rot("R3 220", cx(20) + 16, cy(4), anchor="start", t=10)
    rot("D2", cx(11.5), cy(10) + 28, t=10)
    rot("D3", cx(20) + 22, cy(7.5), anchor="start", t=10)
    rot("Q1 C B E", cx(13), cy(8) - 20, t=10)
    rot("trilho de GND (fio nu)", cx(7), cy(13) + 20, "#222", 10)
    # legenda
    y0 = TAM[1] * P + 2 * M - 10
    s.append(f'<text x="{M}" y="{y0}" font-size="12" font-weight="bold" fill="#111">Placa perfurada: lado dos componentes visto de cima; fios isolados no lado da solda (visto aqui por transparencia)</text>')
    for i, (net, cor) in enumerate(CORES.items()):
        xx = M + (i % 4) * 190
        yy = y0 + 22 + (i // 4) * 20
        s.append(f'<line x1="{xx}" y1="{yy - 4}" x2="{xx + 26}" y2="{yy - 4}" stroke="{cor}" stroke-width="4"/>')
        s.append(f'<text x="{xx + 32}" y="{yy}" font-size="11" fill="#111">{net}</text>')
    s.append("</svg>")
    (DOCS / "perfboard.svg").write_text("\n".join(s))


def tabelas():
    L = ["# Placa perfurada: tabelas geradas por `scripts/perfboard.py`", "",
         "Furo = letra da linha + numero da coluna (ver o desenho `perfboard.png`). Vale para uma placa de 22 colunas x 14 linhas ou maior.", "",
         "## Pecas", "", "| Ref | Peca | Furos |", "|---|---|---|"]
    for ref, (d, pinos) in PECAS.items():
        L.append(f"| {ref} | {d} | " + ", ".join(f"{p}: {nome_furo(*h)}" for p, h in pinos.items()) + " |")
    L += ["", "## Fios (todos isolados, no lado da solda; solde nos furos das pontas e dobre nos furos indicados)", "", "| Net | Caminho |", "|---|---|"]
    for net, pts in FIOS:
        L.append(f"| {net} | " + " > ".join(nome_furo(*h) for h in pts) + " |")
    (DOCS / "perfboard.md").write_text("\n".join(L) + "\n")


def main():
    erros = verificar()
    if erros:
        print("\n".join(erros))
        sys.exit(1)
    desenhar()
    tabelas()
    print(f"ok: {len(ESPERADO)} nets conferidas, {len(FIOS)} fios, {sum(len(p[1]) for p in PECAS.values())} pads")


if __name__ == "__main__":
    main()
