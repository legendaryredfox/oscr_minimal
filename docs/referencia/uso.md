# Guia de uso: casos de uso, cenários e solução de problemas

Este guia vale para a **GUI** (`gui/`, aba "Ajuda" também traz um resumo em português, inglês, russo e chinês) e para a **CLI** (`host/dumper.py`). Montagem da placa: `boards/16_and_8_bits/docs/montagem.md`. Protocolo: `docs/referencia/protocolo.md`.

> **Estado do firmware:** a leitura dos cartuchos (SNES, NES/Famicom, Mega Drive, GBA) foi escrita a partir das sequências do OSCR e a lógica foi testada no PC com cartuchos simulados, mas **ainda não foi validada com hardware real**. Faça primeiro a seção 7.

## 1. Antes de começar

1. Placa montada e testada (`boards/16_and_8_bits/docs/montagem.md`, seções 4 a 7).
2. Mega com o firmware gravado (`firmware/README.md`):
   - `arduino-cli upload ...` ou `pio run -t upload`.
   - Para testar o cabo sem cartucho, grave a versão de teste (`-DOSCR_MOCK` / ambiente `megaatmega2560_mock`).
3. Cabo USB-C **de dados**. No Linux: `sudo usermod -aG dialout $USER` e reinicie a sessão. Clone com CH340: driver no Windows/macOS.
4. **Um cartucho por vez. Desligue o USB antes de trocar de cartucho** (a placa não corta o 5V por software: o desligamento por software foi retirado, D139). O slot GBA é 3,3 V: só cartuchos GBA nele, ou Game Boy/Color pelo adaptador.

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

### 2.6b Gravar a ROM em um cartucho repro de flash

**APAGA a ROM atual do cartucho.** Nunca rodou em hardware: teste primeiro num repro barato e sem valor.

- **NES/Famicom:** NES Maker (mapper 30, até 512 KB) e A29040B (mapper 0, 16/32 KB + CHR 0/8 KB). `dumper rom-write -s nes -i jogo.nes --yes`; o chip sai do mapper do cabeçalho.
- **SNES:** repro com **um chip de flash CFI de 2 ou 4 MB**. Você escolhe a fiação do cartucho: `dumper rom-write -s snes -i jogo.sfc --chip snes-lorom --yes` (ou `snes-hirom`). O cabeçalho de copiadora de 512 bytes é removido sozinho. Na GUI: sistema SNES, "Chip de flash", botão "Gravar ROM". Repro com 2 ou 4 chips ou de 8 MB: `--layout 2x2mb`, `2x4mb`, `4x2mb` ou `1x8mb` (ROM de 6 a 8 MB nas de 8 MB). Cartuchos que o OSCR chama de "LoROM/HiROM (P0)" e "ExLoROM/ExHiROM (P1)": `--chip snes-lorom-p0` (ou `snes-hirom-p0`, `snes-exlorom-p1`, `snes-exhirom-p1`) com `--flash-type` e `--flash-mb`; o tipo está escrito no chip (o OSCR o achava no cartão SD pelo ID). **Tipo errado pode gravar errado.**
- **Game Boy / Game Boy Color** (pelo adaptador no slot GBA, 3,3 V): repro com flash 29F, 39SF ou CFI. `dumper rom-write -s gb -i jogo.gb --chip gb-diy-mbc5 --yes`; escolha a variante igual ao menu do OSCR (`gb-diy-mbc3`, `gb-diy-mbc5`, `gb-hdr-mbc30`, `gb-cam-first` e `gb-cam-second` para os dois jogos do GB Camera, `gb-orange-fm`, `gb-39sf-mbc5`, `gb-cfi`). Variante errada pode gravar errado. Para gravar também o save ("CFI + save"), rode `save-write` depois.
- **GBA:** repro com flash Intel 4000/4400, MX29GL128E, MSP55LV128, PC28F256M29, M29W128GH ou 369-in-1 (identificado sozinho). `dumper rom-write -s gba -i jogo.gba --yes`. No 369-in-1, `--block369 N` grava a partir do bloco de 4 MB N (0 a 63). A conferência depois de gravar não alcança o bloco N; no bloco 0 do 369-in-1 pode não bater (use `--no-verify`). O apagamento do 369-in-1 é longo: aumente `--begin-timeout`.
- **Mega Drive:** repro com flash **MX29F1610 (2 MB)**, **S29GL064N**, M29W320/640, MX29LV320/640, SST39VF320x/640x, **MX29L3211** (cartuchos KY/FlashKit) ou Intel PA28F400; o chip é identificado sozinho pelo ID (tabela em `firmware/oscr/include/dumper/MdFlashCore.h`; só o MX29F1610, S29GL064N e MX29LV640EB têm origem em uso real, os outros IDs vêm de datasheets e **não foram confirmados em chip**). `dumper rom-write -s md -i jogo.md --yes`. ROM binária de tamanho par, até 8 MB e não maior que o chip (sem cabeçalho `.smd`). Apagar ou gravar que não termina agora devolve erro (`E_CARTUCHO_IO`) em vez de travar o firmware (D86).
- Depois de gravar, o programa **lê a ROM de volta e compara** (desligue com `--no-verify`). Se a gravação falhar no meio, o chip fica apagado ou pela metade: regrave.

