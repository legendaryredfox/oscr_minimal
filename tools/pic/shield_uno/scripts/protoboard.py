#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-SA-2.5
"""Montagem na protoboard (dados + verificacao). Os desenhos e as tabelas do README saem de protoboard_desenho.py
a partir destes mesmos dados.

Convencao: cada LINHA NUMERADA (coluna da figura) tem duas tiras: letras a-e (metade de baixo) e f-j (metade de cima).
Trilhos: so os de cima, "+" (13 V) e "-" (GND). Uso: python3 protoboard.py -> codigo 1 se algo diverge.
"""
import sys

# ---- cores dos fios (nome em portugues, cor em hex)
COR = {"preto": "#111111", "vermelho": "#d62828", "laranja": "#f77f00", "azul": "#1d4ed8", "verde": "#2a9d48",
       "roxo": "#9333ea", "amarelo": "#eab308"}

# ---- pecas: ref -> dict(tipo, descricao, pinos={pino: furo}, extra)
PECAS = {
    "U2": dict(tipo="dip", nome="PIC12F629 no soquete DIP-8", pinos={"1": "e10", "2": "e11", "3": "e12", "4": "e13",
                                                                      "8": "f10", "7": "f11", "6": "f12", "5": "f13"}),
    "C1": dict(tipo="cap", nome="Capacitor 100 nF (marcado 104)", pinos={"1": "b10", "2": "b8"}),
    "Q1": dict(tipo="npn", nome="Transistor BC547", pinos={"C": "a13", "B": "a14", "E": "a15"}),
    "R1": dict(tipo="res", nome="Resistor 10 k", faixas=("marrom", "preto", "laranja"), pinos={"1": "c13", "2": "c17"}),
    "R2": dict(tipo="res", nome="Resistor 4,7 k", faixas=("amarelo", "violeta", "vermelho"), pinos={"1": "e18", "2": "e14"}),
    "R4": dict(tipo="res", nome="Resistor 1 k", faixas=("marrom", "preto", "vermelho"), pinos={"1": "a17", "2": "a21"}),
    "D2": dict(tipo="led", cor="vermelho", nome="LED vermelho", pinos={"A": "b21", "K": "b22"}),
    "R3": dict(tipo="res", nome="Resistor 220", faixas=("vermelho", "vermelho", "marrom"), pinos={"1": "g24", "2": "g28"}),
    "D3": dict(tipo="led", cor="amarelo", nome="LED amarelo", pinos={"A": "h28", "K": "h29"}),
}
# ---- fios: (id, furo, destino, cor, texto)   destino = "UNO.xx" | "rail+" | "rail-" | "FONTE.+" | "FONTE.-"
FIOS = [
    ("W_GND_UNO", "UNO.GND", "rail-", "preto", "GND do Uno"),
    ("W_PIC8", "j10", "rail-", "preto", "pino 8 do PIC ao GND"),
    ("W_D2", "c10", "UNO.D2", "laranja", "D2 do Uno: alimenta o PIC"),
    ("W_C1GND", "e8", "rail-", "preto", "capacitor ao GND"),
    ("W_D7", "j11", "UNO.D7", "azul", "D7 do Uno: dados"),
    ("W_D4", "j12", "UNO.D4", "verde", "D4 do Uno: clock"),
    ("W_Q1E", "e15", "rail-", "preto", "emissor do transistor ao GND"),
    ("W_13V", "e17", "rail+", "vermelho", "13 V para o resistor de 10 k e para o LED"),
    ("W_A1", "d18", "UNO.A1", "roxo", "A1 do Uno: comanda o transistor"),
    ("W_LEDK", "e22", "rail-", "preto", "LED vermelho ao GND"),
    ("W_A5", "j24", "UNO.A5", "amarelo", "A5 do Uno: luz de atividade"),
    ("W_LEDK2", "i29", "rail-", "preto", "LED amarelo ao GND"),
    ("W_FPOS", "FONTE.+", "rail+", "vermelho", "positivo da fonte de 13 V"),
    ("W_FNEG", "FONTE.-", "rail-", "preto", "negativo da fonte de 13 V"),
]
# ---- passos: (titulo, [pecas], [fios], o que conferir)
PASSOS = [
    ("Fio de GND do Uno", [], ["W_GND_UNO"], "Todo o circuito precisa do mesmo GND do Uno."),
    ("O chip PIC12F629", ["U2"], ["W_PIC8"],
     "O PIC fica a cavaleiro do vao do meio, com o pino 1 em e10 (o entalhe do chip aponta para a esquerda)."),
    ("Energia do chip", ["C1"], ["W_D2", "W_C1GND"], "O capacitor fica junto do pino 1, perto do chip."),
    ("Dados e clock", [], ["W_D7", "W_D4"], ""),
    ("Transistor e resistor de 10 k", ["Q1", "R1"], ["W_Q1E", "W_13V"],
     "O transistor BC547 entra com o lado CHATO virado para voce (para a borda de baixo da figura): C, B, E da esquerda para a direita."),
    ("Comando do transistor", ["R2"], ["W_A1"], ""),
    ("LED vermelho (tem 13 V)", ["R4", "D2"], ["W_LEDK"], "A perna LONGA do LED e o +; ela vai no furo de numero menor."),
    ("LED amarelo (atividade)", ["R3", "D3"], ["W_A5", "W_LEDK2"], "A perna LONGA do LED e o +; ela vai no furo de numero menor."),
    ("Fonte de 13 V (por ultimo!)", [], ["W_FPOS", "W_FNEG"], "Fonte DESLIGADA e polaridade conferida com o multimetro."),
]
PINOS_UNO = {"D2": "laranja", "D4": "verde", "D7": "azul", "A1": "roxo", "A5": "amarelo", "GND": "preto"}

