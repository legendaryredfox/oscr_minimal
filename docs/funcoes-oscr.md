# Funções do OSCR original e onde cada uma mora neste projeto

**Meta (decisão do usuário, 2026-11-03):** ter **todas as funções do OSCR original**. As **únicas** que não entram nas placas são os **botões de operação sem computador** (modo standalone) e o **cartão SD** (o usuário corrigiu uma primeira leitura mais ampla). Parte das funções vai para o computador, que faz o papel da interface e do armazenamento. Levantado em 2026-11-03 lendo os menus e as funções públicas de `firmware/oscr/src/cores/*.cpp` (upstream, commit `d9cb26a`). **Nada disto rodou em hardware.**

## Como dividir firmware e PC

| Fica no firmware (depende do barramento ou de tempo) | Vai para o PC |
|---|---|
| Leitura de ROM e save, laços de endereço e dado | Menus (no lugar dos botões e da tela do aparelho), escolha de sistema, mapper, tamanhos e tipo de chip |
| Apagar e gravar flash: esperas de microssegundos, polling de dados, verificação byte a byte | Escolha e leitura de arquivo (no lugar do cartão SD), cabeçalho iNES, conferência de tamanho antes de gravar |
| Protocolos seriais do cartucho (EEPROM do Mega Drive e do GBA, MBC7, RTC) | Banco de dados (CRC32, nome do jogo, mapper e tamanhos), nome do arquivo |
| Sequências de registrador de cada mapper | Backup do save antes de gravar, verificação depois (reler e comparar), relatório, log |
| Calibração do Si5351, ligar o cartucho | Avisos de segurança (3,3 V, um cartucho por vez), confirmações |

Regra: nada que precise de resposta em microssegundos atravessa a serial (1 Mbaud, ida e volta de milissegundos). Laços de programação de flash ficam no firmware; o PC decide **o que** gravar e confere **depois**.

Legenda: ✅ feito (compila, nunca rodou) · 🔧 em andamento · ⬜ a fazer · ➖ não se aplica a esta placa.

## SNES / SFC

| Função do OSCR | Onde | Estado |
|---|---|---|
| Ler ROM (LoROM, HiROM, ExHiROM, SA-1, SuperFX, S-DD1, SPC7110, Cx4...) | firmware | ✅ |
| Ler e gravar SRAM | firmware | ✅ (conferência no PC) |
| Usar cabeçalho / 4 MB LoROM / 4 MB HiROM / 6 MB ExROM (configuração de tamanho) | PC (`--prg`) | ✅ |
| Teste de RAM (Test RAM) | firmware | ⬜ |
| Flash repro: CFI LoROM e HiROM, **1x 2 MB e 1x 4 MB** | firmware (laço) + PC (arquivo, chip) | ✅ `WRITE_ROM` (D79; nunca rodou); conferência por leitura de volta |
| Flash repro: 2x 2 MB, 2x 4 MB, 4x 2 MB, 1x 8 MB (CFI); LoROM/HiROM (P0), ExLoROM/ExHiROM (P1) | firmware (laço) + PC (arquivo, chip) | ⬜ |
| SF Memory Cassette (SFM): ler jogo, flash, mapeamento, trocar jogo | firmware + PC | ⬜ |
| Satellaview BS-X: ler e gravar Memory Pack, ler e gravar SRAM | firmware + PC | ⬜ |
| Sufami Turbo: ler slot A e B | firmware | ⬜ |
| Game Processor RAM (GPC) | firmware | ⬜ |
| Calibrar o relógio (Si5351) | firmware + PC | ⬜ |
| Cx4, SA-1, S-DD1 etc. com chip especial | firmware | ✅ (ler) |

## NES / Famicom

| Função do OSCR | Onde | Estado |
|---|---|---|
| Ler ROM iNES (PRG + CHR) e ler PRG/CHR separados (raw) | firmware (+ PC monta o iNES) | ✅ iNES; ⬜ raw |
| Ler e gravar PRG-RAM (save) | firmware | ✅ mappers 1, 4, 5, 69, 118; ⬜ o resto (EEPROM mappers 16 e 159, Namco 163, Sunsoft/Taito...) |
| Escolher mapper, tamanhos e RAM (menu + banco CRDB) | **PC** (campos e base NES 2.0) | ✅ |
| Identificar por CRC32 | **PC** (base No-Intro / NES 2.0) | ✅ |
| Navegar a base de dados | **PC** | ✅ (busca) |
| Mappers de leitura além dos 37 já ligados (o upstream trata mais de 100; o 30 entrou em D78) | firmware | ⬜ (ver `docs/limites-nes.md`) |
| Flash repro: NES Maker (SST 39SF040, mapper 30) | firmware (laço) + PC (arquivo) | ✅ `WRITE_ROM` (D77; nunca rodou); conferência por leitura de volta (D78) |
| Flash repro: A29040B (mapper 0, PRG e CHR) | firmware + PC | ✅ `WRITE_ROM` (D77; nunca rodou); conferência por leitura de volta (D78) |
| EEPROM 24C01/24C02 dos mappers 159 e 16 (ler e gravar) | firmware | ⬜ |

