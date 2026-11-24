# Adaptador do Watara Supervision para o slot SNES (F-20, D218)

O núcleo `Supervision.cpp` do OSCR usa o barramento do slot SNES só para leitura. O endereço sai por PF (A0 a A7), PK (A8 a A15) e PL (`addr >> 16`, o A16 em PL0); os dados D0 a D7 entram por PC. **/RD** (PH6) fica baixo durante a leitura e **/WR** (PH5) fica alto o tempo todo. Os outros pinos de controle (`PH0`, `PH1`, `PH3`, `PH4`) e `TIME` (PJ0) vão a nível alto e **não chegam ao cartucho**. O adaptador não foi desenhado: falta o PCB (conector de 40 posições, 2,5 mm, duas fileiras, chaveamento a confirmar).

## Tensão: 3,3 V (mesmo problema do Neo Geo Pocket, D203)

O núcleo pede 3,3 V (`setVoltage(k3V3)`), apesar de o quadro do cartucho rotular o pino 40 como "+5V". O VCC do slot SNES é **5 V fixo em todas as placas**: ligar o pino 40 direto a ele contraria o núcleo e pode estragar o cartucho. O adaptador precisa do próprio regulador de 3,3 V (LDO), alimentado pelo 5 V do slot (27 e 58) e ligado ao pino 40 do conector. **PENDENTE:** confirmar a tensão real do cartucho (o console usa pilhas e o rótulo do quadro diz 5 V; a decisão do núcleo é 3,3 V).

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 40P 2.5mm pitch connector" no começo de `firmware/oscr/src/cores/Supervision.cpp` (duas colunas: pinos 1 a 20 à esquerda, 40 a 21 à direita). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_supervision.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (40P) |
|---|---|---|---|
| A0 | 17 | PF0 | 2 |
| A1 | 16 | PF1 | 3 |
| A2 | 15 | PF2 | 4 |
| A3 | 14 | PF3 | 5 |
| A4 | 13 | PF4 | 6 |
| A5 | 12 | PF5 | 7 |
| A6 | 11 | PF6 | 8 |
| A7 | 10 | PF7 | 9 |
| A8 | 9 | PK0 | 10 |
| A9 | 8 | PK1 | 11 |
| A10 | 7 | PK2 | 12 |
| A11 | 6 | PK3 | 13 |
| A12 | 37 | PK4 | 14 |
| A13 | 38 | PK5 | 15 |
| A14 | 39 | PK6 | 16 |
| A15 | 40 | PK7 | 17 |
| A16 | 41 | PL0 | 18 |
| D0 | 19 | PC0 | 34 |
| D1 | 20 | PC1 | 33 |
| D2 | 21 | PC2 | 32 |
| D3 | 22 | PC3 | 31 |
| D4 | 50 | PC4 | 30 |
| D5 | 51 | PC5 | 29 |
| D6 | 52 | PC6 | 28 |
| D7 | 53 | PC7 | 27 |
| /RD | 23 | PH6 | 1 |
| /WR | 54 | PH5 | 35 |

Pinos fixos do conector: VCC no 40 (3,3 V do LDO do adaptador, ver acima), GND no 22 e PWR GND no 21 (slot 5 e 36).

## Pontos a conferir com o cartucho na mão

- **A17 a A19 e os pinos de link (L0 a L3, conector 20, 24, 23 e 19) não estão na tabela.** O `readROM` do OSCR lê 512 KB com `addr >> 16` indo até 7 (PL0 a PL2), mas o quadro só tem **A16**. O comentário do núcleo diz que só a variante MAGNUM levou L0 a L3 ao cartucho como bits extras de banco. Como os cartuchos de 512 KB trocam de banco, e por quais pinos, é **PENDENTE**: depende do cartucho. Os de 32 e 64 KB não usam isso.
- Os pinos `nc` (25, 26, 36 a 39) ficam sem ligação.
- A leitura de 32 KB começa em `$8000`; a de 64 KB e a de 512 KB, em `$0000`. A sondagem do firmware lê 32 bytes de `$8000` e só separa slot vazio de cartucho.
