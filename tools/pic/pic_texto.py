#!/usr/bin/env python3
"""Lê e grava o PIC12F629 pelo sketch ProgramPIC do ardpicprog usando só os comandos em TEXTO (READ e WRITE).

Por quê: o ardpicprog usa READBIN (pacotes binários), e na bancada esse fluxo chegou corrompido ao PC
(cabeçalhos de pacote trocados, bytes sobrando). O texto detecta a corrupção: um token que não é hexadecimal
de 4 dígitos, ou a contagem errada de palavras, e a leitura é repetida. Ver docs/decisoes.md.

Uso:
  pic_texto.py ler SAIDA.hex                  lê o chip (programa, ID e configuração) e grava o .hex
  pic_texto.py gravar ENTRADA.hex [--simular] grava SEM apagar: o programa do chip tem de estar em branco
  pic_texto.py conferir ENTRADA.hex           compara o chip com o .hex
Opções: --porta /dev/ttyUSB0

Não escreve a calibração OSCCAL (palavra 0x3FF) e mantém os bits BG da palavra de configuração (0x3000): a
configuração é gravada com WRITE FORCE, com os BG lidos duas vezes antes de qualquer escrita. O WRITE sem FORCE do
ProgramPIC lê os BG uma única vez antes de gravar, e num chip isso apagou um bit (D220). No fim, "gravar" falha se
os BG ou o OSCCAL mudaram. A comparação com o .hex ignora esses dois itens e os bits 11 a 9 da configuração,
que neste chip leem sempre 0.
"""
import re
import sys
import time

import serial

BAUD = 9600
ULTIMA = 0x3FF            # palavra da calibração OSCCAL: nunca é escrita
CFG = 0x2007
MASCARA_BG = 0x3000       # bits de calibração do bandgap
CFG_USADOS = 0x01FF       # bits da configuração que o chip implementa e que valem na comparação (os bits 11 a 9 leem sempre 0)
POR_COMANDO = 4           # palavras por WRITE (a linha de comando do sketch tem no máximo 64 caracteres)


