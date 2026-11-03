# Continuação — estado do projeto e como retomar

Última atualização: **2026-11-03**, fim da sessão do fork do OSCR (D65 a D78). Quem for continuar (pessoa ou Claude Code) deve ler este arquivo, depois `CLAUDE.md` (regras e decisões fixas), `docs/funcoes-oscr.md` (o que falta do OSCR original) e `docs/decisoes.md` (log D1 a D78, com índice no topo).

> **As seções 2 a 5 descrevem o firmware próprio antigo** (`firmware/arquivo/oscr_serial`, arquivado em D76). O firmware atual é `firmware/oscr/` (fork do OSCR); o mapa dele e o estado estão na seção 0 e em `docs/fork-oscr.md`. O que cada sistema lê e grava hoje no fork: seção 0.1.

## 0. Retomada (2026-11-03)

### 0.1 O que está feito

**Meta do projeto (decisão do usuário, 2026-11-03, D77):** ter **todas as funções do OSCR original**. Só **não** entram nas placas os **botões de operação sem computador** e o **cartão SD**. Parte das funções vai para o PC. Regra de implementação: **usar o máximo de código pronto do OSCR** (chamar as funções do upstream, não reescrever). Inventário por função: `docs/funcoes-oscr.md`.

| Área | Feito | Commit / decisão |
|---|---|---|
| Firmware = fork do OSCR (`firmware/oscr/`) | SD trocado pela serial (`StreamFile`), UI muda, laço do protocolo em `src/dumper/Dumper.cpp`; **SNES, NES/Famicom, Mega Drive, GBA e GB/GBC** com `DETECT`, `DUMP_ROM`, `READ_SAVE`, `WRITE_SAVE`. Compila: 151.176 B de flash (59,5%), 3.465 B de RAM (42,3%). | D65, D66, D75 |
| NES no fork | mapper, PRG, CHR e RAM vêm do PC; 37 mappers de ROM (inclui o 30); saves dos mappers 1, 4, 5, 69 e 118; MMC6 tem save de 1 KB | D75, D78 |
| **Gravação de ROM** | `WRITE_ROM` (`0x0B`) para **NES Maker (SST 39SF040, mapper 30)** e **A29040B (mapper 0)**, usando direto `NESmaker_*` e `A29040B_*` do OSCR (`flash = true` em `user.ini`); `NesFlash.cpp` só tem o laço de gravação, com limite de tempo; apagar acontece **antes** do primeiro `ACK` | D77 |
| **Gravação de ROM no Mega Drive** | `WRITE_ROM` para flash MX29F1610 (2 MB) e S29GL064N (4 MB), chamando direto `idFlash`, `eraseFlash`, `write29F1610`, `write29GL` do OSCR; `MdFlash.cpp` só tem a ordem das chamadas; as três interfaces (CLI Python, CLI Kotlin, GUI). Laços do OSCR sem limite de tempo | D81 |
| **Gravação de ROM no SNES** | `WRITE_ROM` para flash **CFI de 1, 2 ou 4 chips e 8 MB** (fiação LoROM ou HiROM; D82) e menus **P0/P1** com tipo de flash informado; antes (D79): CFI de 1 chip de 2 ou 4 MB, chamando `Flash::setup8`, `identifyCFIbyIds`, `sendCFICommand`, `writeByte` do OSCR; `SnesFlash.cpp` só tem o laço com limite de tempo; CLI Python, CLI Kotlin e GUI (combo de chip por sistema) | D79 |
| Conferência depois de gravar a ROM | o PC lê a ROM de volta e compara byte a byte (CLI, GUI, `--no-verify`) | D78 |
| Banco de dados no PC | No-Intro `.dat` (Logiqx) e NES 2.0 XML; identifica por CRC32 (NES também sem cabeçalho e por PRG+CHR); `identify`, `search`, `dump --db`, `dump --game`; nome do jogo na GUI e busca de jogo no NES | D76 |
| Firmware próprio arquivado | `firmware/arquivo/` (oscr_serial, arduino, platformio); o protocolo do fork tem testes em `firmware/oscr/pc-tests/` | D76 |
| Host Python | CLI com `rom-write`, `identify`, `search`, `--db`, `--game`; 104 testes | D74, D76 a D78 |
| GUI Kotlin | painel **Configurações** (idioma, base de dados, ajuda); layout em cartões, duas colunas a partir de 840 dp; **sistema e porta em combo box**, sistemas em ordem alfabética por grupo; botão **Gravar ROM** com seletor de chip, confirmação e conferência; 41 outros cartuchos do OSCR como **stubs** (aviso, ações desabilitadas) | D76, D77 |
| CLI Kotlin | mesmo contrato da Python (`rom-write`, `identify`, `search`) | D74, D76 a D78 |
| Hardware (KiCad) | `16_and_8_bits` e `16_bits` prontas para fabricar; **nada encomendado nem montado** | D70 a D73 |

