# SPDX-License-Identifier: GPL-3.0-or-later
"""Lê uma seção de docs/planos/adaptadores.md: o texto entre a âncora `<a id="adaptador-<chave>"></a>` e a próxima.
`secao_doc("ngp")` devolve um objeto com `read_text()`, para os verificadores lerem a seção como liam o arquivo antigo."""
from __future__ import annotations

import re
from pathlib import Path

DOC = Path(__file__).resolve().parent.parent / "docs/planos/adaptadores.md"
_ANCORA = re.compile(r'^<a id="adaptador-([a-z0-9]+)"></a>\s*$', re.M)


def secao(chave: str) -> str:
    texto = DOC.read_text(encoding="utf-8")
    marcas = list(_ANCORA.finditer(texto))
    for i, m in enumerate(marcas):
        if m.group(1) == chave:
            fim = marcas[i + 1].start() if i + 1 < len(marcas) else len(texto)
            return texto[m.end():fim]
    raise KeyError(f"seção adaptador-{chave} não existe em {DOC}")


class Secao:
    def __init__(self, chave: str) -> None:
        self.chave = chave

    def read_text(self, encoding: str = "utf-8") -> str:   # noqa: ARG002 (mesma assinatura de Path.read_text)
        return secao(self.chave)

    def __str__(self) -> str:
        return f"docs/planos/adaptadores.md#adaptador-{self.chave}"


def secao_doc(chave: str) -> Secao:
    return Secao(chave)
