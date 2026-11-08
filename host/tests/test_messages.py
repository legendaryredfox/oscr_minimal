"""CLI multi-idioma (D133): catálogo completo, escolha do idioma e o que NÃO muda (chaves do JSON, códigos de saída)."""
import json
import re

import pytest

from oscr_host import protocol as P
from oscr_host.cli import main, messages
from oscr_host.cli.messages import CATALOG, LANGS

FIELD = re.compile(r"\{(\w+)(?::[^}]*)?\}")


def test_todo_texto_tem_os_quatro_idiomas_e_os_mesmos_campos():
    for key, row in CATALOG.items():
        assert set(row) == set(LANGS), key
        assert all(row[l].strip() for l in LANGS), key
        fields = {l: sorted(FIELD.findall(row[l])) for l in LANGS}
        assert len({tuple(v) for v in fields.values()}) == 1, (key, fields)


def test_todo_erro_do_dispositivo_tem_texto_e_dica():
    for code in P.ERRORS:
        assert f"dev.{code}.msg" in CATALOG and f"dev.{code}.hint" in CATALOG, code


@pytest.mark.parametrize("raw,esperado", [("pt_BR.UTF-8", "pt-BR"), ("pt", "pt-BR"), ("en_US", "en"), ("ru_RU.UTF-8", "ru"), ("zh_CN", "zh-CN"), ("zh", "zh-CN"), ("de_DE", None), ("", None), (None, None)])
def test_normalize(raw, esperado):
    assert messages.normalize(raw) == esperado


def test_escolha_do_idioma():
    assert messages.detect(["--lang", "ru"], {"LANG": "pt_BR.UTF-8"}) == "ru"          # --lang vence
    assert messages.detect(["x", "--lang=zh"], {}) == "zh-CN"
    assert messages.detect([], {"OSCR_LANG": "en", "LANG": "pt_BR.UTF-8"}) == "en"     # OSCR_LANG vence a locale
    assert messages.detect([], {"LANG": "pt_BR.UTF-8"}) == "pt-BR"
    assert messages.detect([], {"LC_ALL": "ru_RU.UTF-8", "LANG": "pt_BR.UTF-8"}) == "ru"
    assert messages.detect([], {}) == "en"                                              # sem nada: inglês
    assert messages.detect([], {"LANG": "de_DE.UTF-8"}) == "en"                         # idioma sem tradução: inglês


def _run(capsys, *argv):
    code = main(list(argv))
    o = capsys.readouterr()
    return code, o.out, o.err


def test_json_so_muda_o_texto_nao_as_chaves(capsys):
    shapes, kinds = set(), set()
    textos = set()
    for lang in LANGS:
        code, out, _ = _run(capsys, "--json", "--lang", lang, "--simulate", "detect", "-s", "snes", "--power", "keep", "-p", "/dev/x")
        # sem cartucho no simulador: o detect sai com 2; o importante é a forma do JSON
        r = json.loads(out)
        shapes.add(tuple(sorted(r))); kinds.add(code)
        _, out2, _ = _run(capsys, "--json", "--lang", lang, "firmware-flash", "--hex", "/nao/existe.hex", "--yes")
        e = json.loads(out2)["error"]
        assert e["kind"] == "no_hex" and set(e) == {"kind", "message", "hint"}
        textos.add(e["message"])
    assert len(shapes) == 1 and len(kinds) == 1
    assert len(textos) == 4                                                              # um texto diferente por idioma


def test_errors_traduz_e_mantem_os_codigos(capsys):
    for lang in LANGS:
        code, out, _ = _run(capsys, "--json", "--lang", lang, "errors")
        r = json.loads(out)
        assert code == 0 and [d["code"] for d in r["device_errors"]] == list(P.ERRORS) and [c["exit_code"] for c in r["exit_codes"]] == [0, 1, 2, 3, 4, 64, 130]
    _, en, _ = _run(capsys, "--lang", "en", "errors")
    assert "exit 3: serial port not found or device not responding" in en and "error 0x0003: no cartridge detected" in en
    _, zh, _ = _run(capsys, "--lang", "zh", "errors")
    assert "错误 0x0003：未检测到卡带" in zh


def test_erro_do_dispositivo_em_ingles(capsys):
    code, out, _ = _run(capsys, "--json", "--lang", "en", "--simulate", "detect", "-s", "snes", "--power", "keep")
    r = json.loads(out)
    assert code == 2 and r["status"] == 1 and r["status_text"] == "no cartridge"       # o código e o número de status não mudam
    _, out, _ = _run(capsys, "--json", "--lang", "zh", "--simulate", "detect", "-s", "snes", "--power", "keep")
    assert json.loads(out)["status_text"] == "没有卡带"


def test_power_em_ingles_e_pt(capsys):
    _, out, _ = _run(capsys, "--lang", "en", "--simulate", "power", "status")
    assert out.splitlines()[0] == "slots' 5V: on"
    _, out, _ = _run(capsys, "--simulate", "power", "status")
    assert out.splitlines()[0] == "5V dos slots: ligado"


def test_idioma_invalido_e_erro_de_uso(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--json", "--lang", "klingon", "errors"])
    assert e.value.code == 64 and json.loads(capsys.readouterr().out)["error"]["kind"] == "usage"


def test_recusa_em_russo(capsys):
    code, out, _ = _run(capsys, "--json", "--lang", "ru", "-p", "/dev/x", "firmware-flash", "--hex", __file__, "--avrdude", __file__)
    e = json.loads(out)["error"]
    assert code == 4 and e["kind"] == "refused" and "отказано" in e["message"] and "--yes" in e["hint"]