**Estado dos testes na última verificação (2026-11-03):** host 104 (`cd host && python3 -m pytest -q`); `make -C firmware/oscr/pc-tests test` (16 do protocolo); `cd gui && ./gradlew --offline :shared:jvmTest :desktopApp:compileKotlin :cliApp:compileKotlin`; `cd firmware/oscr && ~/.platformio/penv/bin/pio run -e SerialASCII`. O arquivo antigo ainda passa (`make -C firmware/arquivo/oscr_serial test`: 16 + 19 + 41 + 990). **Nenhum teste cobre o código dos núcleos do OSCR (só roda no AVR); nada rodou em hardware.** O CI do GitHub foi reescrito (D76) e **nunca executou**.

### 0.2 O que está pendente, em ordem de valor

**A. Validação em hardware (nada foi feito).** Roteiro em `docs/uso.md` seção 7.
1. Encomendar a placa (`boards/16_and_8_bits/fab/dumper-v1.0-jlcpcb.zip` ou a `16_bits`) e as peças da BOM; conferir medidas dos slots e do módulo Si5351 (D17, D23), lado da etiqueta (D27, D28), espaçadores (D25).
2. Montar, testar continuidade e tensão, gravar o firmware **do fork** (`pio run -e SerialASCII -t upload` em `firmware/oscr`), `INFO`, depois um cartucho simples (SNES LoROM ou NES mapper 0) e comparar o CRC32 com o No-Intro. Pedir os logs.
3. **Ordem de risco nas gravações:** SRAM com backup, depois EEPROM, depois Flash do GBA, e por último `WRITE_ROM` (apaga o chip). Primeiro `WRITE_ROM`: num cartucho repro barato e **sem valor**, A29040B (mapper 0, 16/32 KB) antes do NES Maker (512 KB).
4. Se o fork falhar num cartucho, gravar o firmware arquivado (`firmware/arquivo/`, comando no README dele) para separar defeito do fork de defeito da placa.
5. Pontos mais prováveis de ajuste no fork: tempos do `readPRG`/`readCHR` do NES, `Power::setVoltage` sem VSELECT (**não conferido**), `enableCartridge` sem `ENABLE_ONBOARD_ATMEGA`, baud 1.000.000, laço de gravação do `NesFlash.cpp` (esperas de 14 us e de 8 s), `rom_prepare` com apagamento longo (o host espera 90 s).

**B. Faltas no que já existe (fáceis de pegar).**
- **`save-write` não confere depois de gravar** (CLI Python, Kotlin e GUI): o `WRITE_SAVE` do fork não relê o arquivo (o OSCR relia do SD), então o PC deve **reler o save e comparar**, como já faz com a ROM (`verify_written`). Hoje só existe o backup antes de gravar.
- Detecção de NES sem cartucho é heurística (64 bytes iguais a `$00`/`$FF`).
- Abortar no meio de uma gravação de flash deixa o chip pela metade (inerente; avisar na GUI?).
- Testar a GUI de verdade: conexão serial a 1.000.000 baud (jSerialComm em Linux, macOS e Windows), seletor de arquivo, base de dados carregada, busca do NES, diálogo de gravação de ROM, janela estreita (uma coluna). Só foram vistos: janela, Configurações, combo, stubs e o cartão Gravação (display virtual).
- Revisão das traduções ru e zh por falante nativo. Empacotamento (deb/AppImage, dmg, msi).
- Leitor da base **CRDB** do OSCR (binária; `databases/` do clone vem vazio): só se o usuário trouxer os arquivos.
- Reescrever as seções 2 a 5 deste arquivo para o fork (hoje descrevem o arquivo).

