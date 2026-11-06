#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-SA-2.5
"""Gera hardware/shield_uno.kicad_sch e hardware/uno_shield.kicad_sym.

Circuito: o do ardpicprog (Rhys Weatherley, CC BY-SA 2.5) para o PIC12F629 em DIP-8 direto,
como descrito em tools/pic/uno/README.md (D91). Tudo ligado por rotulos de net; cada pino
recebe um fio curto e um rotulo na ponta.

Uso (da raiz do repositorio):  python3 tools/pic/shield_uno/scripts/gerar_sch.py
"""
import math
import re
import uuid
from pathlib import Path

AQUI = Path(__file__).resolve().parent.parent
HW = AQUI / "hardware"
SYM = Path("/usr/share/kicad/symbols")
PROJETO = "shield_uno"
ROOT = "6f1d3a52-9b0e-4d57-8c3a-5e7a1b2c9d40"  # uuid fixo da folha: o .kicad_pro e as instancias apontam para ele


def uid(semente=None):
    return str(uuid.uuid4()) if semente is None else str(uuid.uuid5(uuid.UUID(ROOT), semente))


# ------------------------------------------------------------------ bibliotecas
def bloco(arq, nome):
    t = (SYM / (arq + ".kicad_sym")).read_text()
    i = t.index('\t(symbol "%s"\n' % nome)
    d = 0
    for j in range(i, len(t)):
        if t[j] == "(":
            d += 1
        elif t[j] == ")":
            d -= 1
            if d == 0:
                return t[i:j + 1]
    raise ValueError(nome)


def pinos(b):
    r = {}
    for m in re.finditer(r"\(pin (\w+) (\w+)\s*\(at ([\-\d.]+) ([\-\d.]+) (\d+)\)\s*\(length ([\d.]+)\)"
                         r"(?:\s*\(hide yes\))?\s*\(name \"([^\"]*)\".*?\(number \"([^\"]*)\"", b, re.S):
        tipo, _, x, y, a, _, nome, num = m.groups()
        r[num] = (float(x), float(y), int(a), nome, tipo)
    return r


# ------------------------------------------------------------------ simbolo do Uno
ESQ = ["SCL", "SDA", "AREF", "GND1", "D13", "D12", "D11", "D10", "D9", "D8",
       "D7", "D6", "D5", "D4", "D3", "D2", "D1", "D0"]
DIR = ["NC", "IORF", "RST1", "3V3", "5V1", "GND2", "GND3", "VIN",
       "A0", "A1", "A2", "A3", "A4", "A5"]
USADOS = {"D2": "power_out", "D4": "bidirectional", "D7": "bidirectional",
          "A1": "output", "A5": "output",
          "GND1": "passive", "GND2": "passive", "GND3": "passive"}


def simbolo_uno():
    L = []
    n = 0
    for lado, nomes, x, ang in (("e", ESQ, -17.78, 0), ("d", DIR, 17.78, 180)):
        topo = (len(nomes) - 1) / 2 * 2.54
        for i, nome in enumerate(nomes):
            y = round(topo - i * 2.54, 2)
            tipo = USADOS.get(nome, "no_connect")
            L.append((nome, tipo, x, y, ang))
    meio = 21.59 + 2.54
    pins = "".join(
        f'\t\t\t(pin {t} line\n\t\t\t\t(at {x} {y} {a})\n\t\t\t\t(length 5.08)\n'
        f'\t\t\t\t(name "{nm}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n'
        f'\t\t\t\t(number "{nm}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)\n'
        for nm, t, x, y, a in L)
    prop = lambda k, v, y, hide="": (
        f'\t\t(property "{k}" "{v}"\n\t\t\t(at 0 {y} 0)\n{hide}\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n')
    corpo = (
        '\t(symbol "Uno_R3_Shield"\n'
        "\t\t(pin_numbers\n\t\t\t(hide yes)\n\t\t)\n"
        "\t\t(pin_names\n\t\t\t(offset 1.016)\n\t\t)\n"
        "\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n"
        + prop("Reference", "A", meio + 2.54)
        + prop("Value", "Uno_R3_Shield", -meio - 2.54)
        + prop("Footprint", "uno_shield:Uno_R3_Shield", 0, "\t\t\t(hide yes)\n")
        + prop("Datasheet", "", 0, "\t\t\t(hide yes)\n")
        + prop("Description", "Headers do Arduino Uno R3 (pinos pelo nome; so os usados tem ligacao)", 0, "\t\t\t(hide yes)\n")
        + '\t\t(symbol "Uno_R3_Shield_0_1"\n'
        f"\t\t\t(rectangle\n\t\t\t\t(start -12.7 {meio})\n\t\t\t\t(end 12.7 {-meio})\n"
        "\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n"
        "\t\t\t\t(fill\n\t\t\t\t\t(type background)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n"
        '\t\t(symbol "Uno_R3_Shield_1_1"\n' + pins + "\t\t)\n"
        "\t\t(embedded_fonts no)\n\t)\n")
    return corpo


