#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gera database/flashgbx/gba.tsv a partir de FlashGBX/config/db_AGB.json (Lesserkuma, GPL-3.0; D160, P2).
Uma linha por jogo de GBA: SHA-1 dos primeiros 0x180 bytes do cabeçalho (0x100 nos códigos de jogo que começam com "M"; 0x0A a 0x180 nos "YJencrypted"),
CRC32 da ROM, tamanho da ROM, tipo de save (a numeração do OSCR e do FlashGBX: 0 nenhum, 1 EEPROM 512 B, 2 EEPROM 8 KB, 3 SRAM 32 KB, 4 Flash 64 KB, 5 Flash 128 KB,
6 Flash 1 MB), tamanho do save e o nome. Uso: python3 tools/importar_flashgbx.py <pasta do FlashGBX> [commit]
(ex.: python3 tools/importar_flashgbx.py references/repos/FlashGBX 5b2398b)"""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
commit = sys.argv[2] if len(sys.argv) > 2 else "?"
db = json.loads((root / "FlashGBX" / "config" / "db_AGB.json").read_text(encoding="utf-8"))
out = Path(__file__).resolve().parents[1] / "database" / "flashgbx"
out.mkdir(parents=True, exist_ok=True)
rows = []
for sha1, v in db.items():
    name = (v["gn"] + " " + v.get("ne", "")).strip().replace("\t", " ")
    rows.append((sha1.upper(), f'{int(v["rc"]):08X}', int(v["rs"]), int(v["st"]), int(v["ss"]), name))
rows.sort(key=lambda r: (r[5].lower(), r[0]))
(out / "gba.tsv").write_text("# sha1_cabecalho\tcrc32\ttamanho_rom\ttipo_save\ttamanho_save\tnome\n" + "".join("\t".join(str(x) for x in r) + "\n" for r in rows), encoding="utf-8")
(out / "ORIGEM.txt").write_text(f"""gba.tsv vem de FlashGBX/config/db_AGB.json (https://github.com/Lesserkuma/FlashGBX, commit {commit}, licença GPL-3.0, de Lesserkuma e colaboradores).
Gerado por tools/importar_flashgbx.py (D160, P2). {len(rows)} jogos de GBA: o SHA-1 dos primeiros 0x180 bytes do cabeçalho dá o tipo e o tamanho do save.
A base do FlashGBX deriva de listas da comunidade e de conferências do autor; ver o 'Third Party Notices.md' do repositório de origem.
""", encoding="utf-8")
print(len(rows), "jogos")
