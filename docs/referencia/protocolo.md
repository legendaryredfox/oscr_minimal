# Protocolo serial — oscr_minimal

Versão do protocolo: **1**. Escrito antes da implementação (`CLAUDE.md`, seção 9). Quem implementa (firmware, `host/`, `gui/`) deve seguir este documento; os vetores de teste da seção 9 valem para todos.

## 1. Camada física

- USB serial do Mega (CH340 ou ATmega16U2), 8 bits, sem paridade, 1 stop bit, sem controle de fluxo.
- **Baud padrão 1.000.000.** Fallbacks: **500.000** e **115.200** (H-3, D166). O host tenta 1.000.000, manda `INFO`, espera 500 ms; sem resposta, tenta 500.000 e depois 115.200 (`--baud` fixa um só; na GUI o escolhido vai primeiro). O firmware abre a serial em **um** baud, escolhido na compilação (`OSCR_DUMPER_BAUD` em `src/dumper/Dumper.cpp`, padrão 1.000.000); uma compilação com `-DOSCR_DUMPER_BAUD=500000` ou `115200` só é achada pelo fallback correspondente. Os 500.000 bauds são exatos no Mega a 16 MHz; a imagem de `firmware/images/` continua só em 1.000.000.
- Ordem de bytes: **little-endian** em todos os campos numéricos.

## 2. Quadro (frame)

```
offset  tamanho  campo
0       2        magia: 0xA5 0x5A
2       1        tipo
3       1        seq        número de sequência (0..255); a resposta repete o seq do pedido
4       2        len        tamanho do payload (0..1024)
6       len      payload
6+len   4        crc32      CRC32 (IEEE 802.3, igual ao zlib) dos bytes de "tipo" até o fim do payload
```

- Tamanho máximo do quadro: 6 + 1024 + 4 = **1034 bytes**.
- Quadro inválido (CRC ruim, `len` > 1024, truncado): descarte e procure a próxima magia. Não responda a um quadro corrompido; o outro lado reenvia por tempo esgotado (seção 7).
- Tempo máximo entre bytes de um quadro: 200 ms. Tempo de espera por resposta: 1.000 ms, exceto durante `DETECT`/leitura real (até 10.000 ms).

## 3. Tipos de quadro

### Host → dispositivo

| Tipo | Nome | Payload |
|---|---|---|
| `0x01` | `INFO` | vazio |
| `0x02` | `DETECT` | `u8 sistema`; opcional, só no sistema 7: `u16 chip`, `u16 prg_kb`, `u16 chr_kb` (D85) |
| `0x03` | `DUMP_ROM` | `u8 sistema`, `u16 bloco` (0 = padrão 512); opcional, só NES/Famicom: `u16 mapper`, `u16 prg_kb`, `u16 chr_kb` (0 = automático/NROM) |
| `0x04` | `READ_SAVE` | `u8 sistema`, `u16 bloco` (0 = padrão 512) |
| `0x05` | `WRITE_SAVE` | `u8 sistema`, `u32 tamanho`, `u16 bloco` (0 = padrão 512); opcional, NES/Famicom: `u16 mapper`, `u16 0`, `u16 0` |
| `0x06` | `ACK` | `u32 offset` do bloco confirmado |
| `0x07` | `NAK` | `u32 offset` do bloco que precisa ser reenviado |
| `0x08` | `ABORT` | vazio |
| `0x09` | `DATA` | `u32 offset` + dados (só em `WRITE_SAVE`, host → dispositivo) |
| `0x0A` | `END` | `u32 total`, `u32 crc32` do arquivo inteiro (só em `WRITE_SAVE` e `WRITE_ROM`) |
| `0x0C` | `ERASE` | `u8 sistema`, `u16 chip`, `u16 prg_kb`, `u16 chr_kb` (as três últimas sempre enviadas). Só o sistema 7 (programador de flash genérico, D85): apaga o chip inteiro e responde `ACK` (offset 0) só no fim, ou `ERRO`. O host espera até 90 s e **nunca reenvia** (reenviar apagaria de novo). `INFO_RESP.flags` bit 4 diz que existe (o `ERASE` do sistema 1 é o preenchimento da SRAM do Test RAM, F-10) |
| `0x0B` | `WRITE_ROM` | `u8 sistema`, `u32 tamanho`, `u16 bloco`, `u16 chip`, `u16 prg_kb`, `u16 chr_kb` (os três últimos são sempre enviados). Grava a **ROM** em cartucho de flash (D77). Só no firmware em modo fluxo (fork do OSCR); `INFO_RESP.flags` bit 3 diz que existe |
| `0x0D` | `VOLT` | `u8 ação`: 0 consulta, 1 escolhe 3,3 V, 2 escolhe 5 V (placa com o seletor de tensão, D138). Responde `VOLT_RESP`. Escolher a tensão solta todos os pinos de sinal, troca o seletor e espera o rail assentar (~0,2 s). O 5V dos slots **nunca é cortado** (o desligamento por software foi retirado, D139). Sem seletor (`INFO` flag bit 5 = 0), a consulta responde 5 V fixo e escolher devolve `0x0001`. A placa sobe em 3,3 V (estado seguro do hardware: abrir a porta reinicia o Mega); o host pede 5 V antes de um comando de cartucho, a menos que o usuário tenha escolhido 3,3 V |
| `0x0F` | `BOARD` | `u8 ação`: 0 consulta o perfil da placa; 1 grava, seguida de `u8 flags` (bit 0 = a placa tem o seletor de tensão 3,3 V/5 V; os outros bits devem ser 0, senão `ERRO` `E_ARGUMENTO` sem gravar). Responde `BOARD_RESP`. **O PC diz ao firmware que placa está ligada** (D162): o firmware guarda o perfil na EEPROM (endereço 4064, quatro bytes: magic `0xB5`, versão 1, flags, flags invertidos; o OSCR só usa o endereço 0) e vale já, sem reiniciar. Com isso **uma imagem de firmware só** serve as placas com e sem o seletor: antes eram duas compilações (`SerialASCII` e `SerialASCII_Volt`). Ao ligar o seletor o firmware solta os pinos, sobe em 3,3 V (estado seguro) e o host pede 5 V depois; ao desligá-lo o D18 volta a ser entrada. Sem perfil guardado vale o padrão da compilação (`OSCR_VOLT_SELECT`). Só existe se `INFO` flag bit 7 = 1; senão devolve `0x0001` |
| `0x10` | `CLOCK` | `u8 ação`: 0 consulta; 1 grava o fator de correção (`i32 ppb`, LE) na EEPROM do Mega e aplica já (`set_correction` do Si5351); 2 liga as três saídas de teste (CLK0 4 MHz, CLK1 1 MHz, CLK2 3,072 MHz, as do `clkcal` do OSCR); 3 desliga. `ppb` positivo = a saída roda alta (convenção da biblioteca Si5351: `corr = (f_medida - f_alvo) / f_alvo × 10⁹`, medido com fator 0). Limite do projeto: `|ppb| ≤ 1.000.000` (`ERRO 0x0004` acima ou em `ação` desconhecida ou `SET` sem o fator). Sem o Si5351 no I²C, só a consulta responde (`presente` = 0); as outras ações dão `ERRO 0x0007`. Firmware sem o comando: `ERRO 0x0001`. Sem bit no `INFO` (os 8 já têm uso): o host descobre pela resposta. O fator guardado é lido no boot por `ClockGen::initialize()` (D167) |
| `0x0E` | `SELFTEST` | sem payload. Autoteste da placa **sem cartucho** (P-12): roda `OSCR::Cores::SelfTest::run()` do OSCR (curtos entre os pinos 2 a 9, 14 a 17, 22 a 37, 42 a 49 e A0 a A15, curto com GND, pull-up de 1 kΩ no D7, Si5351). Responde `SELFTEST_RESP` só no fim; **demora cerca de 45 s** (o host espera até 90 s). Só existe se `INFO` flag bit 6 = 1; senão devolve `0x0001`. Não mexe na tensão do seletor. Deixa os pinos de sinal soltos e os clocks do Si5351 ligados |

### Dispositivo → host

