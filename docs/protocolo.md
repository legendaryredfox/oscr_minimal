# Protocolo serial — oscr_minimal

Versão do protocolo: **1**. Escrito antes da implementação (`CLAUDE.md`, seção 9). Quem implementa (firmware, `host/`, `gui/`) deve seguir este documento; os vetores de teste da seção 9 valem para todos.

## 1. Camada física

- USB serial do Mega (CH340 ou ATmega16U2), 8 bits, sem paridade, 1 stop bit, sem controle de fluxo.
- **Baud padrão 1.000.000.** Fallback: **115.200**. O host tenta 1.000.000, manda `INFO`, espera 500 ms; se não houver resposta, tenta 115.200. O firmware abre a serial em 1.000.000 (configurável em `firmware/.../oscr_config.h`: `OSCR_BAUD`); uma compilação com `OSCR_BAUD 115200` usa só o fallback.
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
| `0x0C` | `ERASE` | `u8 sistema`, `u16 chip`, `u16 prg_kb`, `u16 chr_kb` (as três últimas sempre enviadas). Só o sistema 7 (programador de flash genérico, D85): apaga o chip inteiro e responde `ACK` (offset 0) só no fim, ou `ERRO`. O host espera até 90 s e **nunca reenvia** (reenviar apagaria de novo). `INFO_RESP.flags` bit 4 diz que existe |
| `0x0B` | `WRITE_ROM` | `u8 sistema`, `u32 tamanho`, `u16 bloco`, `u16 chip`, `u16 prg_kb`, `u16 chr_kb` (os três últimos são sempre enviados). Grava a **ROM** em cartucho de flash (D77). Só no firmware em modo fluxo (fork do OSCR); `INFO_RESP.flags` bit 3 diz que existe |
| `0x0D` | `POWER` | `u8 ação`: 0 desliga, 1 liga, 2 consulta o 5V dos slots (chave de 5V da placa, D115). Responde `POWER_RESP`. Desligar solta todos os pinos de sinal, abre a chave e espera a descarga (até ~2 s; o host espera até 5 s). Sem a chave na placa (`INFO` flag bit 5 = 0), ligar e consultar respondem o estado (sempre ligado) e desligar devolve `0x0001`. Com a chave e o 5V desligado, `DETECT`, `DUMP_ROM`, `READ_SAVE`, `WRITE_SAVE`, `WRITE_ROM` e `ERASE` (qualquer sistema menos o `MOCK`) devolvem `0x000C` |

### Dispositivo → host

| Tipo | Nome | Payload |
|---|---|---|
| `0x81` | `INFO_RESP` | `u8 versão_proto`, `u8 maior`, `u8 menor`, `u8 patch` (firmware), `u8 flags`, `u16 sistemas` (máscara de bits, bit = id do sistema), `u16 max_payload` (maior payload que o dispositivo aceita: 1024 no PC/simulador, 520 no AVR; o host usa bloco ≤ `max_payload` − 4; opcional para o host, o campo vem no fim) |
| `0x82` | `DETECT_RESP` | ver seção 5. **Campo opcional depois do nome (D119):** `u8 tentativas` — só no SNES, só quando o firmware precisou de mais de uma leitura do cabeçalho por causa do ciclo de energia do SA-1 (placa com a chave de 5V); ausente = 1. Hosts antigos ignoram o byte |
| `0x83` | `BEGIN` | `u8 tipo_dado` (1 = ROM, 2 = save), `u32 tamanho`, `u16 bloco`. **Tamanho `0xFFFFFFFF` = desconhecido** (firmware baseado nos núcleos do OSCR, modo fluxo: o tamanho real e o CRC32 vêm no `END`; o host aceita qualquer `offset` sequencial até o `END`, e a barra de progresso usa o tamanho do `DETECT`) |
| `0x84` | `DATA` | `u32 offset` + dados (até `bloco` bytes) |
| `0x85` | `END` | `u32 total`, `u32 crc32` do arquivo inteiro |
| `0x86` | `ACK` | `u32 offset` (confirma um pedido ou um bloco de `WRITE_SAVE`) |
| `0x87` | `ERRO` | `u16 código`, `u8 n`, `n` bytes de texto ASCII (diagnóstico, não traduzido) |
| `0x88` | `PROGRESSO` | `u32 offset`, `u32 total` (opcional, a cada ~1 s sem `DATA`) |
| `0x89` | `POWER_RESP` | `u8 estado` (1 = 5V ligado), `u8 recursos` (bit 0 chave física no D18 lida, bit 1 sensor do rail no D53, bit 2 descarga forçada Q2), `u8 chave` (0 aberta, 1 fechada, `0xFF` sem chave física), `u8 rail` (0 baixo = seguro trocar, 1 alto, `0xFF` sem sensor). Placa só com o Q1 (v1.2 da `16_bits`): recursos 0, chave e rail `0xFF`. Com a chave física a flag `INFO` bit 5 também vale 1 (D119) |

