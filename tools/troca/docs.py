#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bloco de troca de cartucho (D126): atualiza README, BOM, montagem, componentes opcionais e PEDIDO.md de uma placa.
Uso: python3 tools/troca/docs.py <placa> [--nets N --links M]   (depois de tools/export_fab.sh <placa> <versão>)"""
import argparse, hashlib, json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser(); ap.add_argument("board"); ap.add_argument("--nets", type=int); ap.add_argument("--links", type=int)
a = ap.parse_args()
cfg = json.loads((ROOT / "tools/troca/boards.json").read_text())[a.board]
B = ROOT / "boards" / a.board
V = cfg["version"]
q, r, d = cfg["q0"], cfg["r0"], cfg["d0"]
v3 = cfg.get("v3", False)
if cfg.get("q1", True):
    q1, q2, q3 = f"Q{q}", f"Q{q+1}", f"Q{q+2}"; n = r + 3
    rg, rs, rl = f"R{r}", f"R{r+1}", f"R{r+2}"            # 100k do gate, 100R, 1k do LED verde
    dg = f"D{d}"; dy = f"D{d+1}"
else:
    sys.exit("placa com Q1 própria: tratar à mão")
r6 = f"R{n}"; n += 1
r6b = None
if v3:
    r6b = f"R{n}"; n += 1
r7, r8, r9 = f"R{n}", f"R{n+1}", f"R{n+2}"
refs_r = f"R{r} a R{n+2}"
T = f"""
## Bloco de troca de cartucho (v1.1, D126)

Circuito e motivo: `docs/referencia/bloco-troca.md` (na raiz do repositório). Peças novas desta placa:

| Ref. | Valor | Função |
|---|---|---|
| {q1} | IRF9540N (P-MOSFET, TO-220) | chave de alta do 5V dos slots (`+5V_CART`); comando no D19 (nível baixo liga) |
| {rg} | 100 kΩ | gate do {q1} ao 5V (desligado com o Mega em reset) |
| {rs} | 100 Ω | D19 ao gate do {q1} |
| {rl}, {dg} | 1 kΩ, LED verde 3 mm | `+5V_CART` presente |
| {q2}, {r6}{(" e " + r6b) if r6b else ""} | 2N7000 (TO-92), 330 Ω{(" (o " + r6b + " descarrega o 3,3 V)") if r6b else ""} | descarga do rail quando o {q1} abre |
| {q3}, {r7}, {r8}, {r9}, {dy} | 2N7000, 100 kΩ, 1 kΩ, 1 kΩ, LED amarelo 3 mm | sensor do rail: {dy} aceso = seguro trocar; {r9} leva o nó ao D53 |

Os pinos de 5V dos slots e dos circuitos que a placa tiver (Si5351, PIC, pull-up, entrada do regulador de 3,3 V) e os capacitores deles ficam em `+5V_CART`. O {q1} (TO-220) fica em pé na placa, sem dissipador (a corrente do cartucho é baixa).
""".strip("\n") + "\n"

MARK = "## Bloco de troca de cartucho"

def edit(path, fn):
    p = B / path
    if not p.exists():
        return
    s = p.read_text(); s2 = fn(s)
    if s2 != s:
        p.write_text(s2)

# README
def readme(s):
    s = re.sub(r"\*\*Estado:\*\* v1\.0", f"**Estado:** {V}", s)
    return s if MARK in s else s.rstrip("\n") + "\n\n" + T
edit("README.md", readme)
# BOM
def bom(s):
    s = s.replace("v1.0", V)
    if MARK in s:
        return s
    s = s.rstrip("\n") + "\n\n" + T + f"""
