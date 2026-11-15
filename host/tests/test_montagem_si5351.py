"""D-6: o aviso do módulo Si5351 é igual em todo montagem.md de placa com o header U1."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_aviso_do_si5351_igual_em_todas_as_placas():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "check_montagem_si5351.py")], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout
