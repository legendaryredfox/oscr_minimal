#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Copia para database/oscr/ as bases do OSCR legado dos sistemas que este projeto lê ou prevê (D88).

Fonte: vendor/oscr/legacy/sd/*.txt (github.com/sanni/cartreader, GPL v3). Os arquivos são copiados byte a byte
(CRLF preservado). Só entram sistemas cuja linha de dados começa pelo CRC32 da ROM e que o projeto usa; os outros
arquivos de legacy/sd (2600, c64, msx, n64, ...) têm outro formato ou outro sistema e ficam de fora.
Uso: python3 tools/importar_base_oscr.py
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "vendor/oscr/legacy/sd"
DST = ROOT / "database/oscr"
SISTEMAS = ["snes", "nes", "md", "32x", "gb", "gba", "gg", "sms", "sg1000", "pce", "vb"]


def main() -> int:
    if not SRC.is_dir():
        print(f"fonte ausente: {SRC} (clone do OSCR legado; ver README.md)", file=sys.stderr)
        return 1
    commit = subprocess.run(["git", "-C", str(SRC), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    DST.mkdir(parents=True, exist_ok=True)
    total = 0
    linhas = []
    for s in SISTEMAS:
        data = (SRC / f"{s}.txt").read_bytes()
        (DST / f"{s}.txt").write_bytes(data)
        texto = [l for l in data.decode("utf-8").replace("\r", "").split("\n") if l.strip()]
        n = len(texto) // 2
        assert all(re.match(r"^[0-9A-Fa-f]{8}(,|$)", texto[i + 1]) for i in range(0, len(texto) - 1, 2)), s
        total += n
        linhas.append(f"{s}.txt  {n} jogos")
    (DST / "INDEX.txt").write_text("\n".join(f"{s}.txt" for s in SISTEMAS) + "\n")
    (DST / "ORIGEM.txt").write_text(
        "Base de jogos do OSCR legado (Cart Reader), usada para identificar o jogo por CRC32 no PC.\n"
        "Origem : https://github.com/sanni/cartreader  (pasta sd/)\n"
        f"Commit : {commit}\n"
        "Licença: GNU GPL v3 (o mesmo do projeto; veja LICENSE.md na raiz)\n"
        "Formato: um bloco por jogo (nome, linha de dados, linha em branco), CRLF. A linha de dados começa pelo CRC32.\n"
        "         nes: CRC32 (PRG+CHR sem cabeçalho), CRC32 de 512 bytes, cabeçalho iNES em hexadecimal.\n"
        "         snes: CRC32, checksum interno, CRC32 da área do cabeçalho, tamanho em Mbit, bancos.\n"
        "         gba: CRC32, id do jogo, tamanho em MB, tipo de save. Os demais: só o CRC32.\n"
        "Gerado por tools/importar_base_oscr.py. Não editar à mão; INDEX.txt lista os arquivos (a GUI lê por ele).\n\n"
        + "\n".join(linhas) + f"\nTotal  {total} jogos\n")
    print(f"{total} jogos em {len(SISTEMAS)} arquivos, commit {commit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
