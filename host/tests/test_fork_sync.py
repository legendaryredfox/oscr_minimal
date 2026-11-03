# SPDX-License-Identifier: GPL-3.0-or-later
"""Os arquivos do protocolo copiados para o fork do OSCR (firmware/oscr/src/dumper) têm que ser idênticos aos de firmware/oscr_serial.

Enquanto o firmware próprio existir, o protocolo mora em oscr_serial (com testes) e o fork usa uma cópia. Quando oscr_serial for
arquivado, a cópia do fork passa a ser a única e este teste sai.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_copias_do_protocolo_no_fork_sao_identicas():
    for name in ("oscr_proto.h", "oscr_proto.cpp", "oscr_session.h", "oscr_session.cpp"):
        a = (ROOT / "firmware/oscr_serial" / name).read_text()
        b = (ROOT / "firmware/oscr/src/dumper" / name).read_text()
        assert a == b, f"{name} diverge entre firmware/oscr_serial e firmware/oscr/src/dumper (copie de oscr_serial)"
