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
| `include/cores/MegaDrive.h` | `extern uint16_t eepSize;` |
| `include/dumper/*`, `src/dumper/*` (novos) | `Dumper` (laço de comandos e backend do Mega Drive), `StreamFile`, e cópias de `oscr_proto`/`oscr_session` de `firmware/oscr_serial`. |
| `README-FORK.md` (novo) | Este arquivo. |

Ambiente de compilação: `~/.platformio/penv/bin/pio run -e SerialASCII` (hardware 5, E/S por serial, sem tela nem botões). Medida em 2026-11-03 com o laço de comandos: flash 113.692 bytes (44,8%), RAM 3.091 bytes (37,7%). O upstream puro ocupa 141.824 bytes.

**Estado (ver `docs/fork-oscr.md`):** o Mega Drive está ligado ao protocolo (compila, nunca rodou). SNES, NES/Famicom, GBA e GB/GBC ainda não.