Peças a comprar a mais por placa: 1 × IRF9540N, 2 × 2N7000, 1 LED verde e 1 LED amarelo de 3 mm, resistores axiais 1/4 W (pequenos, 0204 ou 0207 em pé): 100 kΩ × 2, 100 Ω × 1, 1 kΩ × 3, 330 Ω × {2 if v3 else 1}.
"""
    return s
edit("docs/bom.md", bom)
# montagem
def mont(s):
    s = s.replace("v1.0", V)
    s = s.replace("NÃO COLOQUE NEM RETIRE O CARTUCHO COM USB LIGADO", "SÓ TROQUE O CARTUCHO COM O LED AMARELO ACESO")
    s = s.replace("Desligue o USB antes de trocar de cartucho", "Antes de trocar de cartucho, desligue o 5V dos slots (`dumper.py power off`, espere o LED amarelo acender) ou o USB")
    if MARK in s:
        return s
    s = s.rstrip("\n") + f"""

## Bloco de troca de cartucho ({V})

Solde com os componentes baixos: {refs_r} (em pé, como no silkscreen), os dois 2N7000 ({q2}, {q3}; o lado chato do silk é o lado chato do transistor), os LEDs {dg} (verde) e {dy} (amarelo) e, **por último entre os baixos**, o {q1} (TO-220, em pé, como no silkscreen).

**Firmware:** grave o ambiente `SerialASCII_PowerSense` (`pio run -e SerialASCII_PowerSense -t upload` em `firmware/oscr`): começa com o 5V dos slots desligado; o host liga com `POWER`.

Testes extras (multímetro, sem cartucho):

1. Antes de ligar: continuidade entre o dreno do {q1} (`+5V_CART`) e o VCC do slot; **nenhuma** entre `+5V_CART` e o 5V do Mega.
2. Ligado ao USB, com o firmware padrão: o 5V do Mega presente, `+5V_CART` conforme o comando `POWER` (`dumper.py power on|off`): ligado = LED verde ({dg}) aceso e 4,7 a 5,2 V no VCC do slot; desligado = {dy} aceso e VCC abaixo de 0,5 V em até 1 s.
3. Medir a queda do {q1} em carga e o tempo de descarga; anotar nos logs. O limiar do LED amarelo varia com o 2N7000 (1 a 2,5 V).
"""
    return s
edit("docs/montagem.md", mont)
# componentes opcionais
def opc(s):
    if MARK in s:
        return s
    sec = f"""## Bloco de troca de cartucho ({V})

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| {q1}, {rg}, {rs} | **Não** (sem o {q1} o 5V dos slots não chega: pôr uma ponte do 5V ao `+5V_CART` se quiser abrir mão do `POWER`) | `POWER on/off` em software; a troca segura do cartucho |
| {rl}, {dg} (LED verde) | Sim | só a indicação visual de 5V dos slots |
| {q2}, {r6}{(", " + r6b) if r6b else ""} | Sim | descarga rápida do rail: o firmware espera 2 s em vez de 500 ms |
| {q3}, {r7}, {r8}, {r9}, {dy} (sensor e LED amarelo) | Sim | o LED amarelo e a leitura do D53 (`POWER_RESP.rail` fica `0xFF`) |

Nenhuma peça do bloco afeta quais cartuchos podem ser lidos; todas atuam só na troca de cartucho e no ciclo de energia do SA-1."""
    if re.search(r"> Quando a v1\.1 com o bloco de troca", s):
        return re.sub(r"> Quando a v1\.1 com o bloco de troca.*", lambda m: sec, s)
    return s.rstrip("\n") + "\n\n" + sec + "\n"
edit("docs/componentes-opcionais.md", opc)
# PEDIDO
def pedido(s):
    z = B / "fab" / f"dumper-{V}-jlcpcb.zip"
    sha = hashlib.sha256(z.read_bytes()).hexdigest()
    s = s.replace("v1.0", V)
    s = re.sub(r"SHA-256: `[0-9a-f]{64}`", f"SHA-256: `{sha}`", s)
    s = re.sub(r"Feita em 2026-\d\d-\d\d", "Refeita em 2026-11-07 (bloco de troca de cartucho, D126)", s)
    if a.nets:
        s = re.sub(r"\(\d+ nets, \d+ ligações\)", f"({a.nets} nets, {a.links} ligações)", s)
    return s
edit("fab/PEDIDO.md", pedido)
print("docs de", a.board, "atualizadas")
