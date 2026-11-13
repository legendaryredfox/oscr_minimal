# SPDX-License-Identifier: GPL-3.0-or-later
"""MD-10: a fase `host` da suíte de bancada somente leitura do Mega Drive (tools/boards/megadrive/hwtest_md.py) roda sem hardware e tem que passar."""
import importlib.util
import types
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "tools" / "boards" / "megadrive" / "hwtest_md.py"


def _load():
    spec = importlib.util.spec_from_file_location("hwtest_md", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_fase_host_passa(tmp_path):
    m = _load()
    rep = m.Report("host", tmp_path)
    m.phase_host(rep, types.SimpleNamespace(port=None))
    assert not rep.failed, [r for r in rep.rows if r["status"] == "FAIL"]
    assert len(rep.rows) >= 15


@pytest.mark.parametrize("args", [["rom-write", "x"], ["save-write", "x"], ["flash-erase"], ["detect", "-s", "md", "--flash-id"], ["dump", "-y"], ["firmware-flash"], []])
def test_guarda_recusa_o_que_escreve(args):
    m = _load()
    with pytest.raises(m.Guard):
        m.run_cli(args, simulate=True)
