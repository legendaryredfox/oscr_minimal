# CLI para agentes de IA (e scripts)

A CLI `dumper` (`host/`) funciona para pessoas e para agentes. Este arquivo é o contrato: o que muda no formato de saída ou nos códigos de saída precisa mudar aqui e nos testes (`host/tests/test_cli_agentes.py`).

## Regras

- **Sem prompt fora de um terminal.** O único comando que pergunta é `save-write`, e só quando stdin é um terminal. Sem terminal, ele recusa (saída 4) a menos que receba `--yes`.
- **`--json`**: uma linha de JSON em stdout, sempre com `"ok"`. Vale antes ou depois do subcomando.
- **Erros com `--json`**: também em stdout, uma linha: `{"ok":false,"error":{"kind":"...","message":"...","hint":"..."}}`. Sem `--json`, texto em stderr (`erro: ...`).
- **Progresso**: `--progress jsonl` escreve em **stderr** uma linha por 1 %: `{"event":"progress","label":"rom","done":N,"total":N,"percent":P}`. `label` é `rom`, `save`, `backup` ou `write`. `--progress none` desliga; `auto` (padrão) mostra barra só se stderr for terminal.
- **Sem hardware**: `--simulate` usa o simulador em memória (sistemas `mock`, `snes`, etc. respondem com cartuchos simulados).
- **Arquivos**: `-o` sobrescreve se existir. A extensão certa é acrescentada quando `-o` não tem uma. Sem `-o`, o nome vem do título do cartucho.
- **Descoberta sem porta**: `systems` e `errors` não abrem a porta serial.

## Códigos de saída

| Código | Significado | `error.kind` |
|---|---|---|
| 0 | sucesso | |
| 1 | erro do dispositivo, do protocolo, timeout ou arquivo | `device_error`, `no_save`, `protocol`, `timeout`, `io` |
| 2 | nenhum cartucho | `no_cartridge` (ou `detect` com `status` ≠ 0) |
| 3 | porta serial não encontrada, não abre, ou dispositivo sem resposta | `no_port`, `open_port`, `no_response` |
| 4 | recusado: `save-write` sem `--yes` fora de um terminal | `refused` |
| 64 | argumentos inválidos | `usage` |
| 130 | Ctrl+C | `interrupted` |

`device_error` traz também `error.device_code` (código do protocolo, `docs/protocolo.md` seção 8). `dumper errors --json` lista todos, com a dica de cada um.

## Comandos

| Comando | Saída JSON (além de `ok`) |
|---|---|
| `ports` | `ports`: lista de portas |
| `systems` | `systems`: `[{name, id, extension, options, needs_cartridge}]`; `options` diz quais de `--mapper`, `--prg`, `--chr`, `--ram` o sistema usa. `planned`: `[{name, label, supported:false}]`, os outros cartuchos do OSCR ainda sem suporte (marcadores de lugar; não valem em `-s`) |
| `errors` | `device_errors`, `exit_codes` |
| `info` | `proto`, `firmware`, `mock`, `si5351`, `systems`, `max_payload` |
| `detect -s SISTEMA` | `status`, `status_text`, `system`, `name`, `rom_size`, `save_size`. `ok` é `false` e a saída é 2 se não houver cartucho |
| `dump -s SISTEMA [-o ARQ]` | `file`, `bytes`, `crc32` (hex maiúsculo, 8 dígitos), `checksum` (`ok`, `mismatch`, `na`), e `gba_save_type` no GBA |
| `dump ... --db BASE` | acrescenta `game`: `null` ou `{name, crc32, size, source, kind, match, others}` (e, na base NES 2.0, `mapper`, `submapper`, `prg_kb`, `chr_kb`, `ram_kb`, `battery`). Sem `-o`, o arquivo recebe o nome do jogo |
| `dump -s nes --game NOME --db BASE` | preenche `--mapper`, `--prg` e `--chr` que ficaram em 0 com os do jogo na base NES 2.0. Erros: `game_not_found`, `game_ambiguous` (saída 64) |
| `identify ARQ... --db BASE` | `entries_in_database`, `results`: `[{file, bytes, crc32, game}]`; não abre a porta; saída 1 se algum não for achado. `-s` escolhe o sistema (padrão: pela extensão) |
| `search TEXTO --db BASE [--limit N]` | `entries_in_database`, `results`: entradas da base cujo nome tem todas as palavras; não abre a porta; saída 1 se nada |
| `save-read -s SISTEMA [-o ARQ]` | `file`, `bytes`, `crc32` |
| `rom-write -i ARQ.sfc -s snes --chip snes-lorom\|snes-hirom --layout 1x\|2x2mb\|2x4mb\|4x2mb\|1x8mb` | flash CFI do SNES com 1, 2 ou 4 chips ou 8 MB (`--layout`; as de 8 MB pedem ROM de 6 a 8 MB; o PC reordena a ROM como o OSCR). `layout` na saída |
| `rom-write -i ARQ.sfc -s snes --chip snes-lorom-p0\|snes-hirom-p0\|snes-exlorom-p1\|snes-exhirom-p1 --flash-type TIPO --flash-mb N [--sector-kb K --buffer B]` | menus P0 e P1 do OSCR: flash de 8 bits de tipo informado (`29f032`, `29f1610`, `lh28f0xx`, `29f1601`, `29lv640`, `29f800`, `29gl`, `e28fxxxj3a`); tipos `29gl`, `lh28f0xx` e `e28fxxxj3a` exigem setor e buffer (o `e28fxxxj3a` assume 128 KB e 32 bytes) |
| `rom-write -i ARQ.md -s md [--chip md-flash] --yes` | flash repro do **Mega Drive** (MX29F1610 2 MB ou S29GL064N 4 MB, identificado pelo firmware): ROM binária de tamanho par, até 4 MB (o `.smd` com cabeçalho de copiadora é recusado). A conferência depois de gravar compara o que o `DUMP_ROM` devolve (tamanho pelo cabeçalho da ROM): se o cabeçalho declara menos bytes que o arquivo, o `verify` aponta diferença no fim |
| `rom-write -i ARQ.sfc -s snes --chip snes-lorom\|snes-hirom [--capacity 2048\|4096] --yes` | mesmo comando para o **flash CFI do SNES** (1 chip de 2 ou 4 MB): o `--chip` é obrigatório (fiação do cartucho), o cabeçalho de copiadora de 512 bytes é removido, `--capacity` padrão = a menor em que a ROM cabe; a saída ganha `flash_kb` |
| `rom-write -i ARQ.nes [-s nes] [--chip nesmaker\|a29040b] --yes` | grava a **ROM** em cartucho de flash (APAGA o chip). `chip`, `prg_kb`, `chr_kb`, `bytes`, `crc32`. Sem `--chip`, o chip vem do mapper do cabeçalho (30 = nesmaker, 0 = a29040b). Erros: `bad_rom` (arquivo, saída 64), `usage` (chip indefinido, saída 64), `refused` (falta `--yes`, saída 4), `unsupported_firmware`, e do dispositivo `0x000B` (chip não reconhecido). Espera até `--begin-timeout` s (90) pelo apagamento. Depois de gravar, **lê a ROM de volta e compara** (`verify`: `{ok, read_crc32, expected_crc32, first_diff, read_bytes}`; `"skipped"` com `--no-verify` e no simulador); se não confere, erro `verify_failed` (saída 1) com `first_diff` e `written` |
| `save-write -s SISTEMA -i ARQ --yes` | `backup` (arquivo do save anterior, salvo antes de gravar, a menos que `--no-backup`), `bytes`, `crc32` |

