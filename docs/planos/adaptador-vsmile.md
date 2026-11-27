# Adaptador do V.Smile para o slot SNES (F-20, D228)

O núcleo `VSmile.cpp` do OSCR usa o barramento do slot SNES só para leitura, em palavras de 16 bits. O `read_rom_word` do núcleo põe o endereço de palavra em PF (A1 a A8), PK (A9 a A16) e PL0 a PL5 (A17 a A22), espera 1 µs, sobe **CSB2** (PH4), desce **CSB1** (PH6) e **OE** (PH3), lê D0 a D7 em PC e D8 a D15 em PA e sobe OE e CSB1. O segundo chip dos cartuchos de 6 MB é lido com CSB2 baixo e CSB1 alto (`read_rom2_word`); o segundo chip dos V.Motion de 16 MB, com CSB1 e CSB2 baixos (`read_rom3_word`). Os sinais de controle são ativos em nível baixo. O `cartOn` põe PH3, PH4 e PH6 como saída e os outros bits de PH como entrada com pull-up; PL6 e PL7 também ficam como entrada. O tamanho vem sempre do PC: 4, 6, 8 ou 16 MB (tabela `romSizes` do núcleo). O adaptador não foi desenhado: falta o PCB.

## Tensão: 3,3 V (mesmo problema do Neo Geo Pocket, do Supervision e do Pokémon Mini, D203, D218 e D227)

O núcleo pede 3,3 V (`setVoltage(k3V3)`). O VCC do slot SNES é **5 V fixo em todas as placas**: ligar os VCC do cartucho direto a ele pode estragar o cartucho. O adaptador precisa do próprio regulador de 3,3 V (LDO THT, por exemplo MCP1700 ou LD1117V33, mais capacitores), alimentado pelo 5 V do slot (27 e 58) e ligado aos pinos 24, 25 e 27 do conector. Os sinais do Mega são de 5 V em qualquer caso (D140), como anotado para o Neo Geo Pocket.

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge pinout, 48P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/VSmile.cpp` (pinos 25 a 48 do lado da frente, 1 a 24 do lado de trás), com a lista de portas logo abaixo (D0-D7 em PORTC, D8-D15 em PORTA, A1-A8 em PORTF, A9-A16 em PORTK, A17-A22 em PORTL). As portas de controle vêm dos `#define` de `firmware/oscr/include/cores/VSmile.h` (OE no /CART, CSB1 no /RD e CSB2 no /IRQ do slot SNES). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES); D8 a D15 usam os pinos PA0 a PA7 do slot SNES (28, 59, 29, 60, 30, 61, 3 e 34). `python3 tools/check_adaptador_vsmile.py` confere o quadro, os `#define`, o pinmap e as portas que o núcleo usa.

O cartucho não tem A0: o endereço é de palavra. O `read_rom_word` monta a palavra com PC no byte alto (`(PINC << 8) | PINA`), e o `readROM` grava o byte alto primeiro; no arquivo, os bytes pares vêm de D0 a D7 e os ímpares de D8 a D15.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (48P) |
|---|---|---|---|
| A1 | 17 | PF0 | 12 |
| A2 | 16 | PF1 | 13 |
| A3 | 15 | PF2 | 38 |
| A4 | 14 | PF3 | 14 |
| A5 | 13 | PF4 | 39 |
| A6 | 12 | PF5 | 15 |
| A7 | 11 | PF6 | 40 |
| A8 | 10 | PF7 | 16 |
| A9 | 9 | PK0 | 42 |
| A10 | 8 | PK1 | 18 |
| A11 | 7 | PK2 | 43 |
| A12 | 6 | PK3 | 19 |
| A13 | 37 | PK4 | 44 |
| A14 | 38 | PK5 | 20 |
| A15 | 39 | PK6 | 45 |
| A16 | 40 | PK7 | 21 |
| A17 | 41 | PL0 | 37 |
| A18 | 42 | PL1 | 41 |
| A19 | 43 | PL2 | 17 |
| A20 | 44 | PL3 | 46 |
| A21 | 45 | PL4 | 22 |
| A22 | 46 | PL5 | 47 |
| D0 | 19 | PC0 | 31 |
| D1 | 20 | PC1 | 30 |
| D2 | 21 | PC2 | 29 |
| D3 | 22 | PC3 | 4 |
| D4 | 50 | PC4 | 5 |
| D5 | 51 | PC5 | 6 |
| D6 | 52 | PC6 | 7 |
| D7 | 53 | PC7 | 32 |
| D8 | 28 | PA0 | 35 |
| D9 | 59 | PA1 | 34 |
| D10 | 29 | PA2 | 33 |
| D11 | 60 | PA3 | 8 |
| D12 | 30 | PA4 | 9 |
| D13 | 61 | PA5 | 10 |
| D14 | 3 | PA6 | 36 |
| D15 | 34 | PA7 | 11 |
| OE | 49 | PH3 | 2 |
| CSB1 | 23 | PH6 | 48 |
| CSB2 | 18 | PH4 | 28 |

Pinos fixos do conector: VCC no 24, no 25 e no 27 (3,3 V do LDO do adaptador, ver acima); GND no 3 e no 23 (slot 5 e 36).

**PENDENTE: WE (1) e RAMCS (26).** O núcleo não conduz nenhum dos dois e o quadro não diz o que fazer com eles. Pelo nome, são a escrita e a seleção da RAM do cartucho; deixados soltos, podem flutuar e ligar a RAM no barramento durante a leitura. Candidatos: WE no /WR do slot (54, PH5), que o `cartOn` deixa como entrada com pull-up (nível alto, inativo); RAMCS no VCC do adaptador por um resistor. Conferir com o cartucho na mão ou com o adaptador da comunidade antes de fechar o PCB.

## Pontos a conferir com o cartucho na mão

- **WE e RAMCS:** ver acima.
- **Conector:** o quadro diz 48 pinos a 2,54 mm, com uma divisão entre os pinos 14/38 e 15/39 (a linha `|---------|` no quadro); medir a borda do cartucho antes de escolher a peça.
- **Tamanho:** o cartucho não informa. Pela base do OSCR (`legacy/sd/vsmilecart.txt`), 67 de 74 jogos têm 8 MB; os de 6 MB (Alphabet Park Adventure, Care Bears) têm dois chips; os de 16 MB são do V.Motion (Cars 2, Shrek Forever After, Super WHY!, Toy Story 3).
- A sondagem do firmware (16 palavras do início do primeiro chip) só separa slot vazio de cartucho; o fork não confere assinatura. O V.Smile não tem save no cartucho.
