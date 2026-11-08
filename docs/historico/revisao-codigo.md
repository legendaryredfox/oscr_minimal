# Revisão de código — codebase inteira

Data: 2026-11-02. Revisão da base toda (não só da última diff): firmware, host Python, GUI Kotlin, scripts de hardware e documentação. A revisão de UX/UI está em `docs/historico/revisao-ux.md`.

## 1. Escopo e método

| Parte | Linhas | Como foi revisada |
|---|---|---|
| `firmware/oscr_serial` (protocolo, sessão, backend dos cartuchos, Si5351) | ~2.700 | Leitura completa de `oscr_proto.cpp`, `oscr_session.cpp`, `oscr_arduino.h`; releitura dirigida de `oscr_carts.cpp` (1.000 linhas) e `oscr_avr_buses.h` (480); testes com **ASan + UBSan** e `-Wall -Wextra -Wshadow -Wconversion` |
| Testes do firmware | ~900 | 864 verificações de cartuchos, 16 de protocolo, 19 do Si5351; **testes de mutação manuais** a cada incremento (erro plantado no firmware precisa derrubar ao menos um teste) |
| `host/` (CLI, cliente, protocolo, simulador, verificação) | ~950 | Leitura de `client.py`, `cli.py`, `verify.py`; `pytest` (50 testes, **83 %** de cobertura de linhas) |
| `gui/` (shared + desktopApp) | ~900 | Leitura de `Main.kt`, `Client.kt`, `Protocol.kt`, `SerialTransport.kt`, `Verify.kt`; testes Gradle; GUI aberta num display virtual |
| `tools/` e hardware | ~900 | Execução de `check_netlist.py` (67 nets, 375 ligações conferem com `pinmap.md`), ERC (0 violações) e DRC (0 violações, 0 ligações abertas, 0 problemas de paridade). Os scripts de geração do KiCad não foram relidos linha a linha. |
| Documentação | — | Conferência cruzada de listas (mappers, limites, contagens de testes) entre `uso.md`, `protocolo.md`, GUI e CLI |

**O que esta revisão não cobre:** o HAL do AVR (`oscr_avr_buses.h`) não roda em nenhum teste, e tempos, bits de porta e níveis elétricos só se validam com hardware. Tudo que depende do cartucho real continua **não validado** (ver `docs/continuacao.md`).

## 2. Resumo

| Gravidade | Corrigidos nesta revisão | Abertos |
|---|---|---|
| Alta | 2 | 0 |
| Média | 2 | 7 |
| Baixa | 1 | 9 |

Nenhum problema de memória nem comportamento indefinido no código portátil do firmware. O que mais pesa são riscos que só aparecem com hardware (SRAM do MMC1, Si5351, tempos) e falta de automação (CI, teste do HAL).

## 3. Pontos fortes

- Protocolo pequeno, com CRC32 por quadro e do arquivo, confirmação por bloco e retransmissão. Cliente Python e cliente Kotlin seguem a mesma máquina de estados e são testados contra o firmware real em C++ (`test_firmware_cpp`).
- Separação limpa entre **lógica** (portátil, testável no PC) e **HAL** do AVR (sequências copiadas do OSCR). Isso permitiu 864 verificações com cartuchos simulados independentes.
- Disciplina de testes: cada suporte novo ganhou simulador próprio e foi testado por mutação.
- Documentação de decisões (D1 a D57) e honestidade explícita sobre o que não foi validado.
- Sem alocação dinâmica no firmware, buffers de tamanho fixo, `uint8_t g[80]`/`tx_` dimensionados com folga.

## 4. Achados corrigidos nesta revisão

| ID | Gravidade | Onde | Problema | Correção |
|---|---|---|---|---|
| C-01 | **Alta** | `mmc1_write` (`oscr_carts.cpp`) | O OSCR escreve em `$E000-$FFFF` do MMC1 com `write_reg_byte` (M2 e /ROMSEL trocados direto na porta), justamente para **não corromper a PRG-RAM com bateria**. O firmware usava a escrita comum: dumpar a ROM, ou ler e gravar o save, de um MMC1 com bateria podia **estragar o save**. | Primitiva `NesBus::reg_write_safe` (AVR copia a sequência do OSCR); o simulador do MMC1 corrompe a RAM se a escrita não for a segura. D57. |
| C-02 | **Alta** | Game Boy, `gb_select` e `byte_at` | (a) MBC1 acima de 512 KB: os bancos `$20/$40/$60` não aparecem em `$4000` e saíam como `$21/$41/$61` (o OSCR tem o mesmo defeito); (b) o MBC1 em modo 1 depois de uma leitura de save escondia o banco 0 e o cabeçalho da operação seguinte ("sem cartucho"). | Leitura desses bancos pela janela de `$0000` em modo 1; `probe` zera modo e banco superior antes de ler o cabeçalho. D56. |
| C-03 | Média | `probe` do NES | Faltavam limites de tamanho: MMC1, MMC3, MMC2/4 e FME-7 truncam o número do banco de CHR (5 ou 8 bits) e um cartucho maior saía **errado em silêncio**. | Limites com erro `0x0002` e testes. |
| C-04 | Média | SNES | SRAM de HiROM/ExHiROM sem o CS elevado (o OSCR sobe PH3); LoROM de 4 MB lia `$7E-$7F` (WRAM). | `SnesBus::cs`; LoROM acima de 3 MB lê de `$80+`. D53 e D55. |
| C-05 | Baixa | Teste do GB | UBSan: `16384UL << (rsz + 1)` com `rsz = 0x52` no simulador (não no firmware). | Tamanho do vetor limitado a 8; só o cabeçalho leva o valor inválido. |

