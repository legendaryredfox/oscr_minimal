#!/usr/bin/env python3
"""Converte um .hex Intel de PIC12F629 em um cabeçalho C++ com as palavras de 14 bits.

Uso: hex2words.py entrada.hex saida.h NOME

Só as palavras de programa (endereço de byte < 0x800) entram; a palavra de configuração
(byte 0x400E) é ignorada. Posições não gravadas ficam 0x3FFF, como no chip apagado.
"""
import sys

def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    src, dst, name = sys.argv[1:4]
    words = [0x3FFF] * 1024
    ext = 0
    used = 0
    for line in open(src):
        line = line.strip()
        if not line.startswith(':'):
            continue
        n = int(line[1:3], 16)
        addr = int(line[3:7], 16)
        typ = int(line[7:9], 16)
        data = bytes.fromhex(line[9:9 + 2 * n])
        if (sum(bytes.fromhex(line[1:])) & 0xFF) != 0:
            raise SystemExit(f"checksum errado: {line}")
        if typ == 4:
            ext = int.from_bytes(data, 'big') << 16
        elif typ == 0:
            for i in range(0, n, 2):
                a = ext + addr + i
                if a < 0x800:
                    words[a // 2] = data[i] | (data[i + 1] << 8)
                    used = max(used, a // 2 + 1)
    with open(dst, 'w') as f:
        f.write(f"// Gerado por tools/hex2words.py a partir de {src.split('/')[-1]}. Não edite.\n")
        f.write("#pragma once\n#include <stdint.h>\n\n")
        f.write(f"static const uint16_t {name}[{used}] = {{\n")
        for i in range(0, used, 8):
            f.write("  " + ", ".join(f"0x{w:04X}" for w in words[i:min(i + 8, used)]) + ",\n")
        f.write("};\n")
        f.write(f"static const unsigned {name}_words = {used};\n")
    print(f"{used} palavras -> {dst}")
    return 0

if __name__ == '__main__':
    sys.exit(main())
