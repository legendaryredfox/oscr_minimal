# SPDX-License-Identifier: GPL-3.0-or-later
"""Os quatro guias passo a passo (pt-BR, en, ru, zh-Hans) têm que ter a mesma estrutura (H-5).

Não confere a tradução, só que nenhum idioma ficou para trás: mesmo número de linhas, títulos, passos numerados e os mesmos
trechos de código (comandos, arquivos e opções entre crases não se traduzem; só o texto dentro de `<...>`, como `<placa>`, e o nome de arquivo depois de `-o` ou `-i` podem mudar).
"""
import re
from pathlib import Path

REF = Path(__file__).resolve().parents[2] / "docs/referencia"
GUIAS = {"pt": "guia-passo-a-passo.md", "en": "guia-passo-a-passo.en.md", "ru": "guia-passo-a-passo.ru.md",
         "zh": "guia-passo-a-passo.zh-Hans.md"}


def ler(idioma: str) -> str:
    return (REF / GUIAS[idioma]).read_text(encoding="utf-8")


def norm(c: str) -> str:
    """Tira o que é texto de exemplo: `<placa>` e o nome de arquivo depois de -o / -i (jogo, game...)."""
    c = re.sub(r"<[^>]*>", "<>", c)
    c = re.sub(r"guia-passo-a-passo(\.[a-zA-Z-]+)?\.md", "GUIA", c)
    return re.sub(r"(-[oi]) \S+", r"\1 ARQ", c)


def estrutura(t: str):
    linhas = t.splitlines()
    return {
        "linhas": len(linhas),
        "titulos": [re.match(r"#+", l).group(0) + " " + (re.match(r"#+ (\d+)\.", l) or [None, ""])[1] for l in linhas if l.startswith("#")],
        "passos": [int(m.group(1)) for l in linhas if (m := re.match(r"(\d+)\. ", l))],
        "codigo": sorted(n for n in (norm(c) for c in re.findall(r"`([^`]+)`", t)) if n != "GUIA"),   # as ligações para as outras versões do guia variam
    }


def test_os_quatro_guias_existem_e_nao_estao_vazios():
    for i in GUIAS:
        assert len(ler(i)) > 500, i


def test_mesma_estrutura_nos_quatro_idiomas():
    base = estrutura(ler("pt"))
    for i in ("en", "ru", "zh"):
        e = estrutura(ler(i))
        for chave in ("linhas", "titulos", "passos"):
            assert e[chave] == base[chave], f"{GUIAS[i]}: {chave} diferente do pt-BR"


def test_mesmos_comandos_nos_quatro_idiomas():
    base = estrutura(ler("pt"))["codigo"]
    for i in ("en", "ru", "zh"):
        assert estrutura(ler(i))["codigo"] == base, f"{GUIAS[i]}: trechos de código diferentes do pt-BR"
