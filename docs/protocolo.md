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
| `0x02` | `DETECT` | `u8 sistema` |
| `0x03` | `DUMP_ROM` | `u8 sistema`, `u16 bloco` (0 = padrão 512); opcional, só NES/Famicom: `u16 mapper`, `u16 prg_kb`, `u16 chr_kb` (0 = automático/NROM) |
| `0x04` | `READ_SAVE` | `u8 sistema`, `u16 bloco` (0 = padrão 512) |
| `0x05` | `WRITE_SAVE` | `u8 sistema`, `u32 tamanho`, `u16 bloco` (0 = padrão 512); opcional, NES/Famicom: `u16 mapper`, `u16 0`, `u16 0` |
| `0x06` | `ACK` | `u32 offset` do bloco confirmado |
| `0x07` | `NAK` | `u32 offset` do bloco que precisa ser reenviado |
| `0x08` | `ABORT` | vazio |
| `0x09` | `DATA` | `u32 offset` + dados (só em `WRITE_SAVE`, host → dispositivo) |
| `0x0A` | `END` | `u32 total`, `u32 crc32` do arquivo inteiro (só em `WRITE_SAVE`) |

### Dispositivo → host

| Tipo | Nome | Payload |
|---|---|---|
| `0x81` | `INFO_RESP` | `u8 versão_proto`, `u8 maior`, `u8 menor`, `u8 patch` (firmware), `u8 flags`, `u16 sistemas` (máscara de bits, bit = id do sistema), `u16 max_payload` (maior payload que o dispositivo aceita: 1024 no PC/simulador, 520 no AVR; o host usa bloco ≤ `max_payload` − 4; opcional para o host, o campo vem no fim) |
| `0x82` | `DETECT_RESP` | ver seção 5 |
| `0x83` | `BEGIN` | `u8 tipo_dado` (1 = ROM, 2 = save), `u32 tamanho`, `u16 bloco` |
| `0x84` | `DATA` | `u32 offset` + dados (até `bloco` bytes) |
| `0x85` | `END` | `u32 total`, `u32 crc32` do arquivo inteiro |
| `0x86` | `ACK` | `u32 offset` (confirma um pedido ou um bloco de `WRITE_SAVE`) |
| `0x87` | `ERRO` | `u16 código`, `u8 n`, `n` bytes de texto ASCII (diagnóstico, não traduzido) |
| `0x88` | `PROGRESSO` | `u32 offset`, `u32 total` (opcional, a cada ~1 s sem `DATA`) |

`seq` do host é livre (incremente a cada pedido). O dispositivo repete o `seq` do pedido em todas as respostas daquele pedido (`DATA` do mesmo fluxo repete o `seq` do `DUMP_ROM`/`READ_SAVE`).

### Flags de `INFO_RESP`
bit 0: modo `MOCK` ligado (dados sintéticos, sem cartucho); bit 1: Si5351 detectado; bit 2: PIC (CIC) presente (informativo, pode ser 0 se não houver como detectar); demais: 0.

## 4. Sistemas

| Id | Sistema | Extensão do arquivo de ROM |
|---|---|---|
| 1 | SNES/SFC | `.sfc` |
| 2 | NES | `.nes` |
| 3 | Famicom | `.nes` |
| 4 | Mega Drive/Genesis | `.md` |
| 5 | GBA (3,3 V) | `.gba` |
| 6 | Game Boy (reservado, via adaptador no slot GBA) | `.gb` |
| 255 | `MOCK` (teste, sem cartucho) | `.bin` |

### Opções de `DUMP_ROM` para NES/Famicom e Mega Drive

**Mega Drive:** só `prg_kb` conta e significa o **tamanho da ROM em KB** (0 = pelo cabeçalho, com redução automática quando a ROM aparece espelhada). Mínimo 32 KB; máximo 4 MB (8 MB com o mapper SSF2). `ERRO 0x0004` fora desses limites.

**Saves do Mega Drive** (`READ_SAVE` e `WRITE_SAVE`): a SRAM ou a EEPROM serial, conforme o cabeçalho; sem opções. Na gravação da EEPROM cada `DATA` pode levar vários segundos (ver D49).

**Saves do NES/Famicom** (`READ_SAVE` e `WRITE_SAVE`): contam o `mapper` e o segundo campo (`prg_kb`), que aqui é o **tamanho da RAM em KB** (0 = 8). Só 1 (MMC1) e 4 (MMC3) têm PRG-RAM com bateria aceita (8 KB em $6000-$7FFF); o mapper 1 aceita também 16 KB (SOROM) e 32 KB (SXROM), em bancos de 8 KB escolhidos pelo registrador CHR 0 do MMC1. Outro tamanho, ou 16/32 no mapper 4: `ERRO 0x0004`. Outro mapper: `ERRO 0x000A`. No `WRITE_SAVE` o tamanho do arquivo tem que bater com a RAM. A gravação confere cada byte; cartucho sem RAM ou com RAM protegida dá `ERRO 0x0007`.

**Saves do GBA** (`READ_SAVE` e `WRITE_SAVE`): o campo `mapper` é o **tipo de save**, com a numeração do OSCR: 0 ou 3 = SRAM/FRAM 32 KB (padrão), 1 = EEPROM 512 bytes, 2 = EEPROM 8 KB, 4 = Flash 64 KB, 5 = Flash 128 KB (dois bancos de 64 KB, trocados pelo comando AA/55/B0). Outro valor: `ERRO 0x0004`. `DETECT` continua sem saber o tipo (`tipo_save` 255, 32 KB). O host acha o tipo na ROM já lida procurando `FLASH1M_V`, `FLASH512_V`, `FLASH_V`, `EEPROM_V`, `SRAM_F_V` ou `SRAM_V`. `WRITE_SAVE` do GBA usa o mesmo campo `mapper` (tipos 0 e 3 a 5 e 1/2 como acima; ver D48): `ERRO 0x0004` se o tamanho não bate com o tipo, `ERRO 0x0007` se o chip Flash é desconhecido, não apaga ou a conferência falha. Cada `DATA` pode levar até ~1 s (EEPROM), por isso o host espera `long_timeout` pelo `ACK`.

**NES/Famicom:**

O cartucho de NES não tem cabeçalho com o mapper. Para mappers diferentes de 0 o host informa `mapper`, `prg_kb` (múltiplo de 16) e `chr_kb` (múltiplo de 8, 0 se o cartucho usa CHR-RAM). Mappers aceitos: 0, 1 (MMC1, PRG até 256 KB), 2, 3, 4, 5 (MMC5, PRG até 1 MB), 7, 9 (MMC2, PRG até 128 KB), 10 (MMC4, PRG até 256 KB), 11 (PRG e CHR até 128 KB), 66 (PRG até 128 KB, CHR até 32 KB), 69 (PRG até 512 KB) e 71 (mappers 2, 7 e 71 só com CHR 0; 7, 11 e 66 com PRG múltiplo de 32 KB). Acima dos limites: `ERRO 0x0002`. `ERRO 0x0002` = mapper não suportado; `ERRO 0x0004` = tamanhos inválidos. O arquivo sai com cabeçalho iNES de 16 bytes (mapper nos nibbles dos bytes 6 e 7; espelhamento e bateria ficam 0). Os valores corretos vêm do banco do No-Intro/NESCartDB ou de uma ROM já conhecida do mesmo jogo.

## 5. `DETECT_RESP`

```
u8  sistema
u8  status          0 = cartucho detectado, 1 = nenhum cartucho, 2 = não suportado, 3 = erro de hardware
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
