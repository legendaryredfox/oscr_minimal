# SPDX-License-Identifier: GPL-3.0-or-later
"""Descobrir o sistema do cartucho no slot (P5, D160; ideia do ID de adaptador do UMDv3 e do `-read auto` do SNES_Dumper).

Só LEITURA: usa o `DETECT` de cada sistema (o mesmo que o usuário rodaria à mão), nunca o de flash do Mega Drive (que escreve comandos de ID) e nunca escreve.
Ordem: primeiro os sistemas cujo cabeçalho tem uma marca própria (N64 `80 37 12 40`, logo da Nintendo no GBA e no GB, "SEGA" no Mega Drive, checksum do SNES, "TMR SEGA"
no Master System); o NES por último, porque o `DETECT` dele aceita qualquer dado que não seja um valor só ($00 ou $FF) e acusaria quase tudo. Para no primeiro sistema
que responde "detectado" (status 0). Game Gear e SG-1000 dependem de adaptador e não entram: escolha-os com `-s`. Só vale para detect, dump e save-read; gravar
(save-write, rom-write, flash-*) exige o sistema explícito. Cuidado: as saídas do Mega são de 5 V em qualquer slot; um cartucho de 3,3 V pode ser sondado como sistema
errado antes de ser achado: confira a tensão do cartucho antes."""
from __future__ import annotations

from typing import Iterable, Optional

from . import protocol as P
from .client import TimeoutError_

AUTO_ORDER = ("n64", "gba", "gb", "md", "snes", "sms", "nes")


def autodetect(client, supported: Optional[Iterable[str]] = None) -> Optional[tuple[str, dict]]:
    """-> (nome do sistema, resposta do DETECT) do primeiro sistema detectado, ou None. `supported` = os sistemas que o firmware informa (None = todos)."""
    ok = set(supported) if supported else None                   # lista vazia = o firmware não informa (simulador): tenta todos
    for name in AUTO_ORDER:
        if ok is not None and name not in ok:
            continue
        try:
            r = client.detect(P.SYSTEMS[name][0])
        except (P.DeviceError, P.ProtocolError, TimeoutError_):
            continue
        if r["status"] == 0:
            return name, r
    return None