**C. Funções do OSCR original que faltam (meta D77).** Lista completa e estado em `docs/funcoes-oscr.md`. Resumo, na ordem que sugiro:
1. **Programador de flash genérico** (o SNES CFI de 1 chip já existe, D79; `Flash.cpp`: CFI, 8 e 16 bits, ID, blank check, ler, gravar, apagar, verificar, EPROM, PLCC32 para SNES): serve de base para as flash repro de vários sistemas; `flash = true` já está ligado, falta `flash16`.
2. Flash repro por sistema: SNES (CFI e LoROM/HiROM/ExLoROM/ExHiROM), Mega Drive (29F1610, 29GL), GBA (Intel 4000/4400, MSP55LV128, MX29GL128E, 369-in-1), GB (29F/39SF, CFI, GB Smart, NPower, GameShark, Mega Memory, Datel).
3. SNES: SF Memory (SFM), Satellaview, Sufami Turbo, Game Processor RAM, Test RAM, calibrar o relógio; chips raros (Derby Stallion 96, S-RTC, OBC1, ST018, MSU-1, RTC do SPC7110).
4. NES: leitura raw (PRG/CHR separados), mais mappers (o upstream trata mais de 100; ver `docs/limites-nes.md`), EEPROM dos mappers 16 e 159, saves de outros mappers, flash de CHR em outros chips.
5. Mega Drive: Sega CD RAM, Realtec. GB/GBC: RTC do MBC3, Flash do MBC6, ROM do TAMA5.
6. **Outros sistemas do OSCR** (Atari, N64, PC Engine, Master System, WonderSwan etc.): hoje só stubs na GUI (`PlannedSystems.kt` e `planned.py`). Cada um precisa de pinagem, adaptador, id no protocolo, firmware (o upstream tem o núcleo), host e GUI; o hardware de partida é a placa `completa/`.

**D. Decisões que dependem do usuário.**
- Qual flash repro vem depois da NES (sugestão: o programador genérico, depois SNES CFI).
- Quando encomendar a placa (e qual: `16_bits` ou `16_and_8_bits`).
- Se o CRDB do OSCR deve ser lido (só com arquivos de exemplo).

### 0.3 Como retomar (passo a passo)

```
git pull                                     # (um clone só; remotos github e codeberg, repositórios privados)
git log --oneline | head -20                 # o último commit desta sessão: d877ed9
cat docs/funcoes-oscr.md                     # o que falta do OSCR
cd host && python3 -m pytest -q              # 104 passam
make -C firmware/oscr/pc-tests test          # 16 passam
(cd gui && ./gradlew --offline :shared:jvmTest :desktopApp:compileKotlin :cliApp:compileKotlin)
(cd firmware/oscr && ~/.platformio/penv/bin/pio run -e SerialASCII)
cd gui && ./gradlew :desktopApp:run          # abre a GUI
python3 host/dumper.py --simulate detect     # sem hardware
```

Para cada função nova do OSCR, o caminho (D77): ler o menu no `firmware/oscr/src/cores/*.cpp` → ligar o núcleo em `user.ini` se preciso → **chamar** a função do OSCR de uma costura em `src/dumper/` (uma `Backend`: `rom_prepare` e `stream_write_rom` para gravar ROM; `stream_read` para ler) → comandos e erros em `docs/protocolo.md` e `oscr_proto.h` → host (`protocol.py`, `client.py`, `cli.py`) e GUI (`Client.kt`, `Cli.kt`, `Main.kt`, `I18n.kt` nos 4 idiomas) → simulador (`sim.py`, `SimDevice.kt`, `pc-tests/sim_stdio.cpp`) e testes → docs (`funcoes-oscr.md`, `decisoes.md`, `uso.md`, `cli.md`) → commit e push nos dois remotos.

### 0.4 Armadilhas desta sessão

