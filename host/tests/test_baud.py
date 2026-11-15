# SPDX-License-Identifier: GPL-3.0-or-later
"""Baud do fallback (H-3, P-14): o host tenta 1.000.000, 500.000 e 115.200, nessa ordem; --baud fixa um só."""
import json
import time

from oscr_host import protocol as P
from oscr_host.cli import common, main


class Mudo:
    """Porta que abre mas nunca responde; guarda o baud de cada abertura."""
    abertas: list[int] = []

    def __init__(self, port, baud):
        Mudo.abertas.append(baud)

    def write(self, data): pass
    def read(self, n, timeout):
        time.sleep(min(timeout, 0.01))
        return b""
    def close(self): pass


def test_ordem_dos_bauds():
    assert P.BAUDS == (1_000_000, 500_000, 115_200) and common.BAUDS == P.BAUDS


def test_tenta_os_tres_e_lista_no_erro(monkeypatch, capsys):
    Mudo.abertas = []
    monkeypatch.setattr(common, "SerialTransport", Mudo)
    code = main(["--port", "/dev/falsa", "--json", "info"])
    assert code != 0 and Mudo.abertas == [1_000_000, 500_000, 115_200]
    assert "1000000, 500000, 115200" in json.loads(capsys.readouterr().out)["error"]["message"]


def test_baud_fixo_tenta_so_um(monkeypatch, capsys):
    Mudo.abertas = []
    monkeypatch.setattr(common, "SerialTransport", Mudo)
    main(["--port", "/dev/falsa", "--baud", "500000", "--json", "info"])
    assert Mudo.abertas == [500_000]