## Base de dados de jogos (`--db`)

A identificação do jogo é feita **no PC**, pelo CRC32; o firmware não carrega base. `--db` aceita um arquivo ou uma pasta (procura `.dat` e `.xml`), pode repetir, e a variável `OSCR_DB` (caminhos separados por `:`, ou `;` no Windows) vale como padrão. Formatos lidos: **No-Intro / Redump** (Logiqx XML, `.dat`) e **NES 2.0 XML** (`nes20db.xml`, traz mapper e tamanhos). A base binária CRDB do OSCR não é lida. No NES/Famicom a ROM também é procurada sem o cabeçalho iNES de 16 bytes (o "headerless" do No-Intro) e pelos CRC32 da PRG e da CHR (NES 2.0 XML). Erros: `no_database` (saída 64) e `database` (arquivo inexistente ou XML inválido, saída 1).

## Fluxo recomendado para um agente

```
dumper --json ports                         # achar a porta (ou omitir -p: usa a primeira ttyUSB/ttyACM/COM)
dumper --json info                          # confirma firmware e sistemas
dumper --json detect -s snes                # saída 2 = sem cartucho: pedir ao usuário para encaixar
dumper --json --progress jsonl dump -s snes -o jogo
                                            # comparar "crc32" com o No-Intro; "checksum":"mismatch" = contato sujo, repetir
dumper --json save-read -s snes -o jogo     # gera jogo.sav
dumper --json save-write -s snes -i jogo.sav --yes
```

Dois `dump` seguidos com o mesmo `crc32` é a prova de leitura estável. Gravar save sobrescreve a memória do cartucho: o agente só deve usar `--yes` com autorização do usuário.

## CLI em Kotlin (`gui/cliApp`)

Mesmo contrato (comandos, opções, JSON, códigos de saída), usando o protocolo do módulo `shared` da GUI. Build: `cd gui && ./gradlew :cliApp:installDist`; binário em `gui/cliApp/build/install/dumper/bin/dumper`. Precisa de JVM 17+.

Diferenças em relação à Python:
- Os textos livres (`message`, `hint`, `status_text`) são em inglês; os erros do dispositivo e do protocolo seguem `--lang` (`en`, `pt-BR`, `ru`, `zh-CN`). Agentes devem usar `ok`, `error.kind` e o código de saída, não o texto.
- Opções são aceitas em qualquer comando (a Python rejeita as que o comando não usa).
- `identify`, `search`, `--db` e `--game` existem nas duas; a Kotlin lê a base com StAX e a Python com `xml.etree`, e os dois acham as mesmas entradas (mesmos testes).
- `errors` lista só `code` e `text` (a dica vem dentro do texto).
- `--simulate` só entende o sistema `mock`; os outros respondem "sem cartucho" (igual à Python).
- Os dois simuladores e as duas CLIs produzem o mesmo CRC32 para o mesmo dado (conferido: `mock` = `D1DF4327`).
- `error.kind` extra: `open_port` (saída 3) quando a porta existe mas não abre (as duas CLIs); `internal` (saída 1) só na Kotlin, para exceção inesperada.