# ---- expectativa
ESPERADO = [
    {"UNO.D2", "U2.1", "C1.1"}, {"UNO.D4", "U2.6"}, {"UNO.D7", "U2.7"},
    {"U2.4", "Q1.C", "R1.1"}, {"UNO.A1", "R2.1"}, {"R2.2", "Q1.B"},
    {"UNO.GND", "FONTE.-", "U2.8", "Q1.E", "C1.2", "D2.K", "D3.K"},
    {"R1.2", "R4.1", "FONTE.+"}, {"R4.2", "D2.A"}, {"UNO.A5", "R3.1"}, {"R3.2", "D3.A"},
]
LIVRES = ["U2.2", "U2.3", "U2.5"]
COLS = range(7, 31)


def tira(h):
    if h.startswith(("rail", "UNO.", "FONTE.")):
        return h
    col, lin = h[0], int(h[1:])
    return ("B" if col in "abcde" else "T", lin)


def ocupados():
    """furo -> quem usa (pecas e pontas de fio)"""
    r = {}
    for ref, p in PECAS.items():
        for pino, h in p["pinos"].items():
            r[h] = f"{ref}.{pino}"
    return r


def verificar():
    erros = []
    pai = {}

    def f(a):
        pai.setdefault(a, a)
        while pai[a] != a:
            pai[a] = pai[pai[a]]
            a = pai[a]
        return a
    occ = ocupados()
    pads = {f"{ref}.{pino}": tira(h) for ref, p in PECAS.items() for pino, h in p["pinos"].items()}
    # dois pads no mesmo furo; furo fora da figura
    vistos = {}
    for k, h in {f"{r}.{p}": h for r, ps in PECAS.items() for p, h in ps["pinos"].items()}.items():
        if h in vistos:
            erros.append(f"dois pads no mesmo furo {h}: {k} e {vistos[h]}")
        vistos[h] = k
        if int(h[1:]) not in COLS:
            erros.append(f"furo fora da figura: {h}")
    # ponta de fio num furo ja ocupado por peca
    for fid, furo, dest, cor, _ in FIOS:
        if not furo.startswith(("UNO.", "FONTE.", "rail")):
            if furo in occ:
                erros.append(f"fio {fid} cai no furo {furo}, ocupado por {occ[furo]}")
            if int(furo[1:]) not in COLS:
                erros.append(f"fio {fid}: furo fora da figura {furo}")
        pai[f(tira(furo))] = f(tira(dest))
    for uno in ("UNO.D2", "UNO.D4", "UNO.D7", "UNO.A1", "UNO.A5", "UNO.GND", "FONTE.+", "FONTE.-"):
        pads[uno] = uno
    g = {}
    for nome, t in pads.items():
        g.setdefault(f(t), set()).add(nome)
    achados = [s for s in g.values() if len(s) > 1]
    erros += [f"falta: {sorted(e)}" for e in ESPERADO if e not in achados]
    erros += [f"a mais: {sorted(s)}" for s in achados if s not in ESPERADO]
    for p in LIVRES:
        if any(p in s for s in achados):
            erros.append(p + " devia ficar livre")
    # cada fio e cada peca aparecem em exatamente um passo
    pf = [x for _, _, fs, _ in PASSOS for x in fs]
    pp = [x for _, ps, _, _ in PASSOS for x in ps]
    if sorted(pf) != sorted(x[0] for x in FIOS):
        erros.append("fios fora dos passos ou repetidos")
    if sorted(pp) != sorted(PECAS):
        erros.append("pecas fora dos passos ou repetidas")
    # cores dos fios do Uno batem com PINOS_UNO
    for fid, furo, dest, cor, _ in FIOS:
        if dest.startswith("UNO.") and PINOS_UNO[dest[4:]] != cor:
            erros.append(f"{fid}: cor {cor} difere de PINOS_UNO")
    return erros