- **`pkill -f` e `pgrep -f` com um padrão que aparece na própria linha de comando matam o shell** (aconteceu duas vezes). Use `pkill -x Xvfb` e `kill <pid>`.
- Para ver a GUI sem tela: `Xvfb :97 -screen 0 1920x1100x24 -ac &`, depois `DISPLAY=:97 SKIKO_RENDER_API=SOFTWARE ./gradlew --offline :desktopApp:run` e `import -window root x.png`; `xdotool mousemove X Y click 1` clica. O GL do Skiko falha no Xvfb (por isso o renderizador por software).
- PlatformIO: `~/.platformio/penv/bin/pio` (não está no PATH). O ambiente do fork é `SerialASCII`.
- `HAS_FLASH` custa ~27 KB de flash. `flashfound` e `mmc6` do `NES.cpp` só são ligados, nunca desligados: o firmware os zera antes de cada comando.
- Listas de mappers: acrescentar um mapper exige atualizar CLI (`--mapper`), `I18n.kt` (`NES_HINT` e `HELP_USE_6` nos 4 idiomas; o chinês usa `、`), `docs/uso.md`, `docs/protocolo.md`, `docs/limites-nes.md`, `NesRules.kt`; `host/tests/test_docs_sync.py` confere.
- A lista de stubs (`planned.py` e `PlannedSystems.kt`) precisa ser idêntica; `test_planned.py` confere. A ordem alfabética do combo é só na tela.
- O firmware só volta a ser testável no PC pelo protocolo (`pc-tests`); o que os núcleos do OSCR fazem com o cartucho só se vê em hardware.
- Os arquivos `boards/16_bits/hardware/~dumper.kicad_*.lck` são travas do KiCad aberto: não commitar.

## 1. Onde estamos

| Área | Estado |
|---|---|
| Hardware (KiCad 10) | Pronto para fabricar: DRC com 0 erros e 4 avisos justificados (furos de canto), netlist confere com `boards/16_and_8_bits/docs/pinmap.md`. Gerbers, drill e zip em `boards/16_and_8_bits/fab/`. **Nada foi encomendado nem montado.** |
| Documentação | `README.md`, `docs/{pinmap,bom,montagem,protocolo,uso,decisoes}.md`, este arquivo. |
| Firmware | **Fork do OSCR** (`firmware/oscr/`, ver seção 0); o firmware próprio antigo está em `firmware/arquivo/`. Compila; **nunca rodou em hardware.** |
| Host (Python) | CLI `dumper.py` completa (inclui `rom-write`, `identify`, `search`), 104 testes. |
| GUI (Kotlin) | Compose Desktop, 4 idiomas (pt-BR, en, ru, zh). Compila e tem testes; **a janela nunca foi aberta** nesta máquina. |

Último commit na `main`: ver `git log` (o último incremento foi a conferência depois de gravar a ROM, D78). Remotos `github` e `codeberg`, repositórios **privados**.

## 2. O que cada sistema lê e grava (firmware)

| Sistema | ROM | Save |
|---|---|---|
| SNES | LoROM, HiROM, ExHiROM (até 8064 KB), SA-1 (precisa do Si5351 e do PIC), SuperFX, S-DD1, SPC7110, Cx4 | SRAM: ler e gravar (com conferência) |
| NES / Famicom | mappers 0, 1 (PRG até 256 KB), 2, 3, 4, 5, 7, 9, 10, 11, 66, 69, 71 e o lote de D64 (13, 34, 67, 68, 72, 73, 86, 92, 93, 94, 140, 152, 180, 184), mais os de D50/D57; o usuário informa mapper, PRG e CHR; cabeçalho iNES sintético | PRG-RAM de 8 KB nos mappers 1, 4, 5 e 69, 16/32 KB nos mappers 1 e 5 (`--ram`): ler e gravar |
| Mega Drive | tamanho pelo cabeçalho, redução de espelho, SSF2 até 8 MB, tamanho forçado | SRAM (ímpar, par, ambos): ler e gravar. **EEPROM serial: ler e gravar** (38 checksums do OSCR) |
| GBA | 256 KB a 32 MB (tamanho por espelhamento) | ler e gravar: SRAM 32 KB, Flash 64 e 128 KB, EEPROM 512 B e 8 KB (tipo informado pelo usuário; Flash só com chip conhecido) |
| GB / GBC (adaptador no slot GBA, 3,3 V) | sem mapper, MBC1, MBC1M, MBC2, MBC3, MBC5, MBC6 (ROM e save só leitura), MBC7, MMM01 (até 1 MB), TAMA5 (só ROM), GB Camera | SRAM: ler e gravar (sem RTC); EEPROM do MBC7: ler e gravar |

Detalhes e limites: `docs/uso.md` (tabela por sistema) e as entradas D38 a D59 de `docs/decisoes.md`.