### 2.6c Programador de flash genérico (chips soltos)

Para ler, apagar e gravar flash de 8 ou 16 bits e EPROM 27C322 fora de cartucho, nos adaptadores de flash do OSCR (**os adaptadores não foram conferidos com as placas; veja D85 e `docs/referencia/funcoes-oscr.md`**):

```
dumper flash-id    --bus 8 --flash-kb 512                       # IDs pelas quatro rotinas; depois repita com --flash-type
dumper flash-id    --bus md                                     # cartucho de Mega Drive no slot: nome e capacidade do chip, sem apagar nada
dumper flash-read  --bus 16 --flash-kb 4096 -o chip.bin
dumper flash-blank --bus 8 --flash-kb 512 --flash-type 29f032
dumper flash-write --bus 8 --flash-kb 512 --flash-type 29f032 -i jogo.bin --yes
```

O tipo do flash de 8 bits você informa (o OSCR achava no cartão SD pelo ID); **tipo errado pode gravar errado**. A EPROM não se apaga e precisa estar em branco para gravar. Na GUI, escolha o sistema "FLASH".

### 2.7 Usar vários sistemas na mesma sessão
Troque o sistema na lista; para trocar de **cartucho** desligue o USB (seção 1). SNES, NES e Famicom usam 5 V; GBA 3,3 V. Nunca com dois cartuchos nos slots.

## 3. Cenários por sistema (o que é suportado hoje)

