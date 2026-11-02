# Guia de uso: casos de uso, cenários e solução de problemas

Este guia vale para a **GUI** (`gui/`, aba "Ajuda" também traz um resumo em português, inglês, russo e chinês) e para a **CLI** (`host/dumper.py`). Montagem da placa: `docs/montagem.md`. Protocolo: `docs/protocolo.md`.

> **Estado do firmware:** a leitura dos cartuchos (SNES, NES/Famicom, Mega Drive, GBA) foi escrita a partir das sequências do OSCR e a lógica foi testada no PC com cartuchos simulados, mas **ainda não foi validada com hardware real**. Faça primeiro a seção 7.

## 1. Antes de começar

1. Placa montada e testada (`docs/montagem.md`, seções 4 a 7).
2. Mega com o firmware gravado (`firmware/README.md`):
   - `arduino-cli upload ...` ou `pio run -t upload`.
   - Para testar o cabo sem cartucho, grave a versão de teste (`-DOSCR_MOCK` / ambiente `megaatmega2560_mock`).
3. Cabo USB-C **de dados**. No Linux: `sudo usermod -aG dialout $USER` e reinicie a sessão. Clone com CH340: driver no Windows/macOS.
4. **Um cartucho por vez. Desligue o USB antes de trocar de cartucho.** O slot GBA é 3,3 V: só cartuchos GBA nele.

Interfaces:

| | GUI | CLI |
|---|---|---|
| Abrir | `cd gui && ./gradlew :desktopApp:run` | `python host/dumper.py --help` |
| Escolher porta | lista de portas + "Atualizar" | `--port /dev/ttyUSB0` (ou automático) |
| Detectar | botão **Detectar** | `dumper.py detect -s snes` |
| Ler ROM | **Ler ROM** | `dumper.py dump -s snes -o jogo` (acrescenta `.sfc`) |
| Ler save | **Ler save** | `dumper.py save-read -s snes -o jogo` |
| Gravar save | **Gravar save** | `dumper.py save-write -s snes -i jogo.sav` |
| Sem hardware | (não há) | `dumper.py --simulate dump -s mock` |

Sistemas: `snes`, `nes`, `famicom`, `md`, `gba` (`mock` só no firmware de teste).

## 2. Casos de uso principais

### 2.1 Ler uma ROM e conferir o CRC32
1. Desligue o USB, insira o cartucho, ligue o USB.
2. Conecte (GUI: porta + **Conectar**; CLI: automático).
3. **Detectar**: mostra título, tamanho da ROM e do save.
4. **Ler ROM** e escolha onde salvar. A extensão vem do sistema (`.sfc`, `.nes`, `.md`, `.gba`).
5. A GUI e a CLI mostram o **CRC32** (8 dígitos hexadecimais). Compare com o banco No-Intro (por exemplo, no DAT do sistema). Igual = dump íntegro e idêntico ao original.

### 2.2 Fazer backup do save (jogos com bateria)
Hoje só o **SNES** tem leitura/gravação de save. Faça o backup **antes** de trocar a bateria do cartucho (a troca apaga a SRAM): **Ler save**, guarde o `.sav` em dois lugares.

### 2.3 Restaurar um save
**Gravar save** com um arquivo **do tamanho exato** do save (o **Detectar** mostra o tamanho). O firmware só grava depois de conferir o CRC32 do arquivo e lê de volta o que gravou. Se algo falhar, a mensagem de erro diz onde.

### 2.4 Conferir um cartucho antes de comprar ou vender
**Detectar** mostra título e tamanhos; **Ler ROM** + CRC32 confirmam se é a ROM esperada. Um CRC diferente pode ser outra revisão/região, ROM modificada ou contato sujo (releia 3 vezes).

### 2.5 Testar o cabo e o computador sem cartucho
Grave o firmware de teste (`OSCR_MOCK`). Selecione `mock`, **Ler ROM**: deve dar 32.768 bytes e CRC32 `D1DF4327`. Se funcionar, cabo, driver e permissões estão certos.

### 2.6 Ler uma ROM de NES/Famicom com mapper
Exemplo (Mega Man 3, MMC3, 256 KB de PRG e 128 KB de CHR): `dumper.py dump -s nes --mapper 4 --prg 256 --chr 128 -o megaman3`. Se os tamanhos estiverem errados a ROM sai com o CRC32 errado: confira no banco. Se `0x0002` (mapper não suportado) ou `0x0004` (tamanho inválido), veja a seção 4.

### 2.7 Usar vários sistemas na mesma sessão
Troque o sistema na lista; para trocar de **cartucho** desligue o USB (seção 1). SNES, NES e Famicom usam 5 V; GBA 3,3 V. Nunca com dois cartuchos nos slots.

## 3. Cenários por sistema (o que é suportado hoje)

