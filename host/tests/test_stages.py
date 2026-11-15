# SPDX-License-Identifier: GPL-3.0-or-later
"""PROGRESSO com etapa (F-1): o firmware avisa apagando, gravando, lendo e autoteste; o cliente entrega ao CLI; firmware antigo não emite."""
import json

import pytest

from oscr_host import protocol as P
from oscr_host import sim
from oscr_host.cli import main
from oscr_host.client import Client


def run(capsys, *argv):
    code = main(list(argv))
    cap = capsys.readouterr()
    return code, cap.out, cap.err


def stage_events(err: str) -> list[str]:
    return [json.loads(l)["stage"] for l in err.splitlines() if l.startswith("{") and '"event": "stage"' in l]


def test_parse_progress():
    assert P.parse_progress((5).to_bytes(4, "little") + (9).to_bytes(4, "little") + bytes([P.STAGE_ERASE])) == (5, 9, P.STAGE_ERASE)
    assert P.parse_progress(bytes(8)) == (0, 0, P.STAGE_NONE)                  # firmware sem etapa: 8 bytes, etapa 0
    with pytest.raises(P.ProtocolError):
        P.parse_progress(bytes(7))


def _client(dev):
    t, dev, stop, th = sim.start(dev)
    c = Client(t, timeout=0.5, long_timeout=5.0)
    seen: list[tuple[int, int, int]] = []
    c.on_stage = lambda st, off, total: seen.append((st, off, total))
    return c, seen, stop


def test_client_recebe_as_etapas():
    c, seen, stop = _client(sim.MockDevice())
    try:
        c.selftest()
        c.erase(255, 3, 0, 0)
        res = c.dump_rom(255)
        c.write_save(255, res.data[:1024])
        c.write_rom(255, bytes(2048), 3, 2, 0)
    finally:
        stop.set()
    stages = [s for s, _, _ in seen]
    assert stages == [P.STAGE_SELFTEST, P.STAGE_ERASE, P.STAGE_READ, P.STAGE_WRITE, P.STAGE_ERASE, P.STAGE_WRITE]
    assert seen[2][2] == len(res.data)                                          # a leitura anuncia o total


def test_firmware_antigo_nao_emite_e_nada_quebra():
    c, seen, stop = _client(sim.MockDevice(stages=False))
    try:
        c.erase(255, 3, 0, 0)
        c.dump_rom(255)
    finally:
        stop.set()
    assert seen == []


def test_etapa_torta_nao_derruba_o_comando():
    c, seen, stop = _client(sim.MockDevice())
    try:
        c._stage(P.Frame(P.T_PROGRESSO, 1, b"\x01\x02"))                        # curto demais: ignora
        c._stage(P.Frame(P.T_PROGRESSO, 1, bytes(8)))                           # sem etapa: ignora
    finally:
        stop.set()
    assert seen == []


def test_cli_jsonl_mostra_a_etapa(capsys):
    code, out, err = run(capsys, "--simulate", "--json", "--progress", "jsonl", "selftest")
    assert code == 0 and stage_events(err) == ["selftest"]
    code, out, err = run(capsys, "--simulate", "--json", "--progress", "none", "selftest")
    assert code == 0 and stage_events(err) == []


def test_cli_firmware_antigo_sem_etapa(capsys, monkeypatch):
    monkeypatch.setenv("OSCR_SIM_OLD_FW", "1")
    code, out, err = run(capsys, "--simulate", "--json", "--progress", "jsonl", "selftest")
    assert stage_events(err) == []
