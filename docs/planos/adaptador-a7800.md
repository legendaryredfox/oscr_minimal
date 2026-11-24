# Adaptador do Atari 7800 para o slot SNES (F-20, D209)

O núcleo `Atari7800.cpp` do OSCR usa o barramento do slot SNES: A0 a A7 em PF, A8 a A15 em PK0 a PK7 e D0 a D7 em PC, mais `R/W` (PH6), `HALT` (PH0) e o relógio `CLK`. Com `clockgen = true` (o caso desta placa) o relógio de 2 MHz vem da saída CLK1 do Si5351, que no slot SNES é o pino 57 ("CPU clock"); sem o Si5351 o núcleo usa PH1 como saída, mas PH1 não chega ao slot, então **o 7800 exige o módulo Si5351 instalado**. `HALT` e `R/W` ficam em PH0 e PH6, pinos 26 e 23 do slot. A escrita de bancos (`writeData` e `bankSwitch`) usa o `R/W` e o `CLK`: o PAL16 do cartucho SuperGame trava o endereço com 8 pulsos de `CLK`.

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 32P 2.54mm pitch (USE 36P CONNECTOR)" no começo de `firmware/oscr/src/cores/Atari7800.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_atari.py` confere o quadro, o `pinmap` e as portas que o núcleo escreve. Não vi desenho de adaptador do OSCR para o 7800: a tabela vem do núcleo e do `pinmap`.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector |
|---|---|---|---|
| A0 | 17 | PF0 | 26 |
| A1 | 16 | PF1 | 25 |
| A2 | 15 | PF2 | 24 |
| A3 | 14 | PF3 | 23 |
| A4 | 13 | PF4 | 22 |
| A5 | 12 | PF5 | 21 |
| A6 | 11 | PF6 | 20 |
| A7 | 10 | PF7 | 19 |
| A8 | 9 | PK0 | 12 |
| A9 | 8 | PK1 | 11 |
| A10 | 7 | PK2 | 9 |
| A11 | 6 | PK3 | 10 |
| A12 | 37 | PK4 | 8 |
| A13 | 38 | PK5 | 15 |
| A14 | 39 | PK6 | 16 |
| A15 | 40 | PK7 | 17 |
| D0 | 19 | PC0 | 27 |
| D1 | 20 | PC1 | 28 |
| D2 | 21 | PC2 | 29 |
| D3 | 22 | PC3 | 3 |
| D4 | 50 | PC4 | 4 |
| D5 | 51 | PC5 | 5 |
| D6 | 52 | PC6 | 6 |
| D7 | 53 | PC7 | 7 |
| R/W | 23 | PH6 | 1 |
| HALT | 26 | PH0 | 2 |
| CLK | 57 | - | 32 |

Pinos fixos do conector: +5V no 13 (slot 27 e 58, 5 V fixo; **sem problema de tensão**) e GND nos 14 e 30 (slot 5 e 36). `IRQ` (31) e `AUD` (18) ficam sem ligação.

Falta o desenho do PCB (conector de 32 posições em 2 fileiras de 16, 2,54 mm, o quadro do núcleo manda usar um de 36; chaveamento e espessura no slot SNES a confirmar).
