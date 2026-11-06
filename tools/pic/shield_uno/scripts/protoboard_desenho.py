#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-SA-2.5
"""Desenha a montagem na protoboard passo a passo (docs/protoboard/*.svg e .png) e gera o texto das instrucoes no README.

Os dados vem de protoboard.py (a mesma fonte do verificador). Precisa do google-chrome (ou chromium) para os PNG.
Uso: python3 tools/pic/shield_uno/scripts/protoboard_desenho.py
"""
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import protoboard as pb  # noqa: E402

AQUI = Path(__file__).resolve().parent.parent
OUT = AQUI / "docs" / "protoboard"
README = AQUI / "README.md"

P = 34
X0 = 250
YR = {"rail+": 130, "rail-": 164, "j": 230, "i": 264, "h": 298, "g": 332, "f": 366, "e": 430, "d": 464, "c": 498, "b": 532, "a": 566}
COLS = list(pb.COLS)
W, H = 1270, 760
FUNDO = "#f4efe1"
FAIXA = {"marrom": "#7b4a1e", "preto": "#111", "laranja": "#f77f00", "amarelo": "#eab308", "violeta": "#7c3aed", "vermelho": "#d62828", "dourado": "#c9a227"}


def x(c):
    return X0 + (c - 7) * P


def furo(h):
    return x(int(h[1:])), YR[h[0]]


def nome_pino_uno(dest):
    return dest[4:]


