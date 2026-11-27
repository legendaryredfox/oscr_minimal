# oscr_minimal — dumper de cartuchos SNES / NES / Famicom / Mega Drive / GBA

*English summary: [`README.en.md`](README.en.md).*

Shield para **Arduino Mega 2560 (R3)** que lê ROMs e saves de cartuchos pela USB, direto para o PC.
Sem LCD, sem cartão SD. Somente um cartucho por vez.

> **Estado:** 8 placas com projeto KiCad e gerbers, firmware (fork do OSCR com protocolo serial), CLI Python, CLI e GUI em Kotlin (pt-BR, en, ru, zh). **Nenhuma placa foi montada e nada foi testado com cartucho real**: só os testes automáticos no PC, as verificações de hardware abaixo e, em 2026-11-21, a primeira execução num Mega sem shield (`docs/referencia/teste-de-bancada.md`) rodaram. Ver "O que foi testado e o que falta".

## Atribuição

Baseado no **Open Source Cartridge Reader (OSCR)** de sanni e comunidade.

- Hardware original: <https://github.com/sanni/cartreader> (licença **CC BY 4.0**).
  Upstream atual: <https://github.com/oscartreader>.
- Firmware original: GPL v3. O firmware deste projeto continuará GPL v3.
- Slots (símbolos e footprints) copiados do OSCR, com alterações descritas em `boards/_lib/README.md`.

Adaptado por: <https://github.com/legendaryredfox/oscr_minimal>

## Diferenças em relação ao OSCR original

Este projeto não é uma reimplementação: o firmware é o do OSCR e as placas mantêm a pinagem dele. O que muda é **onde fica a interface** (no computador, não no aparelho) e **o tamanho do hardware**.

| | OSCR original | Este projeto |
|---|---|---|
| **Uso** | Aparelho independente: tela LCD, botão rotativo e cartão SD; o PC é opcional | Só com o computador: controle e arquivos pela USB. **Sem LCD, sem botões, sem cartão SD, sem RTC** |
| **Onde vão ROM e save** | Para arquivos no cartão SD | Direto para o PC por um protocolo serial binário (quadros com CRC32, blocos com ACK, 1.000.000 baud, com recuo para 500.000 e 115.200); o firmware nunca guarda arquivo |
| **Placa** | HW5: placa SMD com o módulo Mega Pro embutido e todos os slots | Shield **100 % THT** sobre um **Arduino Mega 2560 R3** comum, soldável à mão; várias variantes por combinação de sistemas (`boards/README.md`), da mínima de dois slots à completa |
| **Pinagem** | HW5 | **Idêntica**: cada sinal de cada slot vai para o mesmo pino do Mega, e por isso os núcleos de leitura do OSCR rodam sem alteração (`boards/<placa>/docs/pinmap.md` guarda a tabela cruzada com o OSCR) |
| **Tensão dos slots** | Chave 3,3 V / 5 V e VSELECT | 5 V fixo nos slots SNES, NES, Famicom, Mega Drive e Master System; 3,3 V nos slots GBA e N64 (regulador próprio). Algumas versões recentes de placa têm seletor 3,3 V / 5 V opcional, com trava por jumper. O 5 V **não** é desligado por software |
| **Relógio e CIC** | Si5351 e CIC conforme a versão da placa | Módulo Si5351 em header fêmea; CIC do SNES em PIC12F629 num soquete da própria placa (a alternativa com RP2040 está planejada e ainda não foi validada) |
| **Menus e botões** | Menus no LCD | O laço de comandos do protocolo (`firmware/oscr/src/dumper/`) chama as funções dos núcleos direto, **sem menu**; erros fatais e esperas por botão voltam ao laço em vez de travar |
| **Identificação do jogo** | Banco CRDB no SD | No PC: bases No-Intro e NES 2.0 (CRC32, SHA-1), busca e nome do arquivo pelo jogo (`--db`, `--game`) |
| **Segurança de gravação** | Pelo menu | O PC faz backup do save antes de gravar, relê e compara depois, pede confirmação e recusa tamanhos que não cabem no chip |
| **Interface** | Tela e botões | CLI em Python, CLI em Kotlin (mesmo contrato, saída JSON para scripts e agentes) e GUI em Kotlin para Linux, macOS e Windows (pt-BR, en, ru, zh) |
| **Gravar o firmware** | Ferramentas do upstream | `dumper firmware-flash` ou o cartão da GUI; com a placa escolhida o programa confere o firmware, grava o perfil da placa na EEPROM e, se faltar suporte, grava a imagem certa depois de pedir confirmação |

