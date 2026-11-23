# Adaptador do Neo Geo Pocket para o slot SNES (F-20, D203)

O núcleo `NeoGeoPocket.cpp` do OSCR (D202) usa os mesmos pinos do slot SNES: A0 a A15 em PF e PK, A16 a A20 em PL0 a PL4 (BA0 a BA4 do slot), D0 a D7 em PC, `/CE0` em PH3 (`/Cart`), `/CE1` em PH0 (`/RESET`), `/OE` em PH6 (`/RD`), `/WE` em PH5 (`/WR`) e `PWR` em PH4 (`/IRQ`, entrada com pull-up). **O adaptador é só um cartão que liga o conector do cartucho do NGP a esses pinos do slot.**

## Fonte da tabela (conferida)

Esquemático do adaptador do OSCR: `pcb/adapters/ngp_adapter_schematic.png` e `ngp_adapter.zip` (Gerber), repositório `sanni/cartreader`, commit `bd3eaa106b6e4cbdffbfa89a3fb5fedf3e028b17` (hardware CC BY 4.0). Os números foram lidos na imagem ampliada e cruzados com `boards/16_and_8_bits/docs/pinmap.md` (SNES) e com os comentários e a configuração de portas do núcleo; `python3 tools/check_adaptador_ngp.py` refaz essa conferência. O conector do NGP tem **36 posições** (numeração do esquemático do OSCR); a geometria dele (36 furos de 0,65 mm, duas fileiras defasadas, passo de 1,27 mm por fileira e 2 mm entre fileiras) está no arquivo de furação do Gerber do OSCR. Nenhum número de pino foi tirado de memória.

| Sinal | Pino do slot SNES | Porta AVR | Pino do conector NGP |
|---|---|---|---|
| A0 | 17 | PF0 | 2 |
| A1 | 16 | PF1 | 10 |
| A2 | 15 | PF2 | 11 |
| A3 | 14 | PF3 | 12 |
| A4 | 13 | PF4 | 13 |
| A5 | 12 | PF5 | 14 |
| A6 | 11 | PF6 | 15 |
| A7 | 10 | PF7 | 16 |
| A8 | 9 | PK0 | 20 |
| A9 | 8 | PK1 | 21 |
| A10 | 7 | PK2 | 32 |
| A11 | 6 | PK3 | 22 |
| A12 | 37 | PK4 | 23 |
| A13 | 38 | PK5 | 24 |
| A14 | 39 | PK6 | 25 |
| A15 | 40 | PK7 | 26 |
| A16 | 41 | PL0 | 27 |
| A17 | 42 | PL1 | 35 |
| A18 | 43 | PL2 | 17 |
| A19 | 44 | PL3 | 33 |
| A20 | 45 | PL4 | 34 |
| D0 | 19 | PC0 | 6 |
| D1 | 20 | PC1 | 7 |
| D2 | 21 | PC2 | 8 |
| D3 | 22 | PC3 | 9 |
| D4 | 50 | PC4 | 28 |
| D5 | 51 | PC5 | 29 |
| D6 | 52 | PC6 | 30 |
| D7 | 53 | PC7 | 31 |
| /CE0 | 49 | PH3 | 4 |
| /CE1 | 26 | PH0 | 3 |
| /OE | 23 | PH6 | 5 |
| /WE | 54 | PH5 | 19 |
| PWR | 18 | PH4 | 1 |
| GND | 5 e 36 | - | 36 |
| VCC | 27 e 58 | - | 18 |

Pinos do slot sem uso: 24, 25 (CIC), 46 a 48 (BA5 a BA7), 55 a 57 (CIC e CPU clock). Nota do OSCR: a placa do adaptador precisa ter **1,2 mm** de espessura, ou não entra no slot SNES.

## Problema: o VCC do slot SNES é 5 V em todas as placas daqui

O esquemático do OSCR liga o VCC do NGP (pino 18) aos pinos 27 e 58 do slot, porque a placa do OSCR (VSelect) põe 3,3 V ali. **Nenhuma placa deste repositório tem seletor no slot SNES**: o `pinmap` diz "VCC 5V (fixo)" e o `seletor-tensao.md` lista o seletor só nos slots NES, Famicom, Mega Drive e SMS (o SNES fica em 5 V por causa do SA-1). Usar o adaptador do OSCR sem mudança poria **5 V no VCC das flashes do NGP (3,3 V)**. Os sinais do Mega são de 5 V em qualquer caso (D140), como no OSCR com o VSelect; isso fica igual.

Opções (precisa de decisão do usuário):

1. **Adaptador novo com regulador de 3,3 V na própria placa** (LDO THT, por exemplo MCP1700 ou LD1117V33, mais capacitores) alimentado pelos pinos 27 e 58 (5 V) e ligado só ao pino 18 do NGP. É o único que funciona em todas as placas com slot SNES (`snes`, `16_bits`, `16_and_8_bits`, `completa`). Exige desenho de PCB novo (conector de 36 posições, bordas de 1,2 mm no slot).
2. **Gerber do OSCR como está** (1,2 mm), só em placa que dê 3,3 V no slot SNES: nenhuma hoje. Não serve sem alterar uma placa.
3. **Gerber do OSCR com o VCC cortado e ligado a um 3,3 V externo** (modificação à mão). Serve para o primeiro teste; não é produto.

## O que falta

- Decidir a opção (recomendação: 1).
- Escolher o conector do cartucho do NGP (o OSCR usa um soquete de borda cortado; a geometria está no furo do Gerber deles, a peça comercial não foi identificada).
- Desenhar o PCB (1,2 mm, JLCPCB) e o esquemático em KiCad em `boards/adaptadores/ngp/`, com a atribuição ao OSCR (CC BY 4.0) no silkscreen e no README.
- Medir em bancada: continuidade de cada linha, 3,3 V no pino 18, e só então um cartucho.