def verificar_com_diodo():
    """Variante do README ('Com o diodo'): D1 em c29 (anodo) e c25 (catodo); fonte+ em c29; c25 ao trilho +."""
    global PECAS, FIOS, PASSOS, ESPERADO
    guardado = (dict(PECAS), list(FIOS), list(PASSOS), list(ESPERADO))
    try:
        FIOS = [w for w in FIOS if w[0] != "W_FPOS"] + [("W_FPOSD", "FONTE.+", "c29", "vermelho", "positivo da fonte ao anodo"),
                                                         ("W_DK", "c25", "rail+", "vermelho", "catodo ao trilho +")]
        PECAS = dict(PECAS, D1=dict(tipo="dio", nome="Diodo 1N5819", pinos={"A": "c29", "K": "c25"}))
        # a ponta c29/c25 do fio e a perna do diodo: tratamos o fio como estando na mesma tira do pino do diodo
        FIOS = [(a, ("d29" if b == "c29" else "d25" if b == "c25" else b), c, d, e) if a in ("W_FPOSD", "W_DK") else (a, b, c, d, e)
                for a, b, c, d, e in FIOS]
        FIOS = [("W_FPOSD", "FONTE.+", "d29", "vermelho", "x") if w[0] == "W_FPOSD" else w for w in FIOS]
        ESPERADO = [e for e in ESPERADO if "FONTE.+" not in e] + [{"FONTE.+", "D1.A"}, {"D1.K", "R1.2", "R4.1"}]
        PASSOS = [(t, ps, [f for f in fs if f != "W_FPOS"] + (["W_FPOSD", "W_DK"] if "W_FPOS" in fs else []), n) for t, ps, fs, n in PASSOS]
        PASSOS = [(t, ps + (["D1"] if t.startswith("Fonte") else []), fs, n) for t, ps, fs, n in PASSOS]
        return verificar()
    finally:
        PECAS, FIOS, PASSOS, ESPERADO = guardado


def main():
    erros = verificar()
    erros += ["variante com diodo: " + e for e in verificar_com_diodo()]
    if erros:
        print("\n".join(erros))
        sys.exit(1)
    print(f"ok: {len(ESPERADO)} nets conferidas na protoboard, {len(FIOS)} fios, {len(PASSOS)} passos")


if __name__ == "__main__":
    main()
