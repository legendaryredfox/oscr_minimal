# Fork do firmware do OSCR para o shield dumper (oscr_minimal)

Este diretório é uma cópia do firmware novo do OSCR (`vendor/oscr/firmware`, commit `d9cb26a`, 2026-07-28), GPL v3, de sanni e da comunidade (https://github.com/oscartreader). A licença original está em `LICENSE`.

Regra do fork: **mudanças mínimas e localizadas**. O que mudou em relação ao upstream:

| Arquivo | Mudança |
|---|---|
| `user.ini` (novo) | Desliga os núcleos N64, SMS e autoteste (`[cores]`). Ficam SNES, NES/Famicom, Mega Drive e GB/GBC/GBA (`gbx`). |
| `README-FORK.md` (novo) | Este arquivo. |

Ambiente de compilação: `~/.platformio/penv/bin/pio run -e SerialASCII` (hardware 5, E/S por serial, sem tela nem botões). Medida em 2026-11-03: flash 124.660 bytes (49,1%), RAM 2.676 bytes (32,7%), contra 141.824 bytes do upstream sem os ccortes.

**O que ainda falta (ver `docs/fork-oscr.md`):** o upstream grava os dumps no cartão SD. O shield não tem SD, então o `OSCR::Storage` precisa ser trocado por uma saída serial no nosso protocolo (`docs/protocolo.md`).
