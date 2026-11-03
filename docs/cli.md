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
| `systems` | `systems`: `[{name, id, extension, options, needs_cartridge}]`; `options` diz quais de `--mapper`, `--prg`, `--chr`, `--ram` o sistema usa |
| `errors` | `device_errors`, `exit_codes` |
| `info` | `proto`, `firmware`, `mock`, `si5351`, `systems`, `max_payload` |
| `detect -s SISTEMA` | `status`, `status_text`, `system`, `name`, `rom_size`, `save_size`. `ok` é `false` e a saída é 2 se não houver cartucho |
| `dump -s SISTEMA [-o ARQ]` | `file`, `bytes`, `crc32` (hex maiúsculo, 8 dígitos), `checksum` (`ok`, `mismatch`, `na`), e `gba_save_type` no GBA |
| `save-read -s SISTEMA [-o ARQ]` | `file`, `bytes`, `crc32` |
| `save-write -s SISTEMA -i ARQ --yes` | `backup` (arquivo do save anterior, salvo antes de gravar, a menos que `--no-backup`), `bytes`, `crc32` |

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
- `errors` lista só `code` e `text` (a dica vem dentro do texto).
- `--simulate` só entende o sistema `mock`; os outros respondem "sem cartucho" (igual à Python).
- Os dois simuladores e as duas CLIs produzem o mesmo CRC32 para o mesmo dado (conferido: `mock` = `D1DF4327`).
- `error.kind` extra: `open_port` (saída 3) quando a porta existe mas não abre (as duas CLIs); `internal` (saída 1) só na Kotlin, para exceção inesperada.