| Tipo | Nome | Payload |
|---|---|---|
| `0x81` | `INFO_RESP` | `u8 versão_proto`, `u8 maior`, `u8 menor`, `u8 patch` (firmware), `u8 flags`, `u16 sistemas` (máscara de bits, bit = id do sistema), `u16 max_payload` (maior payload que o dispositivo aceita: 1024 no PC/simulador, 520 no AVR; o host usa bloco ≤ `max_payload` − 4; opcional para o host, o campo vem no fim) |
| `0x82` | `DETECT_RESP` | ver seção 5 |
| `0x83` | `BEGIN` | `u8 tipo_dado` (1 = ROM, 2 = save), `u32 tamanho`, `u16 bloco`. **Tamanho `0xFFFFFFFF` = desconhecido** (firmware baseado nos núcleos do OSCR, modo fluxo: o tamanho real e o CRC32 vêm no `END`; o host aceita qualquer `offset` sequencial até o `END`, e a barra de progresso usa o tamanho do `DETECT`) |
| `0x84` | `DATA` | `u32 offset` + dados (até `bloco` bytes) |
| `0x85` | `END` | `u32 total`, `u32 crc32` do arquivo inteiro |
| `0x86` | `ACK` | `u32 offset` (confirma um pedido ou um bloco de `WRITE_SAVE`) |
| `0x87` | `ERRO` | `u16 código`, `u8 n`, `n` bytes de texto ASCII (diagnóstico, não traduzido) |
| `0x88` | `PROGRESSO` | `u32 offset`, `u32 total` (0 = desconhecido), `u8 etapa` (F-1, D165; o 9º byte é opcional, ausente = 0). Etapas: 0 não informada, 1 apagando, 2 gravando, 3 lendo, 4 autoteste. O firmware envia **um** quadro no começo de cada trabalho longo, antes de bloquear no núcleo do OSCR (que não devolve o controle): `ERASE` (etapa 1); `WRITE_ROM` (etapa 1 antes de conferir o chip e apagar, etapa 2 depois do primeiro `ACK`); `WRITE_SAVE` (etapa 2); `DUMP_ROM` e `READ_SAVE` (etapa 3, depois do `ACK` do `BEGIN`); `SELFTEST` (etapa 4). Não há quadros periódicos no meio do laço do núcleo. O quadro leva o `seq` do comando; o host o entrega a quem escuta e segue esperando a resposta de sempre. Host sem suporte ignora o tipo; firmware antigo nunca o envia, então a CLI e a GUI não mostram etapa |
| `0x89` | `VOLT_RESP` | `u8 seletor` (1 = a placa tem o seletor de tensão, D138), `u8 tensão` (0 fixa em 5 V sem seletor, 1 = 3,3 V, 2 = 5 V), `u8 escolhida` (1 = o usuário escolheu 3,3 V; a placa sobe em 3,3 V sem escolha, e só a escolha explícita exige confirmação do host para subir a 5 V) |
| `0x8B` | `BOARD_RESP` | `u8 guardado` (1 = há perfil válido na EEPROM; 0 = vale o padrão da compilação), `u8 flags` (o perfil em vigor; bit 0 = seletor de tensão) |
| `0x8C` | `CLOCK_RESP` | `u8 presente` (o Si5351 respondeu no I²C), `u8 guardado` (há fator válido na EEPROM), `i32 ppb` (o fator em vigor, LE), `u8 teste` (1 = saídas de teste ligadas) |
| `0x8A` | `SELFTEST_RESP` | `u8 cortado` (1 = houve mais achados do que cabem), `u8 n` (0 a 24) e `n` achados de 3 bytes `u8 tipo, u8 pino a, u8 pino b`. Tipos: 1 = pino `a` em curto com GND; 2 = pinos `a` e `b` em curto entre si; 3 = falta o pull-up de 1 kΩ no D7 (`a` = 7; só vale em placa com R2, isto é, com slot de SNES); 4 = o Si5351 não responde. Pinos na numeração do Arduino (54 em diante = A0...). `n` = 0 e `cortado` = 0: nenhum problema |

`seq` do host é livre (incremente a cada pedido). O dispositivo repete o `seq` do pedido em todas as respostas daquele pedido (`DATA` do mesmo fluxo repete o `seq` do `DUMP_ROM`/`READ_SAVE`).

### Flags de `INFO_RESP`
bit 0: modo `MOCK` ligado (dados sintéticos, sem cartucho); bit 1: Si5351 detectado; bit 2: PIC (CIC) presente (informativo, pode ser 0 se não houver como detectar); bit 3: aceita `WRITE_ROM` (D77); bit 5: a placa tem o seletor de tensão 3,3 V/5 V (`VOLT`, D138); bit 4: tem o programador de flash genérico (sistema 7 e `ERASE`, D85); bit 6: tem o autoteste (`SELFTEST`, P-12); bit 7: tem o perfil da placa (`BOARD`, D162); demais: 0. A versão do firmware no `INFO_RESP` passou a **0.2.0** com o `BOARD`; o PC compara essa versão e a máscara `sistemas` com o que a placa escolhida precisa para decidir se grava o firmware (D162).

## 4. Sistemas

| Id | Sistema | Extensão do arquivo de ROM |
|---|---|---|
| 1 | SNES/SFC | `.sfc` |
| 2 | NES | `.nes` |
| 3 | Famicom | `.nes` |
| 4 | Mega Drive/Genesis | `.md` |
| 5 | GBA (3,3 V) | `.gba` |
| 6 | Game Boy / Game Boy Color (via adaptador no slot GBA, 3,3 V) | `.gb` (os jogos só de GBC podem ser renomeados para `.gbc`) |
| 7 | Programador de flash genérico (chips soltos, D85) | `.bin` |
| 8 | Master System / Mark III (slot SMS da placa `megadrive_sms`, ou adaptador no slot Mega Drive; D137) | `.sms` |
| 9 | Game Gear (adaptador Retrode ou Retron no slot Mega Drive; D137) | `.gg` |
| 10 | SG-1000 (adaptador Raphnet no slot Mega Drive; D137) | `.sg` |
| 11 | Nintendo 64 (slot N64 da placa `n64` ou da `completa`, 3,3 V; D158) | `.z64` |
| 12 | ColecoVision (adaptador de 30 pinos no slot SNES, 5 V; F-20, D201) | `.col` |
| 13 | Neo Geo Pocket / Color (3,3 V; adaptador ainda não projetado; F-20, D202) | `.ngp` (os jogos de Color podem ser renomeados para `.ngc`) |
| 14 | Vectrex (adaptador de 36 pinos no slot SNES, 5 V; F-20, D205) | `.vec` |
| 255 | `MOCK` (teste, sem cartucho) | `.bin` |

### Opções para Vectrex (D205)

Usa o núcleo `Vectrex.cpp` do OSCR (`cartOn`, `readSegment`, `cartOff`), só leitura de ROM. O `readROM` do OSCR não é chamado (usa a base de dados do SD); a costura repete os trechos dele (`VecCore.h`, `segments`) e troca o PB6 (PH5) direto no PORTH. `prg_kb` é o **tamanho em KB** e vale sempre: 4, 8, 12, 16, 32 ou 64 (a tabela do menu do OSCR; os de 64 KB leem o segundo banco com o PB6 alto); outro valor dá `ERRO 0x0004`. `DETECT` lê 32 bytes de `$0000` com o PB6 baixo: `status` 1 se todos iguais a `$00` ou `$FF`, 0 se o primeiro byte é `$67` (o que a BIOS do console procura; convenção do console, não do OSCR), 4 se há dados com outro primeiro byte. `READ_SAVE` e `WRITE_SAVE` respondem `ERRO 0x000A`. O `/OE` do cartucho não chega ao slot SNES daqui (`docs/planos/adaptador-vectrex.md`).

### Opções para Neo Geo Pocket (D202)

Usa o núcleo `NeoGeoPocket.cpp` do OSCR (`cartOn`, `getCartInfo`, `writeByte`, `readByte`, `cartOff`), só leitura de ROM. `getCartInfo` entra no modo autoselect da flash (escreve `AA/55/90` no chip e depois `F0`), lê o ID do fabricante e do dispositivo (tamanho de 512 KB a 2 MB; 4 MB para três títulos) e confere o cabeçalho "COPYRIGHT BY SNK CORPORATION" ou " LICENSED BY SNK CORPORATION"; nome, versão e tipo (mono ou cor) saem dele. O menu de tamanho do núcleo (chip desconhecido) fica desligado no fork (`#if !OSCR_DUMPER`). `readROM` do OSCR não é chamado (abre prompt e espera tecla); a costura repete o laço de leitura em blocos de 512 bytes. `prg_kb`: 0 = pelo ID do chip; 512, 1024, 2048 ou 4096 informa o tamanho e vale sempre; outro valor dá `ERRO 0x0004`. `DETECT`: `status` 1 se o ID do chip é `$FFFF` (nada responde), 0 com cabeçalho SNK, 4 se o chip responde mas o cabeçalho não é da SNK (com `prg_kb` o dump segue, como o "Continuar" do OSCR); `rom_size` é 0 com chip desconhecido. Chip desconhecido sem `prg_kb` dá `ERRO 0x0004`. `READ_SAVE` e `WRITE_SAVE` respondem `ERRO 0x000A`. O resumo do dumping.guide recomenda **ler pelo menos 6 vezes e comparar** (a leitura é pouco confiável). Regras puras em `include/dumper/NgpCore.h`, testadas em `pc-tests/test_ngp.cpp`.

