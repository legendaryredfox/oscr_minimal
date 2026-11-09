# SPDX-License-Identifier: GPL-3.0-or-later
"""Família Sega de 8 bits (D137): Master System, Game Gear e SG-1000 no protocolo, na CLI e na lista de sistemas.
O firmware (núcleo SMS.cpp do OSCR) não roda no PC; as regras puras dele estão testadas em firmware/oscr/pc-tests/test_sms.cpp."""
from __future__ import annotations

from oscr_host import protocol as P
from oscr_host.cli import cmd_detect as CD
from oscr_host.cli import cmd_info
from oscr_host.cli.parser import build_parser
from oscr_host.planned import PLANNED


def test_ids_e_extensoes():
    assert P.SYSTEMS["sms"] == (8, ".sms")
    assert P.SYSTEMS["gg"] == (9, ".gg")
    assert P.SYSTEMS["sg1000"] == (10, ".sg")
    assert P.SYSTEM_BY_ID[8] == "sms" and P.SYSTEM_BY_ID[9] == "gg" and P.SYSTEM_BY_ID[10] == "sg1000"
    ids = [v[0] for v in P.SYSTEMS.values()]
    assert len(ids) == len(set(ids))          # nenhum id repetido


def test_sms_saiu_da_lista_de_planejados():
    assert "sms" not in [k for k, _ in PLANNED]
    assert "Master System" not in [l for _, l in PLANNED]


def test_opcoes_por_sistema():
    assert cmd_info.SYSTEM_OPTIONS["sms"] == ["mapper", "prg"]
    assert cmd_info.SYSTEM_OPTIONS["gg"] == ["mapper", "prg"]
    assert cmd_info.SYSTEM_OPTIONS["sg1000"] == ["prg"]


def test_parser_aceita_os_tres_sistemas_e_o_adaptador():
    p = build_parser()
    for s in ("sms", "gg", "sg1000"):
        a = p.parse_args(["--simulate", "detect", "-s", s, "--mapper", "2"])
        assert a.system == s and a.mapper == 2
        a = p.parse_args(["--simulate", "dump", "-s", s, "--mapper", "1", "--prg", "128"])
        assert a.system == s and a.mapper == 1 and a.prg == 128


def test_detect_so_manda_o_adaptador_nos_sistemas_sega(monkeypatch, capsys):
    chamadas = []

    class FakeClient:
        def voltage(self, action=0):                                        # placa sem seletor: o detect não oferece 5 V
            return {"voltage_select": False, "voltage": "5v-fixed", "chosen": False}

        def detect(self, system, chip=0, prg_kb=0, chr_kb=0):
            chamadas.append((system, chip))
            return {"system": system, "status": 1, "name": "", "rom_size": 0, "save_size": 0, "save_type": 0}

    class FakeT:
        def close(self):
            pass

    monkeypatch.setattr(CD.common, "connect", lambda args: (FakeClient(), FakeT(), {"voltage_select": False}))
    p = build_parser()
    for s, esperado in (("sms", 2), ("gg", 2), ("sg1000", 2), ("snes", 0), ("md", 0)):
        a = p.parse_args(["detect", "-s", s, "--mapper", "2"])
        CD.cmd_detect(a)
    assert chamadas == [(8, 2), (9, 2), (10, 2), (1, 0), (4, 0)]


def test_detect_com_adaptador_vai_no_payload():
    # o adaptador viaja no campo "chip" do DETECT (o mesmo uso do programador de flash genérico)
    assert P.build_detect(8, 0) == bytes([8])                       # slot direto: payload curto, como antes
    pl = P.build_detect(9, 1)
    assert pl[0] == 9 and int.from_bytes(pl[1:3], "little") == 1