| Sistema | ROM | Save | Observações |
|---|---|---|---|
| SNES/SFC | LoROM e HiROM até 4 MB | SRAM (ler e gravar) | Detecta pelo checksum do cabeçalho. **Não** lê SA-1, ExHiROM, S-DD1, SuperFX e outros chips especiais. |
| NES | mappers 0, 1 (MMC1, PRG até 256 KB), 2, 3, 4 (MMC3) e 7 | não | Mapper 0 é automático. Para os demais, **informe mapper, PRG e CHR em KB** (GUI: campos "Opções NES/Famicom"; CLI: `--mapper 4 --prg 128 --chr 128`), de uma fonte confiável (No-Intro/NESCartDB). Gera cabeçalho iNES (espelhamento e bateria saem 0; ajuste no emulador se preciso). Mappers 2 e 7 usam CHR-RAM (`--chr 0`). |
| Famicom | os mesmos do NES | não | Mesmo código do NES. |
| Mega Drive | ROM até 4 MB (tamanho do cabeçalho) | não | Precisa da palavra "SEGA" no cabeçalho. Jogos com mapper (SSF2) e SRAM ainda não. |
| GBA | ROM de 256 KB até 32 MB (tamanho por espelhamento) | só **leitura** de 32 KB, assumindo SRAM | Só cartuchos GBA, 3,3 V. O firmware não sabe se o save é SRAM, Flash ou EEPROM: em jogos com Flash ou EEPROM o arquivo lido **não vale**. Gravação de save do GBA não é suportada (risco com cartuchos Flash). |
| GB/GBC | não | não | Reservado (precisa de adaptador no slot GBA). |

Sistemas ou cartuchos fora disso: o firmware responde "sistema não suportado" (código `0x0002`).

## 4. Solução de problemas (básico)

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Nenhuma porta aparece | cabo só de carga; falta de permissão; driver | Troque o cabo; Linux: grupo `dialout`; clone com CH340 pede driver (Windows/macOS). Em `ls /dev/ttyUSB* /dev/ttyACM*` o clone aparece como `ttyUSB0`. |
| "sem resposta do dispositivo" ao conectar | firmware não gravado; baud errado; porta ocupada | Regrave o firmware; tente `--baud 115200`; feche monitor serial/IDE; reconecte o cabo. |
| Detecta "nenhum cartucho" | encaixe, contatos, sistema errado | Encaixe até o fim; limpe com álcool isopropílico; confira o sistema na lista; teste outro cartucho. |
| "sistema não suportado" (`0x0002`) | chip especial / mapper fora da lista | Veja a seção 3. NES: mappers 0, 1, 2, 3, 4 e 7. |
| NES: "argumento inválido" (`0x0004`) | PRG/CHR errados para o mapper | PRG múltiplo de 16 KB (7: de 32 KB), CHR múltiplo de 8 KB; mappers 2 e 7 sem CHR; MMC1 até 256 KB. |
| CRC32 diferente do No-Intro | contato sujo; revisão diferente; ROM não suportada | Limpe, leia 3 vezes (se mudar a cada leitura, é contato); confira região/revisão no DAT. |
| Leitura trava ou dá "reenvios excedidos" (`0x0005`) | cabo ruim, hub USB, ruído | Cabo curto e direto no PC; evite hubs; tente `--baud 115200`. |
| "CRC32 do arquivo não confere" (`0x0006`) | corrupção no USB | Repita a operação; troque o cabo. |
| "erro de leitura/gravação no cartucho" (`0x0007`) | contato, bateria, cartucho com defeito | Limpe os contatos; no save, confira a bateria e o tamanho do arquivo. |
| Gravação do save recusada (`0x0004`) | tamanho diferente do save do cartucho | Use um arquivo com exatamente o tamanho mostrado em **Detectar**. |
| Placa esquenta, cheiro, LED sem acender | curto | Desligue o USB já. Refaça os testes de `docs/montagem.md` (seção 5). |
| GBA não lê | cartucho de outro sistema; solda do slot | Só cartucho GBA; confira a solda dos pads de 1,5 mm e a tensão de 3,3 V no pino 1. |

Códigos de erro do protocolo: `docs/protocolo.md`, seção 8. Na CLI, o código de saída é 1 em erro, 2 se não houver cartucho.

## 5. Dicas

- Leia cada cartucho **duas ou três vezes** e confira que o CRC32 é o mesmo.
- Guarde as ROMs com o nome do No-Intro; o CRC32 mostrado é o da ROM completa.
- Para contribuir com um erro, anexe: sistema, título, saída do **Detectar**, versão do firmware (`dumper.py info`) e a mensagem exata.

## 6. Limites e segurança

- Um cartucho por vez; USB desligado ao trocar.
- Nunca insira cartucho de outro console no slot GBA (3,3 V).
- Cartuchos SNES com chip especial e jogos raros podem exigir leitura adicional (futura).
- Gravar save é irreversível para o conteúdo anterior: faça backup antes.

## 7. Primeira validação com hardware (para quem montou a placa)

Faça nesta ordem e anote o resultado em `docs/decisoes.md`:

1. Firmware de teste (`OSCR_MOCK`): `dumper.py dump -s mock` dá CRC32 `D1DF4327`.
2. Firmware real. `dumper.py info` mostra "sistemas: snes, nes, famicom, md, gba".
3. **SNES LoROM simples:** `detect -s snes`, depois `dump`. Compare com o No-Intro.
4. **NES mapper 0** (por exemplo, Super Mario Bros.): idem. Depois um de cada mapper 1, 2, 3, 4 e 7. Compare o CRC32 da ROM completa (com cabeçalho iNES de 16 bytes, o No-Intro mostra o CRC do conjunto PRG+CHR sem cabeçalho: confira os dois).
5. Mega Drive, Famicom e GBA.
6. Save SNES: leia, faça backup, grave de volta o mesmo arquivo e leia de novo (devem ser iguais).

Se algum sistema falhar, o ponto a olhar é o HAL em `firmware/oscr_serial/oscr_avr_buses.h` (tempos e linhas de controle), comparando com `SNES.ino`, `NES.ino`, `MD.ino` e `GBA.ino` do OSCR e com `docs/pinmap.md`.