### Firmware: o que é do OSCR e o que é daqui

- **Base:** o firmware novo do OSCR (`vendor/oscr/firmware`), copiado para `firmware/oscr/`. Quem escolhe os núcleos é o `user.ini`: SNES (com Sufami Turbo, GPC, Satellaview e SF Memory), NES/Famicom, Mega Drive, Master System, N64, GB/GBC/GBA, programador de flash e o autoteste. Outros consoles do upstream (por exemplo Atari 7800 e Commodore 64) **não estão ligados**.
- **Regra do projeto:** chamar a função do OSCR direto e escrever código próprio só nas costuras. Onde divergimos, o motivo está em `docs/decisoes.md`.
- **Código só daqui** (`firmware/oscr/src/dumper/`): o protocolo e a sessão; o `StreamFile`, arquivo virtual que no lugar do SD manda os bytes pela serial; o laço de comandos; o perfil da placa (`BOARD`, na EEPROM); o comando de tensão (`VOLT`); a calibração do Si5351 (`CLOCK`, guardada na EEPROM, no lugar do arquivo `snes_clk.txt` do SD); e o `SELFTEST`.
- **Remendos no upstream:** poucos e marcados com `OSCR_DUMPER` ou "fork": o tipo do arquivo e do `sd` em `Storage`, a UI de texto muda (`ClockedSerial.mute`), os tratamentos de erro e de `waitButton` do `ascii.cpp` e o `main.cpp` (laço próprio no lugar do menu).
- **Baud:** 1.000.000, contra 250.000 do upstream, definido pelo `monitor_speed` da placa `mega-embed` no `user.ini`.
- **Limites conhecidos do fluxo serial:** só existe leitura sequencial (sem `seek`), e o que o núcleo relê para conferir um save gravado devolve 0 bytes; por isso a conferência fica a cargo do PC, que relê depois de gravar.
- Mapa completo e estado: `docs/referencia/fork-oscr.md`. Cada função do OSCR e onde ela mora aqui: `docs/referencia/funcoes-oscr.md`.

### O que isto **não** substitui

- O OSCR original tem anos de uso e de cartuchos reais. **Este fork quase não tem validação em hardware:** em 2026-11-21 rodou pela primeira vez, num Mega sem shield e sem cartucho, e essa primeira execução achou e corrigiu vários problemas, de baud errado a gravação de firmware que travava (D196 a D199). **Nenhuma leitura de cartucho real foi feita ainda.** Os núcleos do OSCR são os de sempre, mas o que está em volta (protocolo, placas, sequência de chamadas) é novo.
- Quem quer um leitor autônomo, sem computador, deve usar o OSCR original.
- Funções do OSCR que ainda faltam aqui: `docs/referencia/funcoes-oscr.md`.

## Conteúdo

