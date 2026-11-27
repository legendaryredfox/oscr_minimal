#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compila o firmware e gera firmware/images/ (o .hex e o manifest.json) que a GUI e a CLI usam para gravar o Arduino (D162).

O manifest.json (e a cópia manifest.tsv, para o Kotlin) diz, de cada imagem, a versão do firmware, os sistemas que ela lê e o SHA-256 do .hex. A versão e os sistemas saem do código-fonte
(`oscr_session.cpp` e `Dumper.cpp`), então não dá para o manifest mentir sobre o que foi compilado. Hoje há uma imagem só (`completa`):
imagens separadas só se o orçamento de flash estourar (docs/referencia/fork-oscr.md, seção 4).

Uso: python3 tools/build_images.py [--no-build] [--out firmware/images]
Os .hex e o manifest não vão para o git (são resultado de compilação); a release do programa os embute (H-7).
"""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FW = ROOT / "firmware/oscr"
PIO = Path.home() / ".platformio/penv/bin/pio"
ENV = "SerialASCII"


def firmware_version() -> str:
    m = re.search(r"uint8_t p\[9\] = \{PROTO_VERSION, (\d+), (\d+), (\d+),", (FW / "src/dumper/oscr_session.cpp").read_text())
    if not m:
        sys.exit("não achei a versão do firmware em oscr_session.cpp (do_info)")
    return ".".join(m.groups())


def system_ids() -> list[int]:
    proto = (FW / "src/dumper/oscr_proto.h").read_text()
    enum = re.search(r"SYS_SNES = 1,.*?SYS_MOCK = 255", proto, re.S).group(0)
    ids = {n: int(v) for n, v in re.findall(r"SYS_(\w+) = (\d+)", enum)}
    line = re.search(r"uint16_t systems\(\) override \{ return (.*?); \}", (FW / "src/dumper/Dumper.cpp").read_text()).group(1)
    names = re.findall(r"oscr::SYS_(\w+)", line)
    return sorted(ids[n] for n in names)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-build", action="store_true", help="usa o .hex já compilado")
    ap.add_argument("--out", default=str(ROOT / "firmware/images"))
    a = ap.parse_args()
    if not a.no_build:
        r = subprocess.run([str(PIO), "run", "-e", ENV], cwd=FW)
        if r.returncode != 0:
            return r.returncode
    src = FW / ".pio/build" / ENV / "firmware.hex"
    if not src.is_file():
        sys.exit(f"falta {src}; rode sem --no-build")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ver = firmware_version()
    name = f"oscr-{ver}-completa.hex"
    shutil.copy(src, out / name)
    manifest = {"images": [{"id": "completa", "hex": name, "firmware": ver, "sistemas": system_ids(), "env": ENV,
                            "sha256": hashlib.sha256((out / name).read_bytes()).hexdigest()}]}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    e = manifest["images"][0]                                     # o Kotlin lê esta versão (sem biblioteca de JSON): id, hex, firmware, sistemas, sha256
    (out / "manifest.tsv").write_text("# id\thex\tfirmware\tsistemas\tsha256\n" + "\t".join([e["id"], e["hex"], e["firmware"], ",".join(map(str, e["sistemas"])), e["sha256"]]) + "\n")
    print(f"{out / name} (firmware {ver}, sistemas {manifest['images'][0]['sistemas']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
