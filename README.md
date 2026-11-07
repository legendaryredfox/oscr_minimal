# oscr_minimal — dumper de cartuchos SNES / NES / Famicom / Mega Drive / GBA

*English summary: [`README.en.md`](README.en.md).*

Shield para **Arduino Mega 2560 (R3)** que lê ROMs e saves de cartuchos pela USB, direto para o PC.
Sem LCD, sem cartão SD. Somente um cartucho por vez.

> **Estado:** 8 placas com projeto KiCad e gerbers, firmware (fork do OSCR com protocolo serial), CLI Python, CLI e GUI em Kotlin (pt-BR, en, ru, zh). **Nenhuma placa foi montada e nada foi testado com cartucho real**: só os testes automáticos no PC e as verificações de hardware abaixo rodaram. Ver "O que foi testado e o que falta".

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
| `CLAUDE.md` | Decisões de projeto e fases (também serve de instrução para assistentes de código) |
| `boards/` | **Variantes de hardware**, uma pasta cada (índice e estado em `boards/README.md`). Com projeto KiCad e gerbers: `16_and_8_bits/` (5 slots), `16_bits/` (SNES e Mega Drive) e as de um sistema só ou de dois: `megadrive/`, `snes/`, `nes/`, `famicom/`, `famicom_nes/`, `gb_gba/`. `8_bits/` e `completa/` são esqueletos |
| `boards/<placa>/docs/pinmap.md` | **Fonte da verdade** de cada placa: pino do slot → pino do Mega (o da `16_and_8_bits` é gerado por `tools/gen_pinmap.py`; os das outras são recortes dele) |
| `docs/decisoes.md` | Log de decisões, desvios e pendências |
| `boards/<placa>/hardware/`, `fab/`, `docs/` | Projeto KiCad 10 (`dumper.kicad_pro/_sch/_pcb`), gerbers e zip da JLCPCB (`fab/PEDIDO.md` diz como pedir) e `bom.md`/`montagem.md` de cada placa |
| `boards/_lib/` | Símbolos e footprints KiCad compartilhados entre as variantes |
| `docs/uso.md` | **Guia de uso**: casos de uso, cenários por sistema e solução de problemas |
| `docs/revisao-codigo.md` | Revisão de código da base toda (achados, gravidade, o que foi corrigido) |
| `docs/revisao-ux.md` | Revisão de UX/UI da GUI, da CLI e do hardware, com capturas de tela |
| `docs/protocolo.md`, `docs/cli.md`, `docs/fork-oscr.md`, `docs/funcoes-oscr.md` | Protocolo serial, guia da CLI, plano do fork do firmware e inventário das funções do OSCR |
| `docs/placa-v1.3-rp2040.md`, `firmware/cic_rp2040/` | CIC do SNES com RP2040-Zero no lugar do PIC (ainda não validado; as placas atuais usam o PIC12F629) |
| `firmware/`, `host/`, `gui/` | Comuns a todas as variantes |
| `database/oscr/` | Base de jogos (24 007, CRC32) do OSCR legado, GPL v3; carregada sozinha pelo host e pela GUI (D88) |
| `tools/` | Scripts de hardware: `check_netlist.py` (`--board <placa>`), `export_fab.sh`, `gen_pinmap.py`, `build_lib.py`, `fill_zones.py` e os de cada placa (`megadrive/`, `snes/`, `nes/`, `famicom/`, `famicom_nes/`, `gb_gba/`, `revisao/`); ver `tools/README.md` |

## Aviso

- **Use por sua conta e risco.** Hardware e software saem sem garantia (CC BY 4.0 e GPL v3). Placas e firmware são experimentais.
- **Um cartucho por vez.** As placas levam 5 V aos slots de SNES, NES, Famicom e Mega Drive; só o slot GBA é 3,3 V (regulador próprio). Desligue o USB antes de trocar de cartucho e **não use adaptador de GB/GBA** em placa sem o slot GBA.
- **Gravar ROM apaga o chip**, e abortar no meio deixa o chip pela metade. Faça backup do save antes de gravar e comece por cartuchos sem valor (`docs/uso.md`, seção 7).
- **Uso legal.** A ferramenta serve para fazer cópia de segurança dos cartuchos que você possui. Este repositório não distribui ROMs, BIOS nem chaves; `database/oscr/` só tem listas de nomes e CRC32 do OSCR.
- Nintendo, Super Nintendo, Famicom, Game Boy, Sega, Mega Drive e outros nomes são marcas dos seus donos, citadas só para dizer com o que o projeto é compatível. Sem vínculo com essas empresas nem com o projeto OSCR.