| Pasta | O que tem |
|---|---|
| `CLAUDE.md` | Decisões de projeto e fases (também serve de instrução para assistentes de código) |
| `boards/` | **Variantes de hardware**, uma pasta cada (índice e estado em `boards/README.md`). Com projeto KiCad e gerbers: `16_and_8_bits/` (5 slots), `16_bits/` (SNES e Mega Drive) e as de um sistema só ou de dois: `megadrive/`, `snes/`, `nes/`, `famicom/`, `famicom_nes/`, `8_bits/` (NES, Famicom e Master System), `gb_gba/`, `completa/` (sete slots) |
| `boards/<placa>/docs/pinmap.md` | **Fonte da verdade** de cada placa: pino do slot → pino do Mega (o da `16_and_8_bits` é gerado por `tools/gen_pinmap.py`; os das outras são recortes dele) |
| `docs/decisoes.md` | Log de decisões, desvios e pendências |
| `boards/<placa>/hardware-<versão>/` (uma pasta por versão), `fab/`, `docs/` | Projeto KiCad 10 (`dumper.kicad_pro/_sch/_pcb`), gerbers e zip da JLCPCB (`fab/PEDIDO.md` diz como pedir) e `bom.md`/`montagem.md` de cada placa |
| `boards/_lib/` | Símbolos e footprints KiCad compartilhados entre as variantes |
| `docs/referencia/uso.md` | **Guia de uso**: casos de uso, cenários por sistema e solução de problemas |
| `docs/referencia/protocolo.md`, `docs/referencia/cli.md`, `docs/referencia/fork-oscr.md`, `docs/referencia/funcoes-oscr.md` | Protocolo serial, guia da CLI, plano do fork do firmware e inventário das funções do OSCR |
| `docs/planos/placa-v1.3-rp2040.md`, `firmware/cic_rp2040/` | CIC do SNES com RP2040-Zero no lugar do PIC (ainda não validado; as placas atuais usam o PIC12F629) |
| `firmware/`, `host/`, `gui/` | Comuns a todas as variantes |
| `database/oscr/` | Base de jogos (24 007, CRC32) do OSCR legado, GPL v3, mais `json/` (bases do `oscr-databases`, 4,9 mil CRC32 novos; o repositório de origem não declara licença, D127); carregada sozinha pelo host e pela GUI (D88, D127) |
| `tools/` | Scripts de hardware: `check_netlist.py` (`--board <placa>`), `export_fab.sh`, `gen_pinmap.py`, `build_lib.py`, `fill_zones.py` e os de cada placa (`megadrive/`, `snes/`, `nes/`, `famicom/`, `famicom_nes/`, `gb_gba/`, `revisao/`); ver `tools/README.md` |

## Adaptadores e repositórios de referência

O código de leitura dos cartuchos vem do OSCR; o que muda por sistema é o adaptador. Fontes consultadas e adaptadores que o firmware reconhece (D136, D137):

| Referência | Para quê |
|---|---|
| <https://github.com/sanni/cartreader> (pasta `hardware/`: `mastersystem_adapter`, `six_slot_adapter`, `*_adapter`) | KiCad dos adaptadores do OSCR; o slot Master System da `megadrive_sms` e os footprints dos slots vêm daí (CC BY 4.0). Arquivado desde 2026-06 |
| <https://github.com/oscartreader/oscr-firmware> | firmware atual do OSCR (GPL v3), base do fork em `firmware/oscr/` |
| <https://github.com/oscartreader/oscr-databases> | bases de jogos e a tabela de chips de flash (`database/oscr/`, D127 e D135; sem licença declarada) |
| <https://github.com/oscartreader/oscr-hardware> | repositório de hardware do novo upstream (vazio em 2026-11-08) |
| <https://github.com/sanni/cartreader/discussions/874> | discussão do adaptador de Game Gear (slot com o conector do RetroSix) |
| <https://www.raphnet.net/electronique/sms_cartridge_programmer/index_en.php> | adaptador **Raphnet** de Master System / SG-1000 (modo `SMSRaphnet` e `SG1000Raphnet` do `SMS.cpp`) |
| <https://forum.retrode.com> | adaptadores **Retrode** (`SMSRetrode`, `GGRetrode` do `SMS.cpp`) |
| <https://www.retrosix.wiki> | pinagem do cartucho de Game Gear e de outros consoles Sega |
| <https://www.smspower.org/maxim/Documents/Pinouts> | pinagem do conector de cartucho do Master System, Mark III e SG-1000 |