| Sistema | ROM | Save | Observações |
|---|---|---|---|
| SNES/SFC | LoROM e HiROM até 4 MB; **ExHiROM** (mapa `$25`/`$35`) até 7,875 MB | SRAM (ler e gravar; HiROM e ExHiROM com o CS elevado, como o OSCR) | Detecta pelo checksum do cabeçalho. Tamanho: se o cabeçalho mente (SuperFX, Sufami Turbo, repros multijogo, SF2 Turbo), informe `--prg KB` (múltiplo de 64, até 8064; GUI: "Tamanho da ROM"), vale para **todos** os tipos. ExHiROM: se o cabeçalho diz 8 MB, o firmware lê **6 MB** (os ExHiROM conhecidos de mais de 4 MB têm 48 Mbit). **SA-1** (Super Mario RPG, Kirby Super Star...): lê a ROM e **lê e grava** a BW-RAM, **só com o módulo Si5351 e o PIC montados** (o firmware liga os clocks e o CIC sozinho quando não acha um cabeçalho; a detecção demora ~1,2 s a mais). Sem o Si5351 aparece como "sem cartucho". **SuperFX** (Star Fox, Yoshi's Island...), **S-DD1** (Star Ocean, Street Fighter Alpha 2), **SPC7110** e **Cx4** (Mega Man X2 e X3): ROM e SRAM, pelas trocas de registrador do OSCR (ver D55). LoROM de mais de 3 MB sai dos bancos `$80+`. **Não** lê Derby Stallion 96, S-RTC (Daikaijuu Monogatari II), OBC1, ST018 e outros chips raros. |
| NES | mappers 0, 1 (MMC1, PRG até 256 KB), 2, 3, 4 (MMC3), 5 (MMC5), 7, 9 (MMC2), 10 (MMC4), 11 (Color Dreams), 13 (CPROM), 30 (UNROM 512, NES Maker), 33 e 48 (Taito TC0190), 34 (BxROM/NINA-001), 66 (GxROM), 67 (Sunsoft 3), 68 (Sunsoft 4), 69 (FME-7), 70, 71 (Camerica), 72 e 92 (Jaleco), 73 (VRC3), 75 (VRC1), 78, 79 (NINA-003/006), 86, 87, 93, 94, 118 (TxSROM), 140, 152, 180, 184 e 206 (Namco 108/DxROM) | **8 KB** de PRG-RAM com bateria nos mappers 1, 4, 5 (MMC5) e 69 (FME-7) (ler e gravar; informe o mapper); mappers 1 e 5 também **16 e 32 KB** (`--ram`) | Mapper 0 é automático. Para os demais, **informe mapper, PRG e CHR em KB** (GUI: campos "Opções NES/Famicom"; CLI: `--mapper 4 --prg 128 --chr 128`), de uma fonte confiável (No-Intro/NESCartDB). Gera cabeçalho iNES (espelhamento e bateria saem 0; ajuste no emulador se preciso). Mappers 2, 7 e 71 usam CHR-RAM (`--chr 0`). Saves: mappers 1, 4, 5, 69 e 118. |
| Famicom | os mesmos do NES | os mesmos do NES | Mesmo código do NES. |
| Mega Drive | ROM pelo tamanho do cabeçalho: até 4 MB; até 8 MB com mapper SSF2 (cabeçalho "SEGA SSF", como Super Street Fighter II) | SRAM de 8 bits (bytes ímpares ou pares) ou de 16 bits, **lida e gravada**, pelo que o cabeçalho declara; **EEPROM serial lida e gravada** (ver abaixo) | Precisa da palavra "SEGA" no cabeçalho. Se o cabeçalho declara mais do que a ROM tem (ROM espelhada), o firmware reduz sozinho; para forçar, informe o tamanho em KB (GUI: "Tamanho da ROM"; CLI: `--prg 512`). EEPROM serial (jogos da tabela do OSCR, achados pelo checksum do cabeçalho: NBA Jam, NFL Quarterback Club, Wonder Boy in Monster World, Madden 93, Micro Machines 2 e outros ~38 checksums): o `DETECT` mostra o tamanho do save (128 B a 8 KB) e `save-read` faz o backup, devagar (byte a byte). `save-write` grava só os bytes que mudaram, esperando o ciclo de escrita (10 ms por byte, 20 ms nas de 128 e 256 bytes) e conferindo cada um; uma EEPROM de 8 KB totalmente diferente leva ~2 minutos. Faça o backup antes e não desligue o USB durante a gravação. Sem suporte: Pier Solar, Sonic 3 / Sonic & Knuckles (lock-on) e mappers piratas. A gravação confere cada byte depois de gravar. |
| GBA | ROM de 256 KB até 32 MB (tamanho por espelhamento) | **lida e gravada**: SRAM/FRAM 32 KB, Flash 64 KB e 128 KB, EEPROM 512 B e 8 KB | Só cartuchos GBA, 3,3 V. O tipo de save **não é detectado pelo cartucho**: depois do dump da ROM o programa procura a cadeia da biblioteca de save (`FLASH1M_V`, `EEPROM_V`...) e diz o tipo a usar. Informe-o em `save-read`/`save-write --mapper N` (CLI) ou no campo "Tipo de save" (GUI): 1 = EEPROM 512 B, 2 = EEPROM 8 KB, 3 = SRAM (padrão), 4 = Flash 64 KB, 5 = Flash 128 KB. **Gravar:** faça o backup antes (**Ler save**) e use o tipo certo; num cartucho SRAM, escolher Flash escreve alguns bytes de comando no save. A Flash é identificada (Atmel, SST, Macronix, Panasonic, Sanyo) e chip desconhecido é recusado; os demais são apagados inteiros, conferidos como vazios e gravados byte a byte (o Atmel grava páginas de 128 bytes sem apagar). Tudo é conferido depois de gravar. EEPROM e Flash demoram (EEPROM de 8 KB: ~10 s; Flash: alguns segundos para apagar). Não desligue o USB durante a gravação: se ela parar no meio, o save fica incompleto. e-Reader: os últimos 128 bytes de cada banco não são gravados. |
| GB/GBC | sem mapper e MBC1 (inclui MBC1M das 6 coletâneas conhecidas), MBC2, MBC3, MBC5, MBC7, MBC6 (só leitura), MMM01 (até 1 MB), TAMA5, GB Camera, HuC1/HuC3 (tratados como MBC3/5), ROM de 32 KB a 8 MB | **lida e gravada** a SRAM (2, 8, 32, 64 e 128 KB; 512 nibbles do MBC2; GB Camera; EEPROM de 256 B do MBC7, 512 B no Command Master). **MBC6 (Net de Get): `save-read` lê a SRAM de 32 KB mais a Flash de 1 MB (1.081.344 bytes); `save-write` não é aceito (`ERRO 0x0002`)**. TAMA5: só a ROM: `save-read`/`save-write -s gb`. **Sem** o relógio (RTC) do MBC3 | **Precisa do adaptador GB/GBC no slot GBA**, que é **3,3 V**: a maioria dos cartuchos lê bem, mas alguns de GB antigos podem falhar (o OSCR usa 5 V). Detecta pelo checksum do cabeçalho. **Não** lê M161, flash repro, Pocket Camera com RTC, nem ROMs de 1,1/1,2/1,5 MB. Salva `.gbc` se a flag de GBC do cabeçalho (`$143`) estiver ligada, senão `.gb`. |
| Master System / Mark III | 32 KB a 1 MB pelo cabeçalho "TMR SEGA" (ou `--prg` quando não há cabeçalho) | **lida e gravada** a SRAM (sempre 32 KB; o cartucho de 8 KB aparece espelhado) | Slot direto da placa `megadrive_sms` (`--mapper 0`) ou adaptador Retrode (`--mapper 1`) / Retron 3in1 (`--mapper 2`) no slot Mega Drive. O tipo de save não é detectado. **Nada rodou em hardware.** |
| Game Gear | idem | idem | **Só por adaptador** no slot Mega Drive: Retron 3in1 (`--mapper 0`) ou Retrode (`--mapper 1`). Cuidado com a tensão do adaptador (o Game Gear é de 5 V, mas confira o adaptador). |
| SG-1000 | 8, 16, 24 ou 32 KB, sempre com `--prg` (não há cabeçalho) | sem save | Adaptador Raphnet no slot Mega Drive (`--mapper 0`). |

Sistemas ou cartuchos fora disso: o firmware responde "sistema não suportado" (código `0x0002`).

Depois de cada dump o programa confere o **checksum do cabeçalho** (Mega Drive, SNES e GBA) e avisa se não confere. Isso ajuda a achar tamanho errado ou contato sujo, mas não substitui o CRC32 do No-Intro: algumas ROMs têm o checksum errado de fábrica.

## 4. Solução de problemas (básico)

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| Nenhuma porta aparece | cabo só de carga; falta de permissão; driver | Troque o cabo; Linux: grupo `dialout`; clone com CH340 pede driver (Windows/macOS). Em `ls /dev/ttyUSB* /dev/ttyACM*` o clone aparece como `ttyUSB0`. |
| "sem resposta do dispositivo" ao conectar | firmware não gravado; baud errado; porta ocupada | Regrave o firmware; tente `--baud 115200`; feche monitor serial/IDE; reconecte o cabo. |
| Detecta "cabeçalho inválido" (status 4) | há dados no cartucho, mas o checksum do cabeçalho não confere; no Mega Drive com a placa v. 1.2, o pino `/CART` diz que há cartucho mas o cabeçalho não leu (antes isso aparecia como "nenhum cartucho") | Contato sujo quase sempre: limpe, encaixe de novo e repita; em ROM de hack o checksum pode estar errado de fábrica |
| Detecta "nenhum cartucho" | encaixe, contatos, sistema errado | Encaixe até o fim; limpe com álcool isopropílico; confira o sistema na lista; teste outro cartucho. |
| "sistema não suportado" (`0x0002`) | chip especial / mapper fora da lista | Veja a seção 3. NES: mappers 0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 33, 48, 66, 69, 70, 71, 75, 78, 79, 87, 118 e 206. |
| NES: "argumento inválido" (`0x0004`) | PRG/CHR errados para o mapper | PRG múltiplo de 16 KB (7, 11 e 66: de 32 KB), CHR múltiplo de 8 KB; mappers 2, 7 e 71 sem CHR; limites: MMC1 256 KB, mapper 9 PRG 128 KB, 10 PRG 256 KB, 11 PRG e CHR 128 KB, 66 PRG 128 KB e CHR 32 KB, 69 PRG 512 KB, 5 PRG 1 MB (acima disso `0x0002`). |
| Aviso "checksum do cabeçalho NÃO confere" | tamanho errado, contato sujo, ROM modificada (ou checksum ruim de fábrica) | Leia de novo; se for Mega Drive, tente informar o tamanho; compare o CRC32 com o No-Intro. |
| CRC32 diferente do No-Intro | contato sujo; revisão diferente; ROM não suportada | Limpe, leia 3 vezes (se mudar a cada leitura, é contato); confira região/revisão no DAT. |
| Leitura trava ou dá "reenvios excedidos" (`0x0005`) | cabo ruim, hub USB, ruído | Cabo curto e direto no PC; evite hubs; tente `--baud 115200`. |
| "CRC32 do arquivo não confere" (`0x0006`) | corrupção no USB | Repita a operação; troque o cabo. |
| "erro de leitura/gravação no cartucho" (`0x0007`) | contato, bateria, cartucho com defeito | Limpe os contatos; no save, confira a bateria e o tamanho do arquivo. |
| Gravação do save recusada (`0x0004`) | tamanho diferente do save do cartucho | Use um arquivo com exatamente o tamanho mostrado em **Detectar**. |
| Placa esquenta, cheiro, LED sem acender | curto | Desligue o USB já. Refaça os testes de `boards/16_and_8_bits/docs/montagem.md` (seção 5). |
| GBA não lê | cartucho de outro sistema; solda do slot | Só cartucho GBA; confira a solda dos pads de 1,5 mm e a tensão de 3,3 V no pino 1. |

Códigos de erro do protocolo: `docs/referencia/protocolo.md`, seção 8. Na CLI, o código de saída é 1 em erro, 2 se não houver cartucho; os demais e a saída `--json` para agentes estão em `docs/referencia/cli.md`.

### Atualizar ou gravar o firmware do Arduino pela CLI (D131)

Sem o PlatformIO: tenha o `avrdude` instalado e o `.hex` do firmware (compilado em `firmware/oscr/.pio/build/SerialASCII/firmware.hex`, ou o que alguém lhe passou).

```
python3 host/dumper.py firmware-flash --dry-run          # só mostra o comando e a versão atual
python3 host/dumper.py firmware-flash                    # pergunta antes de gravar
python3 host/dumper.py firmware-flash --env SerialASCII_Volt --yes   # placa com o seletor de tensão 3,3 V/5 V (v1.1)
```

O Mega reinicia no fim e a porta some por um instante; o comando tenta o `INFO` de novo por 12 s e mostra a versão nova. Feche a GUI e o monitor serial antes (a porta precisa estar livre). A CLI Kotlin tem o mesmo comando (`dumper firmware-flash`). Na GUI, o cartão **Firmware do Arduino** (abaixo de Conexão) faz o mesmo: escolha a porta, opcionalmente um `.hex`, clique em **Gravar firmware** e confirme; a GUI fecha a conexão antes, e depois você clica em Conectar. Nada foi testado em um Mega de verdade.

## 5. Dicas

- Leia cada cartucho **duas ou três vezes** e confira que o CRC32 é o mesmo.
- Guarde as ROMs com o nome do No-Intro; o CRC32 mostrado é o da ROM completa.
- **Identificar o jogo pelo CRC32:** o programa já traz uma base de jogos (a do OSCR: SNES, NES, Mega Drive, GBA, Game Boy e outros; `database/oscr/`) e a usa sozinho. Para somar a sua, em Configurações, "Base de dados de jogos", adicione um `.dat` do No-Intro (ou uma pasta deles) e/ou o `nes20db.xml`. Depois do dump a GUI mostra o nome do jogo (ou "não encontrado": dump novo, variante ou erro de leitura) e usa o nome no arquivo. Na CLI: `dumper dump --db BASE ...`, `dumper identify rom.sfc --db BASE`, `dumper search "mario" --db BASE`. As bases do No-Intro e do NES 2.0 XML não vêm no repositório: baixe-as das fontes (No-Intro/Redump e o projeto NES 2.0 XML Database).
- **NES/Famicom:** com a base carregada (a do projeto já basta: o cabeçalho iNES dela dá mapper e tamanhos; o `nes20db.xml` acrescenta os jogos que ela não tem), a GUI ganha o campo "Procurar jogo na base NES 2.0": escolha o jogo e mapper, PRG, CHR e RAM são preenchidos. Na CLI: `dumper dump -s nes --game "Nome do jogo" --db nes20db.xml`.
- Para contribuir com um erro, anexe: sistema, título, saída do **Detectar**, versão do firmware (`dumper.py info`) e a mensagem exata.

## 6. Limites e segurança

- Um cartucho por vez; USB desligado ao trocar o cartucho (o 5V dos slots não é cortado por software).
- Nunca insira cartucho de outro console no slot GBA (3,3 V).
- **Os slots de SNES, NES, Famicom e Mega Drive são de 5 V** (decisão do projeto); as placas v1.1 de Mega Drive, SMS, NES e Famicom têm o **seletor 3,3 V/5 V** (D138): liga em 5 V (flashcarts comuns precisam dele), `--voltage 3v3` (ou o botão da GUI) liga a 3,3 V, e passar de 3,3 V para 5 V mostra um alerta e pede confirmação (`--allow-5v` em script). Falha de leitura **não** muda a tensão. O jumper J1 "TRAVA 3,3 V" impede o 5 V por hardware; o fusível F1 (5×20 mm, 500 mA, no suporte de clipes) protege contra curto e se troca sem solda. Alguns flashcarts, cartuchos não licenciados e placas de repro aceitam só 3,3 V: 5 V pode danificá-los **e o dumper**. Confira a placa do cartucho antes; na dúvida, não insira. A GUI mostra esse aviso nesses sistemas (P-07, `docs/historico/pesquisa-comunidade.md`).
- Placas v1.1 com o seletor de tensão: a placa sobe em 3,3 V e o programa passa a 5 V antes da primeira leitura; para um cartucho marcado como 3,3 V use `--voltage 3v3`. Para trocar o cartucho, desligue o USB.
- Cartuchos SNES com chip especial e jogos raros podem exigir leitura adicional (futura).
- Gravar save é irreversível para o conteúdo anterior: faça backup antes.

## 7. Primeira validação com hardware (para quem montou a placa)

Faça nesta ordem e anote o resultado em `docs/decisoes.md`:

0. **Autoteste da placa, sem cartucho:** `dumper.py selftest` (ou o cartão "Autoteste da placa" da GUI). Demora cerca de 45 s e aponta curtos entre pinos, o pull-up do D7 e o Si5351. Rode logo depois de montar, antes de colocar qualquer cartucho; se achar problema, volte à inspeção visual (montagem.md, seção 5).
1. Firmware de teste (`OSCR_MOCK`): `dumper.py dump -s mock` dá CRC32 `D1DF4327`.
2. Firmware real. `dumper.py info` mostra "sistemas: snes, nes, famicom, md, gba".
3. **SNES LoROM simples:** `detect -s snes`, depois `dump`. Compare com o No-Intro.
4. **NES mapper 0** (por exemplo, Super Mario Bros.): idem. Depois um de cada mapper 1, 2, 3, 4, 7 e, se tiver, 5, 9, 10, 11, 66, 69 e 71. Compare o CRC32 da ROM completa (com cabeçalho iNES de 16 bytes, o No-Intro mostra o CRC do conjunto PRG+CHR sem cabeçalho: confira os dois).
5. Mega Drive, Famicom e GBA.
6. Save SNES: leia, faça backup, grave de volta o mesmo arquivo e leia de novo (devem ser iguais).

Se algum sistema falhar, o ponto a olhar é o HAL em `firmware/oscr/src/cores/*.cpp (o firmware do fork; o HAL antigo está em firmware/arquivo/oscr_serial/oscr_avr_buses.h)` (tempos e linhas de controle), comparando com `SNES.ino`, `NES.ino`, `MD.ino` e `GBA.ino` do OSCR e com `boards/16_and_8_bits/docs/pinmap.md`.
