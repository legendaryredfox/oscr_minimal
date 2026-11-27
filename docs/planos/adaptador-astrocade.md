# Adaptador do Bally Astrocade para o slot SNES (F-20, D223)

O núcleo `BallyAstrocade.cpp` do OSCR usa o barramento do slot SNES só para leitura. O endereço sai por PF (A0 a A7) e PK (A8 a A12; o núcleo escreve o byte alto inteiro em PK, mas A13 a A15 ficam sempre em 0 e não chegam ao cartucho); os dados D0 a D7 entram por PC, em ordem normal. **/ENABLE** (PH3) abre a leitura: o `readData` do núcleo o baixa, espera 5 NOP, lê PC e o sobe. `PH0`, `PH1`, `PH4`, `PH5`, `PH6` e `TIME` (PJ0) ficam altos e **não chegam ao cartucho**; PL e PA ficam sem ligação. O cartucho é de 5 V (`setVoltage(k5V)`; o slot SNES é 5 V fixo em todas as placas, sem regulador no adaptador). O adaptador não foi desenhado: falta o PCB (conector de 26 posições numa fileira, 2,54 mm segundo o quadro do núcleo, "26P 2.54mm pitch connector").

## Fonte (conferida)

Pinagem do cartucho: o quadro "Cartridge Pinout, 26P 2.54mm pitch connector" no começo de `firmware/oscr/src/cores/BallyAstrocade.cpp`. Pinos do slot e portas: `boards/16_and_8_bits/docs/pinmap.md` (SNES). `python3 tools/check_adaptador_astrocade.py` confere o quadro, o pinmap e as portas que o núcleo usa.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector (26P) |
|---|---|---|---|
| A0 | 17 | PF0 | 9 |
| A1 | 16 | PF1 | 8 |
| A2 | 15 | PF2 | 7 |
| A3 | 14 | PF3 | 6 |
| A4 | 13 | PF4 | 5 |
| A5 | 12 | PF5 | 4 |
| A6 | 11 | PF6 | 3 |
| A7 | 10 | PF7 | 2 |
| A8 | 9 | PK0 | 24 |
| A9 | 8 | PK1 | 23 |
| A10 | 7 | PK2 | 20 |
| A11 | 6 | PK3 | 19 |
| A12 | 37 | PK4 | 22 |
| D0 | 19 | PC0 | 10 |
| D1 | 20 | PC1 | 11 |
| D2 | 21 | PC2 | 12 |
| D3 | 22 | PC3 | 14 |
| D4 | 50 | PC4 | 15 |
| D5 | 51 | PC5 | 16 |
| D6 | 52 | PC6 | 17 |
| D7 | 53 | PC7 | 18 |
| /ENABLE | 49 | PH3 | 21 |

Pinos fixos do conector: +5V no 25 (slot 27 e 58, 5 V fixo), GND no 1, no 13 e no 26 (slot 5 e 36).

## Pontos a conferir com o cartucho na mão

- **Passo e chaveamento do conector:** o quadro do núcleo diz 26 posições a 2,54 mm numa fileira; medir no cartucho antes de escolher o conector. O lado "BOTTOM"/"TOP" do quadro define a face do cartucho que encosta em cada fileira de contatos.
- O núcleo lê `$0000` em diante com /ENABLE baixo e não aciona outro sinal: cartucho que dependa de outro pino (por exemplo um chip select vindo do console) não é coberto. A tabela não tem nenhum pino que o núcleo deixe sem conduzir.
- O `readROM` lê 2, 4 ou 8 KB (tabela `BALLY` do núcleo): o PC sempre informa o tamanho (`--prg 2|4|8`). Um cartucho menor que o tamanho pedido sai espelhado; um maior sai truncado.
- A sondagem do firmware (32 bytes de `$0000`) só separa slot vazio de cartucho; o fork não confere assinatura nem cabeçalho.