def desenhar(passo):
    """passo = indice (1..n) ou 0 para a montagem completa"""
    ate = len(pb.PASSOS) if passo == 0 else passo
    pecas_ok, fios_ok, novas_p, novos_f = [], [], [], []
    for i, (_, ps, fs, _) in enumerate(pb.PASSOS, 1):
        if i <= ate:
            pecas_ok += ps
            fios_ok += fs
            if i == passo:
                novas_p, novos_f = ps, fs
    S = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="DejaVu Sans, sans-serif">',
         f'<rect width="{W}" height="{H}" fill="{FUNDO}"/>']
    # tabuleiro
    bx0, bx1, by0, by1 = x(7) - 34, x(30) + 34, 100, 604
    S.append(f'<rect x="{bx0}" y="{by0}" width="{bx1 - bx0}" height="{by1 - by0}" rx="10" fill="#e9e9e4" stroke="#9a9a90" stroke-width="2"/>')
    S.append(f'<rect x="{bx0 + 6}" y="{(YR["f"] + YR["e"]) / 2 - 8}" width="{bx1 - bx0 - 12}" height="16" fill="#cfcfc6"/>')
    for c in COLS:
        for l in "jihgfedcba":
            S.append(f'<circle cx="{x(c)}" cy="{YR[l]}" r="4.2" fill="#555"/>')
        for r in ("rail+", "rail-"):
            S.append(f'<circle cx="{x(c)}" cy="{YR[r]}" r="4.2" fill="#555"/>')
        S.append(f'<text x="{x(c)}" y="{YR["j"] - 18}" font-size="11" text-anchor="middle" fill="#333">{c}</text>')
        S.append(f'<text x="{x(c)}" y="{YR["a"] + 24}" font-size="11" text-anchor="middle" fill="#333">{c}</text>')
    for l in "jihgfedcba":
        S.append(f'<text x="{x(7) - 20}" y="{YR[l] + 4}" font-size="12" font-weight="bold" text-anchor="middle" fill="#333">{l}</text>')
    S.append(f'<line x1="{x(7) - 12}" y1="{YR["rail+"]}" x2="{x(30) + 12}" y2="{YR["rail+"]}" stroke="#d62828" stroke-width="3" opacity=".7"/>')
    S.append(f'<line x1="{x(7) - 12}" y1="{YR["rail-"]}" x2="{x(30) + 12}" y2="{YR["rail-"]}" stroke="#1d4ed8" stroke-width="3" opacity=".7"/>')
    S.append(f'<text x="{x(14)}" y="{YR["rail+"] - 10}" font-size="12" font-weight="bold" fill="#d62828">TRILHO + (13 V)</text>')
    S.append(f'<text x="{x(14)}" y="{YR["rail-"] + 18}" font-size="12" font-weight="bold" fill="#1d4ed8">TRILHO − (GND)</text>')
    S.append(f'<text x="{(bx0 + bx1) / 2}" y="{(YR["f"] + YR["e"]) / 2 + 4}" font-size="11" text-anchor="middle" fill="#777">vão do meio</text>')

    def glow_rect(x1, y1, x2, y2):
        S.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" rx="8" fill="#fde047" fill-opacity=".45" stroke="#ca8a04" stroke-width="2" stroke-dasharray="6 4"/>')

    def tag(txt, tx, ty):
        w = 8 + 7.2 * len(txt)
        S.append(f'<rect x="{tx - w / 2}" y="{ty - 11}" width="{w}" height="16" rx="4" fill="#111" fill-opacity=".85"/>')
        S.append(f'<text x="{tx}" y="{ty + 1}" font-size="11" font-weight="bold" text-anchor="middle" fill="#fff">{txt}</text>')

    # pecas
    for ref in pecas_ok:
        p = pb.PECAS[ref]
        novo = ref in novas_p
        pos = {k: furo(h) for k, h in p["pinos"].items()}
        tipo = p["tipo"]
        if tipo == "res":
            (x1, y1), (x2, y2) = pos["1"], pos["2"]
            if novo:
                glow_rect(x1 - 14, y1 - 22, x2 + 14, y1 + 22)
            S.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#777" stroke-width="3"/>')
            bx, bw = x1 + 14, (x2 - x1) - 28
            S.append(f'<rect x="{bx}" y="{y1 - 9}" width="{bw}" height="18" rx="8" fill="#e7d3a1" stroke="#8a7a3a"/>')
            for k, fx in enumerate((0.2, 0.34, 0.48)):
                S.append(f'<rect x="{bx + bw * fx}" y="{y1 - 9}" width="6" height="18" fill="{FAIXA[p["faixas"][k]]}"/>')
            S.append(f'<rect x="{bx + bw * 0.76}" y="{y1 - 9}" width="6" height="18" fill="{FAIXA["dourado"]}"/>')
            S.append(f'<text x="{(x1 + x2) / 2}" y="{y1 - 14}" font-size="12" font-weight="bold" text-anchor="middle" fill="#111">{ref}  {p["nome"].replace("Resistor ", "")}</text>')
        elif tipo == "cap":
            (x1, y1), (x2, y2) = pos["1"], pos["2"]
            xa, xb = min(x1, x2), max(x1, x2)
            if novo:
                glow_rect(xa - 14, y1 - 24, xb + 14, y1 + 24)
            S.append(f'<line x1="{xa}" y1="{y1}" x2="{xb}" y2="{y1}" stroke="#777" stroke-width="3"/>')
            S.append(f'<rect x="{xa + 6}" y="{y1 - 13}" width="{xb - xa - 12}" height="26" rx="10" fill="#f4a261" stroke="#8a4b1a"/>')
            S.append(f'<text x="{(xa + xb) / 2}" y="{y1 + 4}" font-size="11" font-weight="bold" text-anchor="middle" fill="#111">104</text>')
            S.append(f'<text x="{(xa + xb) / 2}" y="{y1 - 18}" font-size="12" font-weight="bold" text-anchor="middle" fill="#111">C1 100 nF</text>')
        elif tipo == "led":
            (xa_, ya), (xk, yk) = pos["A"], pos["K"]
            cor = {"vermelho": "#e63946", "amarelo": "#facc15"}[p["cor"]]
            if novo:
                glow_rect(min(xa_, xk) - 16, ya - 28, max(xa_, xk) + 16, ya + 26)
            S.append(f'<line x1="{xa_}" y1="{ya}" x2="{xa_}" y2="{ya - 4}" stroke="#777" stroke-width="3"/>')
            S.append(f'<circle cx="{(xa_ + xk) / 2}" cy="{ya}" r="19" fill="{cor}" fill-opacity=".75" stroke="#333" stroke-width="2"/>')
            S.append(f'<text x="{xa_}" y="{ya + 5}" font-size="16" font-weight="bold" text-anchor="middle" fill="#111">+</text>')
            S.append(f'<text x="{xk}" y="{ya + 5}" font-size="16" font-weight="bold" text-anchor="middle" fill="#111">−</text>')
            S.append(f'<text x="{(xa_ + xk) / 2}" y="{ya - 24}" font-size="12" font-weight="bold" text-anchor="middle" fill="#111">{ref} LED {p["cor"]}</text>')
        elif tipo == "npn":
            (xc, yc), (xb_, yb), (xe, ye) = pos["C"], pos["B"], pos["E"]
            if novo:
                glow_rect(xc - 30, yc - 40, xe + 30, yc + 40)
            S.append(f'<path d="M{xc - 22} {yc + 6} A 28 30 0 0 1 {xe + 22} {yc + 6} Z" fill="#555" fill-opacity=".55" stroke="#222" stroke-width="2"/>')
            S.append(f'<text x="{xb_}" y="{yc - 16}" font-size="12" font-weight="bold" text-anchor="middle" fill="#fff">BC547</text>')
            for lbl, (px, py) in (("C", (xc, yc)), ("B", (xb_, yb)), ("E", (xe, ye))):
                S.append(f'<text x="{px}" y="{py + 26}" font-size="13" font-weight="bold" text-anchor="middle" fill="#111">{lbl}</text>')
            S.append(f'<text x="{xb_}" y="{yc + 44}" font-size="11" text-anchor="middle" fill="#111">lado chato para voce (para baixo)</text>')
        elif tipo == "dip":
            x1, x2 = pos["1"][0], pos["4"][0]
            yb, yt = pos["1"][1], pos["8"][1]
            if novo:
                glow_rect(x1 - 30, yt - 30, x2 + 30, yb + 30)
            S.append(f'<rect x="{x1 - 18}" y="{yt - 14}" width="{x2 - x1 + 36}" height="{yb - yt + 28}" rx="6" fill="#3a3a3a" stroke="#111" stroke-width="2"/>')
            S.append(f'<path d="M{x1 - 18} {(yt + yb) / 2 - 10} a 10 10 0 0 1 0 20" fill="#e9e9e4" stroke="#111"/>')
            S.append(f'<text x="{(x1 + x2) / 2}" y="{(yt + yb) / 2 + 4}" font-size="13" font-weight="bold" text-anchor="middle" fill="#fff">PIC12F629</text>')
            for k, (px, py) in pos.items():
                S.append(f'<circle cx="{px}" cy="{py}" r="8" fill="#c0c0c0" stroke="#111"/>')
                S.append(f'<text x="{px}" y="{py + 4}" font-size="11" font-weight="bold" text-anchor="middle" fill="#111">{k}</text>')
        # etiquetas dos furos das pecas novas
        if novo:
            for k, (px, py) in pos.items():
                if tipo == "dip" and k not in ("1", "4", "5", "8"):
                    continue
                dy = 30 if py >= YR["e"] else -26
                tag(p["pinos"][k], px, py + dy)
        for k, (px, py) in pos.items():
            if tipo != "dip":
                S.append(f'<circle cx="{px}" cy="{py}" r="5.5" fill="#bbb" stroke="#111" stroke-width="1.5"/>')

    # plugs do Uno / fonte e fios
    top_y = {"A5": 22, "D4": 52, "D7": 82}

    def plug(nome, px, py, cor, novo, w=118):
        if novo:
            S.append(f'<rect x="{px - 6}" y="{py - 20}" width="{w + 12}" height="38" rx="10" fill="#fde047" fill-opacity=".6"/>')
        S.append(f'<rect x="{px}" y="{py - 15}" width="{w}" height="28" rx="7" fill="#fff" stroke="{cor}" stroke-width="4"/>')
        S.append(f'<text x="{px + w / 2}" y="{py + 5}" font-size="14" font-weight="bold" text-anchor="middle" fill="#111">{nome}</text>')

    for fid, fh, dest, cor, txt in pb.FIOS:
        if fid not in fios_ok:
            continue
        novo = fid in novos_f
        c = pb.COR[cor]
        if fh.startswith("FONTE."):
            ry = YR["rail+"] if fh[6:] == "+" else YR["rail-"]
            pts = [(W - 144, ry), (x(30), ry)]
        elif dest.startswith("UNO.") or fh.startswith("UNO."):
            pino = (dest if dest.startswith("UNO.") else fh)[4:]
            if pino == "GND":      # fio GND do Uno -> trilho -
                py = YR["rail-"]
                pts = [(138, py), (x(7), py)]
                plug("GND do Uno", 20, py, c, novo)
            else:
                hx, hy = furo(fh)
                if pino in top_y:
                    py = top_y[pino]
                    pts = [(138, py), (hx, py), (hx, hy)]
                    plug("Uno " + pino, 20, py, c, novo)
                elif pino == "D2":
                    pts = [(138, hy), (hx, hy)]
                    plug("Uno D2", 20, hy, c, novo)
                else:  # A1, pela direita
                    pts = [(W - 138, hy), (hx, hy)]
                    plug("Uno " + pino, W - 138, hy, c, novo)
        else:
            hx, hy = furo(fh)
            pts = [(hx, hy), (hx, YR[dest])]
        path = " ".join(f"{a},{b}" for a, b in pts)
        if novo:
            S.append(f'<polyline points="{path}" fill="none" stroke="#fde047" stroke-width="16" stroke-linecap="round" stroke-linejoin="round" opacity=".7"/>')
        S.append(f'<polyline points="{path}" fill="none" stroke="#fff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>')
        S.append(f'<polyline points="{path}" fill="none" stroke="{c}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
        for (a, b) in (pts[0], pts[-1]):
            S.append(f'<circle cx="{a}" cy="{b}" r="6" fill="{c}" stroke="#fff" stroke-width="2"/>')
        if novo and not fh.startswith(("UNO.", "FONTE.")):
            hx, hy = furo(fh)
            tag(fh, hx, hy + (28 if hy >= YR["e"] else -24))

    # fonte
    if any(f in fios_ok for f in ("W_FPOS", "W_FNEG")):
        novo = "W_FPOS" in novos_f
        if novo:
            S.append(f'<rect x="{W - 150}" y="{YR["rail+"] - 24}" width="140" height="{YR["rail-"] - YR["rail+"] + 48}" rx="10" fill="#fde047" fill-opacity=".6"/>')
        S.append(f'<rect x="{W - 144}" y="{YR["rail+"] - 18}" width="128" height="{YR["rail-"] - YR["rail+"] + 36}" rx="8" fill="#fff" stroke="#333" stroke-width="3"/>')
        S.append(f'<text x="{W - 80}" y="{YR["rail+"] + 4}" font-size="13" font-weight="bold" text-anchor="middle" fill="#d62828">FONTE 13 V  +</text>')
        S.append(f'<text x="{W - 80}" y="{YR["rail-"] + 4}" font-size="13" font-weight="bold" text-anchor="middle" fill="#111">FONTE 13 V  −</text>')

    # legenda do passo
    cap = []
    if passo == 0:
        cap.append("MONTAGEM COMPLETA (confira com a lista de passos)")
    else:
        titulo, ps, fs, nota = pb.PASSOS[passo - 1]
        cap.append(f"PASSO {passo} de {len(pb.PASSOS)}: {titulo}")
        for ref in ps:
            p = pb.PECAS[ref]
            fu = ", ".join(f"{k} em {h}" for k, h in p["pinos"].items() if p["tipo"] != "dip") if p["tipo"] != "dip" else "pino 1 em e10 (pinos 1 a 4 na fileira e, 5 a 8 na fileira f)"
            cap.append(f"• {ref}: {p['nome']}: {fu}")
        for fid in fs:
            _, fh, dest, cor, txt = next(f for f in pb.FIOS if f[0] == fid)
            a = fh if not fh.startswith(("UNO.", "FONTE.")) else dest
            uno = dest if dest.startswith(("UNO.", "FONTE.")) else (fh if fh.startswith(("UNO.", "FONTE.")) else None)
            if uno:
                alvo = a if a.startswith("rail") else a
                cap.append(f"• fio {cor.upper()}: {uno.replace('UNO.', 'Uno ').replace('FONTE.', 'fonte ')} → {'trilho ' + alvo[-1] if alvo.startswith('rail') else 'furo ' + alvo}")
            else:
                cap.append(f"• fio {cor.upper()}: furo {fh} → trilho {dest[-1]}")
    for i, t in enumerate(cap):
        S.append(f'<text x="30" y="{640 + i * 20}" font-size="{16 if i == 0 else 14}" font-weight="{"bold" if i == 0 else "normal"}" fill="#111">{t}</text>')
    S.append("</svg>")
    nome = "montagem-completa" if passo == 0 else f"passo-{passo}"
    (OUT / f"{nome}.svg").write_text("\n".join(S))
    return nome


# ---------------------------------------------------------------- Uno visto de cima
TOPO10 = [("SCL", 18.796), ("SDA", 21.336), ("AREF", 23.876), ("GND", 26.416), ("13", 28.956), ("12", 31.496), ("11", 34.036),
          ("10", 36.576), ("9", 39.116), ("8", 41.656)]
TOPO8 = [("7", 45.72), ("6", 48.26), ("5", 50.8), ("4", 53.34), ("3", 55.88), ("2", 58.42), ("1", 60.96), ("0", 63.5)]
PWR = [("", 27.94), ("IOREF", 30.48), ("RESET", 33.02), ("3V3", 35.56), ("5V", 38.1), ("GND", 40.64), ("GND", 43.18), ("VIN", 45.72)]
ANA = [("A0", 50.8), ("A1", 53.34), ("A2", 55.88), ("A3", 58.42), ("A4", 60.96), ("A5", 63.5)]
ESCOLHIDOS = {("top", "GND"): "GND", ("top", "7"): "D7", ("top", "4"): "D4", ("top", "2"): "D2", ("ana", "A1"): "A1", ("ana", "A5"): "A5"}


def desenhar_uno():
    s = 13.0
    Wd, Hd = 1000, 470
    xx = lambda xu: 70 + xu * s
    S = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{Wd}" height="{Hd}" viewBox="0 0 {Wd} {Hd}" font-family="DejaVu Sans, sans-serif">',
         f'<rect width="{Wd}" height="{Hd}" fill="{FUNDO}"/>',
         '<text x="30" y="34" font-size="20" font-weight="bold" fill="#111">Os 6 pinos do Arduino Uno que usamos (visto de cima, USB à esquerda)</text>',
         f'<rect x="{xx(0)}" y="90" width="{68.58 * s}" height="290" rx="12" fill="#1b7f79" stroke="#0b3d3a" stroke-width="3"/>',
         f'<rect x="{xx(-4)}" y="200" width="{14 * s}" height="95" rx="4" fill="#bbb" stroke="#555" stroke-width="2"/>',
         f'<text x="{xx(3)}" y="253" font-size="14" font-weight="bold" text-anchor="middle" fill="#111">USB</text>',
         f'<text x="{xx(34)}" y="240" font-size="22" font-weight="bold" text-anchor="middle" fill="#fff" opacity=".85">ARDUINO UNO</text>']
    def faixa(pinos, y, nome, lado):
        for lbl, xu in pinos:
            cor = None
            k = ESCOLHIDOS.get((lado, lbl))
            if lado == "pwr":
                k = None
            if lado == "top" and lbl == "GND" and xu != 26.416:
                k = None
            if k:
                cor = pb.COR[pb.PINOS_UNO[k]]
            S.append(f'<rect x="{xx(xu) - 9}" y="{y - 9}" width="18" height="18" rx="3" fill="{cor or "#222"}" stroke="#fff" stroke-width="{3 if cor else 1}"/>')
            ty = y - 18 if lado == "top" else y + 28
            if k:
                S.append(f'<text x="{xx(xu)}" y="{ty + (-12 if lado == "top" else 14)}" font-size="22" font-weight="bold" text-anchor="middle" fill="#111">{k}</text>')
                S.append(f'<text x="{xx(xu)}" y="{y + 5}" font-size="10" font-weight="bold" text-anchor="middle" fill="#fff">●</text>' if False else "")
            else:
                S.append(f'<text x="{xx(xu)}" y="{ty}" font-size="9" text-anchor="middle" fill="#cfe">{lbl}</text>')
    faixa(TOPO10, 120, "", "top")
    faixa(TOPO8, 120, "", "top")
    faixa(PWR, 350, "", "pwr")
    faixa(ANA, 350, "", "ana")
    S.append(f'<text x="{xx(36)}" y="82" font-size="13" fill="#333" text-anchor="middle">fileira de cima (pinos digitais)</text>')
    S.append(f'<text x="{xx(49)}" y="405" font-size="13" fill="#333" text-anchor="middle">fileira de baixo: energia (esq.) e analógicos A0 a A5 (dir.)</text>')
    # legenda
    y0 = 430
    for i, (n, c) in enumerate(pb.PINOS_UNO.items()):
        xx0 = 60 + i * 150
        S.append(f'<rect x="{xx0}" y="{y0 - 14}" width="22" height="22" rx="4" fill="{pb.COR[c]}" stroke="#333"/>')
        S.append(f'<text x="{xx0 + 30}" y="{y0 + 3}" font-size="14" fill="#111">{n}: fio {c}</text>')
    S.append("</svg>")
    (OUT / "uno-pinos.svg").write_text("\n".join(S))


