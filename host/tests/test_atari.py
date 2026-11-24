# SPDX-License-Identifier: GPL-3.0-or-later
"""Atari 5200 e 7800 (F-20, D209): sistemas 16 e 17, tamanhos por mapper (as mesmas regras no firmware, no Python e no Kotlin)."""
from __future__ import annotations

import pathlib
import re

from oscr_host import atari as A
from oscr_host import protocol as P
from oscr_host.cli import cmd_info
from oscr_host.planned import PLANNED

ROOT = pathlib.Path(__file__).parents[2]


def test_ids_e_extensoes():
    assert P.SYSTEMS["a5200"] == (16, ".a52") and P.SYSTEMS["a7800"] == (17, ".a78")
    assert P.SYSTEM_BY_ID[16] == "a5200" and P.SYSTEM_BY_ID[17] == "a7800"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))
    h = (ROOT / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_A52 = 16\b", h) and re.search(r"SYS_A78 = 17\b", h)


def test_sairam_dos_planejados():
    assert not {"a5200", "a7800"} & {k for k, _ in PLANNED}


def test_opcoes():
    assert cmd_info.SYSTEM_OPTIONS["a5200"] == ["mapper", "prg"] and cmd_info.SYSTEM_OPTIONS["a7800"] == ["mapper", "prg"]


def test_tamanhos_5200():
    assert [A.a5200_kb(0, k) for k in (4, 8, 16, 32)] == [4, 8, 16, 32]
    assert A.a5200_kb(0, 12) == 0 and A.a5200_kb(0, 0) == 0
    assert A.a5200_kb(1, 0) == 16 and A.a5200_kb(2, 0) == 40 and A.a5200_kb(3, 16) == 0


def test_tamanhos_7800():
    assert [A.a7800_kb(0, k) for k in (16, 32, 48)] == [16, 32, 48] and A.a7800_kb(0, 64) == 0
    assert [A.a7800_kb(m, 0) for m in (1, 2, 3, 4, 5, 6, 8)] == [128, 144, 64, 128, 64, 64, 144] and A.a7800_kb(9, 16) == 0
    assert [A.a7800_kb(7, k) for k in (32, 48, 64, 128)] == [64, 96, 96, 256] and A.a7800_kb(7, 16) == 0


def test_mesmas_regras_no_firmware():
    """Roda os mesmos casos contra o C++ de AtariCore.h (compila um programa pequeno)."""
    import shutil, subprocess, tempfile
    cxx = shutil.which("g++") or shutil.which("c++")
    if cxx is None:
        import pytest; pytest.skip("sem compilador C++")
    cases52 = [(m, k) for m in range(0, 5) for k in (0, 4, 8, 12, 16, 32, 40)]
    cases78 = [(m, k) for m in range(0, 10) for k in (0, 16, 32, 48, 64, 128, 144)]
    src = '#include <stdio.h>\n#include "dumper/AtariCore.h"\nint main(){\n'
    src += "".join(f'printf("%d\\n", oscr::atari::a52Kb({m},{k}));' for m, k in cases52)
    src += "".join(f'printf("%d\\n", oscr::atari::a78Kb({m},{k}));' for m, k in cases78) + "return 0;}\n"
    with tempfile.TemporaryDirectory() as d:
        (pathlib.Path(d) / "t.cpp").write_text(src)
        subprocess.run([cxx, "-std=c++11", "-I", str(ROOT / "firmware/oscr/include"), "-o", f"{d}/t", f"{d}/t.cpp"], check=True)
        out = [int(x) for x in subprocess.run([f"{d}/t"], check=True, capture_output=True, text=True).stdout.split()]
    want = [A.a5200_kb(m, k) for m, k in cases52] + [A.a7800_kb(m, k) for m, k in cases78]
    assert out == want


def test_atari8_e_lynx():
    assert P.SYSTEMS["a8bit"] == (18, ".rom") and P.SYSTEMS["lynx"] == (19, ".lnx")
    assert not {"a8bit", "lynx"} & {k for k, _ in PLANNED}
    assert cmd_info.SYSTEM_OPTIONS["a8bit"] == ["mapper", "prg"] and cmd_info.SYSTEM_OPTIONS["lynx"] == []
    h = (ROOT / "firmware/oscr/src/dumper/oscr_proto.h").read_text()
    assert re.search(r"SYS_A8 = 18\b", h) and re.search(r"SYS_LYNX = 19\b", h)
    assert [A.a8_kb(0, k) for k in A.A8_SIZES] == list(A.A8_SIZES) and A.a8_kb(0, 24) == 0 and A.a8_kb(1, 0) == 8 and A.a8_kb(2, 8) == 0
    assert A.lynx_bytes(512) == 64 + 131072 and A.lynx_bytes(2048) == 64 + 524288 and A.lynx_bytes(256) == 0


def test_atari8_e_lynx_iguais_no_firmware():
    import shutil, subprocess, tempfile
    cxx = shutil.which("g++") or shutil.which("c++")
    if cxx is None:
        import pytest; pytest.skip("sem compilador C++")
    c8 = [(m, k) for m in range(0, 4) for k in (0, 8, 16, 24, 32, 40, 64, 128)]
    cl = [0, 256, 512, 1024, 2048, 4096]
    src = '#include <stdio.h>\n#include "dumper/AtariCore.h"\nint main(){\n'
    src += "".join(f'printf("%d\\n", oscr::atari8::totalKb({m},{k}));' for m, k in c8)
    src += "".join(f'printf("%u\\n", (unsigned)oscr::lynx::totalBytes({b}));' for b in cl) + "return 0;}\n"
    with tempfile.TemporaryDirectory() as d:
        (pathlib.Path(d) / "t.cpp").write_text(src)
        subprocess.run([cxx, "-std=c++11", "-I", str(ROOT / "firmware/oscr/include"), "-o", f"{d}/t", f"{d}/t.cpp"], check=True)
        out = [int(x) for x in subprocess.run([f"{d}/t"], check=True, capture_output=True, text=True).stdout.split()]
    assert out == [A.a8_kb(m, k) for m, k in c8] + [A.lynx_bytes(b) for b in cl]


def test_jaguar():
    assert P.SYSTEMS["jaguar"] == (20, ".jag") and P.SYSTEM_BY_ID[20] == "jaguar"
    assert "jaguar" not in {k for k, _ in PLANNED}
    assert cmd_info.SYSTEM_OPTIONS["jaguar"] == ["mapper", "prg"]
    assert [A.jaguar_save_bytes(m) for m in range(7)] == [128, 256, 512, 1024, 2048, 131072, 0] and set(A.JAGUAR_SAVES) == set(range(6))
    assert re.search(r"SYS_JAG = 20\b", (ROOT / "firmware/oscr/src/dumper/oscr_proto.h").read_text())
    assert [A.jaguar_index(k) for k in (1024, 2048, 4096, 0, 512, 6144)] == [0, 1, 2, None, None, None]
    import shutil, subprocess, tempfile
    cxx = shutil.which("g++") or shutil.which("c++")
    if cxx is not None:
        ks = (0, 512, 1024, 2048, 4096, 6144)
        src = '#include <stdio.h>\n#include "dumper/AtariCore.h"\nint main(){\n' + "".join(f'printf("%d\\n", oscr::jag::sizeIndex({k}));' for k in ks) + "".join(f'printf("%u\\n", (unsigned)oscr::jag::saveBytes({m}));' for m in range(7)) + "return 0;}\n"
        with tempfile.TemporaryDirectory() as d:
            (pathlib.Path(d) / "t.cpp").write_text(src)
            subprocess.run([cxx, "-std=c++11", "-I", str(ROOT / "firmware/oscr/include"), "-o", f"{d}/t", f"{d}/t.cpp"], check=True)
            out = [int(x) for x in subprocess.run([f"{d}/t"], check=True, capture_output=True, text=True).stdout.split()]
        assert out == [255 if A.jaguar_index(k) is None else A.jaguar_index(k) for k in ks] + [A.jaguar_save_bytes(m) for m in range(7)]


def test_nomes_iguais_no_kotlin():
    kt = (ROOT / "gui/shared/src/commonMain/kotlin/oscr/Atari.kt").read_text()
    names = {int(i): n for i, n in re.findall(r'Mapper\((\d+), "([^"]+)"', kt)}
    # A5200 e A7800 compartilham ids 0 a 2: confere pelo conjunto de (id, nome)
    pares = set(re.findall(r'Mapper\((\d+), "([^"]+)"', kt))
    assert pares == {(str(i), n) for i, n in A.A5200.items()} | {(str(i), n) for i, n in A.A7800.items()}