### Opções para ColecoVision (D201)

Usa o núcleo `Colecovision.cpp` do OSCR (`cartOn`, `readData`, `readSegment`, `cartOff`), só leitura de ROM a partir de `$8000`. O `readROM` do OSCR não é chamado: ele consulta a base de dados do cartão SD (que não existe aqui); a costura repete o que ele faz, sem a base. `prg_kb` é o **tamanho da ROM em KB** e vale sempre: 8, 12, 16, 20, 24 ou 32 (a tabela do menu do OSCR); outro valor dá `ERRO 0x0004`. O cartucho não informa o tamanho. `DETECT` lê 32 bytes de `$8000`: `status` 1 se todos forem iguais a `$00` ou `$FF` (slot vazio), 0 se começam por `$AA55` ou `$55AA` (assinatura do console), 4 se há dados sem assinatura (homebrew ou contato sujo); a assinatura é convenção do console, não do OSCR. `READ_SAVE` e `WRITE_SAVE` respondem `ERRO 0x000A` (cartucho sem save). Regras puras em `include/dumper/ColvCore.h`, testadas em `pc-tests/test_colv.cpp`.

### Opções para Master System, Game Gear e SG-1000 (D137)

Usam o núcleo `SMS.cpp` do OSCR sem alteração de leitura (`getCartInfo`, `readROM`, `readSRAM`, `writeSRAM`). O campo `mapper` é o **adaptador** e vale em `DETECT`, `DUMP_ROM`, `READ_SAVE` e `WRITE_SAVE` (o `DETECT` leva as opções no próprio quadro, como o programador de flash):

| Sistema | `mapper` | Modo do núcleo |
|---|---|---|
| 8 (SMS) | 0 | slot direto da placa `megadrive_sms` ou adaptador Raphnet (`SMSRaphnet`) |
| 8 (SMS) | 1, 2 | adaptador Retrode (`SMSRetrode`), Retron 3in1 (`SMSRetron`), no slot Mega Drive |
| 9 (Game Gear) | 0, 1 | Retron 3in1 (`GGRetron`), Retrode (`GGRetrode`) |
| 10 (SG-1000) | 0 | Raphnet (`SG1000Raphnet`) |

`prg_kb` é o **tamanho da ROM em KB** e vale sempre: SMS e Game Gear 32, 64, 128, 256, 512 ou 1024 (os tamanhos do menu do OSCR); SG-1000 8, 16, 24 ou 32; 0 = pelo cabeçalho. O cabeçalho "TMR SEGA" dá o tamanho (nibble de `$7FFF` e espelhamento); **sem cabeçalho** (Mark III, SG-1000, jogos antigos) o `DETECT` devolve `status` 4 e o `DUMP_ROM` sem `prg_kb` falha com `E_ARGUMENTO`. Slot vazio = o barramento lê um valor só (`$00` ou `$FF`): `status` 1. O save é sempre 32 KB (`READ_SAVE`/`WRITE_SAVE`; o cartucho de 8 KB aparece espelhado); o cabeçalho não diz se há SRAM (`save_type` 255), quem decide é o usuário. Valores fora das tabelas: `E_ARGUMENTO` (ou `status` 2 no `DETECT`). Regras puras em `firmware/oscr/include/dumper/SmsCore.h` (testes em `pc-tests/test_sms.cpp`). O firmware não conhece a tensão: Game Gear a 5 V é problema do adaptador (ver `docs/referencia/uso.md`).

### Opções para Nintendo 64 (D158)

Usa o núcleo `N64.cpp` do OSCR (`cartOn`, `idCart`, `readRom`, `readSave`, `writeSave`). O OSCR achava o tamanho da ROM e o tipo de save numa base de dados no cartão SD (CRC1 do cabeçalho); sem SD, **o PC faz a consulta** (`database/oscr/json/n64.json`, em `host/oscr_host/n64.py` e `gui/.../N64Games.kt`) e manda os dois valores nos comandos.

| Comando | Campos | Resultado |
|---|---|---|
| `DETECT` | nenhum | `status` 0 se os 64 primeiros bytes da ROM começam com `80 37 12 40` (z64); 1 slot vazio (um valor só, `$00` ou `$FF`); 4 há dados mas não é cabeçalho de N64. `name` = `CCCCCCCC IIII TÍTULO` (CRC1 do cabeçalho em hexadecimal, código do jogo e título, até 31 caracteres). `rom_size`, `save_size` e `save_type` vêm em 0: o cabeçalho não diz |
| `DUMP_ROM` | `prg_kb` = **tamanho da ROM em MB** (1 a 64; o campo guarda MB porque 64 MB não cabe em KB de 16 bits) | arquivo z64 (ordem do barramento) |
| `READ_SAVE`, `WRITE_SAVE` | `mapper` = **tipo de save** do OSCR | arquivo de save do tamanho abaixo |

Tipos de save (`mapper`): 0 nenhum, 1 SRAM de 32 KB, 2 SRAM de 96 KB (768 Kbit), 4 FlashRAM de 128 KB, 5 EEPROM de 4 Kbit (512 bytes, 64 páginas de 8), 6 EEPROM de 16 Kbit (2048 bytes, 256 páginas). Outro valor: `ERRO 0x0004`; tipo 0: `ERRO 0x000A` (sem save). A conferência depois de gravar o save é do PC (relê e compara): o `verifySaveData` e a releitura de `writeEeprom` do OSCR usam `rewind()` do arquivo, que o fluxo serial não tem; o núcleo foi alterado só nesses pontos e no `matchCRC` do fim de `readRom` (sem SD não há base), sob `OSCR_DUMPER`. **Não incluído:** gravação de ROM em flash repro, Gameshark, Xplorer, Controller Pak e teste de controle (a placa não tem o conector do controle).

### Opções de `DUMP_ROM` para NES/Famicom e Mega Drive

**Mega Drive:** só `prg_kb` conta e significa o **tamanho da ROM em KB** (0 = pelo cabeçalho, com redução automática quando a ROM aparece espelhada). Mínimo 32 KB; máximo 4 MB (8 MB com o mapper SSF2). `ERRO 0x0004` fora desses limites.

**SNES:** só no ExHiROM, `prg_kb` é o **tamanho da ROM em KB** (0 = pelo cabeçalho; cabeçalho de 8 MB vira 6 MB). Múltiplo de 64, máximo 8064; outro valor `ERRO 0x0004`. LoROM e HiROM ignoram as opções.

**SNES, acessórios e Test RAM (F-10, D178):** o terceiro campo opcional do SNES (`chr_kb`, o do tipo forçado) também leva o **acessório**, a partir de 0x8000: `0x8001` e `0x8002` = Sufami Turbo, slot A e B; `0x8003` = Game Processor RAM Cassette (GPC). Firmware que não conhece o acessório recusa o valor (`E_ARGUMENTO`; no `DETECT`, status 2) em vez de ler o adaptador como um SNES comum, porque o tipo só aceita 0 a 4. **Sufami Turbo:** `DETECT` e `DUMP_ROM` (só ROM): `ST::getHeader` confere o cabeçalho "BANDAI SFC-ADX" do adaptador (banco 0) e do cartucho do slot (bancos 32 e 64): sem um dos dois, `E_SEM_CARTUCHO` (status 1); o tamanho é 512 KB (cabeçalho em início + 16) ou 1 MB; o nome do `DETECT` é o do cartucho. O `DUMP_ROM` chama `ST::readSlot` do OSCR. `READ_SAVE` e `WRITE_SAVE` com Sufami: `E_ARGUMENTO`. **GPC:** `READ_SAVE` (chama `GPC::readRAM`) e `WRITE_SAVE` (exatamente 524288 bytes, senão `E_ARGUMENTO`), sem `DETECT` (status 2) e sem como saber se há cassete: sem ele a leitura devolve o que o barramento mostrar. A gravação é do fork (`src/dumper/SnesAcc.cpp`): o `GPC::writeRAM` do OSCR escolhe o arquivo no SD e confere relendo o arquivo com `rewind`, o que o fluxo não faz; o laço é o dele (protege desligada, 8 bancos $C0 a $C7 de 64 KB, protege religada) e a conferência é do PC. O GPC precisa do Si5351. **Test RAM:** `ERASE` do sistema 1 com `chip` = byte (0 a 255): `eraseSRAM` do OSCR sobrescreve a SRAM inteira com esse byte (`E_SEM_SAVE` se o cartucho não tem SRAM; `E_ARGUMENTO` se `chip` > 255). O OSCR lê o save, escreve 0x0F e 0xF0, grava o save de volta e confere; aqui o PC faz o backup e a restauração (a SRAM não cabe na RAM do Arduino) e chama o `ERASE` duas vezes (`ram-test`). Nunca rodou em hardware.

