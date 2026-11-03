# Licenças

Este projeto deriva do Open Source Cartridge Reader (OSCR), de sanni e comunidade, e **mantém as mesmas licenças do projeto original**:

| Parte | Licença | Texto |
|---|---|---|
| **Hardware** (`boards/`, `docs/`, esquemático, PCB, bibliotecas de símbolos e footprints) | **Creative Commons Atribuição 4.0 Internacional (CC BY 4.0)** | `LICENSES/CC-BY-4.0.txt` |
| **Software** (`firmware/`, `host/`, `gui/`, `tools/`) | **GNU GPL v3** (ou posterior) | `LICENSES/GPL-3.0.txt` |

## Atribuição (obrigatória, CC BY 4.0)

Baseado no **Open Source Cartridge Reader** de sanni e comunidade
(<https://github.com/sanni/cartreader>; atual: <https://github.com/oscartreader>).
Este projeto: <https://github.com/legendaryredfox/oscr_minimal> (adaptado por Legendary Redfox).

Alterações em relação ao OSCR: shield único para Arduino Mega 2560 R3 com slots de SNES, NES, Famicom, Mega Drive e GBA; sem LCD, SD e RTC; interface serial USB com protocolo próprio (`docs/protocolo.md`); footprints dos slots do OSCR com courtyard e silkscreen acrescentados; símbolo do slot GBA recriado. O hardware usa, em parte, símbolos e footprints do OSCR (`boards/_lib/README.md`).

O texto da atribuição também está no silkscreen da placa.

## Software: cabeçalho

Os arquivos de código novos trazem `SPDX-License-Identifier: GPL-3.0-or-later`. O firmware derivado do OSCR continua sob GPL v3.