`seq` do host é livre (incremente a cada pedido). O dispositivo repete o `seq` do pedido em todas as respostas daquele pedido (`DATA` do mesmo fluxo repete o `seq` do `DUMP_ROM`/`READ_SAVE`).

### Flags de `INFO_RESP`
bit 0: modo `MOCK` ligado (dados sintéticos, sem cartucho); bit 1: Si5351 detectado; bit 2: PIC (CIC) presente (informativo, pode ser 0 se não houver como detectar); bit 3: aceita `WRITE_ROM` (D77); bit 5: a placa tem a chave de 5V dos slots (`POWER`; o firmware começa com o 5V desligado, D115); bit 4: tem o programador de flash genérico (sistema 7 e `ERASE`, D85); demais: 0.

## 4. Sistemas

| Id | Sistema | Extensão do arquivo de ROM |
|---|---|---|
| 1 | SNES/SFC | `.sfc` |
| 2 | NES | `.nes` |
| 3 | Famicom | `.nes` |
| 4 | Mega Drive/Genesis | `.md` |
| 5 | GBA (3,3 V) | `.gba` |
| 6 | Game Boy / Game Boy Color (via adaptador no slot GBA, 3,3 V) | `.gb` (os jogos só de GBC podem ser renomeados para `.gbc`) |
| 255 | `MOCK` (teste, sem cartucho) | `.bin` |

### Opções de `DUMP_ROM` para NES/Famicom e Mega Drive

**Mega Drive:** só `prg_kb` conta e significa o **tamanho da ROM em KB** (0 = pelo cabeçalho, com redução automática quando a ROM aparece espelhada). Mínimo 32 KB; máximo 4 MB (8 MB com o mapper SSF2). `ERRO 0x0004` fora desses limites.

**SNES:** só no ExHiROM, `prg_kb` é o **tamanho da ROM em KB** (0 = pelo cabeçalho; cabeçalho de 8 MB vira 6 MB). Múltiplo de 64, máximo 8064; outro valor `ERRO 0x0004`. LoROM e HiROM ignoram as opções.

**Saves do Mega Drive** (`READ_SAVE` e `WRITE_SAVE`): a SRAM ou a EEPROM serial, conforme o cabeçalho; sem opções. Na gravação da EEPROM cada `DATA` pode levar vários segundos (ver D49).

**Saves do NES/Famicom** (`READ_SAVE` e `WRITE_SAVE`): contam o `mapper` e o segundo campo (`prg_kb`), que aqui é o **tamanho da RAM em KB** (0 = 8). Só 1 (MMC1), 4 (MMC3), 5 (MMC5) e 69 (FME-7) têm PRG-RAM com bateria aceita (8 KB em $6000-$7FFF). O mapper 1 aceita também 16 KB (SOROM) e 32 KB (SXROM), em bancos de 8 KB escolhidos pelo registrador CHR 0 do MMC1. O mapper 5 aceita 16 KB (dois chips de 8 KB, bancos 0 e 4 em `$5113`) e 32 KB (bancos 0 a 3 em `$5113`); a gravação libera a proteção (`$5102`/`$5103`) a cada byte e protege de novo no fim. O mapper 69 liga a RAM pelo comando 8 (`$A000 = $C0`) e desliga no fim. Outro tamanho, ou 16/32 nos mappers 4 e 69: `ERRO 0x0004`. **Firmware baseado no OSCR (fork, D75):** o mapper 4 com MMC6 (assinatura "STAR") tem RAM de 1 KB e o `WRITE_SAVE` tem que mandar 1.024 bytes; PRG e CHR precisam ser potência de 2 e os mappers 0 e 3 aceitam PRG de até 32 KB. Outro mapper: `ERRO 0x000A`. No `WRITE_SAVE` o tamanho do arquivo tem que bater com a RAM. A gravação confere cada byte; cartucho sem RAM ou com RAM protegida dá `ERRO 0x0007`.