**SNES, tipo de ROM forçado (F-2, D164):** o terceiro campo opcional (`chr_kb`, que o SNES não usa) leva o **tipo** em `DETECT`, `DUMP_ROM`, `READ_SAVE` e `WRITE_SAVE` (neste, o terceiro campo depois de `mapper` e da RAM): 0 = pelo cabeçalho (padrão), 1 = LoROM, 2 = HiROM, 3 = SA-1, 4 = ExHiROM; maior que 4 dá `ERRO E_ARGUMENTO` (no `DETECT`, status 2). O firmware chama `getCartInfo` do OSCR, troca `romType` e recalcula os bancos com a mesma fórmula do OSCR (`include/dumper/SnesType.h`, testado em `pc-tests/test_snes_type.cpp`). Com tipo **e** `prg_kb` informados, um cabeçalho ilegível não recusa o cartucho. Não há campo novo no fio: um firmware sem este recurso lê só o que sempre leu e **ignora o tipo em silêncio** (o host não tem como saber; confira o `name` e o tamanho no `detect`). Não se usa `mapper` porque o `WRITE_ROM` do SNES o usa como código do chip.


**Saves do Mega Drive** (`READ_SAVE` e `WRITE_SAVE`): a SRAM ou a EEPROM serial, conforme o cabeçalho; sem opções. **RAM de backup do Sega CD** (F-16, D179): o `DETECT` reconhece o cartucho pelo primeiro word e pelo checksum (função `getCartInfo` do OSCR) e devolve `status` 0, `rom_size` 0, `save_size` 128 KB (cartucho oficial) ou 512 KB (Ultra CD), `save_type` 5 e `name` `Sega CD RAM`; `READ_SAVE` e `WRITE_SAVE` chamam `readBram` e `writeBram` do OSCR, `DUMP_ROM` dá `E_ARGUMENTO`. O fio de `/MRES` (B2) a `/VRES` (B27) que o OSCR pede para gravar já existe nas placas (os dois vão ao D17; ver `docs/referencia/uso.md`). **Sonic & Knuckles com jogo encaixado:** `rom_size` do `DETECT` já inclui o jogo de cima (e o Sonic 2 inteiro quando é ele), igual ao que o `DUMP_ROM` envia (D180). **Mapper por banco (D181):** `DUMP_ROM` do Mega Drive com `mapper` 1 (Lion King 3) ou 2 (Pokémon Stadium) e `prg_kb` = tamanho (potência de 2, 128 KB a 4 MB) lê a ROM em pedaços de 32 KB: grava o banco (byte em `$700000`) e lê `$000000` a `$007FFF`; `mapper` 3 (Star Odyssey, D183) usa `prg_kb` múltiplo de 256 (256 a 2048) e pedaços de 256 KB: grava a base `n << 4` em `$000F00` e lê `$000000` a `$03FFFF`; mapa de registrador do MAME (`rom.cpp`, BSD-3), **não vem do OSCR e nunca foi conferido em cartucho**; sem detecção automática (escrever em `$700000` num flash repro pode ser perigoso); fora disso `E_ARGUMENTO`. Regras puras em `include/dumper/MdBank.h` (`pc-tests/test_mdbank.cpp`). **Realtec:** o `DETECT` devolve `name` `Realtec` e `rom_size` 512 KB, e o `DUMP_ROM` lê com `readRealtec` do OSCR (registradores `$400000` e `$404000`). Na gravação da EEPROM cada `DATA` pode levar vários segundos (ver D49).

**Saves do NES/Famicom** (`READ_SAVE` e `WRITE_SAVE`): contam o `mapper` e o segundo campo (`prg_kb`), que aqui é o **tamanho da RAM em KB** (0 = 8). Só 1 (MMC1), 155 (MMC1), 4 (MMC3), 5 (MMC5), 69 (FME-7), 118, 16, 159, 19, 80, 82 e, pelo ramo `default` do `readRAM`/`writeRAM` (8 KB; ligar e desligar a RAM em cada chip), 21, 25, 26 (VRC6), 68, 85 (VRC7) e 153 têm save aceito (F-14, D184): PRG-RAM com bateria de 8 KB em $6000-$7FFF e, nos de D184, **16** = EEPROM serial 24C02 de 256 bytes (I²C, `eepromRead`/`eepromWrite` do OSCR), **159** = 24C01 de 128 bytes, **19** (Namco 163) = SRAM de 8 KB, ou, com `prg_kb` = 1, os 128 bytes de RAM interna do chip, **80** (Taito X1-005) = 128 bytes em `$7F00`, **82** (X1-017) = 5 KB em `$6000`-`$73FF`. Nesses mappers o tamanho do `WRITE_SAVE` é o do chip, não 8 KB. O mapper 1 aceita também 16 KB (SOROM) e 32 KB (SXROM), em bancos de 8 KB escolhidos pelo registrador CHR 0 do MMC1. O mapper 5 aceita 16 KB (dois chips de 8 KB, bancos 0 e 4 em `$5113`) e 32 KB (bancos 0 a 3 em `$5113`); a gravação libera a proteção (`$5102`/`$5103`) a cada byte e protege de novo no fim. O mapper 69 liga a RAM pelo comando 8 (`$A000 = $C0`) e desliga no fim. Outro tamanho, ou 16/32 nos mappers 4 e 69: `ERRO 0x0004`. **Firmware baseado no OSCR (fork, D75):** o mapper 4 com MMC6 (assinatura "STAR") tem RAM de 1 KB e o `WRITE_SAVE` tem que mandar 1.024 bytes; PRG e CHR precisam ser potência de 2 e os mappers 0 e 3 aceitam PRG de até 32 KB. Outro mapper: `ERRO 0x000A`. No `WRITE_SAVE` o tamanho do arquivo tem que bater com a RAM. A gravação confere cada byte; cartucho sem RAM ou com RAM protegida dá `ERRO 0x0007`.

**GBA 369-in-1, leitura (F-18, D174):** `DUMP_ROM` do GBA com o bit 15 do `mapper` ligado (`0x8000 | (bloco << 8)`; bits 0 a 7 e 14 em 0; bloco de 0 a 63, de 4 MB) chama `read369in1` do OSCR ("Read 256MB" e "Read Offset"). Neste modo `prg_kb` é o **tamanho em MB** (não em KB, porque 256 MB não cabe em 16 bits): 0 só vale no bloco 0 e lê os 256 MB; de 1 a 32 MB, e a partir de 4 MB só múltiplos de 4 (o laço do OSCR lê blocos inteiros de 4 MB); a leitura não pode passar do fim dos 32 MB em que o bloco cai (o OSCR não confere e leria além da janela). Pedido fora disso: `ERRO 0x0004`. O mapper comum do GBA (tipo de save, 0 a 6) nunca liga o bit 15, então os pedidos antigos não mudam. O tamanho máximo de um fluxo de leitura subiu de 64 para 256 MB (`MAX_STREAM_BYTES`); a 1 Mbaud, os 256 MB levam cerca de 45 minutos. Regras em `firmware/oscr/include/dumper/Gba369.h`, `host/oscr_host/gba369.py` e `gui/shared/.../Gba369.kt` (três testes conferem as mesmas constantes). Nunca rodou em hardware.

**Saves do GBA** (`READ_SAVE` e `WRITE_SAVE`): o campo `mapper` é o **tipo de save**, com a numeração do OSCR: 0 ou 3 = SRAM/FRAM 32 KB (padrão), 1 = EEPROM 512 bytes, 2 = EEPROM 8 KB, 4 = Flash 64 KB, 5 = Flash 128 KB (dois bancos de 64 KB, trocados pelo comando AA/55/B0). Outro valor: `ERRO 0x0004`. `DETECT` continua sem saber o tipo (`tipo_save` 255, 32 KB). O host acha o tipo na ROM já lida procurando `FLASH1M_V`, `FLASH512_V`, `FLASH_V`, `EEPROM_V`, `SRAM_F_V` ou `SRAM_V`. `WRITE_SAVE` do GBA usa o mesmo campo `mapper` (tipos 0 e 3 a 5 e 1/2 como acima; ver D48): `ERRO 0x0004` se o tamanho não bate com o tipo, `ERRO 0x0007` se o chip Flash é desconhecido, não apaga ou a conferência falha. Cada `DATA` pode levar até ~1 s (EEPROM), por isso o host espera `long_timeout` pelo `ACK`.

**NES/Famicom:**

