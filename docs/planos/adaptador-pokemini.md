# Adaptador do Pokémon Mini para o slot SNES (F-20, D227)

O núcleo `PokemonMini.cpp` do OSCR usa o barramento do slot SNES só para leitura. O cartucho tem o endereço **multiplexado e travado no próprio cartucho**: o `readData` do núcleo põe A10 a A17 em PF e A18 a A20 em PK0 a PK2 e dá um pulso em **HALE** (PH0); depois põe A0 a A7 em PF e A8 e A9 em PK0 e PK1 e sobe **LALE** (PH4). Com LALE alto, sobe **OE** (PH6), espera 5 NOP, lê D0 a D7 em PC e desce OE e LALE. **CS** (PH3) fica alto o tempo todo (os sinais de controle do cartucho são ativos em nível alto); **WE** (PH5) fica baixo. `PH1`, `TIME` (PJ0), PA e PL vão a nível alto e **não chegam ao cartucho**. A leitura tem sempre 512 KB (o núcleo: "ALL ROMS ARE 512K"). O adaptador não foi desenhado: falta o PCB.

## Tensão: 3,3 V (mesmo problema do Neo Geo Pocket e do Supervision, D203 e D218)

O núcleo pede 3,3 V (`setVoltage(k3V3)`) e o quadro do cartucho rotula os três VCC como "VCC (3.3V)". O VCC do slot SNES é **5 V fixo em todas as placas**: ligar os VCC do cartucho direto a ele pode estragar o cartucho. O adaptador precisa do próprio regulador de 3,3 V (LDO THT, por exemplo MCP1700 ou LD1117V33, mais capacitores), alimentado pelo 5 V do slot (27 e 58) e ligado aos pinos B1, A1 e A7 do conector. Os sinais do Mega são de 5 V em qualquer caso (D140), como anotado para o Neo Geo Pocket.

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 32P 0.5mm pitch" no começo de `firmware/oscr/src/cores/PokemonMini.cpp` (fileira de cima B1 a B17, de baixo A1 a A15), com a lista CONTROL PINS (HALE no RESET, CS no /CS, LALE no /IRQ, WE no /WR e OE no /RD do slot SNES). O comentário do `cartOn` do núcleo troca os nomes (`LALE(PH0)`, `HALE(PH4)`), mas os `#define` e a lista CONTROL PINS dizem HALE = PH0 e LALE = PH4, e é isso que o código faz. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_pokemini.py` confere o quadro, a lista CONTROL PINS, o pinmap e as portas que o `readData` usa.

Nos rótulos `A0/A10` a `A9/A19`, o primeiro nome é o bit que vai na fase de LALE e o segundo o da fase de HALE; o A20 só existe na fase de HALE e vai no A10 do slot (PK2), como diz o núcleo.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (32P) |
|---|---|---|---|
| A0/A10 | 17 | PF0 | B7 |
| A1/A11 | 16 | PF1 | A6 |
| A2/A12 | 15 | PF2 | B6 |
| A3/A13 | 14 | PF3 | A5 |
| A4/A14 | 13 | PF4 | B5 |
| A5/A15 | 12 | PF5 | A4 |
| A6/A16 | 11 | PF6 | B4 |
| A7/A17 | 10 | PF7 | A3 |
| A8/A18 | 9 | PK0 | B3 |
| A9/A19 | 8 | PK1 | A2 |
| A20 | 7 | PK2 | B2 |
| D0 | 19 | PC0 | B10 |
| D1 | 20 | PC1 | A9 |
| D2 | 21 | PC2 | B11 |
| D3 | 22 | PC3 | A10 |
| D4 | 50 | PC4 | B12 |
| D5 | 51 | PC5 | A11 |
| D6 | 52 | PC6 | B13 |
| D7 | 53 | PC7 | A12 |
| HALE | 26 | PH0 | B8 |
| CS | 49 | PH3 | A14 |
| LALE | 18 | PH4 | B9 |
| WE | 54 | PH5 | B15 |
| OE | 23 | PH6 | B14 |

Pinos fixos do conector: VCC no B1, no A1 e no A7 (3,3 V do LDO do adaptador, ver acima); GND no A8, no A15 e no B17 (slot 5 e 36). Sem ligação: IRQ (A13) e CARD_N (B16), que o núcleo não usa.

## Pontos a conferir com o cartucho na mão

- **Conector:** o quadro diz "32P 0.5mm pitch" para o cartucho e "33P 1.0mm pitch" para o conector SMD do console; medir a borda do cartucho antes de escolher a peça. A borda tem a fileira de cima e a de baixo deslocadas (o "--" entre A7 e A8 no quadro).
- **CARD_N (B16):** pelo nome, é a detecção de cartucho do console; o núcleo não o lê. Deixar sem ligação até medir no cartucho.
- **Sinais ativos em nível alto:** CS, OE e WE do cartucho são o contrário do slot SNES (/CS, /RD, /WR). O núcleo já os conduz assim; o adaptador liga direto, sem inversor.
- A sondagem do firmware (32 bytes de `$2100`, o primeiro endereço que o console lê do cartucho) só separa slot vazio de cartucho; o fork não confere assinatura. O save do Pokémon Mini fica no console, não no cartucho.