## 5. Achados abertos

### Média

| ID | Onde | Problema | Recomendação |
|---|---|---|---|
| C-10 | GUI: `Protocol.kt`, `Client.kt`, `SerialTransport.kt`, `Main.kt` | **Strings fixas em português no código**, mostradas ao usuário (`"sem resposta ao comando 0x…"`, `"não foi possível abrir …"`, `DeviceError` = `"erro 0x…"`, `"bytes"`, `"CRC32"`). Quebra a regra da seção 9 do `CLAUDE.md` ("nenhuma string fixa no código"); um usuário em inglês, russo ou chinês vê português. | Exceções carregam só um código; a GUI mapeia o código para texto em `I18n.kt` (ver U-05). |
| C-11 | `OscrClient.abort()` (Kotlin) e `Client.abort()` (Python) | `abort` roda em outra thread (botão **Cancelar**) enquanto a thread de E/S escreve ACKs: `write` do transporte não é sincronizado, e dois quadros podem se intercalar na serial. | `synchronized` no `write` dos dois transportes (ou fila de envio única). |
| C-12 | `SerialTransport.write` | Ignora o retorno de `writeBytes` (escrita parcial vira quadro truncado, o CRC pega e há retransmissão, mas fica sem diagnóstico). | Verificar o retorno e lançar erro. |
| C-13 | Repositório | **Sem CI.** Nada roda `make test`, `pytest`, Gradle, `arduino-cli compile` e os sanitizers a cada push; a regressão só aparece quando alguém lembra de rodar. | Workflow (GitHub Actions) com os quatro conjuntos + compilação Arduino; opcional espelho no Codeberg. |
| C-14 | `oscr_avr_buses.h` | **Nenhum teste do HAL.** Erro de bit/porta só aparece em hardware (é o risco principal do projeto). | Mock de `avr/io.h` (registradores `PORTx`/`DDRx` como variáveis) para rodar o HAL no PC e conferir as sequências de porta contra a tabela do `pinmap.md`/OSCR. |
| C-15 | Si5351 + `Wire` (D54) | `Wire.begin()` liga os pull-ups internos de D20/D21 (5 V). Num módulo Si5351 genérico, com SDA/SCL em 3,3 V e sem level shifter, isso pode forçar 5 V nas linhas. O módulo Adafruit tem shifter; os genéricos variam. | Conferir o módulo comprado antes de ligar; se não tiver shifter, usar `TWCR`/`pinMode` sem pull-up e resistores externos para 3,3 V. Anotar a escolha no `montagem.md`. |
| C-16 | Documentação | **Listas repetidas à mão** em seis lugares (mappers e limites em `uso.md`, `protocolo.md`, quatro idiomas da GUI, `cli.py`, `continuacao.md`, `README`). A deriva já aconteceu (a ajuda da GUI dizia "só o SNES tem save"). | Uma fonte única (arquivo de capacidades) usada pela GUI e pelo CLI, ou um teste que confere as listas. |

### Baixa