O cartucho de NES não tem cabeçalho com o mapper. Para mappers diferentes de 0 o host informa `mapper`, `prg_kb` (múltiplo de 16) e `chr_kb` (múltiplo de 8, 0 se o cartucho usa CHR-RAM). Mappers aceitos: 0, 1 (MMC1, PRG até 256 KB), 2, 3, 4, 5 (MMC5, PRG até 1 MB), 7, 9 (MMC2, PRG até 128 KB), 10 (MMC4, PRG até 256 KB), 11 (PRG e CHR até 128 KB), 66 (PRG até 128 KB, CHR até 32 KB), 69 (PRG até 512 KB), 71, e os de CHR-ROM 33/48 (PRG e CHR até 256 KB), 70 (PRG 256 KB, CHR 128 KB), 75 e 78 (PRG e CHR até 128 KB), 79 (até 64 KB cada), 87 (até 32 KB cada), 118 (PRG 512 KB, CHR 256 KB) e 206 (PRG 128 KB, CHR 64 KB); 30 (UNROM 512 e NES Maker flash; PRG até 512 KB, só CHR-RAM, D78); do lote de D64: 13 (CPROM, PRG 32 KB), 34 (BxROM/NINA-001, PRG 512 KB, CHR 64 KB), 67 (PRG e CHR 128 KB), 68 (256 KB cada), 72 (128 KB cada), 73 (VRC3, PRG 128 KB), 86 (PRG 128 KB, CHR 64 KB), 92 (PRG 256 KB, CHR 128 KB), 93 e 94 (PRG 128 KB), 140 e 152 (128 KB cada), 180 (PRG 128 KB) e 184 (32 KB cada); **do lote de D184 (F-14)**, com os limites dos comentários do `readPRG`/`readCHR` do núcleo: 16 e 159 (Bandai FCG), 18 (Jaleco SS8806) e 19 (Namco 163): PRG e CHR até 256 KB; 32 (Irem G-101): PRG 256 KB, CHR 128 KB; 65 (Irem H-3001): 256 KB cada; 80 e 82 (Taito X1-005 e X1-017): PRG 128 KB, CHR 256 KB; 85 (VRC7): PRG 512 KB, CHR 128 KB; 153 (Bandai, CHR-RAM): PRG 512 KB; 154: 128 KB cada; 155 (MMC1 com RAM sempre ligada, mesmos limites do 1); 207 (Taito X1-005 variante): PRG 256 KB, CHR 128 KB; **VRC2, VRC4 e VRC6 (D185):** 21 (VRC4a/c; CHR só 128 ou 256 KB, o núcleo separa as duas variantes pelo tamanho), 22 (VRC2a, CHR 128 KB), 23 (VRC2b/VRC4e/f; o núcleo detecta o VRC4e pela data em `$9FF6`), 24 e 26 (VRC6a/b; CHR 128 KB no 24) e 25 (VRC2c/VRC4b/d): PRG até 256 KB, CHR-ROM obrigatório (mappers 2, 7, 71, 13, 73, 93, 94, 180 e 153 só com CHR 0; 79, 87, 78, 75, 70, 33, 48, 118, 206, 67, 68, 72, 92, 86, 140, 152, 184, 16, 159, 18, 32, 65, 80, 82, 154 e 207 exigem CHR; 34 aceita CHR 0 (BxROM) ou CHR-ROM (NINA-001); 7, 11, 66, 34, 86, 140 e 13 com PRG múltiplo de 32 KB). O mapper 34 espera 200 ms depois de cada troca de banco, então um PRG de 512 KB leva ~3 s a mais. Acima dos limites: `ERRO 0x0002`. `ERRO 0x0002` = mapper não suportado; `ERRO 0x0004` = tamanhos inválidos. O arquivo sai com cabeçalho iNES de 16 bytes (mapper nos nibbles dos bytes 6 e 7; espelhamento e bateria ficam 0). Os valores corretos vêm do banco do No-Intro/NESCartDB ou de uma ROM já conhecida do mesmo jogo.

### Sistema 7: programador de flash genérico (D85)

Lê, apaga, identifica e grava flash e EPROM fora de cartucho de console (adaptadores de flash do OSCR), com as funções de `Flash.cpp`. Campos nos comandos: `chip` (u16; a parte baixa escolhe o barramento) e os dois tamanhos.

| `chip` | Barramento | `prg_kb` | `chr_kb` | Origem no OSCR |
|---|---|---|---|---|
| 1 | flash de 8 bits no adaptador de flash (`mapping` 0) | tamanho do chip em KB (1 a 8192) | tipo do flash \| (log2 do setor << 4) \| (log2 do buffer << 9); 0 = não informado | `setup8`, `id8`, `menuFlash8` |
| 2 | flash de 8 bits PLCC32 no adaptador de SNES (`mapping` 3) | idem | idem | idem |
| 3 | flash de 16 bits | tamanho do chip em KB | 0 | `setup16`, `idFlash16`, `menuFlash16` |
| 4 | EPROM 27C322 | ignorado (4096) | 0 | `setup_Eprom`, `menuEPROM` |
| 5 | flash de um cartucho de Mega Drive no slot MD: **só `DETECT`** | 0 | 0 | `MdFlash::identify` (tabela de `MdFlashCore.h`) |

- `DETECT` com `chip` = 5: identifica o flash do cartucho de Mega Drive pela tabela do firmware. `nome` = `NOME FFDD` (fabricante e dispositivo em hexa) e `rom_size` = capacidade do chip; `status` 0 = chip da tabela, 1 = ID desconhecido (`nome` = `? FFDD`, ou `CFI 32Mbit FFDD` se o chip respondeu à consulta CFI: então `rom_size` é o tamanho dito pelo CFI, só informativo, sem gravação). Ler, apagar e gravar com `chip` = 5 dão `E_ARGUMENTO`: use `DUMP_ROM` e `WRITE_ROM` do sistema Mega Drive. A sondagem escreve comandos de ID no cartucho (ROM de máscara os ignora).
- `DETECT` (com as opções): lê o ID do chip, devolvido como texto em `nome`. No flash de 8 bits sem tipo, devolve `I=XXXX A=XXXX B=XXXX S=XXXX`, os IDs pelas quatro rotinas do `id8` do OSCR (Intel 28F, AMD 29F032, AMD 29F1610, SST 39SF040); `status` 1 se nenhuma respondeu (0000 ou FFFF). O banco CRDB do OSCR, que traduzia o ID em tipo e tamanho, não existe no fork: o usuário informa o tipo.
- `DUMP_ROM`: lê o chip inteiro (`prg_kb` KB). A verificação de "em branco" é do PC (tudo 0xFF).
- `ERASE`: apaga. No 8 bits o tipo é obrigatório; a EPROM não se apaga.
- `WRITE_ROM`: apaga e grava (8 e 16 bits); na EPROM confere antes que está em branco (`E_CARTUCHO_IO` se não). Tamanho múltiplo de 512 e que cabe no chip. A conferência é a leitura de volta do PC.
- Os laços do OSCR (apagar, esperas de status) não têm limite de tempo.

## 5. `DETECT_RESP`

```
u8  sistema
u8  status          0 = cartucho detectado, 1 = nenhum cartucho, 2 = não suportado, 3 = erro de hardware, 4 = cabeçalho inválido (há dados, mas o checksum do cabeçalho não confere: contato sujo ou ROM de hack; SNES e Game Boy) ou, no Mega Drive, cabeçalho ilegível com o `/CART` (D50, placa v. 1.2) baixo, isto é, há cartucho mas ele não leu
u32 tamanho_rom     bytes (0 se desconhecido)
u32 tamanho_save    bytes (0 se não tem)
u8  tipo_save       0 = nenhum, 1 = SRAM, 2 = FLASH, 3 = EEPROM, 255 = desconhecido
u8  n               tamanho do nome
n   nome            ASCII (título interno do cartucho; vazio se desconhecido)
```

## 6. Fluxo de uma leitura (`DUMP_ROM` / `READ_SAVE`)

```
host  -> DUMP_ROM(sistema, bloco)           seq = S
disp  -> BEGIN(tipo, tamanho, bloco)        seq = S
host  -> ACK(offset=0)                      libera o primeiro bloco
disp  -> DATA(offset=0,   bytes[0..bloco))  seq = S
host  -> ACK(offset=0)                      confirma o bloco de offset 0
disp  -> DATA(offset=512, bytes[...])
host  -> ACK(offset=512)
...
disp  -> END(total, crc32)                  seq = S
host  -> ACK(offset=total)                  confirma o fim
```

- **Janela de 1 bloco (pare-e-espere).** O dispositivo só envia o próximo `DATA` depois do `ACK` do anterior. O último bloco pode ser menor que `bloco`.
- Se o host receber um `DATA` com CRC ruim ou `offset` inesperado, envia `NAK(offset)` e o dispositivo reenvia aquele bloco (até 3 vezes; depois `ERRO` 0x0005).
- O host monta o arquivo pelo `offset` (aceita bloco repetido com os mesmos bytes) e, no `END`, confere `total` e o `crc32` do arquivo inteiro. O host mostra o CRC32 para comparar com o No-Intro.
- `ABORT` do host a qualquer momento cancela o fluxo; o dispositivo responde `ACK(0)` e volta ao estado ocioso.