def svg_para_png(svg, png_):
    """SVG -> PNG com o Chrome sem janela (o convert do ImageMagick falha com alguns retangulos arredondados)."""
    m = re.search(r'width="(\d+)" height="(\d+)"', Path(svg).read_text())
    w, h = (int(m.group(1)), int(m.group(2))) if m else (1270, 760)
    for exe in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        try:
            subprocess.run([exe, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", f"--screenshot={png_}",
                            f"--window-size={w},{h}", Path(svg).resolve().as_uri()], capture_output=True, check=True, timeout=120)
            return
        except FileNotFoundError:
            continue
    raise SystemExit("precisa do google-chrome ou chromium para gerar os PNG")


def png(nome):
    svg_para_png(OUT / f"{nome}.svg", OUT / f"{nome}.png")


# ---------------------------------------------------------------- texto do README
def furos_peca(p):
    if p["tipo"] == "dip":
        return "pino 1 em **e10**; pinos 1 a 4 em e10 a e13, pinos 8 a 5 em f10 a f13"
    return ", ".join(f"{k} em **{h}**" for k, h in p["pinos"].items())


def texto_readme():
    L = []
    L.append("### O que você precisa (confira antes de começar)")
    L.append("")
    L.append("| Peça | Quantas | Como reconhecer |")
    L.append("|---|---|---|")
    L.append("| Protoboard de 830 pontos (a de 400 também serve) | 1 | com 2 trilhos no alto: um `+` (vermelho) e um `−` (azul) |")
    L.append("| PIC12F629 em soquete DIP-8 | 1 | chip preto de 8 pernas, com uma marca (ponto ou entalhe) no pino 1 |")
    L.append("| Transistor BC547 | 1 | 3 pernas; tem um lado chato |")
    L.append("| Resistor 10 k | 1 | faixas: **marrom, preto, laranja**, dourado |")
    L.append("| Resistor 4,7 k | 1 | faixas: **amarelo, violeta, vermelho**, dourado |")
    L.append("| Resistor 1 k | 1 | faixas: **marrom, preto, vermelho**, dourado |")
    L.append("| Resistor 220 Ω | 1 | faixas: **vermelho, vermelho, marrom**, dourado |")
    L.append("| Capacitor 100 nF | 1 | disquinho pequeno marcado **104** |")
    L.append("| LED vermelho e LED amarelo | 1 de cada | a perna **longa** é o `+` |")
    L.append("| Fios (jumpers) macho-macho | 11 | cores: preto 6, vermelho 2, laranja, azul, verde, roxo, amarelo (1 de cada; as cores ajudam, não são obrigatórias) |")
    L.append("| Fios macho-fêmea para o Uno | 6 | um para cada pino do Uno: GND, D2, D4, D7, A1, A5 |")
    L.append("| Fonte de 13 V e multímetro | 1 | para a medição antes de ligar |")
    L.append("")
    L.append("### Os 6 pinos do Uno")
    L.append("")
    L.append("![Pinos do Uno usados](docs/protoboard/uno-pinos.png)")
    L.append("")
    L.append("| Pino do Uno | Cor do fio | Vai para | Para que serve |")
    L.append("|---|---|---|---|")
    uso = {"GND": "trilho −", "D2": "furo c10 (pino 1 do PIC)", "D4": "furo j12 (pino 6 do PIC)", "D7": "furo j11 (pino 7 do PIC)",
           "A1": "furo d18 (resistor de 4,7 k)", "A5": "furo j24 (resistor de 220)"}
    para = {"GND": "terra comum", "D2": "dá energia ao PIC (5 V)", "D4": "clock da gravação", "D7": "dados da gravação",
            "A1": "liga e desliga os 13 V no MCLR", "A5": "acende o LED amarelo enquanto grava"}
    for n, c in pb.PINOS_UNO.items():
        L.append(f"| **{n}** | {c} | {uso[n]} | {para[n]} |")
    L.append("")
    L.append("**Como ler os furos:** cada furo tem uma **letra** (linha, a a j) e um **número** (coluna 7 a 30). "
             "Exemplo: **c10** é a linha `c` na coluna `10`. As letras `a b c d e` ficam na metade de baixo e `f g h i j` na de cima; "
             "furos com o mesmo número **e na mesma metade** estão ligados entre si por dentro da protoboard.")
    L.append("")
    L.append("**Regra de ouro:** nada ligado na tomada nem no USB enquanto você monta. A fonte só vai no passo 9.")
    L.append("")
    for i, (titulo, ps, fs, nota) in enumerate(pb.PASSOS, 1):
        L.append(f"#### Passo {i}: {titulo}")
        L.append("")
        L.append(f"![Passo {i}](docs/protoboard/passo-{i}.png)")
        L.append("")
        L.append("| O que | Onde |")
        L.append("|---|---|")
        for ref in ps:
            p = pb.PECAS[ref]
            extra = ""
            if p["tipo"] == "res":
                extra = f" (faixas {', '.join(p['faixas'])}, dourado)"
            L.append(f"| **{p['nome']}**{extra} | {furos_peca(p)} |")
        for fid in fs:
            _, fh, dest, cor, txt = next(f for f in pb.FIOS if f[0] == fid)
            origem = fh if not fh.startswith(("UNO.", "FONTE.")) else dest
            uno = fh if fh.startswith(("UNO.", "FONTE.")) else (dest if dest.startswith(("UNO.", "FONTE.")) else None)
            if uno:
                alvo = "trilho " + origem[-1] if origem.startswith("rail") else f"furo **{origem}**"
                L.append(f"| fio **{cor}** ({txt}) | do **{uno.replace('UNO.', 'Uno ').replace('FONTE.', 'fonte ')}** ao {alvo} |")
            else:
                L.append(f"| fio **{cor}** ({txt}) | do furo **{fh}** ao trilho **{dest[-1]}** |")
        L.append("")
        if nota:
            L.append(f"> {nota}")
            L.append("")
    L.append("#### Pronto: confira")
    L.append("")
    L.append("![Montagem completa](docs/protoboard/montagem-completa.png)")
    L.append("")
    L.append("Com o multímetro em **continuidade (bip)** e **tudo desligado**:")
    L.append("")
    L.append("| Meça entre | Deve dar |")
    L.append("|---|---|")
    L.append("| trilho `+` e trilho `−` | **sem** bip (senão há um curto) |")
    L.append("| trilho `−` e o pino 8 do PIC (furo f10) | bip |")
    L.append("| furo e13 (pino 4 do PIC) e furo a13 (transistor) | bip |")
    L.append("| furo c10 (D2) e furo e10 (pino 1 do PIC) | bip |")
    L.append("")
    L.append("**Depois:** siga \"Antes de ligar\" (medir o MCLR com o chip fora) e \"Gravar\".")
    L.append("")
    L.append("**Com o diodo (opcional, D1).** Tire o fio vermelho que vai do positivo da fonte ao trilho `+`. Ponha o diodo 1N5819 "
             "na fileira `c`: o lado **sem faixa** (anodo) em **c29** e o lado **com faixa** (catodo) em **c25**. Depois: um fio vermelho do "
             "**positivo da fonte** ao furo **c29**, e outro fio vermelho do furo **c25** ao trilho `+`. (O desenho acima não mostra isso.)")
    return "\n".join(L)


def injetar():
    s = README.read_text()
    bloco = "<!-- protoboard -->\n" + texto_readme() + "\n<!-- /protoboard -->"
    if "<!-- protoboard -->" in s:
        s = re.sub(r"<!-- protoboard -->.*?<!-- /protoboard -->", lambda m: bloco, s, flags=re.S)
    else:
        raise SystemExit("README sem os marcadores <!-- protoboard --> ... <!-- /protoboard -->")
    README.write_text(s)


def main():
    erros = pb.verificar()
    if erros:
        print("\n".join(erros))
        sys.exit(1)
    OUT.mkdir(parents=True, exist_ok=True)
    nomes = [desenhar(i) for i in range(1, len(pb.PASSOS) + 1)] + [desenhar(0)]
    desenhar_uno()
    nomes.append("uno-pinos")
    for n in nomes:
        png(n)
    injetar()
    print("ok:", len(nomes), "figuras")


if __name__ == "__main__":
    main()