| ID | Onde | Problema | Recomendação |
|---|---|---|---|
| C-20 | `oscr_carts.cpp` | **Arquivo único de ~1.000 linhas** com seis sistemas misturados; difícil de revisar. | Separar por sistema (`snes`, `nes`, `md`, `gba`, `gb`) mantendo a interface `CartBackend`. |
| C-21 | `CartBackend::read` | Uma chamada virtual por byte, e o GBA lê **uma palavra de 16 bits por byte** (duas leituras). Cabe no tempo (a serial a 1 Mbaud limita), mas desperdiça. | Leitura em bloco por sistema (`read_block`), com o GBA lendo palavras. |
| C-22 | `Session` e `CartBackend::detect` | As opções do NES persistem entre comandos: `DETECT` salva e restaura em vez de limpar, e um erro precoce em `do_read` deixa as opções do comando anterior. Hoje é inofensivo (`do_read`/`do_write` sempre chamam `set_options`), mas é estado herdado. | Limpar as opções em toda saída de comando. |
| C-23 | `_stream_in` / `streamIn` | Sem teto para o `size` do `BEGIN` (protegido por CRC, então só falha de firmware) e sem conferir que o `kind` bate com o pedido. | Teto por sistema e checagem do `kind`. |
| C-24 | `verify.py` e `Verify.kt` | Duplicados, sem verificação de cabeçalho para **GB** (checksum `$14D`) e para NES; a paridade Python x Kotlin só é mantida à mão. | Acrescentar o checksum do GB nos dois; teste cruzado com os mesmos vetores. |
| C-25 | `Cart` / `probe` | A detecção do SNES pelo checksum recusa cartuchos com cabeçalho legítimo mas checksum errado (jogos "limpos" de hack); `status 1` diz "sem cartucho". | Mensagem separada ("cabeçalho inválido") e opção de forçar. |
| C-26 | `MockDevice` (`sim.py`) | O simulador do host só entende os sistemas 0 e 255; os testes de fluxo de um cartucho real vêm do `test_firmware_cpp`. | Documentar; ou usar sempre o simulador C++ nos testes de CLI. |
| C-27 | `tools/*.py` | Scripts do KiCad com caminhos e nomes fixos, e dependência do MCP/`pcbnew` do venv; não relidos a fundo. | Documentar as dependências no README de `tools/`. |
| C-28 | `docs/decisoes.md` | 57 entradas num arquivo só (>40 KB), sem índice. | Índice no topo e separação por fase. |

### Riscos de hardware conhecidos (já registrados, só listados aqui)

- **GBA e GB a 3,3 V com lógica de 5 V do Mega direto nos pinos do cartucho** (D22): é o comportamento do OSCR, risco aceito. Para GB, alguns cartuchos antigos podem não funcionar a 3,3 V (D56).
- **Gravação de Flash do GBA** apaga o chip: primeiro teste real só depois de backup (D48).
- **SA-1:** driver do Si5351 escrito pelo datasheet e não pela biblioteca do OSCR; cristal de 25 MHz assumido (D54).

## 6. Recomendação de ordem

1. C-13 (CI) e C-14 (teste do HAL): protegem tudo o que vem depois.
2. C-10, C-11 e C-12 (GUI e transporte): pequenos, mas afetam o uso real; entram junto com as correções de UX de `revisao-ux.md`.
3. C-15 antes de ligar o módulo Si5351.
4. C-20 e C-21 só quando houver hardware para medir desempenho.

## 7. Estado depois das correções (2026-11-02)

| Achado | Estado |
|---|---|
| C-10 textos fixos na GUI | **Corrigido**: exceções com código e textos em `I18n` (4 idiomas), `describeError`; teste para todos os erros nos 4 idiomas |
| C-11 `abort` e escrita concorrente | **Corrigido** (Kotlin e Python): `write` sincronizado |
| C-12 escrita parcial | **Corrigido**: o retorno é conferido e vira erro |
| C-13 sem CI | **Escrito** (`.github/workflows/ci.yml`); **não executado** nesta máquina |
| C-14 HAL sem teste | **Corrigido**: `tests/test_avr_hal.cpp`, 41 verificações com registradores simulados, testadas por mutação |
| C-15 pull-ups do I²C | **Corrigido no firmware** (sem pull-up interno; `-DOSCR_I2C_PULLUPS` religa). Falta conferir o módulo comprado e anotar no `montagem.md` |
| C-16 listas repetidas | **Coberto por teste** (`test_docs_sync.py`); a fonte única em si não foi criada |
| C-20 arquivo de 1.000 linhas | **Corrigido**: um arquivo por sistema |
| C-21 leitura byte a byte do GBA | **Corrigido para o GBA** (palavras); os outros sistemas continuam por byte |
| C-22 opções herdadas | **Corrigido**: limpas ao fim de todo comando |
| C-23 teto e `kind` do `BEGIN` | **Corrigido** (Python e Kotlin, com teste) |
| C-24 verify do GB | **Corrigido** (checksum `$14D`, Python e Kotlin); NES continua sem verificação (não há o que conferir) |
| C-25 "sem cartucho" para cabeçalho ruim | **Corrigido**: status 4; a opção de forçar a leitura **não** foi feita |
| C-26 simulador do host | **Documentado** |
| C-27 `tools/` | **Documentado** (`tools/README.md`) |
| C-28 `decisoes.md` | **Corrigido**: índice gerado por `tools/gen_decisoes_index.py` |