**Ainda não existe:** SNES com Derby Stallion 96, S-RTC, OBC1, ST018, MSU-1, RTC do SPC7110; NES mappers além da lista acima, outros mappers com save; GB/GBC; Pier Solar, lock-on, mappers piratas.

## 3. Mapa do código

```
firmware/arquivo/oscr_serial/  (ARQUIVADO, D76) biblioteca C++ portátil do firmware próprio; o firmware atual é firmware/oscr/
  oscr_proto.*               quadros, CRC32, decodificador
  oscr_session.*             máquina de estados do protocolo; interface Backend; MockBackend
  oscr_bus.h                 interfaces SnesBus, NesBus, MdBus, GbaBus (o que o hardware precisa fazer)
  oscr_carts.cpp             CartBackend: dispatch, leitura e gravação de save comuns
  oscr_carts_<sistema>.cpp   snes, nes, md, gba, gb: cabeçalho (probe_*), ROM (*_byte), mappers, saves, I2C do Mega Drive
  oscr_carts_internal.h      o que esses arquivos compartilham
  oscr_si5351.h              cálculo dos registradores do Si5351 (portátil)
  oscr_avr_buses.h           HAL do ATmega2560: sequências de porta copiadas do OSCR (NÃO validado)
  oscr_arduino.h             cola com a Serial
  tests/                     test_proto, test_carts (cartuchos simulados), test_si5351, test_avr_hal (HAL do AVR no PC com
                             registradores simulados em tests/avr_mock), sim_stdio (usado pelo host)
firmware/arduino/oscr_dumper/   sketch (real por padrão; -DOSCR_MOCK = modo de teste)
firmware/platformio/            envs megaatmega2560 e megaatmega2560_mock
host/oscr_host/                 protocol, client, sim (MockDevice), cli, transport, verify
host/tests/                     inclui test_firmware_cpp: o cliente Python contra o C++ real
gui/shared/                     Kotlin comum: Protocol, Client, I18n, Errors, NesRules, Verify (+ testes)
gui/desktopApp/                 Main.kt (Compose), Prefs.kt (preferências) e SerialTransport.kt (jSerialComm)
.github/workflows/ci.yml        CI (escrito, ainda não executado)
tools/                          scripts do KiCad (ver README)
vendor/oscr/                    clones do OSCR, só leitura, ignorado pelo git (README explica como recriar)
```

## 4. Como rodar tudo

```
make -C firmware/arquivo/oscr_serial test                  # 16 do protocolo + 19 do Si5351 + 41 do HAL do AVR + 990 de cartuchos simulados
(cd host && python3 -m pytest -q)                  # 50 testes
(cd gui && ./gradlew --offline :shared:jvmTest :desktopApp:compileKotlin)
arduino-cli compile --fqbn arduino:avr:mega --library firmware/arquivo/oscr_serial firmware/arquivo/arduino/oscr_dumper   # firmware arquivado
(cd firmware/oscr && pio run -e SerialASCII)       # firmware atual
make -C firmware/oscr/pc-tests test                # protocolo do fork
(cd firmware/platformio && pio run)                # precisa do PlatformIO (pip install platformio, num venv)
python3 tools/check_netlist.py                     # netlist vs pinmap
kicad-cli pcb drc boards/16_and_8_bits/hardware/dumper.kicad_pcb
cd gui && ./gradlew :desktopApp:run                # abre a GUI (nunca testado em tela)
```

Sem hardware: `python3 host/dumper.py --simulate detect` e `... dump -s snes -o x.sfc` usam o simulador.

Tamanho do firmware: ~31 KB de flash (12%) no Mega.

## 5. Como o trabalho foi feito (padrão para continuar)

Cada suporte novo seguiu o mesmo caminho, e vale repetir:

