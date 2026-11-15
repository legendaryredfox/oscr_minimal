# Corrente do regulador de 3,3 V (MCP1700) com GBA e N64 (K-3)

Data: 2026-11-15. **Resultado: não há número publicado de corrente só do cartucho, então a conta fica em limites e a medição é da bancada.**

## O que se conseguiu confirmar

- **MCP1700-3302E** (U3 nas placas `16_and_8_bits` e `completa`, U2 na `n64`; TO-92): corrente de saída máxima **250 mA** para saídas de 2,5 V ou mais; queda típica de **178 mV a 250 mA** (máxima 350 mV; o valor típico citado é para 2,8 V, o de 3,3 V não foi achado separado, é provavelmente parecido). Resistência térmica junção-ambiente do TO-92: **160 °C/W** na revisão de 2016, 131,9 °C/W numa revisão antiga com outro teste; as fontes divergem. Fontes: datasheets da Microchip espelhados em [Farnell](https://www.farnell.com/datasheets/1784514.pdf) e [Radiolocman](https://www.radiolocman.com/datasheet/pdf.html?di=128895). **Conferir a revisão do datasheet da peça comprada.**
- **N64:** nenhum valor de corrente só do Game Pak. O que existe é do console inteiro: um hobbysta mediu cerca de 1,16 A no trilho de 3,3 V sem cartucho e 1,0 a 1,4 A com cartuchos originais ([página](https://qwertz.w10.site/big_n/n64.html)); a fonte original é de 3,3 V a 2,7 A. Isso **não separa** a parte do cartucho (inclusive a do console), então não serve para dimensionar o U3. O conector do Game Pak tem vários pinos de 3,3 V (9, 17, 34 e 42 no [pinout](https://consolemods.org/wiki/N64:Connector_Pinouts)); a pinagem não dá corrente.
- **GBA:** não achei medida publicada nesta busca. Não vou usar número de memória.

## A conta que dá para fazer (só regulador)

Queda de tensão no regulador linear: 5 V − 3,3 V = 1,7 V. Potência dissipada = 1,7 V × I. Subida de temperatura = potência × θJA (usando 160 °C/W, o caso pior dos dois):

| Corrente do cartucho | Potência no U3 | Subida da junção (160 °C/W) |
|---|---|---|
| 50 mA | 0,085 W | cerca de 14 °C |
| 100 mA | 0,17 W | cerca de 27 °C |
| 150 mA | 0,255 W | cerca de 41 °C |
| 250 mA (limite) | 0,425 W | cerca de 68 °C |

Com 25 °C ambiente, 250 mA daria junção perto de 93 °C: dentro da faixa do componente, mas sem folga para a proteção de curto (o datasheet fala de limite de corrente, e não de uma corrente de operação segura contínua além dos 250 mA). Se o cartucho puxar perto disso, o regulador esquenta e a tensão cai.

## O que medir na bancada

1. Multímetro em série no 3,3 V entre U3 e o slot (ou fio de teste), com o cartucho parado (só inserido) e **durante a leitura**; anotar o pico.
2. Cartuchos diferentes: N64 de mask ROM, N64 com SRAM/FlashRAM, repro; GBA de mask ROM e repro com flash.
3. Medir a tensão de saída do U3 sob carga (cai muito perto de 250 mA).
4. Se algum passar de cerca de 150 mA: pensar em regulador maior (a mesma pinagem TO-92 não serve) antes de encomendar a `completa`.

Registrado também em `docs/continuacao.md` (só com hardware: corrente do U3 com o N64).
