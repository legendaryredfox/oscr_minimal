# SPDX-License-Identifier: GPL-3.0-or-later
"""D199: progresso com tamanho desconhecido (núcleos do OSCR anunciam 0xFFFFFFFF no BEGIN) usa o tamanho do DETECT; `--block` tem mínimo."""
import json

import pytest

from oscr_host import protocol as P
from oscr_host import sim
from oscr_host.cli import main
from oscr_host.client import Client


def _client(unknown: bool):
    dev = sim.MockDevice()
    dev.unknown_size = unknown
    t, dev, stop, th = sim.start(dev)
    return Client(t, timeout=0.5, long_timeout=5.0), stop


def test_sem_dica_o_total_e_zero_quando_o_tamanho_e_desconhecido():
    c, stop = _client(True)
    seen = []
    try:
        res = c.dump_rom(255, 0, lambda d, tot: seen.append((d, tot)))
    finally:
        stop.set()
    assert len(res.data) == 32768 and seen and all(tot == 0 for _, tot in seen)


def test_com_dica_o_progresso_anda_e_nunca_passa_de_100():
    c, stop = _client(True)
    seen = []
    c.size_hint = 30000                                   # estimativa menor que o real: o total sobe junto, sem passar de 100 %
    try:
        c.dump_rom(255, 0, lambda d, tot: seen.append((d, tot)))
    finally:
        stop.set()
    assert seen[0][1] == 30000 and seen[-1] == (32768, 32768)
    assert all(d <= tot for d, tot in seen)


def test_tamanho_conhecido_ignora_a_dica():
    c, stop = _client(False)
    seen = []
    c.size_hint = 5
    try:
        c.dump_rom(255, 0, lambda d, tot: seen.append((d, tot)))
    finally:
        stop.set()
    assert all(tot == 32768 for _, tot in seen)


@pytest.mark.parametrize("blk,ok", [("1", False), ("63", False), ("517", False), ("64", True), ("512", True), ("516", True), ("0", True)])
def test_block_tem_minimo_e_maximo(capsys, tmp_path, blk, ok):
    code = main(["--simulate", "--json", "dump", "-s", "mock", "--block", blk, "-o", str(tmp_path / "x")])
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    if ok:
        assert code == 0 and out["ok"]
    else:
        assert code == 64 and out["error"]["kind"] == "usage"
