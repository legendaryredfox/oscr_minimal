#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""D138: acrescenta aos docs de cada placa (bom.md, montagem.md, componentes-opcionais.md) a seção do F1, do J1 e do seletor de tensão.
Idempotente (marca <!-- d138 -->). Uso (da raiz): python3 tools/troca/docs138.py [placa ...]"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT / "tools/troca/boards.json").read_text())
NOMES = {"MD1": "Mega Drive", "SMS1": "Master System", "NES1": "NES", "FC1": "Famicom", "SNES1": "SNES", "GBA1": "GBA", "N64": "N64"}
MARK = "<!-- d138 -->"
PLACAS = ["16_and_8_bits", "16_bits", "famicom", "famicom_nes", "gb_gba", "megadrive", "megadrive_sms", "n64", "nes", "snes"]


def versoes(b):
    c = CFG[b]
    if b == "16_bits":
        return "v1.2 e v1.3 (a v1.0 já foi encomendada e não muda)", c["version"]
    return "v1.0 e " + c["version"], c["version"]


def manifesto(b):
    p = ROOT / "boards" / b / f"hardware-{CFG[b]['version']}" / "d138.json"
    return json.loads(p.read_text()) if p.exists() else None


PENDENTE = {"16_and_8_bits"}       # v1.1 sem F1 nem seletor: o roteamento automático não fechou (D138); só a v1.0 ganhou o fusível


def secao(b, tipo):
    c = CFG[b]; sel = c.get("sel"); vf, vb = versoes(b)
    m = manifesto(b) or {"novos": [], "rn": []}
    pend = b in PENDENTE
    if pend:
        sel = None; vf = "v1.0"
    slots_sel = [NOMES.get(s, s) for s in sel["slots"]] if sel else []
    nrn = len(m.get("rn", []))
    f1 = ("**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega "
          "(nas versões com bloco de troca, antes do Q1). Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões " + vf + " (exceção declarada à regra \"a v1.0 é a mais barata que funciona\", D138). "
          "**Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.")
    if tipo == "bom":
        t = [f"## F1, J1 e seletor de tensão (D138)", "", MARK, "", "Peças opcionais a comprar a mais por placa:", "", "| Ref. | Peça | Qtd | Onde |", "|---|---|---|---|",
             f"| F1 | suporte de clipes para fusível 5×20 mm (Littelfuse série 100, 2 clipes) e fusível de vidro 5×20 mm de 500 mA, ação rápida | 1 + 1 (compre fusíveis de reserva) | todas as versões ({vf}) |"]
        if sel:
            t += ["| J1 | cabeçalho de 2 pinos de 2,54 mm e um jumper (\"TRAVA 3,3 V\") | 1 | " + vb + " |",
                  "| LDO | LD1117V33 (TO-220) | 1 | " + vb + " |",
                  "| Q4 | IRF9540N (P-MOSFET, TO-220) | 1 | " + vb + " |",
                  "| Q5 | 2N7000 (TO-92) | 1 | " + vb + " |",
                  f"| RN1 a RN{nrn} | rede isolada de 8 resistores de 470 Ω, DIP-16 | {nrn} | " + vb + " |",
                  "| C (2) | 100 nF cerâmico e 10 µF/16 V eletrolítico (entrada e saída do LDO) | 2 | " + vb + " |",
                  "| R (3) | 100 kΩ, 1 kΩ e 220 Ω, axiais 1/4 W | 3 | " + vb + " |"]
        t += ["", f1, ""]
        if pend:
            t += ["**Pendente:** a v1.1 desta placa ainda **não** tem o F1, o J1, o seletor de tensão nem os resistores em série (o Freerouting não conseguiu rotear a placa maior com o bloco de troca e o seletor). Só a v1.0 ganhou o fusível.", ""]
        if sel:
            t += ["Seletor 3,3 V/5 V nos slots " + ", ".join(slots_sel) + " (resto da placa sempre em 5 V). Preço aproximado das peças extras: menos de US$ 3 por placa (estimativa de varejo, não cotada).", ""]
        return "\n".join(t)
    if tipo == "opc":
        t = [f"## F1, J1 e seletor de tensão (D138)", "", MARK, "", "| Peça | Opcional? | O que se perde sem ela |", "|---|---|---|",
             "| F1 (suporte e fusível 5×20 mm, 500 mA) | **Sim**, mas sem o fusível no suporte a placa não tem 5 V (um fio no lugar dele também serve) | só a proteção contra curto no cartucho (placa, Mega e USB) |"]
        if sel:
            t += ["| J1 (jumper TRAVA 3,3 V) | **Sim** | a defesa independente do firmware contra o 5 V num cartucho de 3,3 V; deixe aberto para usar o seletor |",
                  "| LDO, Q4, Q5, C do LDO | Não, se quiser 3,3 V | sem eles o slot fica só em 5 V; o seletor é a tensão padrão (5 V) com o Q4 |",
                  "| RN1 a RN%d (470 Ω) | Não, se quiser proteger cartuchos de 3,3 V | sem os resistores (ponte de fio nos furos) o 3,3 V deixa de proteger contra as saídas de 5 V do Mega |" % nrn]
        t += ["", f1, ""]
        return "\n".join(t)
    t = [f"## F1, J1 e seletor de tensão (D138)", "", MARK, "",
         "1. **Suporte do F1** (clipes para fusível 5×20 mm, furo passante) entra com os componentes baixos, na faixa de 10 mm acrescentada à borda de baixo da placa; solde os 4 furos (as duas pernas de cada clipe). O fusível **não vai soldado**: encaixe um fusível de vidro 5×20 mm de 500 mA (ação rápida) nos clipes depois dos testes, e troque-o assim quando queimar.",
         "2. Teste antes de ligar, com o fusível encaixado: continuidade entre os dois clipes (menos de 2 Ω) e nenhuma entre 5 V e GND."]
    if sel:
        t += [f"3. **Seletor ({vb})**: solde os resistores comuns, as redes RN1 a RN{nrn} (DIP-16 com a marca no pino 1, de preferência em soquete), os capacitores, o Q5, o LDO e o Q4 (TO-220 em pé) e o J1 (cabeçalho de 2 pinos, **sem o jumper**).",
              "4. Gravar `pio run -e SerialASCII_PowerVolt -t upload` (firmware com o seletor no D18). Liga em **5 V** por padrão; `dumper power on --voltage 3v3` liga a 3,3 V.",
              "5. Medidas sem cartucho: em 5 V, o VCC dos slots fica entre 4,6 e 5,1 V (queda do fusível e do Q4); com `--voltage 3v3`, entre 3,2 e 3,4 V (LDO). Com o J1 fechado, `--voltage 5v` não consegue passar de 3,3 V.",
              "6. Os slots " + ", ".join(slots_sel) + " são os únicos com resistores em série e seletor; o resto da placa (Si5351, PIC e outros slots) fica sempre em 5 V."]
    return "\n".join(t)


def acrescenta(path, texto):
    s = path.read_text()
    if MARK in s:
        i = s.index("## F1, J1 e seletor de tensão (D138)")
        s = s[:i].rstrip("\n") + "\n"
    path.write_text(s.rstrip("\n") + "\n\n" + texto.rstrip("\n") + "\n")


for b in (sys.argv[1:] or PLACAS):
    d = ROOT / "boards" / b / "docs"
    acrescenta(d / "bom.md", secao(b, "bom"))
    acrescenta(d / "componentes-opcionais.md", secao(b, "opc"))
    acrescenta(d / "montagem.md", secao(b, "mont"))
    print("docs de", b)
