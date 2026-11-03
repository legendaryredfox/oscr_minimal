# Guia de uso: casos de uso, cenários e solução de problemas

Este guia vale para a **GUI** (`gui/`, aba "Ajuda" também traz um resumo em português, inglês, russo e chinês) e para a **CLI** (`host/dumper.py`). Montagem da placa: `docs/montagem.md`. Protocolo: `docs/protocolo.md`.

> **Estado do firmware:** a leitura dos cartuchos (SNES, NES/Famicom, Mega Drive, GBA) foi escrita a partir das sequências do OSCR e a lógica foi testada no PC com cartuchos simulados, mas **ainda não foi validada com hardware real**. Faça primeiro a seção 7.

## 1. Antes de começar

1. Placa montada e testada (`docs/montagem.md`, seções 4 a 7).
2. Mega com o firmware gravado (`firmware/README.md`):
   - `arduino-cli upload ...` ou `pio run -t upload`.
   - Para testar o cabo sem cartucho, grave a versão de teste (`-DOSCR_MOCK` / ambiente `megaatmega2560_mock`).
3. Cabo USB-C **de dados**. No Linux: `sudo usermod -aG dialout $USER` e reinicie a sessão. Clone com CH340: driver no Windows/macOS.
4. **Um cartucho por vez. Desligue o USB antes de trocar de cartucho.** O slot GBA é 3,3 V: só cartuchos GBA nele, ou Game Boy/Color pelo adaptador.

Interfaces:

| | GUI | CLI |
|---|---|---|
| Abrir | `cd gui && ./gradlew :desktopApp:run` | `python host/dumper.py --help` |
| Escolher porta | lista de portas + "Atualizar" | `--port /dev/ttyUSB0` (ou automático) |
| Detectar | botão **Detectar** | `dumper.py detect -s snes` |
| Ler ROM | **Ler ROM** | `dumper.py dump -s snes -o jogo` (acrescenta `.sfc`) |
| Ler save | **Ler save** | `dumper.py save-read -s snes -o jogo` |
| Gravar save | **Gravar save** (pede confirmação e guarda um backup do save atual em `~/oscr_backups`) | `dumper.py save-write -s snes -i jogo.sav` (pergunta antes; `--yes` para scripts, `--no-backup`, `--backup-dir`) |
| Sem hardware | (não há) | `dumper.py --simulate dump -s mock` |

Sistemas: `snes`, `nes`, `famicom`, `md`, `gba`, `gb` (`mock` só no firmware de teste).

Na CLI, `--json` (antes do comando) imprime o resultado em uma linha de JSON, para scripts; `dump` sem `-o` usa o título detectado como nome do arquivo (`.gbc` para jogos de Game Boy Color).

**GUI:** a barra de baixo mostra sempre o estado, o progresso (com velocidade e tempo restante) e o registro, que pode ser **copiado** ou **salvo** (útil para pedir ajuda). Uma leitura pronta fica na memória até você escolher onde salvar (cancelar o "Salvar como" não perde nada). Atalhos: Ctrl+D detectar, Ctrl+R ler ROM, Ctrl+S ler save, Esc cancelar. A janela lembra idioma, porta, sistema, pasta e tamanho.

## 2. Casos de uso principais

### 2.1 Ler uma ROM e conferir o CRC32
1. Desligue o USB, insira o cartucho, ligue o USB.
2. Conecte (GUI: porta + **Conectar**; CLI: automático).
3. **Detectar**: mostra título, tamanho da ROM e do save.
4. **Ler ROM** e escolha onde salvar. A extensão vem do sistema (`.sfc`, `.nes`, `.md`, `.gba`).
5. A GUI e a CLI mostram o **CRC32** (8 dígitos hexadecimais). Compare com o banco No-Intro (por exemplo, no DAT do sistema). Igual = dump íntegro e idêntico ao original.