## 7. Escrita de save (`WRITE_SAVE`)

```
host  -> WRITE_SAVE(sistema, tamanho, bloco)  seq = S
disp  -> ACK(offset=0)                        pronto para receber (ou ERRO)
host  -> DATA(offset=0, bytes)
disp  -> ACK(offset=0)
...
host  -> END(total, crc32)
disp  -> ACK(offset=total)                    gravou e verificou, ou ERRO
```

O dispositivo só grava na memória do cartucho **depois** do `END` com CRC32 correto. Em caso de `ERRO`, o save do cartucho não é alterado.

## 8. Códigos de erro (`ERRO`)

| Código | Significado |
|---|---|
| 0x0001 | comando desconhecido ou não suportado nesta compilação |
| 0x0002 | sistema desconhecido ou não suportado |
| 0x0003 | nenhum cartucho detectado |
| 0x0004 | argumento inválido (tamanho, bloco) |
| 0x0005 | número máximo de reenvios excedido |
| 0x0006 | CRC32 do arquivo não confere |
| 0x0007 | erro de leitura/gravação no cartucho |
| 0x0008 | dispositivo ocupado |
| 0x0009 | abortado |
| 0x000A | cartucho não tem save |
| 0x000B | chip de flash não reconhecido (`WRITE_ROM`): nada foi gravado |
| 0x000C | reservado (era `cartucho desligado`, retirado em D139: o 5V dos slots fica sempre ligado) |

## 9. Vetores de teste

CRC32 (IEEE, igual ao `zlib.crc32`):

| Entrada (ASCII) | CRC32 |
|---|---|
| `123456789` | `0xCBF43926` |
| (vazio) | `0x00000000` |
| `OSCR` | `0xD2F82B80` |

Quadro `INFO` com `seq = 0x01`: `A5 5A 01 01 00 00 4E D2 3A 98` (o CRC32 de `01 01 00 00` é `0x983AD24E`, gravado em little-endian). Os testes unitários do host (`host/tests/test_protocol.py`) e do firmware (`firmware/oscr_serial/tests/`) contêm os bytes exatos e devem passar nos dois lados.

Padrão do modo `MOCK` (para `DUMP_ROM` com sistema 255 ou 0): tamanho 32.768 bytes; o byte no offset `i` é `(i * 7 + (i >> 8)) & 0xFF`. O CRC32 esperado do arquivo inteiro é calculado nos testes (e mostrado pela CLI).

## 10. Compatibilidade e evolução

`versão_proto` no `INFO_RESP`. Mudanças que quebram o formato incrementam a versão; o host recusa versão maior que a que conhece. Campos novos só entram no fim dos payloads (o receptor ignora bytes a mais).

## 9. `WRITE_ROM` (gravação de ROM em flash, D77)

Fluxo igual ao do `WRITE_SAVE` (`ACK` inicial, blocos `DATA` com `ACK` por bloco, `END` com o CRC32), com uma diferença que importa: **o primeiro `ACK` só sai depois que o firmware conferiu o chip e apagou o que era preciso** (`Backend::rom_prepare`). A UART do AVR guarda 64 bytes e perderia os blocos que chegassem durante um apagamento de segundos, então o PC só manda dados depois do `ACK`. Por isso o host espera até 90 s por esse `ACK` e **nunca reenvia o comando** (reenviar apagaria de novo).

Campos: `sistema` (NES = 2 ou Famicom = 3), `tamanho` (bytes do que vai ser enviado), `chip`, `prg_kb`, `chr_kb`. O PC tira o cabeçalho iNES (o arquivo enviado é PRG e depois CHR) e escolhe o chip; `tamanho` tem que ser `(prg_kb + chr_kb) * 1024`.

| chip | Cartucho | PRG | CHR | Origem no OSCR |
|---|---|---|---|---|
| 1 | NES Maker, SST 39SF040 (mapper 30); aceita também a SF010A (128 KB) e a SF020A (256 KB), D195 | múltiplo de 16 KB, até 512 KB (e até o tamanho do chip achado: senão `E_ARGUMENTO` antes de apagar) | 0 | `NESmaker_*` em `NES.cpp` |
| 2 | A29040B (mapper 0) | 16 ou 32 KB | 0 ou 8 KB | `A29040B_*` em `NES.cpp` |

**SNES (D79, D82):** `sistema` = 1; o campo `chip` (u16) é `(disposição << 8) | fiação`. Fiação: 1 = LoROM, 2 = HiROM, 3 = ExLoROM, 4 = ExHiROM (3 e 4 só no modo genérico). `tamanho` = bytes da ROM sem o cabeçalho de copiadora (múltiplo de 512). O `rom_prepare` identifica o chip e apaga **todos** os chips (E_FLASH se não responde ou é menor que o necessário); depois os dados entram na ordem dos segmentos.

| disposição | Menu do OSCR | `prg_kb` | `chr_kb` | Trechos do fluxo (chip, endereço, bytes, de onde no arquivo) |
|---|---|---|---|---|
| 0 | CFI, 1x 2MB / 1x 4MB | 2048 ou 4096 | 0 | chip 1, 0, tamanho, 0 |
| 1 | CFI, 2x 2MB | 4096 | 0 | chip 1: 0, min(tam, 2 MB), 0; chip 2: 0, tam − 2 MB (ou 0), a partir de 2 MB |
| 2 | CFI, 2x 4MB | 8192 | 0 | ROM de 6 a 8 MB; chip 1: tam − 4 MB do arquivo a partir de 4 MB; chip 2: 4 MB do começo |
| 3 | CFI, 4x 2MB | 8192 | 0 | ROM de 6 a 8 MB; chip 1: arquivo 4 a 6 MB; chip 2: 6 a 8 MB (vazio se a ROM tem 6 MB); chip 3: 0 a 2 MB; chip 4: 2 a 4 MB |
| 4 | CFI, 1x 8MB | 8192 | 0 | ROM de 6 ou 8 MB; chip 1 endereço 0: arquivo a partir de 4 MB (tam − 4 MB); endereço 4 MB: arquivo 0 a 4 MB |
| 0x10 (genérico) | LoROM/HiROM (P0), ExLoROM/ExHiROM (P1) | tamanho do chip em KB (1024 a 8192) | tipo do flash \| (log2 do setor em bytes << 4) \| (log2 do buffer em bytes << 9) | o arquivo inteiro, na ordem |

As disposições 1 a 4 são as regras do `adjustFileSizeOffset` e do `writeCFI` do OSCR (Flash.cpp) aplicadas pelo PC: o firmware não faz `seek` no fluxo, então o PC manda os trechos já reordenados, e o plano está em `firmware/oscr/include/dumper/SnesPlan.h` (código puro, testado em `pc-tests/test_snes_plan.cpp`), espelhado em `host/oscr_host/romimage.py` (`snes_plan`) e `RomImage.kt`, com os mesmos vetores nos três testes. Os chips apagam ao mesmo tempo e o firmware espera DQ7 de cada um por até 80 s no total. Em 1x 8MB o OSCR só se comporta bem com 6 ou 8 MB (em outros tamanhos lê além do fim do arquivo), então só esses dois são aceitos.

**GBA (D83):** `sistema` = 5; `chip` = `(bloco << 8) | 1`, em que o bloco (0 a 63, de 4 MB) só vale no 369-in-1 ("Write Offset" do OSCR; bloco 0 é o "Write 256MB"); `prg_kb` = tamanho da ROM em KB (limitado a 65535, informativo); `chr_kb` = 0; `tamanho` = bytes da ROM (múltiplo de 1 KB; até 32 MB, ou até 256 MB no bloco 0 do 369-in-1). O `rom_prepare` lê o ID com `idFlashrom` do OSCR (`E_FLASH` se não reconhece), recusa bloco ≠ 0 fora do 369-in-1 (`E_ARGUMENTO`) e apaga o que a ROM ocupa. Chips: Intel 4000L0YBQ0 (`0x8802`) e 4400L0ZDQ0 (`0x8816`), MX29GL128E, MSP55LV128(N), PC28F256M29 e M29W128GH (`0x227E`, distinguidos pelo fabricante), 369-in-1 F0088H0 (`0x8812`). O firmware (`src/dumper/GbaFlash.cpp`) chama as funções do OSCR na ordem do `flashRepro`, sem o `verifyFlashrom` (que relê o arquivo). Para a conferência, o `DUMP_ROM` do GBA passou a aceitar `prg_kb` como tamanho da ROM (a detecção por espelho vê o flash inteiro). Laços do OSCR sem limite de tempo.

