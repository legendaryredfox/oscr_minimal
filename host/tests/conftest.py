"""Os testes antigos conferem textos em português: a CLI usa pt-BR a menos que o teste peça outro idioma (D133)."""
import pytest

from oscr_host.cli import messages


@pytest.fixture(autouse=True)
def _idioma_pt(monkeypatch):
    for v in ("LC_ALL", "LC_MESSAGES", "LANG"):
        monkeypatch.delenv(v, raising=False)
    monkeypatch.setenv("OSCR_LANG", "pt-BR")
    messages.set_lang("pt-BR")
    yield
    messages.set_lang("pt-BR")