**Game Gear e SG-1000** não têm slot próprio nas placas deste projeto: usam adaptador no slot Mega Drive (Retron 3in1, Retrode, Raphnet). Os adaptadores que achei são comerciais; **não encontrei arquivos abertos** (KiCad) deles. Se aparecer um adaptador de código aberto, acrescente o link aqui.

**Tensão dos adaptadores (D138).** Os slots são de 5 V; os flashcarts comuns de Mega Drive e Master System precisam disso (regulam 3,3 V por dentro). As placas v1.1 de Mega Drive, SMS, NES e Famicom têm o **seletor 3,3 V/5 V** (padrão 5 V, `--voltage 3v3` para 3,3 V, alerta ao passar de 3,3 V para 5 V) e o jumper J1 \"TRAVA 3,3 V\"; todas as placas têm o fusível F1 (5×20 mm, 500 mA, em suporte de clipes, troca sem solda) opcional. Adaptador de Game Gear ou cartucho de 3,3 V: confira a tensão do adaptador antes de ligar. Detalhes: `docs/decisoes.md` D138.

## Aviso

- **Use por sua conta e risco.** Hardware e software saem sem garantia (CC BY 4.0 e GPL v3). Placas e firmware são experimentais.
- **Um cartucho por vez.** As placas levam 5 V aos slots de SNES, NES, Famicom e Mega Drive; só o slot GBA é 3,3 V (regulador próprio). Desligue o USB antes de trocar de cartucho e **não use adaptador de GB/GBA** em placa sem o slot GBA.
- **Gravar ROM apaga o chip**, e abortar no meio deixa o chip pela metade. Faça backup do save antes de gravar e comece por cartuchos sem valor (`docs/referencia/uso.md`, seção 7).
- **Uso legal.** A ferramenta serve para fazer cópia de segurança dos cartuchos que você possui. Este repositório não distribui ROMs, BIOS nem chaves; `database/oscr/` só tem listas de nomes e CRC32 do OSCR.
- Nintendo, Super Nintendo, Famicom, Game Boy, Sega, Mega Drive e outros nomes são marcas dos seus donos, citadas só para dizer com o que o projeto é compatível. Sem vínculo com essas empresas nem com o projeto OSCR.

## O que foi testado e o que falta

Cobertura medida (Python 90 %, Kotlin 91,7 % das linhas, C++ puro no PC) e o que nenhum teste alcança: [`docs/referencia/cobertura-testes.md`](docs/referencia/cobertura-testes.md).

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
- **Firmware.** Os núcleos do OSCR só rodam no AVR, então nenhum teste os cobre. Pontos prováveis de ajuste: tempos de leitura do NES, 1.000.000 baud, `Power::setVoltage` sem VSELECT e o laço de gravação de flash. Roteiro e ordem de risco das gravações em `docs/referencia/uso.md`, seção 7.
- **GUI e CLI.** Serial a 1.000.000 baud em Linux, macOS e Windows, janela estreita, revisão das traduções ru e zh por falantes nativos, empacotamento (deb/AppImage, dmg, msi). `save-write` ainda não relê o save depois de gravar.
- **Funções do OSCR que faltam** (SF Memory, Satellaview, mais mappers do NES, outros sistemas etc.): `docs/referencia/funcoes-oscr.md`.
- **Próximas sessões:** revisão do código, gravar o firmware no Arduino pelo programa desktop e pela CLI (hoje é com o PlatformIO), e testes com as placas.

## CIC do SNES: alternativas ao chip de 8 pinos

As placas com SNES usam hoje o **PIC12F629** (DIP-8, em soquete, gravado com o `snescic-lock-resync.hex` do OSCR). Estamos **estudando alternativas ao CIC de 8 pinos**; a mais avançada é um RP2040-Zero que roda o mesmo programa num interpretador (`docs/planos/placa-v1.3-rp2040.md`, `firmware/cic_rp2040/`, D89). Nada disso foi validado em hardware, e o PIC continua sendo o caminho suportado.

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
