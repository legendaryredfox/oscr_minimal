# BOM — placa famicom (só Famicom) v1.1

Montagem **manual**. Lista gerada de `boards/famicom/fab/bom-v1.1.csv` mais as peças sem símbolo (pinos e espaçadores).

> **Pendências antes de comprar:** medidas reais do slot Famicom (D17, D23); direção da etiqueta (D27).

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `boards/famicom/fab/dumper-v1.1-jlcpcb.zip` |
| Camadas | 2 |
| Dimensões | 107,1 × 65,1 mm (acima de 100 mm de largura: faixa de preço maior) |
| Espessura / acabamento | 1,6 mm, HASL |
| Quantidade | 5 |
| Furos | metalizados (inclui as vias de costura do GND) e 10 não metalizados de 3,2 mm (4 de canto e 6 do Mega) |
| Demais | trilha/espaço mín. 0,2 mm; sem montagem; sem stencil |

## Componentes

| Ref. | Qtd | Valor | Footprint | Observação |
|---|---|---|---|---|
| A1 | 1 | Arduino Mega 2560 R3 (do usuário, USB-C) | `Mega2560_R3_Shield` | Não vai na compra da placa. |
| FC1 | 1 | Slot de cartucho Famicom 60 pinos, passo 2,54 mm | `FC_Slot` | Igual ao do OSCR. |
| D1 | 1 | LED 3 mm | `LED_D3.0mm` | Ativo em nível baixo (cátodo em D38). |
| R1 | 1 | 220 Ω 1/4 W | `R_Axial_DIN0207...P10.16mm` | Resistor do LED. |
| C1 | 1 | 470 µF / 16 V, radial Ø8 mm, passo 3,5 mm | `CP_Radial_D8.0mm_P3.50mm` | Entrada de 5V. |
| C2 | 1 | 100 nF cerâmico, passo 5 mm | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | No slot Famicom (pinos 30 e 31, VCC). |

Sem Si5351, PIC, R2, regulador nem pontos de teste.

## Pinos e mecânica

| Item | Qtd | Observação |
|---|---|---|
| Pinos macho 2,54 mm, **cauda longa** (≥ 10 mm abaixo, ≥ 5 mm acima) | **85 posições** | Todos os pads do shield, inclusive os sem sinal (2 tiras 1x40 e 1 tira 2x20, corte em 2x18). |
| Espaçador M3 + pé de borracha | 4 (cantos) | Só apoio. |
| Espaçador M3 | 6 (furos do Mega) | Seguram o shield no Mega, como na `16_and_8_bits`. |
| Cabo USB-C | 1 | Interface com o PC. |

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

Peças opcionais a comprar a mais por placa:

| Ref. | Peça | Qtd | Onde |
|---|---|---|---|
| F1 | suporte de clipes para fusível 5×20 mm (Littelfuse série 100, 2 clipes) e fusível de vidro 5×20 mm de 500 mA, ação rápida | 1 + 1 (compre fusíveis de reserva) | todas as versões (v1.0 e v1.1) |
| J1 | cabeçalho de 2 pinos de 2,54 mm e um jumper ("TRAVA 3,3 V") | 1 | v1.1 |
| LDO | LD1117V33 (TO-220) | 1 | v1.1 |
| Q4 | IRF9540N (P-MOSFET, TO-220) | 1 | v1.1 |
| Q5 | 2N7000 (TO-92) | 1 | v1.1 |
| C (2) | 100 nF cerâmico e 10 µF/16 V eletrolítico (entrada e saída do LDO) | 2 | v1.1 |
| R (3) | 100 kΩ, 1 kΩ e 220 Ω, axiais 1/4 W | 3 | v1.1 |

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 e v1.1 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.

Seletor 3,3 V/5 V nos slots Famicom (resto da placa sempre em 5 V). Preço aproximado das peças extras: menos de US$ 3 por placa (estimativa de varejo, não cotada).
