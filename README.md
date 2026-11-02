# oscr_minimal — dumper de cartuchos SNES / NES / Famicom / Mega Drive / GBA

Shield para **Arduino Mega 2560 (R3)** que lê ROMs e saves de cartuchos pela USB, direto para o PC.
Sem LCD, sem cartão SD. Somente um cartucho por vez.

> **Estado:** hardware pronto para fabricar (DRC 0 erros), documentação de montagem e uso, firmware (protocolo + leitura de SNES, NES/Famicom, Mega Drive, GBA), CLI Python e GUI (pt-BR, en, ru, zh).
> **Falta validar com as peças e os cartuchos reais** (firmware e GUI foram testados só no PC). Para retomar o trabalho, leia `docs/continuacao.md`.

## Atribuição

Baseado no **Open Source Cartridge Reader (OSCR)** de sanni e comunidade.

- Hardware original: <https://github.com/sanni/cartreader> (licença **CC BY 4.0**).
  Upstream atual: <https://github.com/oscartreader>.
- Firmware original: GPL v3. O firmware deste projeto continuará GPL v3.
- Slots (símbolos e footprints) copiados do OSCR, com alterações descritas em `hardware/lib/README.md`.

Adaptado por: <https://github.com/legendaryredfox/oscr_minimal>

## Conteúdo

| Pasta | O que tem |
|---|---|
| `CLAUDE.md` | Decisões de projeto e fases |
| `docs/pinmap.md` | **Fonte da verdade:** pino do slot → pino do Mega (gerado) |
| `docs/decisoes.md` | Log de decisões, desvios e pendências |
| `docs/continuacao.md` | **Comece aqui para retomar:** estado, mapa do código, como rodar, pendências |
| `hardware/` | Projeto KiCad 10 (`dumper.kicad_pro/_sch/_pcb`) e `lib/` (símbolos e footprints) |
| `docs/uso.md` | **Guia de uso**: casos de uso, cenários por sistema e solução de problemas |
| `tools/` | `gen_pinmap.py`, `check_netlist.py`, `build_lib.py`, `plan_layout.py`, `gen_connections.py`, `fill_zones.py`, `sync_net_names.py` |

## Verificação

```
python3 tools/check_netlist.py                       # netlist do esquemático vs docs/pinmap.md
kicad-cli sch erc hardware/dumper.kicad_sch          # ERC
kicad-cli pcb drc hardware/dumper.kicad_pcb          # DRC
```

## Recriar o `vendor/` (não versionado)

```
mkdir -p vendor/oscr && cd vendor/oscr
git clone --depth 1 https://github.com/sanni/cartreader legacy
git clone --depth 1 https://github.com/oscartreader/oscr-firmware firmware
```

`tools/gen_pinmap.py` lê `vendor/oscr/legacy/` (pinout.ods, esquemáticos KiCad, firmware).

## Requisitos

KiCad 10.0.8 (`kicad-cli`), Python 3.11+.

## Licença

Hardware: **CC BY 4.0**. Software: **GPL v3 ou posterior**. Mesmas licenças do OSCR; ver `LICENSE.md`.
