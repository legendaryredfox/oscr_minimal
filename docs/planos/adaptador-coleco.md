# Adaptador do ColecoVision para o slot SNES (F-20, D204)

O núcleo `Colecovision.cpp` do OSCR (D201) usa o barramento do slot SNES: A0 a A7 em PF, A8 a A14 em PK0 a PK6, D0 a D7 em PC e os quatro seletores de chip em PH3 a PH6 (`/8000` no `/Cart`, `/A000` no `/IRQ`, `/C000` no `/WR`, `/E000` no `/RD`; comentário do próprio núcleo: "CHIP SELECT PINS ... SNES /CS, /IRQ, /WR, /RD"). O adaptador só liga o conector do cartucho ao slot.

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 30P 2.54mm pitch connector" no início de `firmware/oscr/src/cores/Colecovision.cpp` (ímpares no lado de trás, pares na frente; os pinos 13 e 29 são GND). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_coleco.py` confere as três coisas (quadro do núcleo, `pinmap` e portas que o núcleo escreve). Não vi nenhum desenho de adaptador do OSCR para o ColecoVision: a tabela vem só do núcleo e do `pinmap`.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (30P) |
|---|---|---|---|
| A0 | 17 | PF0 | 7 |
| A1 | 16 | PF1 | 9 |
| A2 | 15 | PF2 | 11 |
| A3 | 14 | PF3 | 15 |
| A4 | 13 | PF4 | 17 |
| A5 | 12 | PF5 | 21 |
| A6 | 11 | PF6 | 23 |
| A7 | 10 | PF7 | 25 |
| A8 | 9 | PK0 | 28 |
| A9 | 8 | PK1 | 26 |
| A10 | 7 | PK2 | 16 |
| A11 | 6 | PK3 | 14 |
| A12 | 37 | PK4 | 24 |
| A13 | 38 | PK5 | 19 |
| A14 | 39 | PK6 | 20 |
| D0 | 19 | PC0 | 5 |
| D1 | 20 | PC1 | 3 |
| D2 | 21 | PC2 | 1 |
| D3 | 22 | PC3 | 4 |
| D4 | 50 | PC4 | 6 |
| D5 | 51 | PC5 | 8 |
| D6 | 52 | PC6 | 10 |
| D7 | 53 | PC7 | 12 |
| /8000 | 49 | PH3 | 18 |
| /A000 | 18 | PH4 | 22 |
| /C000 | 54 | PH5 | 2 |
| /E000 | 23 | PH6 | 27 |
| GND | 5 e 36 | - | 13 e 29 |
| VCC | 27 e 58 | - | 30 |

Pinos do slot sem uso: os demais. **Tensão: o ColecoVision é 5 V**, o VCC do slot SNES é 5 V fixo; não há o problema do adaptador do NGP (D203). Falta o desenho do PCB: conector de 30 posições, passo de 2,54 mm, 2 fileiras (conferir a peça e o chaveamento), e a espessura de 1,2 mm no slot SNES (nota do OSCR para o adaptador do NGP; confirmar para este).
