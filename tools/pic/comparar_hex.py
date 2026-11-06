#!/usr/bin/env python3
"""Compara o .hex lido de um PIC12F629 com o .hex que se quis gravar.

Uso: comparar_hex.py esperado.hex lido.hex

Confere as 1024 palavras de programa e a palavra de configuração (endereço de palavra 0x2007,
byte 0x400E). Posições que o arquivo não traz valem 0x3FFF (chip apagado). A última palavra do
programa (0x3FF) guarda a calibração de fábrica OSCCAL (RETLW xx) e fica de fora: o gravador a
restaura, o .hex do sd2snes não a contém. Sai com 0 se tudo bate, 1 se há diferença.
"""
import sys

CONFIG_BYTE = 0x400E
OSCCAL_WORD = 0x3FF

def load(path):
    prog = {}
    cfg = 0x3FFF
    ext = 0
    for line in open(path):
        line = line.strip()
        if not line.startswith(':'):
            continue
        raw = bytes.fromhex(line[1:])
        if sum(raw) & 0xFF:
            raise SystemExit(f"{path}: checksum errado em {line}")
        n, addr, typ = raw[0], (raw[1] << 8) | raw[2], raw[3]
        data = raw[4:4 + n]
        if typ == 4:
            ext = int.from_bytes(data, 'big') << 16
        elif typ == 0:
            for i in range(0, n - 1, 2):
                a = ext + addr + i
                w = data[i] | (data[i + 1] << 8)
                if a < 0x800:
                    prog[a // 2] = w & 0x3FFF
                elif a == CONFIG_BYTE:
                    cfg = w & 0x3FFF
    return prog, cfg

def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    exp_p, exp_c = load(sys.argv[1])
    got_p, got_c = load(sys.argv[2])
    bad = 0
    for w in range(1024):
        if w == OSCCAL_WORD:
            continue
        e, g = exp_p.get(w, 0x3FFF), got_p.get(w, 0x3FFF)
        if e != g:
            bad += 1
            if bad <= 10:
                print(f"palavra 0x{w:03X}: esperado 0x{e:04X}, lido 0x{g:04X}")
    if bad > 10:
        print(f"... e mais {bad - 10} diferenças")
    if exp_c != got_c:
        bad += 1
        print(f"configuração: esperada 0x{exp_c:04X}, lida 0x{got_c:04X}")
    osc = got_p.get(OSCCAL_WORD)
    if osc is None:
        print("aviso: a palavra 0x3FF (OSCCAL) não está no arquivo lido")
    elif (osc >> 8) != 0x34:
        print(f"aviso: 0x3FF = 0x{osc:04X} não é um RETLW (0x34xx): a calibração de fábrica pode ter sido apagada")
    print("IGUAL (programa e configuração)" if bad == 0 else f"{bad} diferença(s)")
    return 0 if bad == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