1. Ler o `vendor/oscr/legacy/Cart_Reader/*.ino` correspondente.
2. Se precisar de hardware novo, acrescentar uma **primitiva** na interface de `oscr_bus.h` e implementá-la no AVR em `oscr_avr_buses.h` copiando a sequência de porta do OSCR; a **lógica** (cabeçalhos, tamanhos, protocolos seriais) fica em `oscr_carts.cpp`, portátil.
3. Escrever o cartucho simulado **independente** em `tests/test_carts.cpp` e os testes. (Limite conhecido: o simulador não pega erro de transcrição de bits e tempos copiados do OSCR.)
4. Opções do usuário passam pelos campos opcionais de `DUMP_ROM`/`READ_SAVE`/`WRITE_SAVE` (`mapper`, `prg_kb`, `chr_kb`). O campo `mapper` é reaproveitado: mapper do NES, tipo de save do GBA. O `DETECT` ignora as opções.
5. Host: CLI (`--mapper/--prg/--chr`), `verify.py`. GUI: `Main.kt`, textos em `I18n.kt` nos **quatro** idiomas (o teste de tradução exige todos).
6. Docs: `docs/uso.md`, `docs/protocolo.md` se o protocolo mudou, nova entrada em `docs/decisoes.md`, contagens em `firmware/README.md`.
7. Compilar Arduino e PlatformIO, rodar os três conjuntos de testes, commitar e dar push nos dois remotos.

Regras do `CLAUDE.md` que continuam valendo: mudanças mínimas e localizadas, nunca editar `vendor/`, nunca inventar pino (marcar `PENDENTE`), perguntar antes de mudar decisões da seção 1, pedir logs do teste em hardware.

## 6. Git, contas e segredos

- Identidade local do repositório: Legendary Redfox <legendaryredfox.dev@gmail.com> (só no repo, não no global).
- GitHub: `git push github main`, usa o alias SSH `github-legendaryredfox` (chave em `~/.ssh/legendaryredfox/`).
- Codeberg: `git -c http.extraHeader="Authorization: token $(cat ~/.codeberg_token)" push codeberg main`. O token fica em `~/.codeberg_token`; **nunca** gravar o token numa URL de remoto, num arquivo do repositório ou na saída de um comando.
- A conta ativa do `gh` é outra (romulofer); para o GitHub do projeto use `GH_TOKEN=$(gh auth token -u legendaryredfox)` sem trocar a conta ativa.
- **Sem co-autoria de IA:** o usuário é o único autor. Nenhuma linha `Co-Authored-By` nem menção a IA em commits ou PRs (regra do usuário, 2026-11-02; o histórico foi reescrito para remover as linhas antigas).

## 7. Ambiente e armadilhas já encontradas

- **KiCad 10.0.8** (PPA `kicad-10.0-releases`). O `kicad-cli` 9 não abre arquivos gravados pelo MCP.
- **MCP do KiCad** em `~/development/llms/KiCAD-MCP-Server` (v2.8.3): chamadas com limite de 30 s e gravação não atômica; um timeout já zerou o `.kicad_sch`. Lotes de no máximo ~25 pinos e backup antes. Ferramentas destrutivas só com confirmação do usuário.
- Roteamento: Freerouting fora do MCP (`java -jar ~/.kicad-mcp/freerouting.jar -de x.dsn -do x.ses -mp N`); zonas e ajustes finos com scripts `pcbnew` usando o python do venv do MCP.
- `pkill -f` com um padrão que aparece na própria linha de comando mata o shell: use `kill $(pgrep ...)` com padrão preciso.
- O shell do usuário imprime linhas `setValueForKeyFakeAssocArray ... command not found: _encode` em todo comando. É ruído do perfil do zsh, sem relação com o projeto.
- Gradle 9.7, Kotlin 2.4.0, Compose Desktop 1.9.3, jSerialComm 2.11.4 (pacote `com.fazecast.jSerialComm`). A versão de pacote do macOS precisa ser ≥ 1.0.0.
- No Linux o usuário precisa estar no grupo `dialout` para abrir a porta serial.

## 8. O que falta, em ordem de valor

**Histórico da sessão de 2026-11-02:** `docs/sessao-2026-11-02.md`.

**Revisões (2026-11-02):** `docs/revisao-codigo.md` (C-xx) e `docs/revisao-ux.md` (U-xx) têm os achados abertos por gravidade. Antes do primeiro teste com hardware, recomendo U-01, U-02 e U-03 (perda de dados na GUI, gravação sem confirmação, resultado fora da tela), C-13 (CI) e C-14 (teste do HAL), e conferir o módulo Si5351 (C-15).

