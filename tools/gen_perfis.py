#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Gera os perfis das placas (D162): o que cada placa e versão tem, para o programa saber que firmware ela precisa.

Fonte: boards/<placa>/docs/pinmap.md (slots), boards/<placa>/hardware-<versão>/dumper.kicad_pcb (o seletor de tensão 3,3 V/5 V existe se o silk tem
"TRAVA 3,3 V", o jumper J1) e boards/versoes.json (versão atual). Saídas, sempre as mesmas por `--check`:
  boards/perfis.json                                   (fonte, para leitura humana)
  host/oscr_host/perfis.json                           (cópia dentro do pacote Python)
  gui/shared/src/jvmMain/resources/oscr/perfis.tsv     (para o Kotlin, que não tem biblioteca de JSON)
Uso, da raiz do repositório:  python3 tools/gen_perfis.py [--check]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOARDS = ROOT / "boards"
OUT_JSON = BOARDS / "perfis.json"
OUT_PKG = ROOT / "host/oscr_host/perfis.json"
OUT_TSV = ROOT / "gui/shared/src/jvmMain/resources/oscr/perfis.tsv"

# Ids de sistema do protocolo (docs/referencia/protocolo.md, seção 4).
SNES, NES, FAMICOM, MD, GBA, GB, FLASH, SMS, GG, SG1000, N64 = 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11
# O que cada slot lê, com os adaptadores que o protocolo prevê: o slot Mega Drive aceita adaptadores de Master System, Game Gear e SG-1000 (D137);
# o slot GBA aceita adaptador de Game Boy e Game Boy Color (D68); o slot SMS lê Master System e SG-1000.
SLOT_SYSTEMS = {"SNES": [SNES], "NES": [NES], "Famicom": [FAMICOM], "Mega Drive": [MD, SMS, GG, SG1000], "GBA": [GBA, GB],
                "Master System": [SMS, SG1000], "N64": [N64]}
ALWAYS = [FLASH]      # o programador de flash genérico (sistema 7) funciona em qualquer placa com slot; precisa do mesmo firmware
SLOT_RE = re.compile(r"^## (SNES|NES|Famicom|Mega Drive|Master System|GBA|N64) \(", re.M)


def profiles() -> dict:
    atual = json.loads((BOARDS / "versoes.json").read_text())
    out = {}
    for b in sorted(p for p in BOARDS.iterdir() if p.is_dir() and not p.name.startswith("_")):
        pinmap = b / "docs/pinmap.md"
        if not pinmap.exists() or b.name not in atual:
            continue
        slots = list(dict.fromkeys(SLOT_RE.findall(pinmap.read_text())))
        sistemas = sorted({s for sl in slots for s in SLOT_SYSTEMS[sl]} | set(ALWAYS))
        versions = {}
        for hw in sorted(b.glob("hardware-v*")):
            v = hw.name[len("hardware-"):]
            pcb = (hw / "dumper.kicad_pcb").read_text(errors="replace")
            versions[v] = {"seletor": "TRAVA 3,3 V" in pcb}
        out[b.name] = {"atual": atual[b.name]["atual"], "slots": slots, "sistemas": sistemas, "versoes": versions}
    return out


def render_json(p: dict) -> str:
    return json.dumps(p, indent=2, ensure_ascii=False) + "\n"


def render_tsv(p: dict) -> str:
    lines = ["# Gerado por tools/gen_perfis.py (boards/perfis.json). Não edite à mão.",
             "# placa\tversão\tatual\tslots\tsistemas\tseletor de tensão"]
    for board, d in p.items():
        for v, info in d["versoes"].items():
            lines.append("\t".join([board, v, "1" if v == d["atual"] else "0", ",".join(d["slots"]),
                                    ",".join(map(str, d["sistemas"])), "1" if info["seletor"] else "0"]))
    return "\n".join(lines) + "\n"


def main() -> int:
    p = profiles()
    want = {OUT_JSON: render_json(p), OUT_PKG: render_json(p), OUT_TSV: render_tsv(p)}
    if "--check" in sys.argv:
        bad = [str(f.relative_to(ROOT)) for f, t in want.items() if not f.is_file() or f.read_text(encoding="utf-8") != t]
        if bad:
            print("desatualizado (rode python3 tools/gen_perfis.py):", ", ".join(bad), file=sys.stderr)
        return 1 if bad else 0
    for f, t in want.items():
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(t, encoding="utf-8")
    print(f"{len(p)} placas, {sum(len(d['versoes']) for d in p.values())} versões")
    return 0


if __name__ == "__main__":
    sys.exit(main())
