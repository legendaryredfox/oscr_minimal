# Fork do firmware do OSCR

Decisão do usuário em 2026-11-03 (D65): o firmware do projeto é o **firmware novo do OSCR** (`vendor/oscr/firmware`, commit `d9cb26a` de 2026-07-28, GPL v3, de sanni e da comunidade, https://github.com/oscartreader), copiado para `firmware/oscr/` sem cartão SD, LCD nem botões, com o laço do protocolo serial em `src/dumper/`. O firmware próprio anterior está arquivado em `firmware/arquivo/` (D76). O que mudou no upstream depois de `d9cb26a`: `docs/historico/pesquisas-2026-11.md#upstream-oscr-firmware` (D168). **Validação em hardware:** só um Mega nu, sem shield nem cartucho (D196 a D199); nenhum núcleo rodou com cartucho.

Compilar: `cd firmware/oscr && ~/.platformio/penv/bin/pio run -e SerialASCII` (gravar: `-t upload`, ou `dumper firmware-flash`). Testes no PC: `make -C firmware/oscr/pc-tests test` (protocolo e regras puras de `include/dumper/*Core.h`); o código dos núcleos só roda no AVR.

## 1. O que o fork muda no upstream

Regra: **mudanças mínimas e localizadas**, marcadas com `OSCR_DUMPER` ou com um comentário "fork oscr_minimal". Divergências de cada núcleo: `docs/decisoes.md`.

| Arquivo | Mudança |
|---|---|
| `user.ini` (novo) | Liga os núcleos que o dumper usa (SNES, NES/Famicom, Mega Drive, SMS/GG/SG-1000, N64, GB/GBC/GBA, flash, autoteste, Si5351, Satellaview, SF Memory, Sufami Turbo, GPC e os 19 sistemas da F-20) e fixa o baud em 1.000.000 pelo `monitor_speed` da placa `mega-embed` (vira `OSCR_BAUD`; com `ENABLE_STATIC_BAUD` o `begin(baud)` ignora o argumento, D196) |
| `include/flags.h` | `OSCR_DUMPER` (ligado): sem SD, saída pelo protocolo serial |
| `include/api/Storage.h`, `src/arch/avr/generic/Storage.cpp` | `File` usa `StreamFile` (arquivo virtual) e `sd` vira `StreamSd`; sem inicialização do SD |
| `ClockedSerial` (`include/arch/avr/generic/interfaces/`, `src/...`) | `mute` (a UI de texto não escreve) e `rawWrite` (só o protocolo) |
| `src/ui/interfaces/serial/ascii.cpp` | `_error` marca o erro, `_fatalError` volta ao laço por `longjmp`, `waitButton` não espera |
| `src/main.cpp` | `setup()` chama `Dumper::setup()`; `loop()` chama `Dumper::loop()` no lugar do menu |
| `Serial.cpp`, `OSCR.cpp` | sem as chamadas do `Updater` (D207): elas prendiam todos os `menu()` dos núcleos no LTO |
| `src/apps/Prompts.cpp`, `src/apps/FileBrowser.cpp` | sem usuário: os prompts não esperam; `selectFile` abre o arquivo virtual que o PC manda |
| `src/cores/SelfTest.cpp` | cada achado vai para `Dumper::noteSelfTest()`, que o devolve ao PC no `SELFTEST_RESP` |
| `src/hardware/peripherals/ClockGen.cpp` | `ClockGen::initialize()` lê o fator de correção da EEPROM (`Dumper::clockOffset()`, comando `CLOCK`) no lugar do `snes_clk.txt` do SD (D167) |
| Núcleos (`src/cores/*.cpp`) | as consultas ao banco do SD (`matchCRC`, `compareCRC`, `checkAltConf`) sob `#if !OSCR_DUMPER` (D215, D225); `readROM` do GB e do GBA termina no último byte; cabeçalhos com `extern` das variáveis que o laço precisa (`eepSize`, `romBanks`, `sramBanks`...) |
| `include/dumper/*`, `src/dumper/*` (novos) | `Dumper` (laço de comandos e costuras de cada sistema), `StreamFile`, `oscr_proto`/`oscr_session` (o protocolo), regras puras `*Core.h` |

Perfil da placa (`BOARD`, D162): `Dumper.cpp` guarda na EEPROM (endereço 4064: magic `0xB5`, versão 1, flags, flags invertidos) se a placa tem o seletor de tensão; uma imagem só serve as placas com e sem seletor (`voltSelect` é só o padrão sem perfil). O OSCR só usa o endereço 0. Versão do firmware no `INFO`: 0.2.0.

## 2. Como o fluxo serial se comporta

- Os núcleos empurram os bytes durante a leitura (modo fluxo do protocolo): `createFile` vira o `BEGIN` (tamanho `0xFFFFFFFF` quando o núcleo ainda não sabe), `write` vira blocos `DATA` com `ACK`, `close` vira o `END` com o tamanho e o CRC32 reais. No `WRITE_SAVE`, o `ACK` de cada bloco só sai depois que o núcleo consumiu o bloco, para o PC não encher a UART (64 B).
- Cada arquivo que o núcleo abre para escrita grava no **mesmo** fluxo: dois arquivos num comando se concatenam.
- A releitura que alguns núcleos fazem depois do dump (somar checksum, conferir um save gravado) devolve 0 bytes: o CRC32 vai no `END`, e o PC relê o save depois de gravar para conferir.
- Um `longjmp` por cima do código dos núcleos pula destrutores; o laço sempre chama `Power::disableCartridge()` depois.

## 3. Banco de dados: só no computador (D66, D76, D127, D225)

O firmware não carrega a base de cartuchos (CRDB) nem o SdFat: no `DETECT` devolve nome do cabeçalho, tamanhos e checksum, e no `END` o CRC32. O host e a GUI identificam o jogo pela base local (No-Intro `.dat`, NES 2.0 XML, a base do OSCR em `database/oscr/`) e, no NES, escolhem mapper e tamanhos pela base e os mandam no `DUMP_ROM`. Conferido em D225: os fontes `src/common/CRDB.cpp`, `src/common/crdb/` e `src/apps/CRDBBrowser.cpp` ainda compilam (os menus dos núcleos os citam), mas o linker os descarta; sobram os ponteiros `romDetail` e `mapperDetail` (4 B de RAM).

## 4. Orçamento de flash e RAM

`python3 tools/flash_budget.py check` falha acima de 95 % do flash ou 80 % da RAM (a pilha precisa de folga) e roda para `SerialASCII` e `SerialASCII_Volt`; `flash_budget.py measure` soma o tamanho dos símbolos do `firmware.elf` por namespace (`avr-nm -S -C`; o que o LTO embutiu conta no chamador, então o valor de cada núcleo é um piso). Medido em 2026-11-27 (D228): **195.658 B de flash (77,0 %) e 4.462 B de RAM (54,5 %)**; sobram 58 KB até o limite. **Imagem única** enquanto couber (regra do usuário, D162): `tools/build_images.py` gera `firmware/images/` com o `.hex` e o manifest que a GUI e a CLI gravam.

Não dá para medir "sem o núcleo X" desligando-o no `user.ini`: `src/dumper/` chama os núcleos sem `#if`. Uma variante exigiria primeiro condicionar essas chamadas.
