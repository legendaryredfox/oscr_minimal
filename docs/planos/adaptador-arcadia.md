# Adaptador do Emerson Arcadia 2001 para o slot SNES (F-20, D215)

O núcleo `Arcadia2001.cpp` do OSCR usa o barramento do slot SNES só para leitura: A0 a A7 em PF, A8 a A13 em PK (A14 e A15 ficam sem uso), D0 a D7 em PC. Os pinos de controle (`PH0`, `PH1`, `PH3` a `PH6`) e `TIME` (PJ0) vão a nível alto e **não chegam ao cartucho**; os endereços A16 a A23 (PL) e os dados PA ficam sem ligação. O cartucho é de 5 V (o slot SNES é 5 V fixo em todas as placas), então não há problema de tensão. O adaptador não foi desenhado: falta o PCB (conector de 30 posições, 2 fileiras, 2,54 mm, chaveamento a confirmar).

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 30P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/Arcadia2001.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_arcadia.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (30P) |
|---|---|---|---|
| A0 | 17 | PF0 | 6 |
| A1 | 16 | PF1 | 8 |
| A2 | 15 | PF2 | 10 |
| A3 | 14 | PF3 | 12 |
| A4 | 13 | PF4 | 14 |
| A5 | 12 | PF5 | 16 |
| A6 | 11 | PF6 | 18 |
| A7 | 10 | PF7 | 20 |
| A8 | 9 | PK0 | 22 |
| A9 | 8 | PK1 | 24 |
| A10 | 7 | PK2 | 26 |
| A11 | 6 | PK3 | 28 |
| A12 | 37 | PK4 | 30 |
| A13 | 38 | PK5 | 1 |
| D0 | 19 | PC0 | 13 |
| D1 | 20 | PC1 | 17 |
| D2 | 21 | PC2 | 15 |
| D3 | 22 | PC3 | 3 |
| D4 | 50 | PC4 | 5 |
| D5 | 51 | PC5 | 7 |
| D6 | 52 | PC6 | 9 |
| D7 | 53 | PC7 | 11 |

Pinos fixos do conector: +5V no 4 (slot 27 e 58, 5 V fixo), GND nos 2, 25 e 27 (slot 5 e 36). Sem ligação (NC no quadro): 19, 21, 23 e 29.

## Pontos a conferir com o cartucho na mão

- O quadro do núcleo rotula o pino 1 como `A13 (A12)` e o pino 30 como `A12 (/EN)`: as duas linhas são endereço no barramento e o **A12 faz o papel de habilitar (`/EN`)** a ROM, em placas diferentes de cartucho. O núcleo conduz A0 a A13, então o pino 1 vai ao PK5 (A13) e o pino 30 ao PK4 (A12), como na tabela. Se algum cartucho ligar o pino 1 ao A12 em vez do A13, a leitura de 4 KB ou mais sai trocada; só se vê no hardware.
- A ROM é lida em `$0000-$0FFF` e `$2000-$2FFF` (2 KB por trecho): o console enxerga assim o cartucho, e o `readROM` do OSCR segue essa ordem.
