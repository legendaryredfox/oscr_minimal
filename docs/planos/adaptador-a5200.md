# Adaptador do Atari 5200 para o slot SNES (F-20, D209)

O núcleo `Atari5200.cpp` do OSCR usa o barramento do slot SNES: A0 a A7 em PF, A8 a A13 em PK0 a PK5 e D0 a D7 em PC, mais dois selects: `/4000` (PH5, ROM em $4000-$7FFF) e `/8000` (PH6, ROM em $8000-$BFFF). Os dois ficam em PH5 e PH6, que no slot SNES são os pinos 54 e 23. O núcleo deixa PH0, PH1, PH3 e PH4 em nível alto sem ligá-los a nada.

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 36P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/Atari5200.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_atari.py` confere o quadro, o `pinmap` e as portas que o núcleo escreve. Não vi desenho de adaptador do OSCR para o 5200: a tabela vem do núcleo e do `pinmap`.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector |
|---|---|---|---|
| A0 | 17 | PF0 | 19 |
| A1 | 16 | PF1 | 20 |
| A2 | 15 | PF2 | 17 |
| A3 | 14 | PF3 | 21 |
| A4 | 13 | PF4 | 22 |
| A5 | 12 | PF5 | 16 |
| A6 | 11 | PF6 | 15 |
| A7 | 10 | PF7 | 27 |
| A8 | 9 | PK0 | 29 |
| A9 | 8 | PK1 | 31 |
| A10 | 7 | PK2 | 33 |
| A11 | 6 | PK3 | 35 |
| A12 | 37 | PK4 | 34 |
| A13 | 38 | PK5 | 32 |
| D0 | 19 | PC0 | 1 |
| D1 | 20 | PC1 | 2 |
| D2 | 21 | PC2 | 3 |
| D3 | 22 | PC3 | 4 |
| D4 | 50 | PC4 | 5 |
| D5 | 51 | PC5 | 6 |
| D6 | 52 | PC6 | 7 |
| D7 | 53 | PC7 | 8 |
| /4000 | 54 | PH5 | 10 |
| /8000 | 23 | PH6 | 9 |

Pinos fixos do conector: +5V no 26 (slot 27 e 58, 5 V fixo; **sem problema de tensão**) e GND nos 12, 13, 14, 23, 24 e 25 (slot 5 e 36). `INTERLOCK` (18 e 36) e `AUD` (30) ficam sem ligação no adaptador: o `INTERLOCK` é só a ponte que o próprio cartucho faz entre os pinos 18 e 36, e o OSCR não lê áudio. Os pinos 11 e 28 não são ligados (N/C).

Falta o desenho do PCB (conector de 36 posições, 2 fileiras, 2,54 mm, chaveamento e espessura no slot SNES a confirmar). O cartucho do 5200 tem de 4 a 40 KB: o campo `prg` do protocolo informa o tamanho nos mappers que pedem (padrão: 4, 8, 16 ou 32 KB); o mapper do Bounty Bob (2) troca de banco lendo endereços e o do dois chips (1) não precisa de tamanho.
