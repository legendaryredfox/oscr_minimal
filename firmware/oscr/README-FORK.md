# Fork do firmware do OSCR para o shield dumper (oscr_minimal)

Este diretório é uma cópia do firmware novo do OSCR (`vendor/oscr/firmware`, commit `d9cb26a`, 2026-07-28), GPL v3, de sanni e da comunidade (https://github.com/oscartreader). A licença original está em `LICENSE`.

Regra do fork: **mudanças mínimas e localizadas**. O que mudou em relação ao upstream:

| Arquivo | Mudança |
|---|---|
| `user.ini` (novo) | Desliga os núcleos N64, SMS e autoteste (`[cores]`). Ficam SNES, NES/Famicom, Mega Drive e GB/GBC/GBA (`gbx`). |
| `include/flags.h` | `OSCR_DUMPER` (ligado): sem SD, saída pelo protocolo serial. |
| `include/api/Storage.h`, `src/arch/avr/generic/Storage.cpp` | `File` usa `StreamFile` (arquivo virtual) e `sd` vira `StreamSd`; sem inicialização do SD. |
| `include/arch/avr/generic/interfaces/ClockedSerial.h`, `src/.../ClockedSerial.cpp` | `mute` (a UI de texto não escreve) e `rawWrite` (só o protocolo). |
| `src/ui/interfaces/serial/ascii.cpp` | `_error` marca o erro, `_fatalError` volta ao laço por `longjmp`, `waitButton` não espera. |
| `src/main.cpp` | `setup()` chama `Dumper::setup()`; `loop()` chama `Dumper::loop()` no lugar do menu. |
| `include/cores/MegaDrive.h`, `include/cores/GameBoy.h` | `extern` de `eepSize`, `romBanks` e `sramBanks` (o laço de comandos precisa deles). |
| `src/cores/GameBoyAdvance.cpp`, `src/cores/GameBoy.cpp` | `readROM` termina depois do último byte (sem reler o arquivo nem a base de dados). |
| `src/apps/Prompts.cpp`, `src/apps/FileBrowser.cpp` | Sem usuário: os prompts não esperam; `selectFile` abre o arquivo virtual que o PC manda. |
| `src/cores/SNES.cpp` | Sem `checkAltConf` (base de dados); o tamanho vem do cabeçalho ou da opção `prg_kb`. |
| `include/dumper/*`, `src/dumper/*` (novos) | `Dumper` (laço de comandos e backend do Mega Drive), `StreamFile`, e `oscr_proto`/`oscr_session` (o protocolo; vieram de `firmware/arquivo/oscr_serial` e agora evoluem aqui, com testes em `pc-tests/`). |
| `README-FORK.md` (novo) | Este arquivo. |

Ambiente de compilação: `~/.platformio/penv/bin/pio run -e SerialASCII` (hardware 5, E/S por serial, sem tela nem botões). Medida em 2026-11-03 com o laço de comandos: flash 118.572 bytes (46,7%), RAM 3.147 bytes (38,4%). O upstream puro ocupa 141.824 bytes.

**Estado (ver `docs/referencia/fork-oscr.md`):** SNES, Mega Drive, GBA e GB/GBC estão ligados ao protocolo (compila, nunca rodou). NES/Famicom ainda não.
- `user.ini`: `flash = true` (D77) liga o núcleo de flash do OSCR; `src/dumper/NesFlash.cpp` + `include/dumper/NesFlash.h` gravam ROM em NES Maker e A29040B chamando as funções do `NES.cpp` original (`WRITE_ROM`).

