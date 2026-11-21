# SPDX-License-Identifier: GPL-3.0-or-later
"""D199: avrdude travado não prende a CLI para sempre: o tempo limite mata o processo e devolve 124."""
import sys
import time

from oscr_host.cli import cmd_firmware


def test_avrdude_que_nao_termina_e_morto_no_tempo_limite(monkeypatch):
    monkeypatch.setattr(cmd_firmware, "AVRDUDE_TIMEOUT_S", 1)
    t0 = time.time()
    code, msg = cmd_firmware.run_avrdude([sys.executable, "-c", "import time; time.sleep(60)"], lambda label: (lambda d, t: None))
    assert code == 124 and "timeout" in msg and time.time() - t0 < 10


def test_avrdude_normal_nao_e_afetado(monkeypatch):
    code, msg = cmd_firmware.run_avrdude([sys.executable, "-c", "import sys; sys.stderr.write('ok\\n')"], lambda label: (lambda d, t: None))
    assert code == 0 and "ok" in msg
