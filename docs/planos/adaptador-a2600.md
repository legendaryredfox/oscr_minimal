# Adaptador do Atari 2600 para o slot SNES (F-20, D206)

O núcleo `Atari2600.cpp` do OSCR usa só o barramento de endereços e dados do slot SNES: A0 a A7 em PF, A8 a A12 em PK0 a PK4 e D0 a D7 em PC. **Não há sinal de controle**: o cartucho de 2600 não tem `/CE` nem `/OE` (a ROM é selecionada pelo A12), e o núcleo deixa PH0 a PH6 em nível alto sem ligá-los a nada ("Set Control Pins to Output [UNUSED]"). O adaptador liga o conector de 24 pinos do cartucho a esses pinos.

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 24P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/Atari2600.cpp` (fileira de cima 24 a 13 no lado da etiqueta, de baixo 1 a 12). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_a2600.py` confere o quadro, o `pinmap` e as portas que o núcleo escreve. Não vi desenho de adaptador do OSCR para o 2600: a tabela vem do núcleo e do `pinmap`.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (24P) |
|---|---|---|---|
| A0 | 17 | PF0 | 8 |
| A1 | 16 | PF1 | 7 |
| A2 | 15 | PF2 | 6 |
| A3 | 14 | PF3 | 5 |
| A4 | 13 | PF4 | 4 |
| A5 | 12 | PF5 | 3 |
| A6 | 11 | PF6 | 2 |
| A7 | 10 | PF7 | 1 |
| A8 | 9 | PK0 | 22 |
| A9 | 8 | PK1 | 21 |
| A10 | 7 | PK2 | 19 |
| A11 | 6 | PK3 | 20 |
| A12 | 37 | PK4 | 18 |
| D0 | 19 | PC0 | 9 |
| D1 | 20 | PC1 | 10 |
| D2 | 21 | PC2 | 11 |
| D3 | 22 | PC3 | 13 |
| D4 | 50 | PC4 | 14 |
| D5 | 51 | PC5 | 15 |
| D6 | 52 | PC6 | 16 |
| D7 | 53 | PC7 | 17 |

Pinos fixos do conector: +5V no 23 (slot 27 e 58, 5 V fixo; **sem problema de tensão**) e GND nos 12 e 24 (slot 5 e 36). Nenhum outro pino do conector é usado.

Falta o desenho do PCB (conector de 24 posições, 2 fileiras, 2,54 mm, chaveamento e espessura no slot SNES a confirmar). Cartuchos com mapper de RAM ou com `writeData` (3E, E7, FA, FE, X07 e outros) escrevem no cartucho pelo barramento de dados: o 2600 não tem pino de escrita, o OSCR usa o endereço para isso, então o adaptador não precisa de `/WE`.
