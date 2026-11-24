# Adaptador do RCA Studio II para o slot SNES (F-20, D216)

O núcleo `RCAStudio2.cpp` do OSCR usa o barramento do slot SNES só para leitura. O Studio II tem 8 linhas de endereço multiplexadas: o núcleo põe o byte alto de A8 a A15 em PF (PORTF), trava com **TPA** (PH6), e depois põe o byte baixo (A0 a A7) em PF; os dados D0 a D7 entram por PC. O **/MRD** (PH3) abre a leitura. O resto dos pinos de controle (`PH0`, `PH1`, `PH4`, `PH5`) e `TIME` (PJ0) vão a nível alto e **não chegam ao cartucho**; PK, PL e PA ficam sem ligação. O cartucho é de 5 V (o slot SNES é 5 V fixo em todas as placas). O adaptador não foi desenhado: falta o PCB (conector de 22 posições, 3,96 mm, chaveamento a confirmar).

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 22P 3.96mm pitch connector" no começo de `firmware/oscr/src/cores/RCAStudio2.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_rca2.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (22P) |
|---|---|---|---|
| A0 | 17 | PF0 | 11 |
| A1 | 16 | PF1 | 12 |
| A2 | 15 | PF2 | 13 |
| A3 | 14 | PF3 | 14 |
| A4 | 13 | PF4 | 16 |
| A5 | 12 | PF5 | 17 |
| A6 | 11 | PF6 | 18 |
| A7 | 10 | PF7 | 20 |
| D0 | 19 | PC0 | 10 |
| D1 | 20 | PC1 | 9 |
| D2 | 21 | PC2 | 8 |
| D3 | 22 | PC3 | 5 |
| D4 | 50 | PC4 | 4 |
| D5 | 51 | PC5 | 3 |
| D6 | 52 | PC6 | 2 |
| D7 | 53 | PC7 | 1 |
| /MRD | 49 | PH3 | 21 |
| TPA | 23 | PH6 | 19 |

Pinos fixos do conector: +5V no 15 (slot 27 e 58, 5 V fixo), GND no 7 (slot 5 e 36).

## Pontos a conferir com o cartucho na mão

- **ROMCS (22) e ROM_DISABLE (6) não são conduzidos pelo núcleo.** O quadro os lista, mas o `readROM` do OSCR só mexe em /MRD e TPA. Se o cartucho precisar de ROMCS em nível ativo para colocar dados no barramento, o adaptador tem que prendê-lo (GND ou +5 V, conforme a polaridade do cartucho) e deixar ROM_DISABLE no nível que não desabilita a ROM. A polaridade não está no núcleo: **PENDENTE**, só se vê com o cartucho.
- O quadro rotula `/MRD (PH3) - SNES /CS` e `TPA (PH6) - SNES /RD`: nesta tabela o /MRD vai ao pino 49 (PH3) e o TPA ao pino 23 (PH6) do slot, como no pinmap.
- O `readROM` do OSCR lê só `$0400` a `$07FF` (1 KB no índice 1; 512 bytes no índice 0). O menu do OSCR rotula os dois índices como "1" e "2", mas lê 512 B e 1 KB. Cartuchos de 2 KB (mapeados até `$0BFF`) saem truncados em 1 KB; corrigir isso exigiria mexer no núcleo (D216).