**Saves do GBA** (`READ_SAVE` e `WRITE_SAVE`): o campo `mapper` é o **tipo de save**, com a numeração do OSCR: 0 ou 3 = SRAM/FRAM 32 KB (padrão), 1 = EEPROM 512 bytes, 2 = EEPROM 8 KB, 4 = Flash 64 KB, 5 = Flash 128 KB (dois bancos de 64 KB, trocados pelo comando AA/55/B0). Outro valor: `ERRO 0x0004`. `DETECT` continua sem saber o tipo (`tipo_save` 255, 32 KB). O host acha o tipo na ROM já lida procurando `FLASH1M_V`, `FLASH512_V`, `FLASH_V`, `EEPROM_V`, `SRAM_F_V` ou `SRAM_V`. `WRITE_SAVE` do GBA usa o mesmo campo `mapper` (tipos 0 e 3 a 5 e 1/2 como acima; ver D48): `ERRO 0x0004` se o tamanho não bate com o tipo, `ERRO 0x0007` se o chip Flash é desconhecido, não apaga ou a conferência falha. Cada `DATA` pode levar até ~1 s (EEPROM), por isso o host espera `long_timeout` pelo `ACK`.

**NES/Famicom:**

O cartucho de NES não tem cabeçalho com o mapper. Para mappers diferentes de 0 o host informa `mapper`, `prg_kb` (múltiplo de 16) e `chr_kb` (múltiplo de 8, 0 se o cartucho usa CHR-RAM). Mappers aceitos: 0, 1 (MMC1, PRG até 256 KB), 2, 3, 4, 5 (MMC5, PRG até 1 MB), 7, 9 (MMC2, PRG até 128 KB), 10 (MMC4, PRG até 256 KB), 11 (PRG e CHR até 128 KB), 66 (PRG até 128 KB, CHR até 32 KB), 69 (PRG até 512 KB), 71, e os de CHR-ROM 33/48 (PRG e CHR até 256 KB), 70 (PRG 256 KB, CHR 128 KB), 75 e 78 (PRG e CHR até 128 KB), 79 (até 64 KB cada), 87 (até 32 KB cada), 118 (PRG 512 KB, CHR 256 KB) e 206 (PRG 128 KB, CHR 64 KB); 30 (UNROM 512 e NES Maker flash; PRG até 512 KB, só CHR-RAM, D78); do lote de D64: 13 (CPROM, PRG 32 KB), 34 (BxROM/NINA-001, PRG 512 KB, CHR 64 KB), 67 (PRG e CHR 128 KB), 68 (256 KB cada), 72 (128 KB cada), 73 (VRC3, PRG 128 KB), 86 (PRG 128 KB, CHR 64 KB), 92 (PRG 256 KB, CHR 128 KB), 93 e 94 (PRG 128 KB), 140 e 152 (128 KB cada), 180 (PRG 128 KB) e 184 (32 KB cada) (mappers 2, 7, 71, 13, 73, 93, 94 e 180 só com CHR 0; 79, 87, 78, 75, 70, 33, 48, 118, 206, 67, 68, 72, 92, 86, 140, 152 e 184 exigem CHR; 34 aceita CHR 0 (BxROM) ou CHR-ROM (NINA-001); 7, 11, 66, 34, 86, 140 e 13 com PRG múltiplo de 32 KB). O mapper 34 espera 200 ms depois de cada troca de banco, então um PRG de 512 KB leva ~3 s a mais. Acima dos limites: `ERRO 0x0002`. `ERRO 0x0002` = mapper não suportado; `ERRO 0x0004` = tamanhos inválidos. O arquivo sai com cabeçalho iNES de 16 bytes (mapper nos nibbles dos bytes 6 e 7; espelhamento e bateria ficam 0). Os valores corretos vêm do banco do No-Intro/NESCartDB ou de uma ROM já conhecida do mesmo jogo.

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
| 0x000C | cartucho desligado: a placa tem a chave de 5V e o 5V dos slots está cortado (`POWER`). Com texto `chave` (`POWER` ligar com a chave física aberta, D119); com texto `off` (comando de cartucho com o 5V desligado) |

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
| 1 | NES Maker, SST 39SF040 (mapper 30) | múltiplo de 16 KB, até 512 KB | 0 | `NESmaker_*` em `NES.cpp` |
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

**Game Boy (D84):** `sistema` = 6; `chip` = o item do menu do OSCR: 1 DIY MBC3 (WR), 2 DIY MBC5 (WR), 3 HDR MBC30 (WE no pino de áudio), 4 HDR GameBoy Cam 1º jogo (apaga), 5 HDR GameBoy Cam 2º jogo (sem apagar), 6 Orange FM (39SF010 sem MBC, só 32 KB), 7 39SF040 MBC5 (WE no pino de áudio), 8 flash CFI; `prg_kb` = tamanho da ROM em KB (informativo); `chr_kb` = 0; `tamanho` = bytes (múltiplo de 16 KB, 32 KB a 4 MB; o número de bancos sai do tamanho). O `rom_prepare` lê o ID (E_FLASH se 0000 ou FFFF; no CFI, se não responde ao CFI; E_ARGUMENTO se a ROM tem mais bancos que o chip) e apaga o chip (menos no chip 5). O firmware (`src/dumper/GbFlash.cpp`) usa direto `cartOn`, `writeByte`, `readByte`, `sendFlashCommand`, `sendCFICommand`, `identifyCFI` do OSCR. O `GB::writeFlash` e o `GB::writeCFI` inteiros não servem: consultam o banco CRDB, usam seek/rewind e releem o arquivo; só o laço dos bancos é do fork, com limite de tempo por byte. O ID do 29F não é conferido contra uma lista (no OSCR vinha do CRDB); a conferência da gravação é a leitura de volta do PC.

