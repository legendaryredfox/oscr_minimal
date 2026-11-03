# Continuação — estado do projeto e como retomar

Escrito em 2026-11-02, ao fim de uma sessão longa. Quem for continuar (pessoa ou Claude Code) deve ler este arquivo, depois `CLAUDE.md` (regras e decisões fixas) e `docs/decisoes.md` (log D1 a D59, com índice no topo).

## 1. Onde estamos

| Área | Estado |
|---|---|
| Hardware (KiCad 10) | Pronto para fabricar: DRC com 0 erros e 4 avisos justificados (furos de canto), netlist confere com `docs/pinmap.md`. Gerbers, drill e zip em `hardware/fab/`. **Nada foi encomendado nem montado.** |
| Documentação | `README.md`, `docs/{pinmap,bom,montagem,protocolo,uso,decisoes}.md`, este arquivo. |
| Firmware | Protocolo v1 e leitura de cartuchos escritos e testados **só no PC**, com cartuchos simulados. Compila para o Mega (Arduino e PlatformIO). **Nunca rodou em hardware.** |
| Host (Python) | CLI `dumper.py` completa, 50 testes. |
| GUI (Kotlin) | Compose Desktop, 4 idiomas (pt-BR, en, ru, zh). Compila e tem testes; **a janela nunca foi aberta** nesta máquina. |

Último commit na `main`: ver `git log` (o último incremento foi a aplicação das correções das revisões de código e de UX/UI, D59). Remotos `github` e `codeberg`, repositórios **privados**.

## 2. O que cada sistema lê e grava (firmware)

| Sistema | ROM | Save |
|---|---|---|
| SNES | LoROM, HiROM, ExHiROM (até 8064 KB), SA-1 (precisa do Si5351 e do PIC), SuperFX, S-DD1, SPC7110, Cx4 | SRAM: ler e gravar (com conferência) |
| NES / Famicom | mappers 0, 1 (PRG até 256 KB), 2, 3, 4, 5, 7, 9, 10, 11, 66, 69, 71; o usuário informa mapper, PRG e CHR; cabeçalho iNES sintético | PRG-RAM de 8 KB nos mappers 1, 4, 5 e 69, 16/32 KB nos mappers 1 e 5 (`--ram`): ler e gravar |
| Mega Drive | tamanho pelo cabeçalho, redução de espelho, SSF2 até 8 MB, tamanho forçado | SRAM (ímpar, par, ambos): ler e gravar. **EEPROM serial: ler e gravar** (38 checksums do OSCR) |
| GBA | 256 KB a 32 MB (tamanho por espelhamento) | ler e gravar: SRAM 32 KB, Flash 64 e 128 KB, EEPROM 512 B e 8 KB (tipo informado pelo usuário; Flash só com chip conhecido) |
| GB / GBC (adaptador no slot GBA, 3,3 V) | sem mapper, MBC1, MBC1M, MBC2, MBC3, MBC5, MBC6 (ROM e save só leitura), MBC7, MMM01 (até 1 MB), TAMA5 (só ROM), GB Camera | SRAM: ler e gravar (sem RTC); EEPROM do MBC7: ler e gravar |

Detalhes e limites: `docs/uso.md` (tabela por sistema) e as entradas D38 a D59 de `docs/decisoes.md`.

**Ainda não existe:** SNES com Derby Stallion 96, S-RTC, OBC1, ST018, MSU-1, RTC do SPC7110; NES mappers além da lista acima, outros mappers com save; GB/GBC; Pier Solar, lock-on, mappers piratas.

## 3. Mapa do código