**N64 (F-19, D176):** `sistema` = 11; `chip` = 1 (flash repro; o firmware identifica o chip pelo ID); `prg_kb` = tamanho da ROM em KB (limitado a 65535, informativo); `chr_kb` = 0; `tamanho` = bytes da ROM em ordem z64, **múltiplo de 128 KB, de 128 KB a 64 MB** (o `flashRepro` do OSCR lê o arquivo em setores de 128 KB, ou 32 KB no MX29LV640; o host converte v64 e n64 para z64 e completa com `$FF`). O `rom_prepare` lê o ID com `idFlashrom` do OSCR (`E_FLASH` se `cartSize` fica 0: ROM de máscara ou chip fora da lista), recusa ROM maior que o chip achado (`E_ARGUMENTO`; o OSCR divide por 1 MB e arredonda para baixo, aqui a conta é em bytes), apaga (`eraseSector(0x20000)` nos 227E, `eraseSector(0x8000)` no MX29LV640, `eraseMSP55LV100`, `eraseIntel4400`) e confere em branco com `blankcheckFlashrom` (`E_FLASH` se não ficou em branco; sem isso o OSCR não grava). Chips: Spansion S29GL256N (32 ou 64 MB, um ou dois chips) e S29GL128N, ST M29W128GL, Macronix MX29LV640 (um ou dois), Intel 4400L0ZDQ0 e 512M29EW, Fujitsu MSP55LV100S e MSP55LV512. **Desvios do OSCR:** o menu de chip desconhecido (tamanho, buffer e setor à mão) não existe: chip desconhecido é recusado, porque o OSCR calcula o tamanho do setor a partir da tabela de buffers (defeito dele); o `verifyFlashrom` (que relê o arquivo) é feito pelo PC, lendo o cartucho de volta (`DUMP_ROM` do N64, `prg_kb` em MB, comparando só o prefixo gravado). O apagamento e o blankcheck de até 64 MB levam minutos antes do primeiro ACK: o host espera 600 s por padrão no N64 (`--begin-timeout`). Laços do OSCR sem limite de tempo. Gameshark e Xplorer 64: ver o parágrafo seguinte.

**N64, Gameshark e Xplorer 64 (F-19, D177):** a flash do próprio acessório, não de um cartucho de jogo. `WRITE_ROM` do sistema 11 com `chip` = 2 (Gameshark) ou 3 (Xplorer 64). **Gameshark:** `tamanho` = múltiplo de 16 KB, de 16 KB a 1 MB (páginas de 256 bytes nos 2 x 29LE010 e parentes, setores de 16 KB no SST 28LF040); o `rom_prepare` lê o ID (`unlockGSAddressRanges` e `idGameshark` do OSCR: 0x0808 SST 29LE010, 0x3535 AT29LV010A, 0x0707 SST 29EE010, 0x0404 SST 28LF040; outro valor: `E_FLASH`), recusa o que não cabe no chip achado (256 KB nos três primeiros, 1 MB no último; `E_ARGUMENTO`), apaga (`eraseGameshark`) e confere em branco (`blankCheck`, `E_FLASH` se falhar). **Xplorer 64:** `tamanho` = exatamente 262144; ID por `idXplorer` (0x0808); `eraseXplorer` e `blankCheck_XP64`. **O Xplorer 64 recebe o arquivo reordenado pelo PC:** o `writeXplorer` do OSCR busca a palavra j do buffer em `unscramble(j)` do arquivo com `seekSet`, e o `StreamFile::seekSet` do fork só aceita ficar onde está; então o host manda, na posição j do fluxo, a palavra `unscramble(j)` do arquivo (`split_xplorer`; a função é a do OSCR, e um teste do host a confere contra o texto do `N64.cpp`), e o firmware chama o `writeXplorer` do OSCR sem mudança. O CRC32 do `END` é o do fluxo reordenado. **Backup obrigatório antes de apagar:** `DUMP_ROM` do sistema 11 com o **bit 15 do `mapper` ligado** e o chip nos bits 0 a 7 (`0x8002` Gameshark, `0x8003` Xplorer 64; o `prg_kb` é ignorado) chama `backupGameshark` (256 KB, ou 1 MB no SST 28LF040) ou `backupXplorer` (256 KB) do OSCR; ID desconhecido: `E_FLASH`; qualquer outro valor com o bit 15: `E_ARGUMENTO`. O bit 15 evita confundir com o `mapper` comum do N64 (tipo de save, 0 a 6). A CLI e a GUI leem esse backup, gravam em `--backup-dir` (padrão `~/oscr_backups`) e só então mandam o `WRITE_ROM`; `--no-backup` pula (a flash do acessório não tem outra cópia). A conferência depois de gravar é a leitura de volta com o mesmo `DUMP_ROM`, comparando só o tamanho gravado. Laços do OSCR sem limite de tempo. O OSCR avisa que o SST 29EE010 (0x0707) talvez exija 5 V para gravar: o N64 daqui fica em 3,3 V; leitura funciona, **gravação nesse chip não foi testada por ninguém**.

**SNES, BS-X e SF Memory (F-11, D187):** no mesmo terceiro campo de acessório, `0x8004` = Memory Pack do BS-X (`DUMP_ROM`, 1 MB; confere antes o checksum `8B86` em `$00:FFDE` do cartucho base: sem ele `ERRO 0x0003`), `0x8005` = SRAM do BS-X (`READ_SAVE` e `WRITE_SAVE`, 32.768 bytes, bancos `$10` a `$17`, `$5000` a `$5FFF`), `0x8006` = flash inteira do SF Memory Cassette (`DUMP_ROM`, 4 MB), `0x8007` = mapeamento do SFM (`DUMP_ROM`, 512 bytes), `0x8010` a `0x8016` = jogo 0 a 6 do SFM (`DUMP_ROM`: o firmware destrava o cassete, lê o menu (`getGames` do OSCR), troca para o jogo, espera `7Dh` com no máximo 5 tentativas e lê o jogo; índice que não existe no menu: `ERRO 0x0007`). Só o GPC e a SRAM do BS-X gravam; os outros recusam `WRITE_SAVE` com `ERRO 0x0004`. **Game Boy, acessórios (F-17, D186):** `DUMP_ROM` do sistema 6 com `mapper` de 1 a 6 lê um acessório em vez de um jogo (sem cabeçalho de jogo, `prg_kb` e `chr_kb` ignorados): 1 Pelican (`readPelican`: 256 KB com 29EE020/W29C020, 512 KB com SST 28LF040), 2 Datel Mega Memory (`readMegaMem`: ROM de 16 KB e depois 32 bancos de 16 KB de dados, 540.672 bytes no total), 3 GameShark GBC (`readGameshark`: SST 39SF010, 128 KB), 4 GB Memory Module (`readROM` do `GameBoyMem`, 1 MB), 5 mapeamento do GB Memory Module (`readMapping`, 128 bytes), 6 GB Smart Card (`readFlash`, 4 MB). Outro valor: `ERRO 0x0004`. Sem o acessório (ID desconhecido) a leitura termina sem bytes: `ERRO 0x0007`; o GB Memory Module sem o módulo estourava num laço sem fim no OSCR e agora vira o mesmo erro (limite de 10 tentativas). **Gravação (D188):** `WRITE_ROM` do sistema 6 com `chip` 9 = Pelican (arquivo de 262.144 bytes no W29C020/29EE020 ou de 524.288 no SST 28LF040; o tamanho tem que bater com o chip achado, `ERRO 0x0004` antes de apagar), 10 = Mega Memory (só o chip de dados, 524.288 bytes), 11 = GameShark GBC (131.072 bytes); ID desconhecido: `ERRO 0x000B`; apagar que não deixa tudo `FF`, ou byte que não grava no limite de tempo: `ERRO 0x0007`. As sequências são as de `writePelican`, `writeMegaMem` e `writeGameshark` do OSCR, com todo laço de espera limitado e sem a conferência que relê o arquivo (o PC lê de volta com `DUMP_ROM` e `mapper` 1, 2 ou 3; no Mega Memory descarta os 16 KB de ROM que vêm antes). O PC lê o backup do acessório antes de apagar (`--no-backup` desliga). **Módulos da Nintendo (D189):** `WRITE_ROM` do sistema 6 com `chip` 12 = GB Memory Module (ROM de 1.048.576 bytes, `writeFlash` do `GameBoyMem`), 13 = mapeamento do GB Memory Module (128 bytes, `writeMapping`), 14 = GB Smart Card 32M (4.194.304 bytes, as duas LH28F016SUT, `writeFlash` do `GameBoySmart`). O tamanho tem que ser exato (`ERRO 0x0004` antes de apagar). ID: o GB Memory só grava com o ID `C289` (senão `ERRO 0x000B`); o GB Smart recusa ID `0000` ou `FFFF` em qualquer das duas flashes (o OSCR não confere ID nenhum). Apagar que não fica em `FF` ou página que não grava no limite de tempo: `ERRO 0x0007`. O PC lê o backup antes de apagar (`DUMP_ROM` com `mapper` 4, 5 ou 6; `--no-backup` desliga) e confere depois pela mesma leitura. **Memory Pack do BS-X e SF Memory Cassette (D190):** `WRITE_ROM` do sistema 1 (SNES) com `chip` = `0x2001` (Memory Pack, arquivo de 1.048.576 bytes), `0x2002` (flash do SFM, 4.194.304 bytes: 2 MiB para o chip do banco `$C0` e 2 MiB para o do `$E0`) ou `0x2003` (mapeamento do SFM, 512 bytes: 256 para `$D0` e 256 para `$E0`); `chr_kb` = 0 e `prg_kb` informativo. O tamanho tem que ser exato (`ERRO 0x0004` antes de apagar). Sem o cartucho base do BS-X (checksum `8B86`) ou sem o cassete (o destrave do SFM falha): `ERRO 0x0003`; ID das flashes diferente de `C2F3` ou apagar que não fica em `FF`: `ERRO 0x000B`; espera que estoura o limite, byte ou página que não grava, arquivo que acaba antes: `ERRO 0x0007`. Sequências do `Satellaview::writeFlash`, `SFM::write`, `eraseMapping` e `writeMapping` do OSCR, com todo laço de espera limitado. O PC lê o backup antes de apagar (`DUMP_ROM` do SNES com o terceiro campo `0x8004`, `0x8006` ou `0x8007`; `--no-backup` desliga) e confere depois pela mesma leitura. O primeiro ACK vem depois do apagamento e da conferência em branco, então o PC espera até 300 s. **Game Boy (D84):** `sistema` = 6; `chip` = o item do menu do OSCR: 1 DIY MBC3 (WR), 2 DIY MBC5 (WR), 3 HDR MBC30 (WE no pino de áudio), 4 HDR GameBoy Cam 1º jogo (apaga), 5 HDR GameBoy Cam 2º jogo (sem apagar), 6 Orange FM (39SF010 sem MBC, só 32 KB), 7 39SF040 MBC5 (WE no pino de áudio), 8 flash CFI; `prg_kb` = tamanho da ROM em KB (informativo); `chr_kb` = 0; `tamanho` = bytes (múltiplo de 16 KB, 32 KB a 4 MB; o número de bancos sai do tamanho). O `rom_prepare` lê o ID (E_FLASH se 0000 ou FFFF; no CFI, se não responde ao CFI; E_ARGUMENTO se a ROM tem mais bancos que o chip) e apaga o chip (menos no chip 5). O firmware (`src/dumper/GbFlash.cpp`) usa direto `cartOn`, `writeByte`, `readByte`, `sendFlashCommand`, `sendCFICommand`, `identifyCFI` do OSCR. O `GB::writeFlash` e o `GB::writeCFI` inteiros não servem: consultam o banco CRDB, usam seek/rewind e releem o arquivo; só o laço dos bancos é do fork, com limite de tempo por byte. O ID do 29F não é conferido contra uma lista (no OSCR vinha do CRDB); a conferência da gravação é a leitura de volta do PC.