## O que foi testado e o que falta

**Testado (2026-11-06; tudo no PC, nada em hardware):**

| Parte | O que rodou | Resultado |
|---|---|---|
| Host Python (`host/`) | `cd host && python3 -m pytest -q` | 142 testes passam |
| Firmware, núcleos testáveis no PC | `make -C firmware/oscr/pc-tests test` (protocolo, sessão, plano do SNES, núcleo de flash do Mega Drive etc.) | passam (inclui 21 verificações do plano do SNES e 734 do núcleo de flash do Mega Drive) |
| Firmware, compilação | `pio run -e SerialASCII` em `firmware/oscr` | compila para o Mega 2560 |
| GUI e CLI Kotlin | `cd gui && ./gradlew :shared:jvmTest :desktopApp:compileKotlin :cliApp:compileKotlin` | testes passam, os dois módulos compilam; a janela foi vista só em display virtual |
| Placas (as 8) | ERC, DRC (`--schematic-parity`) e `tools/check_netlist.py --board <placa>` | ERC sem violações; DRC sem erros nem ligações abertas (só avisos de biblioteca e de paridade); netlist confere com o `pinmap.md` de cada placa |
| Gerbers | `16_bits` v1.0 (a antiga `rev2`, D110): zip idêntico ao exportado de `hardware-v1.0`; prévias 3D das placas novas vistas | ok |
| CI (`.github/workflows/ci.yml`) | **nunca executou**; a primeira execução será ao publicar | pendente |

**Falta (nada disso foi feito):**

- **Hardware.**
  - Montar uma placa, medir continuidade e tensão e rodar o primeiro dump (SNES LoROM, NES mapper 0 ou um Mega Drive simples) comparando o CRC32 com o No-Intro.
  - Conferir com as peças reais as medidas dos slots e do módulo Si5351 (D17, D23), o lado da etiqueta (D27, D28) e a altura dos espaçadores (D25).
  - Revisar à mão, no KiCad, os layouts feitos por autoroteador (`megadrive`, `snes`, `nes`, `famicom`, `famicom_nes`, `gb_gba`).
  - A única placa encomendada até agora é a `16_bits` v1.0 original (trilhas de alimentação em 0,3 mm); o repositório guarda no lugar dela a v1.0 revisada, a antiga `rev2` (D110).
- **Firmware.** Os núcleos do OSCR só rodam no AVR, então nenhum teste os cobre. Pontos prováveis de ajuste: tempos de leitura do NES, 1.000.000 baud, `Power::setVoltage` sem VSELECT e o laço de gravação de flash. Roteiro e ordem de risco das gravações em `docs/uso.md`, seção 7.
- **GUI e CLI.** Serial a 1.000.000 baud em Linux, macOS e Windows, janela estreita, revisão das traduções ru e zh por falantes nativos, empacotamento (deb/AppImage, dmg, msi). `save-write` ainda não relê o save depois de gravar.
- **Funções do OSCR que faltam** (SF Memory, Satellaview, mais mappers do NES, outros sistemas etc.): `docs/funcoes-oscr.md`.
- **Próximas sessões:** revisão do código, gravar o firmware no Arduino pelo programa desktop e pela CLI (hoje é com o PlatformIO), e testes com as placas.

## CIC do SNES: alternativas ao chip de 8 pinos

As placas com SNES usam hoje o **PIC12F629** (DIP-8, em soquete, gravado com o `snescic-lock-resync.hex` do OSCR). Estamos **estudando alternativas ao CIC de 8 pinos**; a mais avançada é um RP2040-Zero que roda o mesmo programa num interpretador (`docs/placa-v1.3-rp2040.md`, `firmware/cic_rp2040/`, D89). Nada disso foi validado em hardware, e o PIC continua sendo o caminho suportado.

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

## Contribuir

Veja `CONTRIBUTING.md`. Testes em hardware são o que mais ajuda: abra uma issue com o modelo "Teste em hardware" (placa, cartucho, versão, logs).

## Requisitos

KiCad 10.0.8 (`kicad-cli`), Python 3.11+. Para refazer layouts: o servidor MCP do KiCad (Python com `pcbnew`) e o Freerouting; ver `tools/README.md` e `docs/decisoes.md` (D92 a D101).

## Licença

Hardware: **CC BY 4.0**. Software: **GPL v3 ou posterior**. Mesmas licenças do OSCR; ver `LICENSE.md`.