```
firmware/oscr_serial/        biblioteca C++ portátil (testável no PC)
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
make -C firmware/oscr_serial test                  # 16 do protocolo + 19 do Si5351 + 41 do HAL do AVR + 914 de cartuchos simulados
(cd host && python3 -m pytest -q)                  # 50 testes
(cd gui && ./gradlew --offline :shared:jvmTest :desktopApp:compileKotlin)
arduino-cli compile --fqbn arduino:avr:mega --library firmware/oscr_serial firmware/arduino/oscr_dumper
(cd firmware/platformio && pio run)                # precisa do PlatformIO (pip install platformio, num venv)
python3 tools/check_netlist.py                     # netlist vs pinmap
kicad-cli pcb drc hardware/dumper.kicad_pcb
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
1. Encomendar a placa (`hardware/fab/dumper-v1.0-jlcpcb.zip`) e as peças da `docs/bom.md`.
2. Antes de comprar, conferir com as peças reais: medidas dos slots e do módulo Si5351 (D17, D23), lado da etiqueta de cada slot (D27, D28), altura dos espaçadores (D25).
3. Montar (`docs/montagem.md`), testes de continuidade e de tensão, gravar o firmware, rodar o modo `MOCK`, depois um cartucho simples (SNES LoROM ou NES mapper 0) e comparar o CRC32 com o No-Intro.
4. Pedir os logs. Pontos mais prováveis de ajuste: `oscr_avr_buses.h` (tempos), EEPROM do GBA (`eeprom_block`, `eeprom_write_block`), gravação de Flash do GBA, EEPROM do Mega Drive (bits por tipo em `eep_state`), troca de banco do GBA.

**B. Pequenos itens de software.**
- ~~Abrir a GUI numa tela~~ Feito em 2026-11-02 num display virtual (Xvfb; renderizador por software, o GL do Skiko falha lá): a janela abre, troca de idioma, mostra as opções do NES e a ajuda. Corrigidos: textos de ajuda desatualizados (4 idiomas), chip GB sem suporte (escondido), rótulo do campo de tamanho cortado. **Não testado:** conexão com porta serial (sem porta no Xvfb; o jSerialComm não lista pty), progresso, seleção de arquivo. Para repetir: `Xvfb :97 -screen 0 1280x900x24 -ac &` e `DISPLAY=:97 ./gradlew :desktopApp:run`, captura com `import -window root`.
- Conferir o jSerialComm a 1.000.000 baud no Linux, macOS e Windows.
- Revisão das traduções ru e zh por falante nativo.
- Empacotamento (deb/AppImage, dmg, msi), previsto para depois.

**C. Mais suporte de cartuchos** (cada um é um ciclo do passo 5): mais mappers do NES, save do MMC5/FME-7, SNES ExHiROM e SA-1, GB/GBC.

**Limites do NES levantados em 2026-11-03:** `docs/limites-nes.md` (o que falta no `NesBus`, mappers por motivo de bloqueio, ordem sugerida do próximo lote).

**Próximo passo sugerido:** ciclo C de novo: gravação da Flash do MBC6 (ver D61), RTC do MBC3 (MBC6, MBC7, MMM01 e TAMA5 já estão em D60 e D61), RTC do MBC3, SNES com os chips raros acima. Hardware do D56: o silk do slot GBA já foi atualizado; opcional: jumper de solda 5V para GB. Mappers do NES feitos em D50 (ver lá o desvio do `$5130` no MMC5); mais mappers: ler `NES.ino`, estender `nes_setup_mapper`/`nes_prg_byte`/`nes_chr_byte`, a lista `known` em `probe` e `SimMapper`.

Estado dos testes na última verificação: 16 do protocolo + 19 do Si5351 + 41 do HAL do AVR + 914 de cartuchos, 60 do host, Gradle `:shared:jvmTest` e `:desktopApp:compileKotlin` ok. PlatformIO não rodou nesta máquina (sem `pio`); o Arduino compila.

Armadilha: um `until ! pgrep -f '<padrão>'` em segundo plano nunca termina se o padrão aparecer na própria linha de comando do `until`. Use `kill -0 <pid>` ou `wait`.

## 9. Preferências do usuário

- Respostas no chat curtas, estilo "caveman" (`~/.claude/CLAUDE.md`); código, commits e documentos em linguagem normal. Documentação do projeto em português do Brasil.
- Mudanças mínimas; perguntar antes de decisões grandes; relatar com franqueza o que não foi validado (hoje: tudo que depende de hardware).
- Commitar e dar push nos dois remotos ao fim de cada incremento.