# ------------------------------------------------------------------ esquema
LIBS = {}  # lib_id -> texto do simbolo (com nome qualificado)


def lib(arq, nome):
    chave = f"{arq}:{nome}"
    if chave not in LIBS:
        b = bloco(arq, nome)
        LIBS[chave] = b.replace('\t(symbol "%s"\n' % nome, '\t(symbol "%s"\n' % chave, 1)
    return chave


PINOS = {}
SAIDA = []   # itens apos os simbolos (fios, rotulos, nc)
INST = []    # instancias de simbolos


def pin_pos(chave, num, x, y, rot):
    px, py, a, nome, tipo = PINOS[chave][num]
    r = math.radians(rot)
    X = px * math.cos(r) - py * math.sin(r)
    Y = px * math.sin(r) + py * math.cos(r)
    # direcao "para fora do corpo" no esquema (y para baixo)
    ar = math.radians(a + rot)
    dx, dy = -math.cos(ar), math.sin(ar)
    return round(x + X, 2), round(y - Y, 2), round(dx), round(dy)


def f(v):
    return ("%.2f" % v).rstrip("0").rstrip(".")


def fio(x1, y1, x2, y2):
    SAIDA.append(f'\t(wire\n\t\t(pts\n\t\t\t(xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})\n\t\t)\n'
                 f'\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{uid()}")\n\t)\n')


def rotulo(nome, x, y, dx, dy):
    ang = {(1, 0): 0, (-1, 0): 180, (0, 1): 270, (0, -1): 90}[(dx, dy)]
    just = "right bottom" if ang == 180 else "left bottom"
    SAIDA.append(f'\t(label "{nome}"\n\t\t(at {f(x)} {f(y)} {ang})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n'
                 f'\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{uid()}")\n\t)\n')


def nc(x, y):
    SAIDA.append(f'\t(no_connect\n\t\t(at {f(x)} {f(y)})\n\t\t(uuid "{uid()}")\n\t)\n')


def prop(k, v, x, y, oculto=False, just=""):
    return (f'\t\t(property "{k}" "{v}"\n\t\t\t(at {f(x)} {f(y)} 0)\n' + ("\t\t\t(hide yes)\n" if oculto else "")
            + f'\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n{just}\t\t\t)\n\t\t)\n')


def comp(chave, ref, valor, fp, x, y, rot, ligacoes, descr="", nao_usados=(), energia=False, sem_bom=False, off=None, dnp=False):
    """ligacoes: {numero do pino: nome da net}. Pinos fora de ligacoes e de nao_usados dao erro."""
    x, y = round(x / 2.54) * 2.54, round(y / 2.54) * 2.54
    for num, (px, py, a, nome, tipo) in PINOS[chave].items():
        x0, y0, dx, dy = pin_pos(chave, num, x, y, rot)
        if num in ligacoes:
            fio(x0, y0, x0 + dx * 5.08, y0 + dy * 5.08)
            rotulo(ligacoes[num], x0 + dx * 5.08, y0 + dy * 5.08, dx, dy)
        elif num in nao_usados:
            nc(x0, y0)
        else:
            raise SystemExit(f"{ref} pino {num} ({nome}) sem destino")
    pins = "".join(f'\t\t(pin "{n}"\n\t\t\t(uuid "{uid()}")\n\t\t)\n' for n in PINOS[chave])
    voff = 2.54
    if not off and chave == "Device:R":
        off, voff = (-3, -2.5), 5.08
    elif not off and chave in ("Device:LED", "Device:D_Schottky"):
        off = (-4, 3.5)
    ox, oy = off if off else ((3.81, -3.81) if not energia else (3.81, 0))
    INST.append(
        f'\t(symbol\n\t\t(lib_id "{chave}")\n\t\t(at {f(x)} {f(y)} {rot})\n\t\t(unit 1)\n\t\t(body_style 1)\n'
        f'\t\t(exclude_from_sim no)\n\t\t(in_bom {"no" if energia or sem_bom else "yes"})\n\t\t(on_board {"no" if energia else "yes"})\n'
        f'\t\t(in_pos_files {"no" if energia else "yes"})\n\t\t(dnp {"yes" if dnp else "no"})\n\t\t(uuid "{uid()}")\n'
        + prop("Reference", ref, x + ox, y + oy, just="\t\t\t\t(justify left)\n")
        + prop("Value", valor, x + ox, y + oy + voff, just="\t\t\t\t(justify left)\n")
        + prop("Footprint", fp, x, y, True)
        + prop("Datasheet", "", x, y, True)
        + prop("Description", "", x, y, True)
        + pins
        + f'\t\t(instances\n\t\t\t(project "{PROJETO}"\n\t\t\t\t(path "/{ROOT}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')