**Modo genérico (P0/P1):** o firmware chama direto `eraseFlash*`, `writeFlash*` e `idFlash*` do `menuFlash8` do OSCR, escolhidos pelo tipo (`FlashType` do `Flash.h`: 1 29F032, 2 29F1610, 3 LH28F0XX, 4 29F1601, 5 29LV640, 6 29F800, 7 29GL, 8 E28FXXXJ3A). No OSCR o tipo, o tamanho, o setor e o buffer vinham do banco CRDB do cartão SD; aqui o PC informa. Tipos 29GL, LH28F0XX e E28FXXXJ3A exigem setor e buffer; no 29GL o PC completa a ROM com 0xFF até um múltiplo do setor (o OSCR grava setores inteiros). Esses laços do OSCR **não têm limite de tempo**.

Erros: `0x0004` (chip ou tamanhos inválidos, antes de tocar no cartucho), `0x000B` (ID do chip diferente do esperado: nada foi gravado), `0x0007` (um byte não gravou dentro do limite de tempo: o chip pode ter ficado apagado ou pela metade, regrave), `0x0001` (firmware sem `WRITE_ROM`), `0x0006` (CRC32 do arquivo não confere).

**Mega Drive (D81, D86):** `sistema` = 4; `chip` 1 = automático; `prg_kb` = tamanho da ROM em KB arredondado para cima (informativo); `chr_kb` = 0; `tamanho` = bytes da ROM (par, até 8 MB). O `rom_prepare` sonda o chip (ID com desbloqueio 5555h, depois 555h, depois Intel; tabela em `include/dumper/MdFlashCore.h`: MX29F1610, S29GL064N, M29W320/640, MX29LV320/640, MX29L3211, PA28F400, SST39VF320x/640x; outro ID → `E_FLASH`), confere que a ROM cabe **no chip encontrado** (`E_ARGUMENTO`) e apaga: o chip inteiro no MX29F1610 e no S29GL064N, setores ou blocos por layout nos demais. O firmware (`src/dumper/MdFlash.cpp`) chama `MD::eraseFlash`, `resetFlash`, `write29F1610` e `write29GL` do OSCR nos dois chips do OSCR, que leem o "arquivo" pelo `StreamFile`; os outros usam o núcleo `MdFlashCore.h`. Os laços de espera ganharam limite de tempo: apagar ou gravar que não termina devolve `E_CARTUCHO_IO` em vez de travar.

No SNES o firmware (`src/dumper/SnesFlash.cpp`) usa direto `Flash::setup8`, `identifyCFIbyIds`, `sendCFICommand`, `writeByte`, `readByte`, `writeByteCompensated`; o laço de apagar e gravar é novo pelo mesmo motivo (o `writeCFI` do OSCR lê o SD e o `busyWait` espera para sempre), e a conferência do `verifyFlash` (que relê o arquivo) é feita pelo PC com `DUMP_ROM` (`prg_kb` = tamanho da ROM). As opções do OSCR com 2 ou 4 chips e a de 8 MB ainda não existem. O firmware usa direto as funções do OSCR original (`NESmaker_ID`, `NESmaker_SectorErase`, `NESmaker_ByteProgram`, `A29040B_*`); o laço de gravação é novo porque o original lê o arquivo do SD e espera para sempre (`do { } while`) por um byte que talvez nunca confira, enquanto aqui toda espera tem limite de tempo. **Conferência depois da gravação (D78):** é do PC e vem ligada por padrão. Depois do `END`, o host faz um `DUMP_ROM` com o mapper do chip (30 ou 0) e os tamanhos gravados, tira o cabeçalho iNES sintético e compara byte a byte com o que enviou. O mapper 30 passou a ter leitura de ROM no firmware (o `readPRG` do OSCR já tratava o caso 30; só faltava liberá-lo em `nesCheckRom`, PRG até 512 KB e só CHR-RAM). O OSCR original só conferia cada byte logo depois de programá-lo; a leitura completa pega também o que mudou depois.

