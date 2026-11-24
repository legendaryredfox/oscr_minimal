# Adaptador do Tomy Pyuuta para o slot SNES (F-20, D217)

O núcleo `TomyPyuuta.cpp` do OSCR usa o barramento do slot SNES só para leitura. O endereço de 16 bits sai por PF (A0 a A7 do slot, byte baixo) e PK (A8 a A15, byte alto); os dados D0 a D7 entram por PC. **/DBIN** (PH4) abre a leitura e **/CS0** (PH3) e **/CS1** (PH6) escolhem a janela: /CS0 em `$8000-$BFFF` (8 e 16 KB), /CS1 em `$4000-$7FFF` (os 16 KB a mais dos cartuchos de 32 KB, jogos 3D). O `/RESET` (PH0) é levado a nível alto pelo núcleo. O resto dos pinos de controle (`PH1`, `PH5`) e `TIME` (PJ0) vão a nível alto e **não chegam ao cartucho**; PL e PA ficam sem ligação. O cartucho é de 5 V (o slot SNES é 5 V fixo em todas as placas). O adaptador não foi desenhado: falta o PCB (conector de 36 posições, 2,54 mm, duas fileiras, chaveamento a confirmar).

## Ordem dos bits (a armadilha deste sistema)

O Pyuuta usa a numeração do TMS9995: **A0 é o bit mais significativo e A15 o menos; D0 é o bit mais significativo do byte e D7 o menos**. O núcleo põe o endereço `addr` em PF/PK e lê o dado em PC com o bit 0 como o menos significativo. Por isso a fiação do adaptador **inverte** a ordem: o pino A15 do cartucho vai a PF0 e o A0 a PK7; D7 vai a PC0 e D0 a PC7. A tabela abaixo já está nessa ordem. O comentário do núcleo diz o mesmo ("PCB ADAPTER WIRED FOR DIFFERENCE").

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 36P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/TomyPyuuta.cpp` (duas colunas: pinos pares à esquerda, ímpares à direita). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_pyuuta.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (36P) |
|---|---|---|---|
| A0 | 40 | PK7 | 31 |
| A1 | 39 | PK6 | 27 |
| A2 | 38 | PK5 | 25 |
| A3 | 37 | PK4 | 24 |
| A4 | 6 | PK3 | 30 |
| A5 | 7 | PK2 | 28 |
| A6 | 8 | PK1 | 26 |
| A7 | 9 | PK0 | 22 |
| A8 | 10 | PF7 | 20 |
| A9 | 11 | PF6 | 18 |
| A10 | 12 | PF5 | 16 |
| A11 | 13 | PF4 | 14 |
| A12 | 14 | PF3 | 12 |
| A13 | 15 | PF2 | 10 |
| A14 | 16 | PF1 | 23 |
| A15 | 17 | PF0 | 8 |
| D0 | 53 | PC7 | 17 |
| D1 | 52 | PC6 | 15 |
| D2 | 51 | PC5 | 13 |
| D3 | 50 | PC4 | 11 |
| D4 | 22 | PC3 | 9 |
| D5 | 21 | PC2 | 7 |
| D6 | 20 | PC1 | 5 |
| D7 | 19 | PC0 | 3 |
| /CS0 | 49 | PH3 | 35 |
| /CS1 | 23 | PH6 | 21 |
| /DBIN | 18 | PH4 | 29 |
| /RESET | 26 | PH0 | 4 |

Pinos fixos do conector: +5V no 19 (slot 27 e 58, 5 V fixo), GND no 1 e no 2 (slot 5 e 36).

## Pontos a conferir com o cartucho na mão

- **Pinos que o núcleo não conduz:** J1-6 (6), /WE/CPUCLK (32), SOUND (33), /INT4 /EC (34) e CRUIN (36). Só a leitura de ROM não precisa deles; se o cartucho depender de algum (por exemplo CPUCLK para o decodificador), o adaptador tem que prendê-lo no nível certo. **PENDENTE**, depende do cartucho.
- A janela `$8000-$9FFF` (/CS0) vale para todos os tamanhos. O cartucho de 16 KB lê `$A000-$BFFF` também em /CS0, o de 32 KB lê `$4000-$7FFF` em /CS1.
- A sondagem do firmware (32 bytes de `$8000` com /DBIN e /CS0 baixos) só separa slot vazio de cartucho: a ROM do Pyuuta não tem assinatura.