def texto(s, x, y, tam=1.27, negrito=False):
    SAIDA.append(f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {tam} {tam})\n'
                 + ("\t\t\t\t(bold yes)\n" if negrito else "") + f'\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{uid()}")\n\t)\n')


def main():
    uno_txt = simbolo_uno()
    (HW / "uno_shield.kicad_sym").write_text(
        '(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "gerar_sch.py")\n\t(generator_version "10.0")\n' + uno_txt + ")\n")
    LIBS["uno_shield:Uno_R3_Shield"] = uno_txt.replace('\t(symbol "Uno_R3_Shield"\n', '\t(symbol "uno_shield:Uno_R3_Shield"\n', 1)
    PINOS["uno_shield:Uno_R3_Shield"] = pinos(
        uno_txt.replace("(number ", "(number ").replace('(name "', '(name "'))

    R, C, LED, D, Q = lib("Device", "R"), lib("Device", "C"), lib("Device", "LED"), lib("Device", "D_Schottky"), lib("Transistor_BJT", "Q_NPN_CBE")
    PIC, TB, CONN, TP, FLG, = (lib("MCU_Microchip_PIC12", "PIC12F629-xP"), lib("Connector", "Screw_Terminal_01x02"),
                               lib("Connector", "Conn_01x06_Pin"), lib("Connector", "TestPoint"), lib("power", "PWR_FLAG"))
    CONN2 = lib("Connector_Generic", "Conn_01x02")
    for k in list(LIBS):
        if k != "uno_shield:Uno_R3_Shield":
            PINOS[k] = pinos(LIBS[k])

    fp_r = "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P10.16mm_Horizontal"
    fp_led = "LED_THT:LED_D3.0mm"

    # ---- Uno
    comp("uno_shield:Uno_R3_Shield", "A1", "Uno_R3_Shield", "uno_shield:Uno_R3_Shield", 71.12, 129.54, 0,
         {"D2": "VDD", "D4": "CLK", "D7": "DAT", "A1": "VPP_CTL", "A5": "LED_ATIVO",
          "GND1": "GND", "GND2": "GND", "GND3": "GND"},
         "Headers do Arduino Uno R3", off=(-12, -30),
         nao_usados={n for n, p in PINOS["uno_shield:Uno_R3_Shield"].items() if p[4] == "no_connect"})
    texto("ARDUINO UNO (so estes pinos sao usados)", 40, 85, 1.5, True)
    texto("D2 = Vdd do PIC; D4 = clock; D7 = dados; A1 = comando do MCLR (nivel baixo = 13 V); A5 = LED de atividade", 40, 90)

    # ---- Entrada de 13 V + diodo
    texto("1) ENTRADA DE 13 V", 160, 30, 1.5, True)
    comp(TB, "J1", "13V", "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
         190, 45, 0, {"1": "VIN13", "2": "GND"}, "Entrada da fonte de 13 V (1 = +, 2 = GND)")
    comp(D, "D1", "1N5819 (DNP)", "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal", 245, 45, 180, {"1": "V13", "2": "VIN13"},
         "Opcional: protecao contra polaridade invertida", dnp=True)
    comp(CONN2, "JP1", "Ponte (padrao: fechada)", "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical", 300, 45, 0,
         {"1": "VIN13", "2": "V13"}, "Liga a entrada de 13 V ao resto sem o diodo D1")
    texto("D1 NAO e montado (DNP): a placa sai sem diodo. JP1 fechado (fio, jumper ou solda) liga a entrada ao circuito.", 160, 58)
    texto("Para proteger contra fonte invertida: montar D1 (faixa = K para o lado do circuito) e ABRIR o JP1.", 160, 62)
    texto("Sem D1 a fonte tem que estar na polaridade certa. Medir o Vpp no TP1.", 160, 66)

    # ---- MCLR
    texto("2) MCLR: 13 V (transistor cortado) ou GND (transistor ligado)", 160, 80, 1.5, True)
    comp(R, "R1", "10k", fp_r, 190, 105, 90, {"1": "V13", "2": "MCLR"}, "Pull-up do MCLR para os 13 V")
    comp(Q, "Q1", "BC547", "Package_TO_SOT_THT:TO-92_Inline_Wide", 275, 105, 0, {"1": "MCLR", "2": "BASE", "3": "GND"},
         "NPN pequeno: BC547/BC548 (CBE); 2N3904/2N2222 (EBC) entram virados 180 graus")
    comp(R, "R2", "4k7", fp_r, 235, 130, 90, {"1": "VPP_CTL", "2": "BASE"}, "Base do transistor, comandada pelo A1")

    # ---- PIC
    texto("3) PIC12F629 (DIP-8 em soquete) E CABECALHO ICSP", 160, 155, 1.5, True)
    comp(PIC, "U2", "PIC12F629", "Package_DIP:DIP-8_W7.62mm_Socket", 205, 195, 0,
         {"1": "VDD", "8": "GND", "4": "MCLR", "6": "CLK", "7": "DAT"}, "PIC12F629-I/P (DIP-8) em soquete",
         nao_usados={"2", "3", "5"}, off=(10, -18))
    comp(C, "C1", "100n", "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P5.00mm", 285, 195, 0, {"1": "VDD", "2": "GND"},
         "Desacoplamento do Vdd do PIC")
    comp(CONN, "J2", "ICSP", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", 345, 190, 0,
         {"1": "MCLR", "2": "VDD", "3": "GND", "4": "DAT", "5": "CLK"},
         "ICSP na ordem do PICkit: 1 MCLR, 2 Vdd, 3 GND, 4 dados, 5 clock, 6 livre", nao_usados={"6"}, off=(0, -9))

    # ---- LEDs
    texto("4) LEDS", 160, 232, 1.5, True)
    comp(R, "R4", "1k", fp_r, 190, 250, 90, {"1": "V13", "2": "LED13_A"}, "Resistor do LED de 13 V presente")
    comp(LED, "D2", "LED vermelho", fp_led, 250, 250, 0, {"1": "GND", "2": "LED13_A"}, "Aceso = 13 V presentes")
    comp(R, "R3", "220", fp_r, 190, 270, 90, {"1": "LED_ATIVO", "2": "LEDA_A"}, "Resistor do LED de atividade (A5)")
    comp(LED, "D3", "LED amarelo", fp_led, 250, 270, 0, {"1": "GND", "2": "LEDA_A"}, "Atividade do ardpicprog (A5)")

    # ---- pontos de teste e flags
    texto("5) PONTOS DE TESTE", 320, 232, 1.5, True)
    comp(TP, "TP1", "MCLR", "TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm", 325, 245, 0, {"1": "MCLR"}, "Medir o Vpp (~13 V)", sem_bom=True)
    comp(TP, "TP2", "VDD", "TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm", 345, 245, 0, {"1": "VDD"}, "Medir o Vdd do PIC (5 V)", sem_bom=True)
    comp(TP, "TP3", "GND", "TestPoint:TestPoint_THTPad_D2.0mm_Drill1.0mm", 365, 245, 0, {"1": "GND"}, "Terra para o multimetro", sem_bom=True)
    comp(FLG, "#FLG01", "PWR_FLAG", "", 385, 245, 0, {"1": "GND"}, "", energia=True)

    texto("Programador de PIC12F629 (CIC do OSCR) para Arduino Uno - derivado do circuito do ardpicprog", 20, 20, 2.0, True)
    texto("Circuito original: Rhys Weatherley (ardpicprog), CC BY-SA 2.5. Este shield: CC BY-SA 2.5. v1.0", 20, 26)

    libs = "".join("".join("\t" + l + "\n" for l in LIBS[k].split("\n")) for k in sorted(LIBS))
    out = (f'(kicad_sch\n\t(version 20260101)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n\t(uuid {ROOT})\n\t(paper "A3")\n'
           f"\t(lib_symbols\n{libs}\t)\n"
           + "".join(INST) + "".join(SAIDA)
           + '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n)\n')
    (HW / "shield_uno.kicad_sch").write_text(out)
    print("ok:", len(INST), "simbolos")


if __name__ == "__main__":
    main()
