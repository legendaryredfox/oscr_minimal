#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Copia para database/oscr/json/ as bases JSON de cartuchos do repositório oscartreader/oscr-databases (D127).

Fonte: data/*.json de um clone de https://github.com/oscartreader/oscr-databases (passe a pasta como argumento; o clone fica fora do repositório).
Só entram os arquivos de cartucho (`type` CART). Os arquivos são copiados byte a byte. O `INDEX.txt` de database/oscr/ (a GUI lê por ele)
mantém as linhas da base antiga e ganha uma linha `json/<arquivo>` por arquivo copiado.
Uso: python3 tools/importar_oscr_databases.py <clone>/data   (ou o clone: a pasta `data` é achada sozinha)"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DST = ROOT / "database" / "oscr"
JDST = DST / "json"


def main(argv) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    src = Path(argv[1]).resolve()
    if (src / "data").is_dir():
        src = src / "data"
    if not src.is_dir():
        print(f"pasta inexistente: {src}", file=sys.stderr)
        return 1
    commit = subprocess.run(["git", "-C", str(src), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip() or "?"
    JDST.mkdir(parents=True, exist_ok=True)
    for old in JDST.glob("*.json"):
        old.unlink()
    nomes, linhas, total, validos = [], [], 0, 0
    for f in sorted(src.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(d, dict) or d.get("type") != "CART" or not isinstance(d.get("records"), list):
            continue
        (JDST / f.name).write_bytes(f.read_bytes())
        ok = sum(1 for r in d["records"] if isinstance(r.get("crc32"), str) and re.fullmatch(r"[0-9A-Fa-f]{1,8}", r["crc32"]) and int(r["crc32"], 16) != 0)
        nomes.append(f"json/{f.name}")
        linhas.append(f"{f.name}  {d.get('system', '?')}  {len(d['records'])} registros, {ok} com CRC32")
        total += len(d["records"]); validos += ok
    flash = src / "flash.json"                                        # tabela de chips (type IC): ID -> tipo, tamanho, setor, buffer (D135)
    if flash.is_file():
        (DST / "chips").mkdir(exist_ok=True)
        (DST / "chips" / "flash.json").write_bytes(flash.read_bytes())
        (DST / "chips" / "ORIGEM.txt").write_text(
            "Tabela de chips de flash do OSCR (ID -> tipo, tamanho, setor, buffer), usada pelo flash-id para sugerir --flash-type e --flash-kb (D135).\n"
            f"Origem : https://github.com/oscartreader/oscr-databases  (data/flash.json)\nCommit : {commit}\n"
            "Licença: a mesma do resto de database/oscr/json (o repositório de origem não declara licença; ver ../json/ORIGEM.txt).\n"
            "Cópia byte a byte. Gerado por tools/importar_oscr_databases.py. Não editar à mão.\n")
    index = DST / "INDEX.txt"
    antigas = [l for l in index.read_text().split() if not l.startswith("json/")] if index.exists() else []
    index.write_text("\n".join(antigas + nomes) + "\n")
    (JDST / "ORIGEM.txt").write_text(
        "Bases de cartuchos do OSCR (formato JSON), usadas no PC para identificar o jogo por CRC32 (D127).\n"
        "Origem : https://github.com/oscartreader/oscr-databases  (pasta data/)\n"
        f"Commit : {commit}\n"
        "Licença: o repositório de origem NÃO declara licença (sem arquivo de licença; a API do GitHub devolve 404, conferido em 2026-11-07).\n"
        "         Importado a pedido do usuário em 2026-11-07. O conteúdo são nomes de jogos e CRC32 (fatos); se os autores pedirem, remova esta pasta.\n"
        "Formato: {\"system\", \"type\": \"CART\", \"records\": [{\"name\", \"crc32\" (hexadecimal sem zeros à esquerda; \"0\" = sem CRC), ...}]}.\n"
        "         nes: header (iNES de 16 bytes em hexadecimal). snes: checksum, id32, size (bytes), banks. gba: serial, size (MB), saveType.\n"
        "Só entra na base do PC o CRC32 que ainda não está nos .txt do OSCR antigo (o nome do .txt vence).\n"
        "Gerado por tools/importar_oscr_databases.py. Não editar à mão.\n\n"
        + "\n".join(linhas) + f"\nTotal  {total} registros, {validos} com CRC32\n")
    print(f"{len(nomes)} arquivos, {validos} registros com CRC32, commit {commit}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
