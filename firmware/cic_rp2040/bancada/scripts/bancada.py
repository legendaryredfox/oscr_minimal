#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Protoboard de teste do CIC no RP2040: dados, verificador, desenhos passo a passo e texto do README.

Os desenhos (docs/passo-N.svg/.png) e as tabelas do README saem destes mesmos dados. O verificador confere, so no PC,
que cada fio e cada peca ligam exatamente o que `firmware/cic_rp2040/README.md` pede (nada foi montado de verdade).

Uso: python3 bancada.py            -> verifica, desenha (PNG pelo google-chrome) e reescreve o README
     python3 bancada.py --so-verificar
Convencao dos furos: letra da linha (a..j) + numero da coluna. Letras a-e = metade de baixo, f-j = metade de cima;
furos de mesmo numero e mesma metade estao ligados. Trilhos: T- e T+ (em cima), B- e B+ (embaixo), escritos "T-@44"
(trilho T- perto da coluna 44).
"""
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
OUT = AQUI / "docs"
README = AQUI / "README.md"

COR = {"preto": "#111111", "vermelho": "#d62828", "laranja": "#f77f00", "amarelo": "#eab308", "verde": "#2a9d48",
       "azul": "#1d4ed8", "roxo": "#9333ea", "branco": "#f5f5f5", "cinza": "#8a8a8a", "marrom": "#7b4a1e"}
FAIXAS = {"1k": ("marrom", "preto", "vermelho"), "2k": ("vermelho", "preto", "vermelho"),
          "3k3": ("laranja", "laranja", "vermelho"), "10k": ("marrom", "preto", "laranja")}
NOMER = {"1k": "1 kΩ", "2k": "2,0 kΩ", "3k3": "3,3 kΩ", "10k": "10 kΩ"}
CURTO = {"1k": "1k", "2k": "2k", "3k3": "3,3k", "10k": "10k"}
TRILHO = {"T-": "trilho − de cima", "T+": "trilho + de cima", "B-": "trilho − de baixo", "B+": "trilho + de baixo"}

IC0 = 44   # coluna do pino 1 do 74HCT125 (fileira e); pino 14 fica em f44
IC_PINOS = {}
for k in range(1, 8):
    IC_PINOS[str(k)] = f"e{IC0 + k - 1}"
for k in range(8, 15):
    IC_PINOS[str(k)] = f"f{IC0 + 14 - k}"

MOD_PINOS = {"5V": "e8", "GND": "e9", "3V3": "e10", "GP29": "e11", "GP28": "e12", "GP27": "e13", "GP26": "e14",
             "GP15": "e15", "GP14": "e16", "GP0": "i8", "GP1": "i9", "GP2": "i10", "GP3": "i11", "GP4": "i12",
             "GP5": "i13", "GP6": "i14", "GP7": "i15", "GP8": "i16"}
MOD_BLOQUEADO = {f"{l}{c}" for l in "fgh" for c in range(8, 17)}

PECAS = {
    "M1": dict(tipo="mod", nome="Módulo RP2040-Zero com os dois pinos macho soldados", pinos=MOD_PINOS),
    "D1": dict(tipo="diodo", nome="Diodo 1N5819 (faixa = lado K)", pinos={"A": "a4", "K": "a8"}),
    "R1": dict(tipo="res", v="1k", nome="Resistor 1 kΩ", pinos={"1": "b7", "2": "b11"}),
    "R2": dict(tipo="res", v="2k", nome="Resistor 2,0 kΩ", pinos={"1": "c18", "2": "c22"}),
    "R3": dict(tipo="res", v="3k3", nome="Resistor 3,3 kΩ", pinos={"1": "a22", "2": "B-@22"}),
    "R4": dict(tipo="res", v="2k", nome="Resistor 2,0 kΩ", pinos={"1": "c26", "2": "c30"}),
    "R5": dict(tipo="res", v="3k3", nome="Resistor 3,3 kΩ", pinos={"1": "a30", "2": "B-@30"}),
    "R6": dict(tipo="res", v="2k", nome="Resistor 2,0 kΩ", pinos={"1": "c34", "2": "c38"}),
    "R7": dict(tipo="res", v="3k3", nome="Resistor 3,3 kΩ", pinos={"1": "a38", "2": "B-@38"}),
    "U1": dict(tipo="ic", nome="Chip 74HCT125 (DIP-14)", pinos=IC_PINOS),
    "C1": dict(tipo="cap", nome="Capacitor 100 nF (marcado 104)", pinos={"1": "T+@30", "2": "T-@32"}),
    "R8": dict(tipo="res", v="10k", nome="Resistor 10 kΩ", pinos={"1": "a44", "2": "B+@44"}),
    "R9": dict(tipo="res", v="10k", nome="Resistor 10 kΩ", pinos={"1": "a47", "2": "B+@47"}),
    "R10": dict(tipo="res", v="10k", nome="Resistor 10 kΩ", pinos={"1": "j49", "2": "T-@49"}),
    "R11": dict(tipo="res", v="10k", nome="Resistor 10 kΩ", pinos={"1": "j46", "2": "T-@46"}),
}
# fios: id -> (de, para, cor, texto)
FIOS = {
    "W_GNDLINK": ("T-@2", "B-@2", "preto", "liga o trilho − de cima ao de baixo"),
    "W_MGND": ("a9", "B-@9", "preto", "GND do módulo ao trilho −"),
    "W_M3V3": ("a10", "B+@10", "laranja", "3V3 do módulo ao trilho +"),
    "W_5V": ("d4", "T+@4", "vermelho", "5 V da placa ao trilho + de cima"),
    "W_GP28": ("b12", "b22", "cinza", "GP28 ao divisor do D40"),
    "W_GP27": ("b13", "b30", "verde", "GP27 ao divisor do slot 24"),
    "W_GP26": ("b14", "b38", "azul", "GP26 ao divisor do slot 55"),
    "W_VCC": ("j44", "T+@44", "vermelho", "pino 14 do 74HCT125 aos 5 V"),
    "W_G13": ("j45", "T-@45", "preto", "pino 13 do 74HCT125 ao GND"),
    "W_G10": ("j48", "T-@48", "preto", "pino 10 do 74HCT125 ao GND"),
    "W_G7": ("a50", "B-@50", "preto", "pino 7 do 74HCT125 ao GND"),
    "W_GP15": ("b15", "b45", "azul", "GP15 ao pino 2 do 74HCT125"),
    "W_GP14": ("b16", "b48", "verde", "GP14 ao pino 5 do 74HCT125"),
    "W_GP0": ("j8", "b44", "marrom", "GP0 ao pino 1 do 74HCT125"),
    "W_GP1": ("j9", "b47", "marrom", "GP1 ao pino 4 do 74HCT125"),
    "W_GP2": ("j10", "g49", "roxo", "GP2 ao pino 9 do 74HCT125"),
    "W_GP3": ("j11", "g46", "branco", "GP3 ao pino 12 do 74HCT125"),
    "W_L24": ("d26", "d49", "verde", "slot 24 ao pino 6 do 74HCT125"),
    "W_L55": ("d34", "d46", "azul", "slot 55 ao pino 3 do 74HCT125"),
    "F1": ("U2.1", "c4", "vermelho", "pino 1 do soquete U2 (5 V)"),
    "F8": ("U2.8", "B-@5", "preto", "pino 8 do soquete U2 (GND)"),
    "F2": ("U2.2", "c7", "amarelo", "pino 2 do soquete U2 (CLK2)"),
    "F4": ("U2.4", "b18", "cinza", "pino 4 do soquete U2 (D40)"),
    "F6": ("U2.6", "b26", "verde", "pino 6 do soquete U2 (slot 24)"),
    "F7": ("U2.7", "b34", "azul", "pino 7 do soquete U2 (slot 55)"),
    "F3": ("U2.3", "h47", "branco", "pino 3 do soquete U2 (D41)"),
    "F5": ("U2.5", "h50", "roxo", "pino 5 do soquete U2 (slot 25)"),
}
PASSOS = [
    ("O módulo RP2040-Zero", ["M1"], [],
     "USB-C para a ESQUERDA. O módulo cobre as colunas 8 a 16. A fileira de pinos que tem 5V, GND e 3V3 vai na fileira e (embaixo); o 5V é o pino mais perto da USB-C, no furo e8. A outra fileira (GP0 em diante) vai na fileira i."),
    ("O fio de GND entre os trilhos", [], ["W_GNDLINK"],
     "Os trilhos de cima e de baixo precisam ser o mesmo GND. Se a sua protoboard tem o trilho cortado no meio, o fio vai no mesmo lado dos outros fios."),
    ("Energia do módulo", ["D1"], ["W_MGND", "W_M3V3", "W_5V"],
     "O diodo tem uma faixa prateada: a faixa fica do lado do módulo (furo a8). O fio vermelho do furo d4 vai no trilho + de cima."),
    ("Clock (CLK2)", ["R1"], [], "A perna do resistor no furo b7 fica na coluna 7, fora do módulo."),
    ("Divisor do D40", ["R2", "R3"], ["W_GP28"],
     "O resistor R3 fica em pé: uma perna no furo a22, a outra no trilho − de baixo."),
    ("Divisor do slot 24", ["R4", "R5"], ["W_GP27"], "R5 em pé, como o R3."),
    ("Divisor do slot 55", ["R6", "R7"], ["W_GP26"], "R7 em pé, como o R3."),
    ("O chip 74HCT125 e o capacitor", ["U1", "C1"], ["W_VCC"],
     "O chip cavalga o vão do meio, com o entalhe para a ESQUERDA (pino 1 em e44). O capacitor não tem lado; as pernas vão nos dois trilhos de cima."),
    ("Terra do 74HCT125", [], ["W_G13", "W_G10", "W_G7"], ""),
    ("Resistores de segurança", ["R8", "R9", "R10", "R11"], [],
     "R8 e R9 (puxam para 3,3 V) vão ao trilho + de baixo. R10 e R11 (puxam para GND) vão ao trilho − de cima. Todos em pé."),
    ("Fios GP15 e GP14", [], ["W_GP15", "W_GP14"], "Estes dois mandam os dados do módulo para o chip."),
    ("Fios GP0 e GP1 (ligam e desligam o chip)", [], ["W_GP0", "W_GP1"],
     "Estes fios saem da fileira de cima do módulo (furos j8 e j9), dão a volta pela direita do módulo e entram no chip por baixo."),
    ("Fios GP2 e GP3", [], ["W_GP2", "W_GP3"], ""),
    ("Fios dos divisores ao chip", [], ["W_L24", "W_L55"], ""),
    ("Fios do soquete U2: energia e clock", [], ["F1", "F8", "F2"],
     "Estes fios têm uma ponta na protoboard e outra que vai no soquete U2 da placa. Por enquanto deixe a ponta do soquete solta."),
    ("Fios do soquete U2: D40, slot 24 e slot 55", [], ["F4", "F6", "F7"], ""),
    ("Fios do soquete U2: D41 e slot 25", [], ["F3", "F5"], "Estes dois entram na metade de CIMA da protoboard (furos h47 e h50)."),
]
# corpo da protoboard esperado: conjuntos de pinos que devem estar na mesma rede
ESPERADO = [
    {"U2.1", "D1.A", "C1.1", "U1.14"},
    {"U2.8", "M1.GND", "C1.2", "U1.7", "U1.10", "U1.13", "R3.2", "R5.2", "R7.2", "R10.2", "R11.2"},
    {"D1.K", "M1.5V"},
    {"M1.3V3", "R8.2", "R9.2"},
    {"U2.2", "R1.1"}, {"R1.2", "M1.GP29"},
    {"U2.4", "R2.1"}, {"R2.2", "R3.1", "M1.GP28"},
    {"U2.6", "R4.1", "U1.6"}, {"R4.2", "R5.1", "M1.GP27"},
    {"U2.7", "R6.1", "U1.3"}, {"R6.2", "R7.1", "M1.GP26"},
    {"U2.5", "U1.8"}, {"U2.3", "U1.11"},
    {"M1.GP15", "U1.2"}, {"M1.GP14", "U1.5"},
    {"M1.GP0", "U1.1", "R8.1"}, {"M1.GP1", "U1.4", "R9.1"},
    {"M1.GP2", "U1.9", "R10.1"}, {"M1.GP3", "U1.12", "R11.1"},
]
LIVRES = ["M1.GP4", "M1.GP5", "M1.GP6", "M1.GP7", "M1.GP8"]
PLUGS_BAIXO = ["F8", "F1", "F2", "F4", "F6", "F7"]   # ordem da esquerda para a direita
PLUGS_CIMA = ["F3", "F5"]
COLS_MAX = 52


def parse(e):
    """endpoint -> ('furo', letra, col) | ('trilho', nome, col) | ('plug', nome)"""
    if e.startswith("U2."):
        return ("plug", e)
    m = re.fullmatch(r"([TB][+-])@(\d+)", e)
    if m:
        return ("trilho", m.group(1), int(m.group(2)))
    m = re.fullmatch(r"([a-j])(\d+)", e)
    if m:
        return ("furo", m.group(1), int(m.group(2)))
    raise ValueError(e)


def no(e):
    p = parse(e)
    if p[0] == "furo":
        return ("meio" if False else ("B" if p[1] in "abcde" else "T"), p[2])
    if p[0] == "trilho":
        return ("rail", p[1])
    return p


def verificar():
    erros = []
    pai = {}

    def f(a):
        pai.setdefault(a, a)
        while pai[a] != a:
            pai[a] = pai[pai[a]]
            a = pai[a]
        return a

    ocupado = {}     # furo/trilho exato -> quem
    pads = {}
    for ref, p in PECAS.items():
        for pino, e in p["pinos"].items():
            nome = f"{ref}.{pino}"
            if e in ocupado:
                erros.append(f"{nome} e {ocupado[e]} no mesmo furo {e}")
            ocupado[e] = nome
            if parse(e)[0] == "furo" and not 1 <= parse(e)[2] <= COLS_MAX:
                erros.append(f"{nome}: coluna fora do desenho {e}")
            if p["tipo"] != "mod" and e in MOD_BLOQUEADO:
                erros.append(f"{nome} cai debaixo do módulo ({e})")
            pads[nome] = no(e)
    for fid, (a, b, cor, txt) in FIOS.items():
        for e in (a, b):
            if e.startswith("U2."):
                continue
            if e in ocupado:
                erros.append(f"fio {fid} cai em {e}, ocupado por {ocupado[e]}")
            ocupado[e] = fid
            if e in MOD_BLOQUEADO:
                erros.append(f"fio {fid} cai debaixo do módulo ({e})")
            if parse(e)[0] == "furo" and not 1 <= parse(e)[2] <= COLS_MAX:
                erros.append(f"fio {fid}: coluna fora do desenho {e}")
        pai[f(no(a))] = f(no(b))
    for i in range(1, 9):
        pads[f"U2.{i}"] = ("plug", f"U2.{i}")
    grupos = {}
    for nome, t in pads.items():
        grupos.setdefault(f(t), set()).add(nome)
    achados = [s for s in grupos.values() if len(s) > 1]
    for e in ESPERADO:
        if e not in achados:
            erros.append(f"falta (ou junta demais): {sorted(e)}")
    for s in achados:
        if s not in ESPERADO:
            erros.append(f"a mais: {sorted(s)}")
    for p in LIVRES:
        if any(p in s for s in achados):
            erros.append(p + " devia ficar livre")
    pf = [x for _, _, fs, _ in PASSOS for x in fs]
    pp = [x for _, ps, _, _ in PASSOS for x in ps]
    if sorted(pf) != sorted(FIOS):
        erros.append("fios fora dos passos ou repetidos")
    if sorted(pp) != sorted(PECAS):
        erros.append("pecas fora dos passos ou repetidas")
    # um chip 74HCT125 tem 14 pinos; o ic cavalga o vao (pinos 1-7 em e, 8-14 em f, mesma coluna de 14 e 1)
    if IC_PINOS["14"] != f"f{IC0}":
        erros.append("pino 14 do chip fora do lugar")
    return erros


# ------------------------------------------------------------------ desenho
P = 28
X0 = 150
W, H = 1700, 1010
YR = {}
YR["T+"] = 170
YR["T-"] = 198
for i, l in enumerate("jihgf"):
    YR[l] = 254 + i * P
YR["e"] = YR["f"] + 3 * P
for i, l in enumerate("edcba"):
    YR[l] = YR["e"] + i * P
YR["B-"] = YR["a"] + 2 * P
YR["B+"] = YR["B-"] + P
FUNDO = "#f4efe1"
FAIXA_COR = {"marrom": "#7b4a1e", "preto": "#111", "laranja": "#f77f00", "vermelho": "#d62828"}


def x(c):
    return X0 + (c - 1) * P


def ponto(e, plugs):
    p = parse(e)
    if p[0] == "furo":
        return (x(p[2]), YR[p[1]])
    if p[0] == "trilho":
        return (x(p[2]), YR[p[1]])
    return plugs[e]


def drawing(passo, saida):
    """passo = 1..n ou 0 (completo)"""
    ate = len(PASSOS) if passo == 0 else passo
    pecas_ok, fios_ok, novas_p, novos_f = [], [], [], []
    for i, (_, ps, fs, _) in enumerate(PASSOS, 1):
        if i <= ate:
            pecas_ok += ps
            fios_ok += fs
            if i == passo:
                novas_p, novos_f = ps, fs
    # posicoes dos plugs (caixas): embaixo e em cima
    plugs = {}
    for k, fid in enumerate(PLUGS_BAIXO):
        plugs[FIOS[fid][0]] = (200 + k * 215, 905)
    for k, fid in enumerate(PLUGS_CIMA):
        plugs[FIOS[fid][0]] = (x(44) + k * 215, 38)
    S = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="DejaVu Sans, sans-serif">',
         f'<rect width="{W}" height="{H}" fill="{FUNDO}"/>']
    bx0, bx1, by0, by1 = x(1) - 40, x(COLS_MAX) + 40, YR["T+"] - 28, YR["B+"] + 28
    S.append(f'<rect x="{bx0}" y="{by0}" width="{bx1 - bx0}" height="{by1 - by0}" rx="10" fill="#e9e9e4" stroke="#9a9a90" stroke-width="2"/>')
    gap_y = (YR["f"] + YR["e"]) / 2
    S.append(f'<rect x="{bx0 + 6}" y="{gap_y - 12}" width="{bx1 - bx0 - 12}" height="24" fill="#cfcfc6"/>')
    S.append(f'<text x="{(bx0 + bx1) / 2}" y="{gap_y + 5}" font-size="14" text-anchor="middle" fill="#777">vão do meio</text>')
    for c in range(1, COLS_MAX + 1):
        for l in "jihgfedcba":
            S.append(f'<circle cx="{x(c)}" cy="{YR[l]}" r="4.5" fill="#555"/>')
        for r in ("T+", "T-", "B+", "B-"):
            S.append(f'<circle cx="{x(c)}" cy="{YR[r]}" r="3.5" fill="#777"/>')
        if c % 2 == 0 or c < 10:
            S.append(f'<text x="{x(c)}" y="{YR["j"] - 14}" font-size="12" text-anchor="middle" fill="#333">{c}</text>')
            S.append(f'<text x="{x(c)}" y="{YR["a"] + 22}" font-size="12" text-anchor="middle" fill="#333">{c}</text>')
    for l in "jihgfedcba":
        S.append(f'<text x="{x(1) - 22}" y="{YR[l] + 5}" font-size="14" font-weight="bold" text-anchor="middle" fill="#333">{l}</text>')
    for r, cor, nome in (("T+", "#d62828", "+ 5 V"), ("T-", "#1d4ed8", "− GND"),
                         ("B-", "#1d4ed8", "− GND"), ("B+", "#f77f00", "+ 3,3 V")):
        S.append(f'<line x1="{x(1) - 10}" y1="{YR[r]}" x2="{x(COLS_MAX) + 10}" y2="{YR[r]}" stroke="{cor}" stroke-width="3" opacity=".6"/>')
        S.append(f'<text x="{x(1) - 48}" y="{YR[r] + 5}" font-size="14" font-weight="bold" text-anchor="end" fill="{cor}">{nome}</text>')
    S.append(f'<text x="{x(1) - 48}" y="{YR["T-"] - 36}" font-size="12" text-anchor="end" fill="#555">trilhos de cima</text>')
    S.append(f'<text x="{x(1) - 48}" y="{YR["B+"] + 28}" font-size="12" text-anchor="end" fill="#555">trilhos de baixo</text>')

    def glow(x1, y1, x2, y2):
        S.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" rx="8" fill="#fde047" fill-opacity=".5" stroke="#ca8a04" stroke-width="2" stroke-dasharray="6 4"/>')

    def tag(txt, tx, ty):
        w = 10 + 8.6 * len(txt)
        S.append(f'<rect x="{tx - w / 2}" y="{ty - 13}" width="{w}" height="19" rx="4" fill="#111" fill-opacity=".88"/>')
        S.append(f'<text x="{tx}" y="{ty + 2}" font-size="14" font-weight="bold" text-anchor="middle" fill="#fff">{txt}</text>')

    # ---- pecas
    for ref in pecas_ok:
        p = PECAS[ref]
        novo = ref in novas_p
        pos = {k: ponto(e, plugs) for k, e in p["pinos"].items()}
        t = p["tipo"]
        if t == "mod":
            xa, xb = x(8) - 26, x(16) + 26
            ya, yb = YR["i"] - 24, YR["e"] + 24
            if novo:
                glow(xa - 70, ya - 10, xb + 10, yb + 10)
            S.append(f'<rect x="{xa - 38}" y="{(ya + yb) / 2 - 38}" width="42" height="76" rx="6" fill="#bbb" stroke="#555" stroke-width="2"/>')
            S.append(f'<text x="{xa - 17}" y="{(ya + yb) / 2 + 5}" font-size="13" font-weight="bold" text-anchor="middle" fill="#111" transform="rotate(-90 {xa - 17} {(ya + yb) / 2})">USB-C</text>')
            S.append(f'<rect x="{xa}" y="{ya}" width="{xb - xa}" height="{yb - ya}" rx="6" fill="#2a2f45" fill-opacity=".92" stroke="#111" stroke-width="2"/>')
            S.append(f'<text x="{(xa + xb) / 2}" y="{(ya + yb) / 2 + 6}" font-size="20" font-weight="bold" text-anchor="middle" fill="#fff">RP2040-Zero</text>')
            for k, (px, py) in pos.items():
                usado = k not in ("GP4", "GP5", "GP6", "GP7", "GP8")
                S.append(f'<circle cx="{px}" cy="{py}" r="8" fill="{"#e8c547" if usado else "#888"}" stroke="#111"/>')
                dy = -14 if py == YR["e"] else 21
                S.append(f'<text x="{px}" y="{py + dy}" font-size="11" text-anchor="middle" fill="#fff">{k.replace("GP", "")}</text>')
        elif t == "res":
            (x1, y1), (x2, y2) = pos["1"], pos["2"]
            vert = abs(x1 - x2) < 3
            if novo:
                glow(min(x1, x2) - 14, min(y1, y2) - 16, max(x1, x2) + 14, max(y1, y2) + 16)
            S.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#777" stroke-width="3"/>')
            if vert:
                cy = (y1 + y2) / 2
                S.append(f'<rect x="{x1 - 8}" y="{cy - 20}" width="16" height="40" rx="7" fill="#e7d3a1" stroke="#8a7a3a"/>')
                for k, fy in enumerate((-13, -6, 1)):
                    S.append(f'<rect x="{x1 - 8}" y="{cy + fy}" width="16" height="4" fill="{FAIXA_COR[FAIXAS[p["v"]][k]] if FAIXAS[p["v"]][k] in FAIXA_COR else {"vermelho": "#d62828"}.get(FAIXAS[p["v"]][k], "#111")}"/>')
                S.append(f'<rect x="{x1 - 8}" y="{cy + 10}" width="16" height="4" fill="#c9a227"/>')
                lado = -1 if ref == "R11" else 1
                if y1 < YR["e"]:       # resistor de cima: o rotulo fica na fileira i, ao lado
                    ty = YR["i"] + 5
                else:                  # resistor de baixo: o rotulo fica abaixo do trilho +
                    ty = YR["B+"] + 22
                S.append(f'<text x="{x1 + 12 * lado}" y="{ty}" font-size="13" font-weight="bold" text-anchor="{"end" if lado < 0 else "start"}" fill="#111" stroke="#f4efe1" stroke-width="4" paint-order="stroke">{ref} {CURTO[p["v"]]}</text>')
            else:
                bx, bw = min(x1, x2) + 14, abs(x2 - x1) - 28
                S.append(f'<rect x="{bx}" y="{y1 - 9}" width="{bw}" height="18" rx="8" fill="#e7d3a1" stroke="#8a7a3a"/>')
                for k, fx in enumerate((0.2, 0.34, 0.48)):
                    c = FAIXAS[p["v"]][k]
                    S.append(f'<rect x="{bx + bw * fx}" y="{y1 - 9}" width="6" height="18" fill="{ {"marrom": "#7b4a1e", "preto": "#111", "laranja": "#f77f00", "vermelho": "#d62828"}[c] }"/>')
                S.append(f'<rect x="{bx + bw * 0.76}" y="{y1 - 9}" width="6" height="18" fill="#c9a227"/>')
                S.append(f'<text x="{(x1 + x2) / 2}" y="{y1 - 14}" font-size="12" font-weight="bold" text-anchor="middle" fill="#111">{ref} {NOMER[p["v"]]}</text>')
        elif t == "diodo":
            (x1, y1), (x2, y2) = pos["A"], pos["K"]
            if novo:
                glow(x1 - 14, y1 - 22, x2 + 14, y1 + 22)
            S.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#777" stroke-width="3"/>')
            S.append(f'<rect x="{x1 + 18}" y="{y1 - 9}" width="{x2 - x1 - 36}" height="18" rx="4" fill="#222" stroke="#000"/>')
            S.append(f'<rect x="{x2 - 34}" y="{y1 - 9}" width="8" height="18" fill="#cfd3d8"/>')
            S.append(f'<text x="{(x1 + x2) / 2}" y="{y1 - 14}" font-size="12" font-weight="bold" text-anchor="middle" fill="#111">D1</text>')
        elif t == "cap":
            (x1, y1), (x2, y2) = pos["1"], pos["2"]
            if novo:
                glow(x1 - 18, y1 - 24, x2 + 18, y2 + 24)
            S.append(f'<line x1="{x1}" y1="{y1}" x2="{x1}" y2="{(y1 + y2) / 2}" stroke="#777" stroke-width="3"/>')
            S.append(f'<line x1="{x2}" y1="{y2}" x2="{x2}" y2="{(y1 + y2) / 2}" stroke="#777" stroke-width="3"/>')
            S.append(f'<rect x="{x1 - 2}" y="{(y1 + y2) / 2 - 11}" width="{x2 - x1 + 4}" height="22" rx="9" fill="#f4a261" stroke="#8a4b1a"/>')
            S.append(f'<text x="{(x1 + x2) / 2}" y="{(y1 + y2) / 2 + 5}" font-size="11" font-weight="bold" text-anchor="middle" fill="#111">104</text>')
        elif t == "ic":
            x1, x7 = pos["1"][0], pos["7"][0]
            yb, yt = pos["1"][1], pos["14"][1]
            if novo:
                glow(x1 - 24, yt - 26, x7 + 24, yb + 26)
            S.append(f'<rect x="{x1 - 16}" y="{yt - 12}" width="{x7 - x1 + 32}" height="{yb - yt + 24}" rx="6" fill="#3a3a3a" stroke="#111" stroke-width="2"/>')
            S.append(f'<path d="M{x1 - 16} {(yt + yb) / 2 - 10} a 10 10 0 0 1 0 20" fill="#e9e9e4" stroke="#111"/>')
            S.append(f'<text x="{(x1 + x7) / 2}" y="{(yt + yb) / 2 + 5}" font-size="15" font-weight="bold" text-anchor="middle" fill="#fff">74HCT125</text>')
            for k, (px, py) in pos.items():
                S.append(f'<circle cx="{px}" cy="{py}" r="9" fill="#c0c0c0" stroke="#111"/>')
                S.append(f'<text x="{px}" y="{py + 4}" font-size="11" font-weight="bold" text-anchor="middle" fill="#111">{k}</text>')
        if novo:
            for k, e in p["pinos"].items():
                if t == "mod" and k not in ("5V", "GND", "GP0", "GP14"):
                    continue
                if t == "ic" and k not in ("1", "7", "8", "14"):
                    continue
                px, py = pos[k]
                tag(e if parse(e)[0] == "furo" else e, px, py + (34 if py >= YR["e"] or e[0] in "B" else -26))
        if t in ("res", "diodo", "cap"):
            for k, (px, py) in pos.items():
                S.append(f'<circle cx="{px}" cy="{py}" r="5.5" fill="#bbb" stroke="#111" stroke-width="1.5"/>')

    # ---- plugs e fios
    def caixa(nome, px, py, cor, novo, txt):
        w = 196
        if novo:
            S.append(f'<rect x="{px - w / 2 - 6}" y="{py - 25}" width="{w + 12}" height="50" rx="10" fill="#fde047" fill-opacity=".65"/>')
        S.append(f'<rect x="{px - w / 2}" y="{py - 21}" width="{w}" height="42" rx="7" fill="#fff" stroke="{cor}" stroke-width="5"/>')
        S.append(f'<text x="{px}" y="{py - 4}" font-size="15" font-weight="bold" text-anchor="middle" fill="#111">{nome}</text>')
        S.append(f'<text x="{px}" y="{py + 14}" font-size="12" text-anchor="middle" fill="#333">{txt}</text>')

    lane_top, lane_bot = [0], [0]

    def lane_t():
        lane_top[0] += 1
        return 150 - 10 * lane_top[0] + 4 if False else 130 - 9 * lane_top[0]

    def lane_b():
        lane_bot[0] += 1
        return YR["B+"] + 22 + 9 * lane_bot[0]

    def meia(e):
        p = parse(e)
        if p[0] == "furo":
            return "T" if p[1] in "fghij" else "B"
        if p[0] == "trilho":
            return "T" if p[1][0] == "T" else "B"
        return "P"

    # ordem de desenho: todos, mas as faixas (lanes) so contam os fios presentes
    for fid, (a, b, cor, txt) in FIOS.items():
        if fid not in fios_ok:
            lane_t() if False else None
            continue
        novo = fid in novos_f
        c = COR[cor]
        pa, pb_ = ponto(a, plugs), ponto(b, plugs)
        ma, mb = meia(a), meia(b)
        pts = None
        if fid == "W_GNDLINK":
            pts = [pa, (x(1) - 30, pa[1]), (x(1) - 30, pb_[1]), pb_]
        elif parse(a)[0] == "plug" or parse(b)[0] == "plug":
            plug = a if parse(a)[0] == "plug" else b
            hole = b if plug == a else a
            if parse(hole)[0] == "trilho":      # plug direto ao trilho (F8)
                lane = lane_b()
                pts = [plugs[plug], (plugs[plug][0], lane), (ponto(hole, plugs)[0], lane), ponto(hole, plugs)]
            elif meia(hole) == "T":
                lane = lane_t()
                pp = plugs[plug]
                hp = ponto(hole, plugs)
                pts = [pp, (pp[0], lane), (hp[0], lane), hp]
            else:
                lane = lane_b()
                pp = plugs[plug]
                hp = ponto(hole, plugs)
                pts = [pp, (pp[0], lane), (hp[0], lane), hp]
        elif parse(a)[0] == "trilho" or parse(b)[0] == "trilho":
            pts = [pa, pb_]
        elif ma == mb == "B":
            lane = lane_b()
            pts = [pa, (pa[0], lane), (pb_[0], lane), pb_]
        elif ma == mb == "T":
            lane = lane_t()
            pts = [pa, (pa[0], lane), (pb_[0], lane), pb_]
        else:     # atravessa pelo lado direito do modulo
            top, bot = (pa, pb_) if ma == "T" else (pb_, pa)
            lt, lb = lane_t(), lane_b()
            xc = x(41) + 9 * lane_bot[0]
            pts = [top, (top[0], lt), (xc, lt), (xc, lb), (bot[0], lb), bot]
        path = " ".join(f"{u},{v}" for u, v in pts)
        if novo:
            S.append(f'<polyline points="{path}" fill="none" stroke="#fde047" stroke-width="15" stroke-linecap="round" stroke-linejoin="round" opacity=".75"/>')
        S.append(f'<polyline points="{path}" fill="none" stroke="#fff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>')
        S.append(f'<polyline points="{path}" fill="none" stroke="{c}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>')
        for (u, v) in (pts[0], pts[-1]):
            S.append(f'<circle cx="{u}" cy="{v}" r="6" fill="{c}" stroke="#555" stroke-width="2"/>')
        for e in (a, b):
            if parse(e)[0] == "plug":
                caixa("soquete U2 pino " + e[3:], plugs[e][0], plugs[e][1], c, novo, txt.split("(")[-1].rstrip(")") if "(" in txt else "")
        if novo:
            for e in (a, b):
                if parse(e)[0] == "furo":
                    u, v = ponto(e, plugs)
                    tag(e, u, v + (34 if meia(e) == "B" else -26))
                elif parse(e)[0] == "trilho":
                    u, v = ponto(e, plugs)
                    tag(TRILHO[parse(e)[1]].replace("trilho ", ""), u, v + (-22 if parse(e)[1] in ("T+", "B-") else 30))
    # titulo
    if passo == 0:
        titulo = "MONTAGEM COMPLETA (confira com a lista de passos)"
    else:
        titulo = f"PASSO {passo} de {len(PASSOS)}: {PASSOS[passo - 1][0]}"
    S.append(f'<text x="30" y="{H - 14}" font-size="20" font-weight="bold" fill="#111">{titulo}</text>')
    S.append("</svg>")
    nome = "montagem-completa" if passo == 0 else f"passo-{passo}"
    (OUT / f"{nome}.svg").write_text("\n".join(S))
    return nome


def svg_para_png(svg, png):
    m = re.search(r'width="(\d+)" height="(\d+)"', Path(svg).read_text())
    w, h = int(m.group(1)), int(m.group(2))
    for exe in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        try:
            subprocess.run([exe, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", f"--screenshot={png}",
                            f"--window-size={w},{h}", Path(svg).resolve().as_uri()], capture_output=True, check=True, timeout=120)
            return
        except FileNotFoundError:
            continue
    raise SystemExit("precisa do google-chrome ou chromium para gerar os PNG")


# ------------------------------------------------------------------ texto
def onde_peca(p):
    if p["tipo"] == "mod":
        return "pino **5V** em **e8** (USB-C para a esquerda); pinos 5V, GND, 3V3, GP29, GP28, GP27, GP26, GP15, GP14 em e8 a e16; GP0 a GP8 em i8 a i16"
    if p["tipo"] == "ic":
        return f"entalhe para a esquerda; **pino 1 em e{IC0}**, pinos 1 a 7 em e{IC0} a e{IC0 + 6}, pino 14 em f{IC0} e pinos 14 a 8 em f{IC0} a f{IC0 + 6}"
    def n(k, e):
        q = parse(e)
        return f"perna {k} em **{e}**" if q[0] == "furo" else f"perna {k} no **{TRILHO[q[1]]}**"
    return ", ".join(n(k + (" (a da faixa)" if k == "K" else ""), e) for k, e in p["pinos"].items())


def nome_ponta(e):
    q = parse(e)
    if q[0] == "plug":
        return f"soquete **U2**, pino **{e[3:]}**"
    if q[0] == "trilho":
        return f"**{TRILHO[q[1]]}**"
    return f"furo **{e}**"


def texto_passos():
    L = []
    for i, (titulo, ps, fs, nota) in enumerate(PASSOS, 1):
        L.append(f"#### Passo {i}: {titulo}")
        L.append("")
        L.append(f"![Passo {i}](docs/passo-{i}.png)")
        L.append("")
        L.append("| Feito | O que | Onde |")
        L.append("|:-:|---|---|")
        for ref in ps:
            p = PECAS[ref]
            extra = ""
            if p["tipo"] == "res":
                extra = f" (faixas {', '.join(FAIXAS[p['v']])}, dourado)"
            L.append(f"| ☐ | **{ref}**: {p['nome']}{extra} | {onde_peca(p)} |")
        for fid in fs:
            a, b, cor, txt = FIOS[fid]
            L.append(f"| ☐ | fio **{cor}** ({txt}) | do {nome_ponta(a)} ao {nome_ponta(b)} |")
        L.append("")
        if nota:
            L.append(f"> {nota}")
            L.append("")
    return "\n".join(L)


def texto_fios():
    L = ["| Feito | Cor | De | Para | O que faz |", "|:-:|---|---|---|---|"]
    for fid, (a, b, cor, txt) in FIOS.items():
        L.append(f"| ☐ | **{cor}** | {nome_ponta(a)} | {nome_ponta(b)} | {txt} |")
    return "\n".join(L)


def texto_material():
    return "\n".join([
        "| Qtd | Peça | Ref. | Como reconhecer |", "|---|---|---|---|",
        "| 1 | Placa 16_bits v1.0 (ou v1.2) pronta, com o Mega, o módulo Si5351 e **sem o PIC** no soquete U2 | | |",
        "| 1 | Módulo **Waveshare RP2040-Zero** | M1 | placa pequena, 18 × 23,5 mm, USB-C numa ponta |",
        "| 2 | Barras de pinos macho 1×9, passo 2,54 mm | | soldadas no módulo (ver \"Antes de começar\") |",
        "| 1 | Chip **SN74HCT125N** (DIP-14) | U1 | 14 pernas. Tem que ter o **T** no nome: o 74HC125 **não serve** |",
        "| 1 | Diodo **1N5819** | D1 | preto, com uma faixa prateada de um lado |",
        "| 1 | Capacitor 100 nF | C1 | disquinho laranja marcado **104** |",
        "| 1 | Resistor 1 kΩ | R1 | faixas: marrom, preto, vermelho, dourado |",
        "| 3 | Resistor 2,0 kΩ | R2, R4, R6 | faixas: vermelho, preto, vermelho, dourado |",
        "| 3 | Resistor 3,3 kΩ | R3, R5, R7 | faixas: laranja, laranja, vermelho, dourado |",
        "| 4 | Resistor 10 kΩ | R8 a R11 | faixas: marrom, preto, laranja, dourado |",
        "| 1 | Protoboard de 830 pontos | | com 4 trilhos: 2 em cima e 2 embaixo (o desenho usa as colunas 1 a 52) |",
        "| 27 | Fios macho-macho (jumpers) | | 8 deles vão ao soquete U2 (a ponta macho entra no furo do soquete; se ficar frouxa, prenda com um pouco de fita). Misture comprimentos de 10 cm e 20 cm; os fios do módulo ao chip 74HCT125 precisam de 20 cm |",
        "| 1 | Cabo USB-C | | para gravar e ver os números do módulo |",
        "| 1 | Multímetro | | |",
        "| 1 | Cartucho de SNES com SA-1 (Super Mario RPG, Kirby Super Star...) | | para o teste de verdade |",
    ])


def cobrir(s, nome, bloco):
    pad = re.compile(rf"<!-- {nome} -->.*?<!-- /{nome} -->", re.S)
    novo = f"<!-- {nome} -->\n{bloco}\n<!-- /{nome} -->"
    if not pad.search(s):
        raise SystemExit(f"README sem os marcadores {nome}")
    return pad.sub(lambda m: novo, s)


def injetar():
    s = README.read_text()
    s = cobrir(s, "material", texto_material())
    s = cobrir(s, "fios", texto_fios())
    s = cobrir(s, "passos", texto_passos())
    README.write_text(s)


def main():
    erros = verificar()
    if erros:
        print("\n".join(erros))
        sys.exit(1)
    print("verificador ok:", len(PECAS), "pecas,", len(FIOS), "fios,", len(ESPERADO), "redes")
    if "--so-verificar" in sys.argv:
        return
    OUT.mkdir(parents=True, exist_ok=True)
    nomes = [drawing(i, None) for i in range(1, len(PASSOS) + 1)] + [drawing(0, None)]
    for n in nomes:
        svg_para_png(OUT / f"{n}.svg", OUT / f"{n}.png")
    injetar()
    print("ok:", len(nomes), "figuras")


if __name__ == "__main__":
    main()
