# oscr_minimal — dumper de cartuchos SNES / NES / Famicom / Mega Drive / GBA

Shield para **Arduino Mega 2560 (R3)** que lê ROMs e saves de cartuchos pela USB, direto para o PC.
Sem LCD, sem cartão SD. Somente um cartucho por vez.

> **Estado:** 8 placas com projeto KiCad e gerbers (DRC sem erros, ERC e netlist conferidos; **nenhuma montada nem testada com cartucho**; só a `16_bits` v1.0 foi encomendada, pelo usuário), documentação de montagem e uso, firmware (protocolo + leitura de SNES, NES/Famicom, Mega Drive, GBA), CLI Python e GUI (pt-BR, en, ru, zh).
> **Falta validar com as peças e os cartuchos reais** (firmware e GUI foram testados só no PC). Para retomar o trabalho, leia `docs/continuacao.md`.

## Atribuição

Baseado no **Open Source Cartridge Reader (OSCR)** de sanni e comunidade.

- Hardware original: <https://github.com/sanni/cartreader> (licença **CC BY 4.0**).
  Upstream atual: <https://github.com/oscartreader>.
- Firmware original: GPL v3. O firmware deste projeto continuará GPL v3.
- Slots (símbolos e footprints) copiados do OSCR, com alterações descritas em `boards/_lib/README.md`.

Adaptado por: <https://github.com/legendaryredfox/oscr_minimal>

## Conteúdo

| Pasta | O que tem |
|---|---|
| `CLAUDE.md` | Decisões de projeto e fases |
| `boards/` | **Variantes de hardware**, uma pasta cada (índice e estado em `boards/README.md`). Com projeto KiCad e gerbers: `16_and_8_bits/` (5 slots), `16_bits/` (SNES e Mega Drive) e as de um sistema só ou de dois: `megadrive/`, `snes/`, `nes/`, `famicom/`, `famicom_nes/`, `gb_gba/`. `8_bits/` e `completa/` são esqueletos |
| `boards/<placa>/docs/pinmap.md` | **Fonte da verdade** de cada placa: pino do slot → pino do Mega (o da `16_and_8_bits` é gerado por `tools/gen_pinmap.py`; os das outras são recortes dele) |
| `docs/decisoes.md` | Log de decisões, desvios e pendências |
| `docs/continuacao.md` | **Comece aqui para retomar:** estado, mapa do código, como rodar, pendências |
| `boards/<placa>/hardware/`, `fab/`, `docs/` | Projeto KiCad 10 (`dumper.kicad_pro/_sch/_pcb`), gerbers e zip da JLCPCB (`fab/PEDIDO.md` diz como pedir) e `bom.md`/`montagem.md` de cada placa |
| `boards/_lib/` | Símbolos e footprints KiCad compartilhados entre as variantes |
| `docs/uso.md` | **Guia de uso**: casos de uso, cenários por sistema e solução de problemas |
| `docs/revisao-codigo.md` | Revisão de código da base toda (achados, gravidade, o que foi corrigido) |
| `docs/sessao-2026-11-02.md` | Histórico da sessão de 2026-11-02: o que foi feito, defeitos achados, o que falta |
| `docs/revisao-ux.md` | Revisão de UX/UI da GUI, da CLI e do hardware, com capturas de tela |
| `docs/protocolo.md`, `docs/cli.md`, `docs/fork-oscr.md`, `docs/funcoes-oscr.md` | Protocolo serial, guia da CLI, plano do fork do firmware e inventário das funções do OSCR |
| `docs/placa-v1.3-rp2040.md`, `firmware/cic_rp2040/` | CIC do SNES com RP2040-Zero no lugar do PIC (ainda não validado; as placas atuais usam o PIC12F629) |
| `firmware/`, `host/`, `gui/` | Comuns a todas as variantes |
| `database/oscr/` | Base de jogos (24 007, CRC32) do OSCR legado, GPL v3; carregada sozinha pelo host e pela GUI (D88) |
| `tools/` | Scripts de hardware: `check_netlist.py` (`--board <placa>`), `export_fab.sh`, `gen_pinmap.py`, `build_lib.py`, `fill_zones.py` e os de cada placa (`megadrive/`, `snes/`, `nes/`, `famicom/`, `famicom_nes/`, `gb_gba/`, `revisao/`); ver `tools/README.md` |

## Verificação

```
python3 tools/check_netlist.py --board <placa>        # netlist do esquemático vs boards/<placa>/docs/pinmap.md
kicad-cli sch erc boards/<placa>/hardware/dumper.kicad_sch                # ERC
kicad-cli pcb drc --schematic-parity boards/<placa>/hardware/dumper.kicad_pcb   # DRC
tools/export_fab.sh <placa> v1.0                      # gerbers, furos, BOM e zip em boards/<placa>/fab/
```

## Recriar o `vendor/` (não versionado)

```
mkdir -p vendor/oscr && cd vendor/oscr
git clone --depth 1 https://github.com/sanni/cartreader legacy
git clone --depth 1 https://github.com/oscartreader/oscr-firmware firmware
```

`tools/gen_pinmap.py` lê `vendor/oscr/legacy/` (pinout.ods, esquemáticos KiCad, firmware).

## Requisitos

KiCad 10.0.8 (`kicad-cli`), Python 3.11+. Para refazer layouts: o servidor MCP do KiCad (Python com `pcbnew`) e o Freerouting; ver `tools/README.md` e `docs/decisoes.md` (D92 a D101).

## Licença

Hardware: **CC BY 4.0**. Software: **GPL v3 ou posterior**. Mesmas licenças do OSCR; ver `LICENSE.md`.