**Game Boy, relógio do MBC3 (F-17, D192):** `DUMP_ROM` do GB com `mapper` = 7 devolve 5 bytes, e `WRITE_SAVE` do GB com `mapper` = 7 e tamanho 5 grava 5 bytes: segundos, minutos, horas, dias (byte baixo) e dias (byte alto: bit 0 = bit 8 dos dias, bit 6 = parado, bit 7 = estouro), na ordem dos registradores 08h a 0Ch. O firmware confere o byte `0x0147` do cabeçalho (`0Fh` ou `10h`); outro tipo responde `ERRO 0x000A` (`E_SEM_SAVE`). Leitura: habilita (`0x0A` em `0x0000`), trava (`0` e `1` em `0x6000`), seleciona cada registrador em `0x4000` e lê em `0xA000` com o CS (`readByteSRAM`). Gravação: para o relógio (bit 6 do dia alto), escreve os quatro primeiros e por último o dia alto com o bit de parada pedido; o firmware recusa (`E_ARGUMENTO`) segundos ou minutos acima de 59, horas acima de 23 e bits fora de 0, 6 e 7 no dia alto. O PC confere lendo de volta (andando, aceita até 2 s a mais). Sem hora no firmware: a hora vem do PC.

**Modo genérico (P0/P1):** o firmware chama direto `eraseFlash*`, `writeFlash*` e `idFlash*` do `menuFlash8` do OSCR, escolhidos pelo tipo (`FlashType` do `Flash.h`: 1 29F032, 2 29F1610, 3 LH28F0XX, 4 29F1601, 5 29LV640, 6 29F800, 7 29GL, 8 E28FXXXJ3A). No OSCR o tipo, o tamanho, o setor e o buffer vinham do banco CRDB do cartão SD; aqui o PC informa. Tipos 29GL, LH28F0XX e E28FXXXJ3A exigem setor e buffer; no 29GL o PC completa a ROM com 0xFF até um múltiplo do setor (o OSCR grava setores inteiros). Esses laços do OSCR **não têm limite de tempo**.

Erros: `0x0004` (chip ou tamanhos inválidos, antes de tocar no cartucho), `0x000B` (ID do chip diferente do esperado: nada foi gravado), `0x0007` (um byte não gravou dentro do limite de tempo: o chip pode ter ficado apagado ou pela metade, regrave), `0x0001` (firmware sem `WRITE_ROM`), `0x0006` (CRC32 do arquivo não confere).

**Mega Drive (D81, D86):** `sistema` = 4; `chip` 1 = automático; `prg_kb` = tamanho da ROM em KB arredondado para cima (informativo); `chr_kb` = 0; `tamanho` = bytes da ROM (par, até 8 MB). O `rom_prepare` sonda o chip (ID com desbloqueio 5555h, depois 555h, depois Intel; tabela em `include/dumper/MdFlashCore.h`: MX29F1610, S29GL064N, M29W320/640, MX29LV320/640, MX29L3211, PA28F400, LH28F320BJE, AM29F800, SST39VF320x/640x; outro ID → `E_FLASH`), confere que a ROM cabe **no chip encontrado** (`E_ARGUMENTO`) e apaga: o chip inteiro no MX29F1610 e no S29GL064N, setores ou blocos por layout nos demais. O firmware (`src/dumper/MdFlash.cpp`) chama `MD::eraseFlash`, `resetFlash`, `write29F1610` e `write29GL` do OSCR nos dois chips do OSCR, que leem o "arquivo" pelo `StreamFile`; os outros usam o núcleo `MdFlashCore.h`. Os laços de espera ganharam limite de tempo: apagar ou gravar que não termina devolve `E_CARTUCHO_IO` em vez de travar. Depois de apagar, o firmware lê de volta a área da ROM e exige `FFFFh` (`blankRange`); sobra de dado devolve `E_CARTUCHO_IO` (nativos: `kNotBlank`). O nome do chip no `DETECT` do sistema 7 traz os quatro bytes do autoselect (`S29GL064N 017E1000`).

No SNES o firmware (`src/dumper/SnesFlash.cpp`) usa direto `Flash::setup8`, `identifyCFIbyIds`, `sendCFICommand`, `writeByte`, `readByte`, `writeByteCompensated`; o laço de apagar e gravar é novo pelo mesmo motivo (o `writeCFI` do OSCR lê o SD e o `busyWait` espera para sempre), e a conferência do `verifyFlash` (que relê o arquivo) é feita pelo PC com `DUMP_ROM` (`prg_kb` = tamanho da ROM). As opções do OSCR com 2 ou 4 chips e a de 8 MB ainda não existem. O firmware usa direto as funções do OSCR original (`NESmaker_ID`, `NESmaker_SectorErase`, `NESmaker_ByteProgram`, `A29040B_*`); o laço de gravação é novo porque o original lê o arquivo do SD e espera para sempre (`do { } while`) por um byte que talvez nunca confira, enquanto aqui toda espera tem limite de tempo. **Conferência depois da gravação (D78):** é do PC e vem ligada por padrão. Depois do `END`, o host faz um `DUMP_ROM` com o mapper do chip (30 ou 0) e os tamanhos gravados, tira o cabeçalho iNES sintético e compara byte a byte com o que enviou. O mapper 30 passou a ter leitura de ROM no firmware (o `readPRG` do OSCR já tratava o caso 30; só faltava liberá-lo em `nesCheckRom`, PRG até 512 KB e só CHR-RAM). O OSCR original só conferia cada byte logo depois de programá-lo; a leitura completa pega também o que mudou depois.