**A. Validação com hardware (nada disso foi feito).** Roteiro em `docs/uso.md` seção 7:
0. **Ordem de risco para os primeiros testes de gravação:** SRAM do SNES/GBA com backup feito, depois EEPROM do GBA, e a Flash do GBA por último (apaga o chip).
1. Encomendar a placa (`boards/16_and_8_bits/fab/dumper-v1.0-jlcpcb.zip`) e as peças da `boards/16_and_8_bits/docs/bom.md`.
2. Antes de comprar, conferir com as peças reais: medidas dos slots e do módulo Si5351 (D17, D23), lado da etiqueta de cada slot (D27, D28), altura dos espaçadores (D25).
3. Montar (`boards/16_and_8_bits/docs/montagem.md`), testes de continuidade e de tensão, gravar o firmware, rodar o modo `MOCK`, depois um cartucho simples (SNES LoROM ou NES mapper 0) e comparar o CRC32 com o No-Intro.
4. Pedir os logs. Pontos mais prováveis de ajuste: `oscr_avr_buses.h` (tempos), EEPROM do GBA (`eeprom_block`, `eeprom_write_block`), gravação de Flash do GBA, EEPROM do Mega Drive (bits por tipo em `eep_state`), troca de banco do GBA.

**B. Pequenos itens de software.**
- ~~Abrir a GUI numa tela~~ Feito em 2026-11-02 num display virtual (Xvfb; renderizador por software, o GL do Skiko falha lá): a janela abre, troca de idioma, mostra as opções do NES e a ajuda. Corrigidos: textos de ajuda desatualizados (4 idiomas), chip GB sem suporte (escondido), rótulo do campo de tamanho cortado. **Não testado:** conexão com porta serial (sem porta no Xvfb; o jSerialComm não lista pty), progresso, seleção de arquivo. Para repetir: `Xvfb :97 -screen 0 1280x900x24 -ac &` e `DISPLAY=:97 ./gradlew :desktopApp:run`, captura com `import -window root`.
- Conferir o jSerialComm a 1.000.000 baud no Linux, macOS e Windows.
- Revisão das traduções ru e zh por falante nativo.
- Empacotamento (deb/AppImage, dmg, msi), previsto para depois.

**C. Mais suporte de cartuchos** (cada um é um ciclo do passo 5): mais mappers do NES, save do MMC5/FME-7, SNES ExHiROM e SA-1, GB/GBC.

**Achados no firmware original do OSCR:** `docs/achados-oscr-original.md` (o firmware novo é uma reescrita com as mesmas sequências; a diferença útil é a base de dados CRDB, que não está no clone).

**Limites levantados em 2026-11-03:** `docs/limites-nes.md` (NES) e `docs/limites-gb.md` (Game Boy) (o que falta no `NesBus`, mappers por motivo de bloqueio, ordem sugerida do próximo lote; para o GB: limites da placa a 3,3 V, de cada mapper e acessórios não portados).

**Próximo passo sugerido:** ciclo C de novo: gravação da Flash do MBC6 (ver D61), RTC do MBC3 (MBC6, MBC7, MMM01 e TAMA5 já estão em D60 e D61), RTC do MBC3, SNES com os chips raros acima. Hardware do D56: o silk do slot GBA já foi atualizado; opcional: jumper de solda 5V para GB. Mappers do NES feitos em D50 (ver lá o desvio do `$5130` no MMC5); mais mappers: ler `NES.ino`, estender `nes_setup_mapper`/`nes_prg_byte`/`nes_chr_byte`, a lista `known` em `probe` e `SimMapper`.

Estado dos testes na última verificação: 16 do protocolo + 19 do Si5351 + 41 do HAL do AVR + 990 de cartuchos, 60 do host, Gradle `:shared:jvmTest` e `:desktopApp:compileKotlin` ok. PlatformIO não rodou nesta máquina (sem `pio`); o Arduino compila.

Armadilha: um `until ! pgrep -f '<padrão>'` em segundo plano nunca termina se o padrão aparecer na própria linha de comando do `until`. Use `kill -0 <pid>` ou `wait`.

## 9. Preferências do usuário

- Respostas no chat curtas, estilo "caveman" (`~/.claude/CLAUDE.md`); código, commits e documentos em linguagem normal. Documentação do projeto em português do Brasil.
- Mudanças mínimas; perguntar antes de decisões grandes; relatar com franqueza o que não foi validado (hoje: tudo que depende de hardware).
- Commitar e dar push nos dois remotos ao fim de cada incremento.
