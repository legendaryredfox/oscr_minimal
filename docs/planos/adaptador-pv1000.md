# Adaptador do Casio PV-1000 para o slot SNES (F-20, D219)

O núcleo `CasioPV1000.cpp` do OSCR usa o barramento do slot SNES só para leitura. O endereço de 16 bits sai por PF (A0 a A7, byte baixo) e PK (A8 a A15, byte alto); os dados D0 a D7 entram por PC, sem inversão de bits (ordem normal). **/RD** (PH6) abre a leitura e **/CS1** (PH4) ou **/CS2** (PH3) escolhem a ROM: /CS1 para o cartucho de 8 KB, /CS2 para o de 16 KB (o `readROM` baixa um deles por vez e lê `$0000` em diante). **/WR** (PH5) fica alto o tempo todo. `PH0` e `PH1` (também altos) e `TIME` (PJ0) **não chegam ao cartucho**; PL e PA ficam sem ligação. O cartucho é de 5 V (`setVoltage(k5V)`; o slot SNES é 5 V fixo em todas as placas, sem regulador no adaptador). O adaptador não foi desenhado: falta o PCB (conector de 36 posições em duas fileiras de 18, 2,54 mm; o quadro do núcleo chama de "36P 2.54mm pitch").

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 36P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/CasioPV1000.cpp` (fileira B, a da frente, à esquerda; fileira A, a de trás, à direita). Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_pv1000.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (36P) |
|---|---|---|---|
| A0 | 17 | PF0 | B10 |
| A1 | 16 | PF1 | A10 |
| A2 | 15 | PF2 | B09 |
| A3 | 14 | PF3 | A09 |
| A4 | 13 | PF4 | B08 |
| A5 | 12 | PF5 | A08 |
| A6 | 11 | PF6 | B07 |
| A7 | 10 | PF7 | A07 |
| A8 | 9 | PK0 | B06 |
| A9 | 8 | PK1 | A06 |
| A10 | 7 | PK2 | B05 |
| A11 | 6 | PK3 | A05 |
| A12 | 37 | PK4 | B04 |
| A13 | 38 | PK5 | A04 |
| A14 | 39 | PK6 | B03 |
| A15 | 40 | PK7 | A03 |
| D0 | 19 | PC0 | B14 |
| D1 | 20 | PC1 | A14 |
| D2 | 21 | PC2 | B13 |
| D3 | 22 | PC3 | A13 |
| D4 | 50 | PC4 | B12 |
| D5 | 51 | PC5 | A12 |
| D6 | 52 | PC6 | B11 |
| D7 | 53 | PC7 | A11 |
| /CS1 | 18 | PH4 | B15 |
| /CS2 | 49 | PH3 | A15 |
| /RD | 23 | PH6 | A16 |
| /WR | 54 | PH5 | B16 |

Pinos fixos do conector: +5V em B01 e B18 (slot 27 e 58, 5 V fixo), GND em A01 e A18 (slot 5 e 36).

## Pontos a conferir com o cartucho na mão

- **Pinos que o núcleo não conduz:** CON (B17) e /IORQ (A17), mais os dois NC (B02 e A02). Só a leitura de ROM não precisa deles; se o cartucho depender de /IORQ ou de CON (por exemplo para desabilitar a ROM), o adaptador tem que prendê-los no nível certo. **PENDENTE**, depende do cartucho.
- O núcleo pressupõe ROM de 8 KB só com /CS1 e de 16 KB só com /CS2, e lê `$0000` em diante nos dois casos. Cartucho com RAM extra ou outro mapeamento não é coberto.
- A sondagem do firmware (32 bytes de `$0000`, primeiro com /CS1 baixo e, se vier vazio, com /CS2 baixo) só separa slot vazio de cartucho: a ROM do PV-1000 não tem assinatura. Fica a conferir se os dois /CS juntos num cartucho de 8 KB causam conflito de barramento (a sondagem só baixa um por vez).
- O PV-2000 usa o mesmo cartucho no quadro do núcleo (título "PV-1000/PV-2000"), mas só o PV-1000 foi levado em conta.
