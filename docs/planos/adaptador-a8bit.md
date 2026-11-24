# Adaptador do Atari 8 bits (400/800/XL/XE) para o slot SNES (F-20, D210)

O núcleo `Atari8.cpp` do OSCR usa o barramento do slot SNES: A0 a A7 em PF, A8 a A12 em PK0 a PK4 e D0 a D7 em PC, mais os selects `/S4` (PH6, ROM em $8000-$9FFF), `/S5` (PH3, ROM em $A000-$BFFF), `R/W` (PH5) e `/CCTL` (PL0, o bloco de controle $D500 que troca de banco). Conector do cartucho de 30 pinos (15 por lado, pinos `A` a `S` no lado da etiqueta e 1 a 15 no lado de baixo).

## Fonte (conferida)

Pinagem do cartucho: o quadro "Left Slot Cartridge Pinout, 30P 2.54mm pitch" no começo de `firmware/oscr/src/cores/Atari8.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_atari8_lynx.py` confere o quadro, o `pinmap` e as portas que o núcleo escreve. Não vi desenho de adaptador do OSCR: a tabela vem do núcleo e do `pinmap`. Nos cartuchos do slot direito (8 KB) o `/S4` deles vem no pino 12, que no conector esquerdo é o `/S5`: o núcleo já trata isso (`atari8right`, lê com o `/S5`), então o mesmo adaptador serve.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector |
|---|---|---|---|
| A0 | 17 | PF0 | 5 |
| A1 | 16 | PF1 | 4 |
| A2 | 15 | PF2 | 3 |
| A3 | 14 | PF3 | 2 |
| A4 | 13 | PF4 | C |
| A5 | 12 | PF5 | D |
| A6 | 11 | PF6 | E |
| A7 | 10 | PF7 | F |
| A8 | 9 | PK0 | H |
| A9 | 8 | PK1 | J |
| A10 | 7 | PK2 | P |
| A11 | 6 | PK3 | N |
| A12 | 37 | PK4 | K |
| D0 | 19 | PC0 | 10 |
| D1 | 20 | PC1 | 9 |
| D2 | 21 | PC2 | 8 |
| D3 | 22 | PC3 | L |
| D4 | 50 | PC4 | 6 |
| D5 | 51 | PC5 | 7 |
| D6 | 52 | PC6 | 11 |
| D7 | 53 | PC7 | M |
| /S4 | 23 | PH6 | 1 |
| /S5 | 49 | PH3 | 12 |
| R/W | 54 | PH5 | R |
| /CCTL | 41 | PL0 | 15 |

Pinos fixos do conector: +5V no `13` (slot 27 e 58, 5 V fixo; **sem problema de tensão**) e GND no `B` (slot 5 e 36). `RD4` (`A`) e `RD5` (`14`) são entradas que o núcleo configura mas **não lê**: ficam sem ligação no adaptador. Nada mais é usado.

## PENDENTE: PHI2

O pino `S` (`PHI2`, o relógio do 6502, 1,79 MHz) é **pulsado por PH1** na troca de banco (`bankSwitch`, 2 pulsos) e nada mais usa PH1. **PH1 não chega ao slot SNES nesta placa** (o pino 57 do slot, "CPU clock", vem do CLK1 do Si5351, e o núcleo do 8 bits não programa o Si5351). Consequência: **cartuchos com troca de banco (XE de 32, 64 e 128 KB e o Necromancer de 16 KB) não vão trocar de banco** com a placa como está; os de 8 KB, 16 KB sem troca e o Bounty Bob (40 KB, troca por leitura de endereço) não dependem do `PHI2`. Para resolver é preciso decidir entre (a) ligar o `PHI2` ao pino 57 e programar o CLK1 do Si5351 em 1,79 MHz no firmware, ou (b) levar PH1 até o adaptador por um pino livre do slot. Nenhuma das duas foi feita.

Falta o desenho do PCB (conector de 30 posições, 2,54 mm; o do slot direito usa o mesmo adaptador com os pinos em outra ordem, chaveamento e espessura no slot SNES a confirmar).
