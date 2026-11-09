#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gera um README.md por versão de cada placa, dentro da pasta de hardware da versão
(boards/<placa>/hardware-<versão>/README.md, uma pasta por versão).
Cada README leva os renders 3D (cima e baixo) da versão, a lista de peças (kicad-cli sch export bom),
o que muda em relação à versão anterior, os arquivos de fábrica e os comandos de verificação.
Uso (python do venv do KiCad MCP, que tem pcbnew), da raiz do repositório:
    python tools/gen_readme_versoes.py [placa ...]
Os renders vêm de tools/render_board.sh; rode-o antes."""
import csv, json, re, subprocess, sys, tempfile
from pathlib import Path
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
BOARDS = ROOT / "boards"

# Texto por placa. "ver" = (versão, pasta de hardware, pasta de gerbers, reservado (sempre False desde D139), nota própria da versão)
TROCA = ("O 5V dos slots vai direto do Mega e **não é cortado por software** (o desligamento por software foi retirado, D139). "
         "Para trocar o cartucho, **desligue a placa tirando o cabo USB** do Mega; nunca com a USB ligada.")

NOMES_SLOT = {"MD1": "Mega Drive", "SMS1": "Master System", "NES1": "NES", "FC1": "Famicom", "SNES1": "SNES", "GBA1": "GBA", "N64": "N64"}
SEL_CFG = json.loads((Path(__file__).resolve().parent / "troca" / "boards.json").read_text())


def protecao(placa, linhas):
    """Proteção de corrente (F1) e de tensão (J1 e seletor 3,3 V/5 V) conforme as peças da versão (D138)."""
    refs = set(re.split(r"[,\s]+", " ".join(r["Ref"] for r in linhas)))
    out = []
    if "F1" in refs:
        out += ["## Proteção de corrente e tensão (D138)", "",
                "**F1: fusível de vidro 5×20 mm de 500 mA (ação rápida) em suporte de clipes, opcional.** O suporte é de furo passante (Littelfuse série 100 ou equivalente) e o fusível queimado se troca **sem solda**; fica em série com o 5 V que a placa recebe do Mega "
                "Um curto no cartucho queima o fusível e protege a placa, o Mega e a porta USB. A queda é de 0,1 a 0,2 V a 200 mA "
                "(o SA-1 do SNES continua abaixo de ~5,2 V). **Sem o fusível no suporte a placa fica sem 5 V** (um fio no lugar dele também serve). "
                "Ele limita corrente e não protege contra tensão errada.", ""]
    if "J1" in refs:
        sel = (SEL_CFG.get(placa) or {}).get("sel") or {"slots": []}
        com = [NOMES_SLOT.get(x, x) for x in sel["slots"]]
        out += ["**Seletor de tensão 3,3 V/5 V dos slots " + ", ".join(com) + "** (LDO LD1117V33 em TO-220, Q4 de bypass, Q5 de carga, redes de resistores de 470 Ω em série com as linhas "
                "entre o Mega e esses slots, comando no D18). **Padrão: 5 V**; 3,3 V só quando o usuário pede (`--voltage 3v3`, ou o botão da GUI). Passar de 3,3 V para 5 V mostra "
                "um alerta e pede confirmação. Os outros slots e o Si5351/PIC ficam direto no 5 V. Cartuchos de 3,3 V ligados em 5 V podem queimar.", "",
                "**J1: jumper \"TRAVA 3,3 V\", opcional.** Fechado, prende o gate do Q4 no 5 V e o slot nunca passa de 3,3 V, mesmo com erro de software ou de GUI: é a única "
                "defesa independente do firmware. Aberto, o seletor funciona normalmente.", ""]
    return out


PLACAS = {
    "16_and_8_bits": dict(
        nome="16_and_8_bits", slots="SNES (62p), NES (72p), Famicom (60p), Mega Drive (64p), todos a 5 V, e GBA (32p, SMD, 1,5 mm) a 3,3 V (regulador U3)",
        extra="Si5351 em header fêmea e PIC12F629 (CIC do SNES) em soquete.",
        versoes=[("v1.0", "hardware-v1.0", "gerbers-v1.0", False, ""),
                 ]),
    "16_bits": dict(
        nome="16_bits", slots="SNES (62p) e Mega Drive (64p), 5 V",
        extra="Si5351 em header fêmea e PIC12F629 (CIC do SNES) em soquete. Sem botão de reset em nenhuma versão (D128).",
        versoes=[("v1.0", "hardware-v1.0", "gerbers-v1.0", False,
                  "Antiga `rev2` (D97): alimentação em 0,8 mm, sem resistores série nem TVS nas linhas de controle, sem `/CART` no D50, sem C5, C6 e pontos de teste, sem furos M3 do Mega. A v1.0 original (trilhas de 0,3 mm) foi encomendada pelo usuário em 2026-11-06 e seus gerbers saíram do repositório (D110)."),
                 ("v1.2", "hardware-v1.2", "gerbers-v1.2", False,
                  "Resistores série (0 Ω) nas 12 linhas de controle (**sem os TVS**, D130), pull-up de `/VRES` (DNP), `/CART` no D50, C5, C6, pontos de teste e três furos M3 alinhados com o Mega. Sem a chave de 5V (Q1) e sem o botão de reset (D128); D19 e RST ficam sem ligação."),
                 ("v1.3", "hardware-v1.3", "gerbers-v1.3", False,
                  "A v1.2 mais os 12 TVS 5 V (D3 a D14, DNP), o seletor de tensão 3,3 V/5 V do slot Mega Drive (D138) e os resistores em série das linhas desse slot. Roteada pelo Freerouting: **revisar no KiCad antes de encomendar**.")]),
    "megadrive": dict(nome="megadrive", slots="Mega Drive (64p, 2,54 mm), 5 V", extra="Si5351 e PIC12F629 (herdados da `16_bits`, ver `docs/componentes-opcionais.md`).",
                      versoes=[("v1.0", "hardware-v1.0", "gerbers-v1.0", False, ""), ("v1.1", "hardware-v1.1", "gerbers-v1.1", False, "")]),
    "megadrive_sms": dict(nome="megadrive_sms", slots="Mega Drive (64p, 2,54 mm) e Master System / Mark III (50p, 2,54 mm), 5 V ou 3,3 V (seletor na v1.1); **um cartucho por vez**", extra="Sem Si5351 e sem PIC (pino 47, Clock, do slot SMS sem ligação).",
                          versoes=[("v1.0", "hardware-v1.0", "gerbers-v1.0", False, ""), ("v1.1", "hardware-v1.1", "gerbers-v1.1", False, "")]),
    "snes": dict(nome="snes", slots="SNES (62p, 2,5 mm), 5 V", extra="Si5351 em header fêmea e PIC12F629 (CIC) em soquete.",
                 versoes=[("v1.0", "hardware-v1.0", "gerbers-v1.0", False, "")]),
    "nes": dict(nome="nes", slots="NES (72p, 2,5 mm), 5 V", extra="Si5351 (clock do slot), sem PIC.",
                versoes=[("v1.0", "hardware-v1.0", "gerbers-v1.0", False, ""), ("v1.1", "hardware-v1.1", "gerbers-v1.1", False, "")]),
    "famicom": dict(nome="famicom", slots="Famicom (60p, 2,54 mm), 5 V", extra="Sem Si5351 e sem PIC.",
                    versoes=[("v1.0", "hardware-v1.0", "gerbers-v1.0", False, ""), ("v1.1", "hardware-v1.1", "gerbers-v1.1", False, "")]),
    "famicom_nes": dict(nome="famicom_nes", slots="Famicom (60p) e NES (72p) em paralelo, 5 V; **um cartucho por vez, em um slot só**", extra="Si5351, sem PIC.",
                        versoes=[("v1.0", "hardware-v1.0", "gerbers-v1.0", False, ""), ("v1.1", "hardware-v1.1", "gerbers-v1.1", False, "")]),
    "gb_gba": dict(nome="gb_gba", slots="GBA (32 pads SMD, 1,5 mm), 3,3 V; GB e GBC só com adaptador", extra="Sem Si5351 e sem PIC.",
                   versoes=[("v1.0", "hardware-v1.0", "gerbers-v1.0", False, "")]),
    "n64": dict(nome="n64", slots="N64 (50 pinos), 3,3 V", extra="Si5351 só para a EEPROM.",
                versoes=[("v1.0", "hardware-v1.0", "gerbers-v1.0", False, "")]),
}


def bom(sch):
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "bom.csv"
        subprocess.run(["kicad-cli", "sch", "export", "bom", "--fields", "Reference,Value,Footprint,${QUANTITY}", "--labels", "Ref,Valor,Footprint,Qtd",
                        "--group-by", "Value,Footprint", "--ref-range-delimiter", "", "-o", str(out), str(sch)], check=True, capture_output=True)
        return [r for r in csv.DictReader(open(out, encoding="utf-8"))]


def tamanho(pcb):
    bb = pcbnew.LoadBoard(str(pcb)).GetBoardEdgesBoundingBox()
    return f"{bb.GetWidth() / 1e6:.1f} × {bb.GetHeight() / 1e6:.1f} mm".replace(".", ",")


def chave(r):
    return (r["Valor"], r["Footprint"])


def gerar(placa):
    cfg = PLACAS[placa]
    base = BOARDS / placa
    vers = cfg["versoes"]
    anterior = None
    for i, (v, hw, gd, bloco, nota) in enumerate(vers):
        pcb = base / hw / "dumper.kicad_pcb"; sch = base / hw / "dumper.kicad_sch"
        linhas = bom(sch)
        mapa = {chave(r): r for r in linhas}
        md = [f"# {placa} {v}", ""]
        md += [f"![{placa} {v}, vista de cima (render 3D do KiCad)](render-cima.png)", "",
               f"![{placa} {v}, vista de baixo (render 3D do KiCad)](render-baixo.png)", ""]
        md += [f"Versão **{v}** da placa [`{placa}`](../README.md): shield 100% THT para Arduino Mega 2560 R3, só USB. "
               f"{'Esta é a versão mais nova.' if i == len(vers) - 1 else 'Versão anterior, mantida ao lado da mais nova.'}", "",
               "| | |", "|---|---|",
               f"| Slots | {cfg['slots']} |", f"| Circuitos | {cfg['extra']} |", f"| Tamanho | {tamanho(pcb)} |",
               f"| Projeto KiCad | [`{hw}/`](.) (`dumper.kicad_pro`, `.kicad_sch`, `.kicad_pcb`) |",
               f"| Fábrica (JLCPCB) | `../fab/{gd}/`, `../fab/dumper-{v}-jlcpcb.zip` |",
               f"| Renders | `render-cima.png`, `render-baixo.png` |",
               "| Estado | Nada montado nem testado com cartucho; revisar o layout no KiCad antes de encomendar |", ""]
        md += ["## Troca de cartucho", "", TROCA, ""]
        md += protecao(placa, linhas)
        if nota:
            md += ["## Particularidades desta versão", "", nota, ""]
        if anterior:
            pv, pm = anterior
            novas = [(k, mapa[k]) for k in mapa if k not in pm]
            sumiram = [(k, pm[k]) for k in pm if k not in mapa]
            muda = [(k, pm[k]["Qtd"], mapa[k]["Qtd"]) for k in mapa if k in pm and pm[k]["Qtd"] != mapa[k]["Qtd"]]
            md += [f"## O que muda em relação à {pv}", ""]
            if not (novas or sumiram or muda):
                md += ["Mesma lista de peças.", ""]
            else:
                md += ["| Peça | Referências | Antes | Agora |", "|---|---|---|---|"]
                for k, r in sumiram:
                    md.append(f"| {k[0]} | {r['Ref']} | {r['Qtd']} | 0 |")
                for k, r in novas:
                    md.append(f"| {k[0]} | {r['Ref']} | 0 | {r['Qtd']} |")
                for k, a, b in muda:
                    md.append(f"| {k[0]} | {mapa[k]['Ref']} | {a} | {b} |")
                md.append("")
        md += ["## Lista de peças", "", "| Referências | Valor | Footprint | Qtd |", "|---|---|---|---|"]
        for r in linhas:
            md.append(f"| {r['Ref']} | {r['Valor']} | `{r['Footprint']}` | {r['Qtd']} |")
        md += ["", "Gerada do esquemático desta versão (`kicad-cli sch export bom`). Peças marcadas DNP ou opcionais: `docs/componentes-opcionais.md` da placa.", ""]
        chk = f"python3 tools/check_netlist.py --board {placa} {'--sem-tvs ' if (placa, v) == ('16_bits', 'v1.2') else ''}boards/{placa}/{hw}/dumper.kicad_sch"
        gx = ""
        sem_chk = (placa, v) == ("16_bits", "v1.0")   # o pinmap atual inclui C5, C6, D3 a D14 e TP2, que a v1.0 não tem
        md += ["## Verificação e fábrica (da raiz do repositório)", "", "```",
               *([] if sem_chk else [chk]),
               f"kicad-cli sch erc boards/{placa}/{hw}/dumper.kicad_sch",
               f"kicad-cli pcb drc boards/{placa}/{hw}/dumper.kicad_pcb",
               f"{gx}tools/export_fab.sh {placa} {v}",
               f"tools/render_board.sh {placa} {' '.join(x[0] for x in vers)}",
               "```", "",
               *(["`tools/check_netlist.py` não se aplica à v1.0 da `16_bits`: o `pinmap.md` atual inclui C5, C6, D3 a D14 e TP2, que esta versão não tem.", ""] if sem_chk else []),
               f"Mais: [README da placa](../README.md), [`docs/`](../docs/)."
               + (f" Comparação entre as versões: [`docs/versoes.md`](../docs/versoes.md)." if placa == "16_bits" else ""), ""]
        (base / hw / "README.md").write_text("\n".join(md), encoding="utf-8")
        print("escrito", (base / hw / "README.md").relative_to(ROOT))
        anterior = (v, mapa)


if __name__ == "__main__":
    for p in (sys.argv[1:] or PLACAS):
        gerar(p)