## Mega Drive / Genesis

| Função do OSCR | Onde | Estado |
|---|---|---|
| Ler ROM (tamanho pelo cabeçalho, forçar tamanho, SSF2) | firmware | ✅ |
| Ler e gravar SRAM e EEPROM serial (38 checksums do OSCR) | firmware | ✅ |
| Sega CD RAM (BRAM): ler e gravar | firmware | ⬜ |
| Realtec (ler) | firmware | ⬜ |
| Flash repro: MX29F1610 (2 MB) e S29GL064N (4 MB), apagar e gravar | firmware + PC | ✅ `WRITE_ROM` (D81; nunca rodou); conferência por leitura de volta |

## Game Boy Advance

| Função do OSCR | Onde | Estado |
|---|---|---|
| Ler ROM | firmware | ✅ |
| Ler e gravar save: SRAM, FRAM, Flash 64/128 KB, EEPROM 512 B e 8 KB | firmware | ✅ |
| Tipo de save (menu "Set save type") | **PC** (`--mapper`, dica pela ROM) | ✅ |
| Flash repro: Intel 4000/4400, MSP55LV128, MX29GL128E | firmware + PC | ⬜ |
| 369-in-1 (ler e gravar 256 MB, por offset) | firmware + PC | ⬜ |
| GBA Repro (3 V) via slot GB | firmware | ⬜ |

## Game Boy / Game Boy Color (adaptador no slot GBA, 3,3 V)

| Função do OSCR | Onde | Estado |
|---|---|---|
| Ler ROM, ler e gravar SRAM (sem mapper, MBC1, 1M, 2, 3, 5, 6, 7, MMM01, TAMA5, Camera) | firmware | ✅ (MBC6 só leitura; sem RTC) |
| RTC do MBC3, Flash do MBC6, ROM do TAMA5 | firmware | ⬜ |
| Flash repro: 29F/39SF (DIY MBC3, DIY MBC5, HDR MBC30, HDR GB Cam, Orange FM, 39SF MBC5), CFI, CFI + save | firmware + PC | ⬜ |
| GB Smart (Game Menu, Flash Menu, trocar jogo) | firmware + PC | ⬜ |
| NPower GB Memory (ler ID, ler e gravar mapeamento) | firmware + PC | ⬜ |
| Mega Memory (ler e gravar), GBC GameShark (ler e gravar), Datel, Codebreaker, Pelican | firmware + PC | ⬜ |

## Programador de flash genérico (`Flash.cpp`)

| Função do OSCR | Onde | Estado |
|---|---|---|
| CFI, flash de 8 bits, flash de 16 bits, PLCC32 para SNES, EPROM | firmware + PC | ⬜ |
| Por chip: ID, blank check, ler, gravar, apagar, imprimir, verificar | firmware (laços) + PC (arquivo, chip, verificação) | ⬜ |

## Gravação de ROM: o que já existe e o que falta

O protocolo ganhou `WRITE_ROM` (`0x0B`), D77 (`docs/protocolo.md` seção 9; CLI `rom-write`; botão "Gravar ROM" na GUI). Regra de implementação: **chamar as funções do OSCR original** (habilitando o núcleo em `user.ini`) e escrever código próprio só nas costuras. O desenho vale para todos os chips acima:
1. O PC manda `WRITE_ROM` com o sistema, o tamanho e as opções (chip, tamanhos).
2. O firmware roda `rom_prepare` **antes** do primeiro `ACK`: confere o ID do chip e apaga o que for preciso. Só então o PC manda os blocos (a UART do AVR tem 64 bytes e perderia dados durante um apagamento de segundos).
3. `stream_write_rom` consome os blocos e programa com verificação byte a byte, com **limite de tempo** (o OSCR original espera para sempre num chip que não responde).
4. Chip não reconhecido: `ERRO 0x000B`. Nada é gravado.

Cada chip novo é uma rotina em `firmware/oscr/src/dumper/` copiada da sequência do OSCR, mais uma entrada na lista de chips do PC.

## Outros sistemas do OSCR (stubs na GUI)

Arcadia 2001, Atari 2600/5200/7800/8-bit/Jaguar/Lynx, Bally Astrocade, Casio Loopy e PV-1000, Channel F, ColecoVision, Commodore 64 e VIC-20, CPS3, Intellivision, Leapster, Little Jammer e Pro, Nintendo 64, Virtual Boy, Pokémon Mini, Neo Geo Pocket, Odyssey 2, PC Engine, Pocket Challenge W, RCA Studio II, Master System, Super A'can, Watara Supervision, TI-99/4A, Tomy Pyuuta, TRS-80, Vectrex, V.Smile, WonderSwan, MSX. Todos ⬜, cada um com a sua pinagem e (alguns) adaptador; o hardware da placa `completa/` é o ponto de partida.