### 2.2 Fazer backup do save (jogos com bateria)
Hoje **SNES**, **Mega Drive**, **NES/Famicom** (mappers 1, 4, 5 e 69) e **GBA** têm leitura/gravação de save (incluindo a EEPROM serial do Mega Drive). No NES informe o mapper: `dumper.py save-read -s nes --mapper 4 -o jogo`. RAM de 16 KB (MMC1 SOROM, MMC5) ou 32 KB (MMC1 SXROM, MMC5; confira o tamanho da RAM no banco do jogo) só nos mappers 1 e 5: acrescente `--ram 16` ou `--ram 32` (GUI: campo "RAM (KB)"); sem isso lê 8 KB. Use o mesmo `--ram` em `save-write`: o arquivo precisa ter exatamente esse tamanho. Faça o backup **antes** de trocar a bateria do cartucho (a troca apaga a SRAM): **Ler save**, guarde o `.sav` em dois lugares.

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
| SNES/SFC | LoROM e HiROM até 4 MB; **ExHiROM** (mapa `$25`/`$35`) até 7,875 MB | SRAM (ler e gravar; HiROM e ExHiROM com o CS elevado, como o OSCR) | Detecta pelo checksum do cabeçalho. ExHiROM: se o cabeçalho diz 8 MB, o firmware lê **6 MB** (os ExHiROM conhecidos de mais de 4 MB têm 48 Mbit); para outro tamanho informe `--prg KB` (múltiplo de 64, até 8064; GUI: "Tamanho da ROM"). **SA-1** (Super Mario RPG, Kirby Super Star...): lê a ROM e **lê e grava** a BW-RAM, **só com o módulo Si5351 e o PIC montados** (o firmware liga os clocks e o CIC sozinho quando não acha um cabeçalho; a detecção demora ~1,2 s a mais). Sem o Si5351 aparece como "sem cartucho". **SuperFX** (Star Fox, Yoshi's Island...), **S-DD1** (Star Ocean, Street Fighter Alpha 2), **SPC7110** e **Cx4** (Mega Man X2 e X3): ROM e SRAM, pelas trocas de registrador do OSCR (ver D55). LoROM de mais de 3 MB sai dos bancos `$80+`. **Não** lê Derby Stallion 96, S-RTC (Daikaijuu Monogatari II), OBC1, ST018 e outros chips raros. |
| NES | mappers 0, 1 (MMC1, PRG até 256 KB), 2, 3, 4 (MMC3), 5 (MMC5), 7, 9 (MMC2), 10 (MMC4), 11 (Color Dreams), 33 e 48 (Taito TC0190), 66 (GxROM), 69 (FME-7), 70, 71 (Camerica), 75 (VRC1), 78, 79 (NINA-003/006), 87, 118 (TxSROM) e 206 (Namco 108/DxROM) | **8 KB** de PRG-RAM com bateria nos mappers 1, 4, 5 (MMC5) e 69 (FME-7) (ler e gravar; informe o mapper); mappers 1 e 5 também **16 e 32 KB** (`--ram`) | Mapper 0 é automático. Para os demais, **informe mapper, PRG e CHR em KB** (GUI: campos "Opções NES/Famicom"; CLI: `--mapper 4 --prg 128 --chr 128`), de uma fonte confiável (No-Intro/NESCartDB). Gera cabeçalho iNES (espelhamento e bateria saem 0; ajuste no emulador se preciso). Mappers 2, 7 e 71 usam CHR-RAM (`--chr 0`). Saves: mappers 1, 4, 5, 69 e 118. |
| Famicom | os mesmos do NES | os mesmos do NES | Mesmo código do NES. |
| Mega Drive | ROM pelo tamanho do cabeçalho: até 4 MB; até 8 MB com mapper SSF2 (cabeçalho "SEGA SSF", como Super Street Fighter II) | SRAM de 8 bits (bytes ímpares ou pares) ou de 16 bits, **lida e gravada**, pelo que o cabeçalho declara; **EEPROM serial lida e gravada** (ver abaixo) | Precisa da palavra "SEGA" no cabeçalho. Se o cabeçalho declara mais do que a ROM tem (ROM espelhada), o firmware reduz sozinho; para forçar, informe o tamanho em KB (GUI: "Tamanho da ROM"; CLI: `--prg 512`). EEPROM serial (jogos da tabela do OSCR, achados pelo checksum do cabeçalho: NBA Jam, NFL Quarterback Club, Wonder Boy in Monster World, Madden 93, Micro Machines 2 e outros ~38 checksums): o `DETECT` mostra o tamanho do save (128 B a 8 KB) e `save-read` faz o backup, devagar (byte a byte). `save-write` grava só os bytes que mudaram, esperando o ciclo de escrita (10 ms por byte, 20 ms nas de 128 e 256 bytes) e conferindo cada um; uma EEPROM de 8 KB totalmente diferente leva ~2 minutos. Faça o backup antes e não desligue o USB durante a gravação. Sem suporte: Pier Solar, Sonic 3 / Sonic & Knuckles (lock-on) e mappers piratas. A gravação confere cada byte depois de gravar. |
| GBA | ROM de 256 KB até 32 MB (tamanho por espelhamento) | **lida e gravada**: SRAM/FRAM 32 KB, Flash 64 KB e 128 KB, EEPROM 512 B e 8 KB | Só cartuchos GBA, 3,3 V. O tipo de save **não é detectado pelo cartucho**: depois do dump da ROM o programa procura a cadeia da biblioteca de save (`FLASH1M_V`, `EEPROM_V`...) e diz o tipo a usar. Informe-o em `save-read`/`save-write --mapper N` (CLI) ou no campo "Tipo de save" (GUI): 1 = EEPROM 512 B, 2 = EEPROM 8 KB, 3 = SRAM (padrão), 4 = Flash 64 KB, 5 = Flash 128 KB. **Gravar:** faça o backup antes (**Ler save**) e use o tipo certo; num cartucho SRAM, escolher Flash escreve alguns bytes de comando no save. A Flash é identificada (Atmel, SST, Macronix, Panasonic, Sanyo) e chip desconhecido é recusado; os demais são apagados inteiros, conferidos como vazios e gravados byte a byte (o Atmel grava páginas de 128 bytes sem apagar). Tudo é conferido depois de gravar. EEPROM e Flash demoram (EEPROM de 8 KB: ~10 s; Flash: alguns segundos para apagar). Não desligue o USB durante a gravação: se ela parar no meio, o save fica incompleto. e-Reader: os últimos 128 bytes de cada banco não são gravados. |
| GB/GBC | sem mapper e MBC1 (inclui MBC1M das 6 coletâneas conhecidas), MBC2, MBC3, MBC5, GB Camera, HuC1/HuC3 (tratados como MBC3/5), ROM de 32 KB a 8 MB | **lida e gravada** a SRAM (2, 8, 32, 64 e 128 KB; 512 nibbles do MBC2; GB Camera): `save-read`/`save-write -s gb`. **Sem** o relógio (RTC) do MBC3 | **Precisa do adaptador GB/GBC no slot GBA**, que é **3,3 V**: a maioria dos cartuchos lê bem, mas alguns de GB antigos podem falhar (o OSCR usa 5 V). Detecta pelo checksum do cabeçalho. **Não** lê MBC6, MBC7, MMM01, TAMA5, M161, flash repro, Pocket Camera com RTC, nem ROMs de 1,1/1,2/1,5 MB. Salva `.gb`; renomeie para `.gbc` se for GBC. |

Sistemas ou cartuchos fora disso: o firmware responde "sistema não suportado" (código `0x0002`).

Depois de cada dump o programa confere o **checksum do cabeçalho** (Mega Drive, SNES e GBA) e avisa se não confere. Isso ajuda a achar tamanho errado ou contato sujo, mas não substitui o CRC32 do No-Intro: algumas ROMs têm o checksum errado de fábrica.

## 4. Solução de problemas (básico)

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Nenhuma porta aparece | cabo só de carga; falta de permissão; driver | Troque o cabo; Linux: grupo `dialout`; clone com CH340 pede driver (Windows/macOS). Em `ls /dev/ttyUSB* /dev/ttyACM*` o clone aparece como `ttyUSB0`. |
| "sem resposta do dispositivo" ao conectar | firmware não gravado; baud errado; porta ocupada | Regrave o firmware; tente `--baud 115200`; feche monitor serial/IDE; reconecte o cabo. |
| Detecta "cabeçalho inválido" (status 4) | há dados no cartucho, mas o checksum do cabeçalho não confere | Contato sujo quase sempre: limpe, encaixe de novo e repita; em ROM de hack o checksum pode estar errado de fábrica |
| Detecta "nenhum cartucho" | encaixe, contatos, sistema errado | Encaixe até o fim; limpe com álcool isopropílico; confira o sistema na lista; teste outro cartucho. |
| "sistema não suportado" (`0x0002`) | chip especial / mapper fora da lista | Veja a seção 3. NES: mappers 0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 33, 48, 66, 69, 70, 71, 75, 78, 79, 87, 118 e 206. |
| NES: "argumento inválido" (`0x0004`) | PRG/CHR errados para o mapper | PRG múltiplo de 16 KB (7, 11 e 66: de 32 KB), CHR múltiplo de 8 KB; mappers 2, 7 e 71 sem CHR; limites: MMC1 256 KB, mapper 9 PRG 128 KB, 10 PRG 256 KB, 11 PRG e CHR 128 KB, 66 PRG 128 KB e CHR 32 KB, 69 PRG 512 KB, 5 PRG 1 MB (acima disso `0x0002`). |
| Aviso "checksum do cabeçalho NÃO confere" | tamanho errado, contato sujo, ROM modificada (ou checksum ruim de fábrica) | Leia de novo; se for Mega Drive, tente informar o tamanho; compare o CRC32 com o No-Intro. |
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
4. **NES mapper 0** (por exemplo, Super Mario Bros.): idem. Depois um de cada mapper 1, 2, 3, 4, 7 e, se tiver, 5, 9, 10, 11, 66, 69 e 71. Compare o CRC32 da ROM completa (com cabeçalho iNES de 16 bytes, o No-Intro mostra o CRC do conjunto PRG+CHR sem cabeçalho: confira os dois).
5. Mega Drive, Famicom e GBA.
6. Save SNES: leia, faça backup, grave de volta o mesmo arquivo e leia de novo (devem ser iguais).

Se algum sistema falhar, o ponto a olhar é o HAL em `firmware/oscr_serial/oscr_avr_buses.h` (tempos e linhas de controle), comparando com `SNES.ino`, `NES.ino`, `MD.ino` e `GBA.ino` do OSCR e com `docs/pinmap.md`.
