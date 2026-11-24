# Adaptador do Atari Jaguar (F-20, D211): PENDENTE, o slot não tem todos os pinos

O núcleo `AtariJaguar.cpp` do OSCR lê 32 bits por vez e **gera o endereço com 74HC595 em cascata** (3 bytes deslocados por `shiftOutFAST`), então o adaptador do Jaguar leva os dois chips de ROM (U1 nos bits 0 a 15 e U2 nos bits 16 a 31 do dado) e os registradores de deslocamento. A leitura de ROM está no firmware (D211); **o adaptador não foi projetado porque nenhum slot da placa tem todos os pinos que o núcleo usa**.

## Fonte (conferida) e o conflito

Portas e sinais: o quadro "HARDWARE PROFILE" e o código de `firmware/oscr/src/cores/AtariJaguar.cpp` (`cartOn`, `shiftOutFAST`, `readData`). Pinos do slot: `boards/16_and_8_bits/docs/pinmap.md`. `python3 tools/check_adaptador_jaguar.py` confere a tabela abaixo e o conflito. **Não há pinagem do conector do cartucho do Jaguar no núcleo** (só portas), então a coluna do conector do cartucho não existe aqui: falta o desenho do adaptador do OSCR (não está em `vendor/oscr/`).

Sinais no slot SNES (todos os que existem lá):

| Sinal | Porta AVR | Pinos do slot SNES |
|---|---|---|
| D0 a D7 (ROM U1, bits 0-7) | PF0 a PF7 | 17, 16, 15, 14, 13, 12, 11, 10 |
| D8 a D15 (ROM U1, bits 8-15) | PK0 a PK7 | 9, 8, 7, 6, 37, 38, 39, 40 |
| D16 a D23 (ROM U2, bits 0-7) | PL0 a PL7 | 41, 42, 43, 44, 45, 46, 47, 48 |
| D24 a D31 (ROM U2, bits 8-15) | PC0 a PC7 | 19, 20, 21, 22, 50, 51, 52, 53 |
| SRCLR do 74HC595 | PE4 | 32 |
| SRCLK do 74HC595 | PE5 | 33 |
| RCLK do 74HC595 | PG5 | 2 |
| OEH | PH3 | 49 |
| OEL | PH4 | 18 |
| CE | PH5 | 54 |
| WE | PH6 | 23 |
| EEPDO (EEPROM, entrada) | PA5 | 61 |
| EEPSK (EEPROM) | PA6 | 3 |
| EEPCS (EEPROM) | PA7 | 34 |

**Falta no slot SNES: `SER` do 74HC595 em PE3** (o núcleo escreve `PORTE |= (1 << 3)`). PE3 só chega ao slot Mega Drive (pino B15, `EDCLK`); o slot SNES tem PJ0 no pino 4, que não é PE3. **E o slot Mega Drive não tem PL7** (D23 do Jaguar). Resultado: **nenhum slot da placa tem PE3 e PL7 ao mesmo tempo**; nas fontes do `pinmap` (esquemático, `ods` e `six_slot_adapter`) o pino 4 do SNES é PJ0 e o B15 do Mega Drive é PE3. Como o OSCR original liga o Jaguar não consegui apurar: o núcleo comenta `ADDR (PE3-PJ0)`, sem dizer qual dos dois.

Caminhos (nenhum foi feito; decisão do usuário):
1. **Slot SNES com `SER` em PJ0 (pino 4):** troca no núcleo de `PORTE bit 3` para `PORTJ bit 0` (macros `SER_SET`/`SER_CLEAR` e o `DDRE` de `cartOn`, 3 linhas) e ligar o `SER` do adaptador ao pino 4. Desvio da regra de reuso, a justificar em `docs/decisoes.md`.
2. **Slot Mega Drive** e aceitar D23 sem ligação: o dado do bit 23 sai errado; não serve.
3. Uma placa nova com o Jaguar (não está no escopo).
