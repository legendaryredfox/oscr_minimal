# Adaptador do Vectrex para o slot SNES (F-20, D205)

O núcleo `Vectrex.cpp` do OSCR usa o barramento do slot SNES: A0 a A7 em PF, A8 a A15 em PK, D0 a D7 em PC, `/CART` em PH3 (`/Cart`, pino 49), `PB6` em PH5 (`/WR`, pino 54, a troca de banco dos cartuchos de 64 KB) e `R/W` em PH6 (`/RD`, pino 23). O adaptador liga o conector de 36 pinos do cartucho a esses pinos.

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 36P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/Vectrex.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_vectrex.py` confere o quadro, o `pinmap` e as portas que o núcleo escreve. Não vi desenho de adaptador do OSCR para o Vectrex: a tabela vem do núcleo e do `pinmap`.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (36P) |
|---|---|---|---|
| A0 | 17 | PF0 | 17 |
| A1 | 16 | PF1 | 15 |
| A2 | 15 | PF2 | 13 |
| A3 | 14 | PF3 | 11 |
| A4 | 13 | PF4 | 9 |
| A5 | 12 | PF5 | 7 |
| A6 | 11 | PF6 | 5 |
| A7 | 10 | PF7 | 3 |
| A8 | 9 | PK0 | 6 |
| A9 | 8 | PK1 | 8 |
| A10 | 7 | PK2 | 14 |
| A11 | 6 | PK3 | 10 |
| A12 | 37 | PK4 | 29 |
| A13 | 38 | PK5 | 31 |
| A14 | 39 | PK6 | 33 |
| A15 | 40 | PK7 | 16 |
| D0 | 19 | PC0 | 19 |
| D1 | 20 | PC1 | 21 |
| D2 | 21 | PC2 | 23 |
| D3 | 22 | PC3 | 26 |
| D4 | 50 | PC4 | 24 |
| D5 | 51 | PC5 | 22 |
| D6 | 52 | PC6 | 20 |
| D7 | 53 | PC7 | 18 |
| /CART | 49 | PH3 | 32 |
| PB6 | 54 | PH5 | 35 |
| R/W | 23 | PH6 | 30 |

Pinos fixos do conector: +5V nos 2 e 4 (slot 27 e 58, 5 V fixo, sem problema de tensão), GND nos 25, 27 e 28 (slot 5 e 36). Sem ligação ao Mega (o núcleo não os usa): `/HALT` (1), `/NMI` (34), `/IRQ` (36).

## Achado: `/OE` (pino 12 do conector) não chega ao slot SNES daqui

O comentário do núcleo diz "`/OE` (PH1) = SNES CPUCLK" (pino 57 do slot). Neste repositório o pino 57 do slot SNES é o `CPU_Clock_57`, ligado ao **Si5351 CLK1**; o PH1 só está nos slots Mega Drive (B19 `VCLK`) e GBA (`CLK_2`). Então o Mega não consegue dirigir o `/OE` do Vectrex pelo slot SNES. **O núcleo mantém o `/OE` em nível baixo o tempo todo** (`cartOn`: "Set /OE LOW", e nenhuma leitura o muda), então a proposta é **ligar o pino 12 do conector ao GND no próprio adaptador**, o que é elétricamente o mesmo. Isto é uma dedução do código, não está confirmado em cartucho; conferir em bancada (continuidade pino 12 a GND e uma leitura de um jogo de 4 KB). O pino 57 do slot fica sem ligação no adaptador (senão o clock do Si5351 iria ao `/OE`).

Falta o desenho do PCB (conector de 36 posições, 2 fileiras, 2,54 mm, chaveamento e espessura no slot SNES a confirmar).
