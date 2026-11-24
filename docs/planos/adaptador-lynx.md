# Adaptador do Atari Lynx para o slot SNES (F-20, D210)

O núcleo `AtariLynx.cpp` do OSCR usa o barramento do slot SNES: A0 a A7 em PF, os bits seguintes do endereço em PK e PL, D0 a D7 em PC, `/OE` (PH6, pino 9 do Arduino) e `/WE` (PH5, pino 8 do Arduino; só a gravação de flash escreve). O `/CE` do cartucho fica no GND (o núcleo diz: "CE is tied low, not accessible"). O cartucho do Lynx não é lido pelo slot de 2,54 mm: o adaptador do OSCR ("SNES-Lynx adapter") liga o conector de cartucho do Lynx (34 posições, quadro no núcleo) ao slot SNES.

## Fonte (conferida) e o que ficou PENDENTE

Pinagem do cartucho: o quadro no começo de `firmware/oscr/src/cores/AtariLynx.cpp` (34 pinos). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_atari8_lynx.py` confere o quadro, o `pinmap` e as portas que o núcleo escreve. Não vi desenho de adaptador do OSCR para o Lynx.

**Só entram na tabela os sinais cuja ligação o núcleo confirma.** `setAddr` faz `PORTF = addr`, `PORTK = addr >> 8` e `PORTL = (addr >> 16) & 0xF`, e o comentário do núcleo diz "A11 doesn't exist" e "AUDIN connected to L3". Os bits 11 a 18 do endereço do núcleo são o **número do bloco** (256 blocos), e o quadro do cartucho nomeia as linhas de bloco `A12` a `A19`: **qual linha do cartucho recebe qual bit** (PK3 a PK7 e PL0 a PL3) e se `A19` (pino 22) e `AUDIN` (pino 32) vão ambos a PL3 não está no código, e eu não inventei: ficam PENDENTES até conferir com um adaptador do OSCR ou com o usuário.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector |
|---|---|---|---|
| A0 | 17 | PF0 | 17 |
| A1 | 16 | PF1 | 11 |
| A2 | 15 | PF2 | 12 |
| A3 | 14 | PF3 | 13 |
| A4 | 13 | PF4 | 15 |
| A5 | 12 | PF5 | 16 |
| A6 | 11 | PF6 | 14 |
| A7 | 10 | PF7 | 18 |
| A8 | 9 | PK0 | 28 |
| A9 | 8 | PK1 | 29 |
| A10 | 7 | PK2 | 30 |
| D0 | 19 | PC0 | 7 |
| D1 | 20 | PC1 | 5 |
| D2 | 21 | PC2 | 3 |
| D3 | 22 | PC3 | 2 |
| D4 | 50 | PC4 | 4 |
| D5 | 51 | PC5 | 6 |
| D6 | 52 | PC6 | 8 |
| D7 | 53 | PC7 | 9 |
| /OE | 23 | PH6 | 10 |
| /WE | 54 | PH5 | 27 |

PENDENTES (não ligados até confirmar): `A12` a `A19` (pinos 26, 25, 24, 23, 19, 20, 21 e 22 do conector) e `AUDIN` (32). Pinos fixos: GND no 1 (slot 5 e 36); `VCC` nos 31 e 33 e `SWVCC` no 34 (slot 27 e 58, 5 V fixo; **sem problema de tensão**, mas o que o `SWVCC` pede não está no código). **Sem os bits altos o adaptador só enxerga os 2 KB do primeiro bloco: não serve para ler cartucho** até resolver os PENDENTES.