def carregar_hex(caminho):
    """Devolve (programa {palavra: valor}, configuração) de um .hex Intel do PIC12F629."""
    prog, cfg, ext = {}, 0x3FFF, 0
    for linha in open(caminho):
        linha = linha.strip()
        if not linha.startswith(":"):
            continue
        raw = bytes.fromhex(linha[1:])
        if sum(raw) & 0xFF:
            raise SystemExit(f"{caminho}: checksum errado em {linha}")
        n, end, tipo = raw[0], (raw[1] << 8) | raw[2], raw[3]
        dados = raw[4:4 + n]
        if tipo == 4:
            ext = int.from_bytes(dados, "big") << 16
        elif tipo == 0:
            for i in range(0, n - 1, 2):
                a = ext + end + i
                w = (dados[i] | (dados[i + 1] << 8)) & 0x3FFF
                if a < 0x800:
                    prog[a // 2] = w
                elif a == 0x400E:
                    cfg = w
    return prog, cfg


def escrever_hex(caminho, prog, cfg_palavras, id_palavras):
    """Grava um .hex no mesmo layout do ardpicprog: programa em 0x0000, IDs em 0x4000, configuração em 0x400E."""
    regs = []

    def reg(end, dados):
        b = bytes([len(dados), (end >> 8) & 0xFF, end & 0xFF, 0]) + bytes(dados)
        regs.append(":" + (b + bytes([(-sum(b)) & 0xFF])).hex().upper())

    for w in sorted(prog):
        if prog[w] != 0x3FFF:
            reg(w * 2, [prog[w] & 0xFF, prog[w] >> 8])
    for i, v in enumerate(id_palavras):
        if v != 0x3FFF:
            reg(0x4000 + i * 2, [v & 0xFF, v >> 8])
    reg(0x400E, [cfg_palavras[7] & 0xFF, cfg_palavras[7] >> 8])
    regs.append(":00000001FF")
    open(caminho, "w").write("\n".join(regs) + "\n")


class Programador:
    def __init__(self, porta):
        self.s = serial.Serial(porta, BAUD, timeout=0.3)
        fim = time.time() + 12
        time.sleep(2.5)                       # o Uno reinicia ao abrir a porta
        while time.time() < fim:
            self.s.reset_input_buffer()
            self.s.write(b"PROGRAM_PIC_VERSION\n")
            if b"ProgramPIC 1." in self._ate(lambda d: b"\n" in d and b"ProgramPIC" in d, 1.2):
                break
        else:
            raise SystemExit("o sketch ProgramPIC não respondeu")
        self.cmd("SETDEVICE PIC12F629", b".\r\n")

    def _ate(self, pronto, limite):
        d, t = b"", time.time()
        while time.time() - t < limite and not pronto(d):
            d += self.s.read(256)
        return d

    def cmd(self, texto, fim, limite=6.0):
        self.s.reset_input_buffer()
        self.s.write(texto.encode() + b"\n")
        return self._ate(lambda d: d.endswith(fim) or d.endswith(b"ERROR\r\n"), limite).decode(errors="replace")

    def ler(self, ini, fim_, tentativas=8):
        """Lê palavras [ini, fim_] em texto; repete se algum token vier inválido ou faltar palavra."""
        n = fim_ - ini + 1
        for _ in range(tentativas):
            r = self.cmd(f"READ {ini:04X}-{fim_:04X}", b".\r\n")
            tok = r.split()
            if len(tok) == n + 2 and tok[0] == "OK" and tok[-1] == "." and all(re.fullmatch(r"[0-9A-F]{4}", t) for t in tok[1:-1]):
                return [int(t, 16) for t in tok[1:-1]]
            time.sleep(0.4)
        raise SystemExit(f"leitura de 0x{ini:04X}-0x{fim_:04X} não ficou válida em {tentativas} tentativas")

    def ler_blocos(self, ini, fim_, bloco=64):
        saida = []
        for a in range(ini, fim_ + 1, bloco):
            saida += self.ler(a, min(a + bloco - 1, fim_))
        return saida

    def ler_confirmado(self, ini, fim_, bloco=64):
        """Lê duas vezes e só aceita se as duas leituras forem iguais."""
        for _ in range(5):
            a, b = self.ler_blocos(ini, fim_, bloco), self.ler_blocos(ini, fim_, bloco)
            if a == b:
                return a
        raise SystemExit("duas leituras seguidas nunca coincidiram")

    def identificar(self):
        cfg = self.ler_confirmado(0x2000, 0x2007)
        if (cfg[6] & 0xFFE0) != 0x0F80:
            raise SystemExit(f"ID 0x{cfg[6]:04X} não é de um PIC12F629 (esperado 0x0F8x)")
        return cfg

    def escrever(self, end, palavras, forcar=False):
        verbo = "WRITE FORCE" if forcar else "WRITE"
        r = self.cmd("%s %04X %s" % (verbo, end, " ".join("%04X" % w for w in palavras)), b"OK\r\n", 8.0)
        if "OK" not in r or "ERROR" in r:
            raise SystemExit(f"o sketch recusou WRITE em 0x{end:04X}: {r.strip()!r}")


def cmd_ler(p, saida):
    cfg = p.identificar()
    prog = dict(enumerate(p.ler_confirmado(0, ULTIMA)))
    escrever_hex(saida, prog, cfg, cfg[:6])
    print(f"ok: ID 0x{cfg[6]:04X}, configuração 0x{cfg[7]:04X}, OSCCAL 0x{prog[ULTIMA]:04X}, lido duas vezes igual -> {saida}")


def diferencas(p, esperado, cfg_esp):
    """Compara o chip com o esperado, sem olhar a calibração 0x3FF nem os bits BG. Devolve a lista de diferenças."""
    chip = p.ler_confirmado(0, ULTIMA - 1)
    cfg = p.ler_confirmado(CFG, CFG)[0]
    dif = []
    for w in range(ULTIMA):
        e = esperado.get(w, 0x3FFF)
        if chip[w] != e:
            dif.append(f"palavra 0x{w:03X}: esperado 0x{e:04X}, lido 0x{chip[w]:04X}")
    if (cfg & CFG_USADOS) != (cfg_esp & CFG_USADOS):
        dif.append(f"configuração: esperada 0x{cfg_esp & CFG_USADOS:04X}, lida 0x{cfg & CFG_USADOS:04X} (BG e bits 11 a 9 ignorados)")
    return dif


def cmd_gravar(p, entrada, simular):
    esperado, cfg_esp = carregar_hex(entrada)
    cfg = p.identificar()
    osc = p.ler_confirmado(ULTIMA, ULTIMA)[0]
    print(f"chip: ID 0x{cfg[6]:04X}, configuração 0x{cfg[7]:04X}, OSCCAL 0x{osc:04X}")
    atual = p.ler_confirmado(0, ULTIMA - 1)
    alvo = {w: v for w, v in esperado.items() if w < ULTIMA and v != 0x3FFF}
    ocupadas = [w for w in alvo if atual[w] != 0x3FFF and atual[w] != alvo[w]]
    if ocupadas:
        raise SystemExit(f"o chip não está em branco nas palavras {[hex(w) for w in ocupadas[:6]]}: apague antes (este script não apaga)")
    faltam = sorted(w for w in alvo if atual[w] != alvo[w])
    print(f"palavras a gravar: {len(faltam)} de {len(alvo)}" + ("  [simulação: nada será escrito]" if simular else ""))
    i = 0
    while i < len(faltam):
        grupo = [faltam[i]]
        while len(grupo) < POR_COMANDO and i + len(grupo) < len(faltam) and faltam[i + len(grupo)] == grupo[-1] + 1:
            grupo.append(faltam[i + len(grupo)])
        if not simular:
            p.escrever(grupo[0], [alvo[w] for w in grupo])
            lido = p.ler(grupo[0], grupo[-1])
            if lido != [alvo[w] for w in grupo]:
                raise SystemExit(f"conferência falhou em 0x{grupo[0]:04X}: esperado {[hex(alvo[w]) for w in grupo]}, lido {[hex(x) for x in lido]}")
        i += len(grupo)
        if (i // POR_COMANDO) % 25 == 0:
            print(f"  {i}/{len(faltam)}")
    bg = cfg[7] & MASCARA_BG                  # de identificar(): duas leituras iguais, antes de qualquer escrita
    if not simular and (cfg[7] & CFG_USADOS) != (cfg_esp & CFG_USADOS):
        p.escrever(CFG, [bg | (cfg_esp & CFG_USADOS)], forcar=True)
    if simular:
        print("simulação concluída")
        return
    dif = diferencas(p, esperado, cfg_esp)
    bg_fim = p.ler_confirmado(CFG, CFG)[0] & MASCARA_BG
    if bg_fim != bg:
        dif.append(f"bits BG mudaram: antes 0x{bg:04X}, agora 0x{bg_fim:04X} (anote o valor de antes)")
    osc_fim = p.ler_confirmado(ULTIMA, ULTIMA)[0]
    if osc_fim != osc:
        dif.append(f"OSCCAL mudou: antes 0x{osc:04X}, agora 0x{osc_fim:04X} (anote o valor de antes)")
    if dif:
        print("\n".join(dif))
        raise SystemExit("FALHOU: há diferenças")
    print(f"OK: programa e configuração conferem com o .hex; BG 0x{bg:04X} e OSCCAL 0x{osc:04X} iguais aos de antes")


def main():
    a = sys.argv[1:]
    porta = "/dev/ttyUSB0"
    if "--porta" in a:
        i = a.index("--porta")
        porta = a[i + 1]
        del a[i:i + 2]
    simular = "--simular" in a
    a = [x for x in a if x != "--simular"]
    if len(a) != 2 or a[0] not in ("ler", "gravar", "conferir"):
        print(__doc__)
        return 2
    p = Programador(porta)
    try:
        if a[0] == "ler":
            cmd_ler(p, a[1])
        elif a[0] == "gravar":
            cmd_gravar(p, a[1], simular)
        else:
            esp, cfg = carregar_hex(a[1])
            dif = diferencas(p, esp, cfg)
            print("\n".join(dif) if dif else "OK: confere com o .hex")
            return 1 if dif else 0
    finally:
        p.s.write(b"PWROFF\n")
        p.s.close()


if __name__ == "__main__":
    sys.exit(main())
