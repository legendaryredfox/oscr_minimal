#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-SA-2.5
"""Desenha o 'mapa das ligacoes' do shield do Uno: um esquema para quem nunca viu um esquematico.

Cada ligacao e um fio colorido entre caixas com nome em portugues; nada de simbolos de eletronica. As ligacoes sao
conferidas contra `protoboard.ESPERADO` (a mesma tabela do verificador da protoboard e da placa perfurada):
se um fio do desenho ligar o que nao deve, o script para com erro.

Saida: docs/esquema-simples.svg e docs/esquema-simples.png (o PNG usa o Chrome sem janela).
Uso: python3 tools/pic/shield_uno/scripts/esquema_simples.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import protoboard as pb  # noqa: E402
from protoboard_desenho import svg_para_png  # noqa: E402

AQUI = Path(__file__).resolve().parent.parent
OUT = AQUI / "docs"

W, H = 1560, 1290
FUNDO = "#fbf7ec"
COR = dict(pb.COR)
COR["rosa"] = "#db2777"
GROSSURA = 9

# ------------------------------------------------------------------ pontos (pinos das pecas)
RAIL_V, RAIL_G = 130, 900
XD = 780             # pinos do lado direito do chip
XN = 840             # coluna do no MCLR, do no do pino 1 e do R1
XC = 890             # capacitor C1
XQ = 1020            # centro do transistor
XL = 1230            # coluna R4 + LED vermelho
XF = 1420            # fonte
PIN = {
    "UNO.D4": (250, 300), "UNO.D7": (250, 350), "UNO.D2": (250, 460), "UNO.A1": (250, 540), "UNO.A5": (250, 700),
    "UNO.GND": (250, RAIL_G),
    # PIC12F629 desenhado com o entalhe para BAIXO: esquerda de cima para baixo 5,6,7,8; direita 4,3,2,1
    "U2.5": (500, 250), "U2.6": (500, 300), "U2.7": (500, 350), "U2.8": (500, 400),
    "U2.4": (XD, 250), "U2.3": (XD, 300), "U2.2": (XD, 350), "U2.1": (XD, 400),
    "R1.2": (XN, 170), "R1.1": (XN, 230),            # R1 na vertical: 1 = lado do chip, 2 = lado dos 13 V
    "C1.1": (XC, 430), "C1.2": (XC, 520),
    "Q1.C": (XQ, 330), "Q1.B": (XQ - 50, 385), "Q1.E": (XQ, 440),
    "R2.1": (560, 540), "R2.2": (680, 540),
    "R4.1": (XL, 170), "R4.2": (XL, 230), "D2.A": (XL, 290), "D2.K": (XL, 360),
    "R3.1": (290, 700), "R3.2": (370, 700), "D3.A": (410, 745), "D3.K": (410, 815),
    "FONTE.+": (XF, 420), "FONTE.-": (XF, 540),
}
# ------------------------------------------------------------------ fios: (cor, [pontos], rotulo opcional)
FIOS = [
    ("laranja", [PIN["UNO.D2"], (XN, 460), (XN, 400)], None),                        # Uno D2 -> sobe ate o no do pino 1
    ("laranja", [PIN["U2.1"], (XC, 400), PIN["C1.1"]], None),                        # pino 1 -> capacitor
    ("verde", [PIN["UNO.D4"], PIN["U2.6"]], None),
    ("azul", [PIN["UNO.D7"], PIN["U2.7"]], None),
    ("preto", [PIN["U2.8"], (470, 400), (470, RAIL_G)], None),                      # pino 8 -> GND
    ("preto", [PIN["C1.2"], (XC, RAIL_G)], None),
    ("preto", [PIN["Q1.E"], (XQ, RAIL_G)], None),
    ("preto", [PIN["D2.K"], (XL, RAIL_G)], None),
    ("preto", [PIN["D3.K"], (410, RAIL_G)], None),
    ("preto", [PIN["UNO.GND"], (XF, RAIL_G), PIN["FONTE.-"]], None),               # trilho de GND
    ("rosa", [PIN["U2.4"], (XN, 250), PIN["R1.1"]], None),                           # MCLR ate o resistor de 10 k
    ("rosa", [(XN, 250), (XQ, 250), PIN["Q1.C"]], None),                             # e ate o coletor do transistor
    ("vermelho", [PIN["FONTE.+"], (XF, RAIL_V), (XN, RAIL_V), PIN["R1.2"]], None),  # trilho de 13 V
    ("vermelho", [(XL, RAIL_V), PIN["R4.1"]], None),
    ("vermelho", [PIN["R4.2"], PIN["D2.A"]], None),
    ("roxo", [PIN["UNO.A1"], PIN["R2.1"]], None),
    ("roxo", [PIN["R2.2"], (XQ - 80, 540), (XQ - 80, 385), PIN["Q1.B"]], None),
    ("amarelo", [PIN["UNO.A5"], PIN["R3.1"]], None),
    ("amarelo", [PIN["R3.2"], (410, 700), PIN["D3.A"]], None),
]
# pontos onde um fio SE ENCONTRA com outro (bolinha preta no desenho)
JUNCOES = [(XN, 400), (470, RAIL_G), (XC, RAIL_G), (XQ, RAIL_G), (XL, RAIL_G), (410, RAIL_G), (XN, 250), (XL, RAIL_V)]


# ------------------------------------------------------------------ verificacao
def sobre(p, a, b):
    (x, y), (x1, y1), (x2, y2) = p, a, b
    return min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2) and (x1 == x2 == x or y1 == y2 == y)


def segmentos(f):
    return list(zip(f[1][:-1], f[1][1:]))


def verificar():
    erros = []
    n = len(FIOS)
    pai = list(range(n))

    def raiz(i):
        while pai[i] != i:
            pai[i] = pai[pai[i]]
            i = pai[i]
        return i
    # dois fios se unem se tiverem um ponta/vertice comum, ou se uma PONTA de um estiver sobre o outro numa juncao declarada
    for i in range(n):
        for j in range(i + 1, n):
            for p in JUNCOES:
                ti = any(sobre(p, a, b) for a, b in segmentos(FIOS[i]))
                tj = any(sobre(p, a, b) for a, b in segmentos(FIOS[j]))
                if ti and tj:
                    pai[raiz(i)] = raiz(j)
            pts_i, pts_j = set(FIOS[i][1]), set(FIOS[j][1])
            if pts_i & pts_j and not (pts_i & pts_j) <= set(PIN.values()):
                pass  # vertice comum que nao e juncao declarada: nao une (so as JUNCOES unem)
    grupos = {}
    for i, f in enumerate(FIOS):
        for p in (f[1][0], f[1][-1]):
            for nome, xy in PIN.items():
                if xy == p:
                    grupos.setdefault(raiz(i), set()).add(nome)
    redes = [g for g in grupos.values()]
    # pecas que ligam duas redes por dentro nao fazem parte de nenhum fio: nao entram aqui
    esperado = [e - {"U2.2", "U2.3", "U2.5"} for e in pb.ESPERADO]
    # Q1.B e R2.2 ficam na mesma rede; R2.1 e UNO.A1 tambem; e assim por diante: comparamos as redes que tem >= 2 pinos
    vistos = [frozenset(g) for g in redes if len(g) >= 2]
    for e in esperado:
        if frozenset(e) not in vistos:
            erros.append(f"rede esperada nao desenhada: {sorted(e)}")
    for v in vistos:
        if set(v) not in esperado:
            erros.append(f"rede desenhada que nao existe: {sorted(v)}")
    for nome in PIN:
        if not any(nome in g for g in redes):
            erros.append(f"pino sem fio: {nome}" + (" (ok, nao liga)" if nome in pb.LIVRES else ""))
    return [e for e in erros if "(ok, nao liga)" not in e]


def cruzamentos():
    """(x, y, indice_do_fio_horizontal) de cada ponto onde um fio horizontal passa por cima de um vertical sem juncao."""
    out = []
    for i, f in enumerate(FIOS):
        for (a, b) in segmentos(f):
            if a[1] != b[1]:
                continue
            for j, g in enumerate(FIOS):
                if i == j:
                    continue
                for (c, d) in segmentos(g):
                    if c[0] != d[0]:
                        continue
                    x, y = c[0], a[1]
                    if min(a[0], b[0]) < x < max(a[0], b[0]) and min(c[1], d[1]) < y < max(c[1], d[1]) and (x, y) not in JUNCOES:
                        out.append((x, y, i))
    return out


# ------------------------------------------------------------------ desenho
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;")


def texto(x, y, t, tam=16, peso="normal", cor="#222", ancora="start"):
    return f'<text x="{x}" y="{y}" font-size="{tam}" font-weight="{peso}" fill="{cor}" text-anchor="{ancora}">{esc(t)}</text>'


def caminho(f, hops):
    pts = f[1]
    d = f"M{pts[0][0]},{pts[0][1]}"
    for a, b in zip(pts[:-1], pts[1:]):
        if a[1] == b[1]:
            xs = sorted([h[0] for h in hops if h[1] == a[1] and min(a[0], b[0]) < h[0] < max(a[0], b[0])], reverse=b[0] < a[0])
            for x in xs:
                r = 10
                d += f" L{x - r if b[0] > a[0] else x + r},{a[1]} A{r},{r} 0 0 {1 if b[0] > a[0] else 0} {x + r if b[0] > a[0] else x - r},{a[1]}"
        d += f" L{b[0]},{b[1]}"
    return d


def fio_svg(i, f, todos):
    hops = [(x, y) for x, y, k in todos if k == i]
    d = caminho(f, hops)
    c = COR[f[0]]
    return (f'<path d="{d}" fill="none" stroke="#1f1f1f" stroke-width="{GROSSURA + 4}" stroke-linecap="round" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{GROSSURA}" stroke-linecap="round" stroke-linejoin="round"/>')


def resistor(x1, y1, x2, y2, bands, nome, valor, lado):
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    horiz = y1 == y2
    L = abs(x2 - x1) if horiz else abs(y2 - y1)
    corpo = 76
    s = []
    if horiz:
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#888" stroke-width="4"/>')
        s.append(f'<rect x="{cx - corpo / 2}" y="{cy - 14}" width="{corpo}" height="28" rx="10" fill="#e8c98f" stroke="#7a5a1e" stroke-width="2"/>')
        for k, b in enumerate(bands):
            s.append(f'<rect x="{cx - 24 + k * 18}" y="{cy - 14}" width="8" height="28" fill="{FAIXA[b]}"/>')
        s.append(texto(cx, cy - 24, f"{nome}  {valor}", 15, "bold", ancora="middle"))
    else:
        s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#888" stroke-width="4"/>')
        s.append(f'<rect x="{cx - 14}" y="{cy - corpo / 2 + 4}" width="28" height="{corpo - 8}" rx="10" fill="#e8c98f" stroke="#7a5a1e" stroke-width="2"/>')
        for k, b in enumerate(bands):
            s.append(f'<rect x="{cx - 14}" y="{cy - 22 + k * 15}" width="28" height="7" fill="{FAIXA[b]}"/>')
        s.append(texto(cx + 26 if lado == "d" else cx - 26, cy - 2, nome, 15, "bold", ancora="start" if lado == "d" else "end"))
        s.append(texto(cx + 26 if lado == "d" else cx - 26, cy + 16, valor, 15, ancora="start" if lado == "d" else "end"))
    return "".join(s)


FAIXA = {"marrom": "#7b4a1e", "preto": "#111", "laranja": "#f77f00", "amarelo": "#eab308", "violeta": "#7c3aed",
         "vermelho": "#d62828"}


def led(x, y_a, y_k, cor, nome, dica, lado):
    cy = (y_a + y_k) / 2
    s = [f'<line x1="{x}" y1="{y_a}" x2="{x}" y2="{y_k}" stroke="#888" stroke-width="4"/>',
         f'<circle cx="{x}" cy="{cy}" r="24" fill="{cor}" stroke="#333" stroke-width="3"/>',
         f'<circle cx="{x - 8}" cy="{cy - 8}" r="6" fill="#fff" opacity="0.6"/>',
         texto(x, y_a + 14, "+", 18, "bold", "#111", "middle")]
    dx = 36 if lado == "d" else -36
    anc = "start" if lado == "d" else "end"
    s.append(texto(x + dx, cy - 4, nome, 15, "bold", ancora=anc))
    s.append(texto(x + dx, cy + 14, dica, 14, ancora=anc))
    return "".join(s)


def caixa(x, y, w, h, titulo, cor="#fff", borda="#333"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{cor}" stroke="{borda}" stroke-width="3"/>'
            + texto(x + w / 2, y + 30, titulo, 20, "bold", ancora="middle"))


def etiqueta_pino(x, y, nome, cor, dica):
    """Plaquinha colorida com o nome do pino do Uno, dentro da caixa, rente a borda direita."""
    return (f'<rect x="{x - 150}" y="{y - 17}" width="140" height="34" rx="8" fill="#fff" stroke="{COR[cor]}" stroke-width="5"/>'
            + texto(x - 80, y + 6, nome, 18, "bold", ancora="middle") + texto(x - 160, y + 5, dica, 13, ancora="end", cor="#555"))


def desenhar():
    todos = cruzamentos()
    S = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="DejaVu Sans, sans-serif">',
         f'<rect width="{W}" height="{H}" fill="{FUNDO}"/>',
         texto(40, 50, "MAPA DAS LIGAÇÕES: siga os fios pela cor", 30, "bold"),
         texto(40, 80, "Cada fio colorido liga uma peça a outra. Fio da mesma cor = mesmo caminho. Monte tudo com a fonte DESLIGADA.", 17, cor="#444")]
    # ---- Uno
    S.append(caixa(40, 250, 210, 690, "ARDUINO UNO", "#dff0f7", "#0b5d7a"))
    for nome, cor in (("D4", "verde"), ("D7", "azul"), ("D2", "laranja"), ("A1", "roxo"), ("A5", "amarelo"), ("GND", "preto")):
        y = PIN["UNO." + nome][1]
        S.append(f'<rect x="100" y="{y - 17}" width="150" height="34" rx="8" fill="#fff" stroke="{COR[cor]}" stroke-width="5"/>')
        S.append(texto(175, y + 6, nome, 19, "bold", ancora="middle"))
    S.append(texto(145, 965, "(os furos do Uno", 13, ancora="middle", cor="#555"))
    S.append(texto(145, 983, "onde os fios entram)", 13, ancora="middle", cor="#555"))
    # ---- fios: verticais primeiro, depois horizontais (os pulinhos ficam por cima)
    ordem = sorted(range(len(FIOS)), key=lambda i: 0 if all(a[0] == b[0] for a, b in segmentos(FIOS[i])) else 1)
    for i in ordem:
        S.append(fio_svg(i, FIOS[i], todos))
    # ---- PIC (entalhe para baixo)
    S.append(f'<rect x="520" y="215" width="{XD - 20 - 520}" height="240" rx="10" fill="#3a3a3a" stroke="#111" stroke-width="3"/>')
    xm = (520 + XD - 20) / 2
    S.append(f'<path d="M{xm - 30},455 A30,30 0 0 1 {xm + 30},455 Z" fill="{FUNDO}"/>')
    for nome in ("5", "6", "7", "8"):
        x, y = PIN["U2." + nome]
        S.append(f'<line x1="{x}" y1="{y}" x2="520" y2="{y}" stroke="#bbb" stroke-width="5"/>')
    for nome in ("4", "3", "2", "1"):
        x, y = PIN["U2." + nome]
        S.append(f'<line x1="{XD - 20}" y1="{y}" x2="{x}" y2="{y}" stroke="#bbb" stroke-width="5"/>')

    def bolha(x, y, n):
        return f'<circle cx="{x}" cy="{y}" r="15" fill="#fff" stroke="#111" stroke-width="2"/>' + texto(x, y + 6, n, 17, "bold", "#111", "middle")
    desc_e = {"5": "livre", "6": "relógio", "7": "dados", "8": "GND"}
    desc_d = {"4": "MCLR", "3": "livre", "2": "livre", "1": "energia"}
    for n, t in desc_e.items():
        y = PIN["U2." + n][1]
        S.append(bolha(548, y, n) + texto(572, y + 6, t, 16, "bold", "#fff"))
    for n, t in desc_d.items():
        y = PIN["U2." + n][1]
        S.append(bolha(XD - 48, y, n) + texto(XD - 72, y + 6, t, 16, "bold", "#fff", "end"))
    S.append(texto(xm, 202, "PIC12F629 (o chip)", 18, "bold", "#111", "middle"))
    S.append(texto(xm, 478, "entalhe", 14, "bold", "#555", "middle"))
    S.append(texto(XD + 4, 432, "pino 1", 14, "bold", "#111"))
    # pinos livres: X
    for n in ("U2.5", "U2.3", "U2.2"):
        x, y = PIN[n]
        xx = x - 14 if n == "U2.5" else x + 14
        S.append(f'<path d="M{xx - 7},{y - 7} L{xx + 7},{y + 7} M{xx - 7},{y + 7} L{xx + 7},{y - 7}" stroke="#888" stroke-width="4"/>')
    S.append(texto(XD + 34, 304, "sem fio", 13, "normal", "#777"))
    S.append(texto(XD + 34, 354, "sem fio", 13, "normal", "#777"))
    S.append(texto(470, 258, "sem fio", 13, "normal", "#777", "end"))
    # ---- pecas
    S.append(resistor(*PIN["R1.1"], *PIN["R1.2"], ("marrom", "preto", "laranja"), "R1", "10 kΩ", "d"))
    S.append(resistor(*PIN["R4.1"], *PIN["R4.2"], ("marrom", "preto", "vermelho"), "R4", "1 kΩ", "d"))
    S.append(resistor(*PIN["R2.1"], *PIN["R2.2"], ("amarelo", "violeta", "vermelho"), "R2", "4,7 kΩ", "d"))
    S.append(resistor(*PIN["R3.1"], *PIN["R3.2"], ("vermelho", "vermelho", "marrom"), "R3", "220 Ω", "d"))
    S.append(led(XL, PIN["D2.A"][1], PIN["D2.K"][1], "#ef4444", "LED vermelho", "acende = há 13 V", "d"))
    S.append(led(410, PIN["D3.A"][1], PIN["D3.K"][1], "#facc15", "LED amarelo", "pisca = ativo", "e"))
    # capacitor (o nome e o valor ficam dentro do corpo)
    cx = XC
    S.append(f'<line x1="{cx}" y1="430" x2="{cx}" y2="520" stroke="#888" stroke-width="4"/>')
    S.append(f'<rect x="{cx - 34}" y="445" width="68" height="60" rx="14" fill="#f4a261" stroke="#7a3e0c" stroke-width="2"/>')
    S.append(texto(cx, 470, "C1", 17, "bold", "#111", "middle"))
    S.append(texto(cx, 490, "100 nF", 14, "normal", "#111", "middle"))
    # transistor
    qx = XQ - 50
    S.append(f'<rect x="{qx}" y="330" width="100" height="110" rx="12" fill="#444" stroke="#111" stroke-width="3"/>')
    S.append(texto(XQ, 372, "BC547", 17, "bold", "#fff", "middle"))
    S.append(texto(XQ, 392, "(transistor)", 13, "normal", "#ddd", "middle"))
    S.append(texto(XQ, 424, "chato p/ você", 12, "normal", "#ddd", "middle"))
    for nome in ("C", "B", "E"):
        x, y = PIN["Q1." + nome]
        S.append(f'<circle cx="{x}" cy="{y}" r="13" fill="#fff" stroke="#111" stroke-width="2"/>' + texto(x, y + 6, nome, 16, "bold", "#111", "middle"))
    S.append(texto(XQ + 62, 336, "C: recebe o rosa", 13, cor="#555"))
    S.append(texto(XQ + 62, 391, "B: recebe o roxo", 13, cor="#555"))
    S.append(texto(XQ + 62, 446, "E: vai ao GND", 13, cor="#555"))
    # fonte
    S.append(caixa(XF - 80, 420, 160, 120, "FONTE 13 V", "#fff3d6", "#8a5a00"))
    S.append(f'<circle cx="{XF}" cy="420" r="15" fill="#d62828" stroke="#111" stroke-width="2"/>' + texto(XF, 427, "+", 22, "bold", "#fff", "middle"))
    S.append(f'<circle cx="{XF}" cy="540" r="15" fill="#111" stroke="#111" stroke-width="2"/>' + texto(XF, 547, "−", 22, "bold", "#fff", "middle"))
    S.append(texto(XF, 470, "liga POR ÚLTIMO", 14, ancora="middle", cor="#444"))
    S.append(texto(XF, 490, "confira o + e o −", 14, ancora="middle", cor="#444"))
    S.append(texto(XF, 510, "com o multímetro", 14, ancora="middle", cor="#444"))
    # rotulos dos trilhos (acima do vermelho, abaixo do preto)
    S.append(texto(1010, RAIL_V - 18, "13 V (fio vermelho)", 17, "bold", COR["vermelho"], "middle"))
    S.append(texto(640, RAIL_G + 36, "GND = terra (fio preto, o caminho de volta)", 17, "bold", "#111", "middle"))
    # juncoes e dicas
    for x, y in JUNCOES:
        S.append(f'<circle cx="{x}" cy="{y}" r="9" fill="#fff" stroke="#111" stroke-width="3"/><circle cx="{x}" cy="{y}" r="4" fill="#111"/>')
    S.append(texto(360, 288, "relógio: marca o ritmo", 14, ancora="middle", cor="#1f7a38"))
    S.append(texto(360, 338, "dados: o que vai gravar", 14, ancora="middle", cor=COR["azul"]))
    S.append(texto(360, 448, "energia do chip", 14, ancora="middle", cor="#b85c00"))
    S.append(texto(360, 528, "comanda o transistor", 14, ancora="middle", cor=COR["roxo"]))
    S.append(texto(XN + 24, 234, "MCLR: 13 V para gravar", 14, "bold", COR["rosa"], "start"))
    # ---- legenda
    ly = 1030
    S.append(f'<rect x="40" y="{ly - 30}" width="{W - 80}" height="250" rx="14" fill="#fff" stroke="#999" stroke-width="2"/>')
    S.append(texto(60, ly, "COMO LER", 22, "bold"))
    S.append(f'<circle cx="80" cy="{ly + 34}" r="9" fill="#fff" stroke="#111" stroke-width="3"/><circle cx="80" cy="{ly + 34}" r="4" fill="#111"/>')
    S.append(texto(100, ly + 40, "bolinha: os fios SE ENCONTRAM aqui (estão ligados).", 17))
    S.append(f'<path d="M62,{ly + 78} L72,{ly + 78} A10,10 0 0 1 92,{ly + 78} L102,{ly + 78}" fill="none" stroke="#111" stroke-width="5"/>')
    S.append(texto(112, ly + 84, "pulinho: um fio passa POR CIMA do outro, sem encostar.", 17))
    S.append(f'<path d="M66,{ly + 112} L90,{ly + 136} M66,{ly + 136} L90,{ly + 112}" stroke="#888" stroke-width="5"/>')
    S.append(texto(112, ly + 130, "X: pino do chip que não leva fio. Não ligue nada nele.", 17))
    cores = [("laranja", "energia do chip (D2)"), ("verde", "relógio (D4)"), ("azul", "dados (D7)"), ("roxo", "comanda o transistor (A1)"),
             ("amarelo", "luz amarela (A5)"), ("rosa", "MCLR, o pino dos 13 V"), ("vermelho", "13 V da fonte"), ("preto", "GND: o fio de volta")]
    for k, (c, t) in enumerate(cores):
        x = 800 + (k % 2) * 380
        y = ly + 20 + (k // 2) * 40
        S.append(f'<rect x="{x}" y="{y - 14}" width="46" height="18" rx="9" fill="{COR[c]}" stroke="#111" stroke-width="2"/>')
        S.append(texto(x + 58, y + 2, t, 16))
    S.append(texto(60, ly + 176, "Dica: o GND de TODAS as peças é o mesmo. Por isso há um fio preto largo embaixo e vários fios pretos curtos chegando nele.", 16, cor="#333"))
    S.append(texto(60, ly + 202, "Confira com a lista fio a fio do README: faça um traço em cada fio que montar.", 16, cor="#333"))
    S.append("</svg>")
    return "\n".join(S)


def frases():
    """Lista fio a fio (README). Cada linha: cor, de, para."""
    return [
        ("preto", "GND do Uno", "trilho preto de GND"),
        ("preto", "pino 8 do chip", "trilho preto de GND"),
        ("preto", "capacitor C1 (perna de baixo)", "trilho preto de GND"),
        ("preto", "emissor (E) do transistor", "trilho preto de GND"),
        ("preto", "LED vermelho (perna curta)", "trilho preto de GND"),
        ("preto", "LED amarelo (perna curta)", "trilho preto de GND"),
        ("preto", "negativo (−) da fonte", "trilho preto de GND"),
        ("laranja", "D2 do Uno", "pino 1 do chip e perna de cima do capacitor C1"),
        ("verde", "D4 do Uno", "pino 6 do chip"),
        ("azul", "D7 do Uno", "pino 7 do chip"),
        ("rosa", "pino 4 do chip (MCLR)", "resistor R1 (10 kΩ) e coletor (C) do transistor"),
        ("roxo", "A1 do Uno", "resistor R2 (4,7 kΩ), e dele à base (B) do transistor"),
        ("amarelo", "A5 do Uno", "resistor R3 (220 Ω), e dele à perna longa (+) do LED amarelo"),
        ("vermelho", "positivo (+) da fonte", "resistor R1 (o outro lado dele) e resistor R4 (1 kΩ), e dele à perna longa (+) do LED vermelho"),
    ]


def texto_readme():
    L = ["![Mapa das ligações](docs/esquema-simples.png)", "",
         "Lista **fio a fio** (faça um traço em cada fio que montar). Os fios pretos vão todos ao **GND**; o resto liga duas peças:", "",
         "| Feito | Cor do fio | De | Para |", "|:-:|---|---|---|"]
    for cor, de, para in frases():
        L.append(f"| ☐ | **{cor}** | {de} | {para} |")
    L += ["", "Os pinos 2, 3 e 5 do chip **não levam fio**. O desenho (`docs/esquema-simples.svg` e `.png`) sai de `scripts/esquema_simples.py`, "
          "que confere cada fio contra a tabela de ligações do verificador (`protoboard.py`) e para com erro se algum fio ligar o que não deve."]
    return "\n".join(L)


def injetar():
    import re
    readme = AQUI / "README.md"
    t = readme.read_text()
    bloco = "<!-- mapa -->\n" + texto_readme() + "\n<!-- /mapa -->"
    if "<!-- mapa -->" not in t:
        raise SystemExit("README sem os marcadores <!-- mapa --> ... <!-- /mapa -->")
    readme.write_text(re.sub(r"<!-- mapa -->.*?<!-- /mapa -->", lambda m: bloco, t, flags=re.S))


def main():
    erros = verificar()
    if erros:
        print("\n".join(erros))
        sys.exit(1)
    (OUT / "esquema-simples.svg").write_text(desenhar())
    svg_para_png(OUT / "esquema-simples.svg", OUT / "esquema-simples.png")
    injetar()
    print("ok: esquema-simples.svg/.png;", len(cruzamentos()), "pulinhos")


if __name__ == "__main__":
    main()
