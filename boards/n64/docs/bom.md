# BOM — placa n64 (só N64) v1.1

Montagem **manual**. Lista gerada de `boards/n64/fab/bom-v1.1.csv` mais as peças sem símbolo (pinos e espaçadores).

> **Pendências antes de comprar:** medidas reais do slot N64 (50 pinos, 2,5 mm; o contorno do footprint é estimativa, D17/D120), do módulo Si5351 (D17, D23) e direção da etiqueta (D27).

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `boards/n64/fab/dumper-v1.1-jlcpcb.zip` |
| Camadas | 2 |
| Dimensões | 110,1 × 65,1 mm (acima de 100 mm de largura: faixa de preço maior) |
| Espessura / acabamento | 1,6 mm, HASL |
| Quantidade | 5 |
| Furos | metalizados (inclui as vias de costura do GND) e 10 não metalizados de 3,2 mm (4 de canto e 6 do Mega) |
| Demais | trilha/espaço mín. 0,2 mm; sem montagem; sem stencil |

## Componentes

| Ref. | Qtd | Valor | Footprint | Observação |
|---|---|---|---|---|
| A1 | 1 | Arduino Mega 2560 R3 (do usuário, USB-C) | `Mega2560_R3_Shield` | Não vai na compra da placa. |
| N64_1 | 1 | Slot de cartucho N64, 50 pinos, passo 2,5 mm, duas fileiras de 25 | `N64_Slot` | Footprint do OSCR (`N64 Slot`). **3,3 V.** |
| U1 | 1 | Módulo Si5351 (CJMCU-5351, 25 MHz) + header fêmea 1x7 | `PinSocket_1x07_P2.54mm_Vertical` | Pinos: VIN, GND, SDA, SCL, 2, 1, 0. Só o `CLK1` vai ao slot (EEPROM_CLK, pino 19). |
| U2 | 1 | MCP1700-3302E/TO (3,3 V, 250 mA, TO-92) | `TO-92` | Só para o slot N64. |
| D1 | 1 | LED 3 mm | `LED_D3.0mm` | Ativo em nível baixo (cátodo em D38). |
| R1 | 1 | 220 Ω 1/4 W | `R_Axial_DIN0207...P10.16mm` | Resistor do LED. |
| R2 | 1 | 1 kΩ 1/4 W | idem | Pull-up do D7 (EEPROM_DATA, pino 21) **ao 3,3 V**. |
| C1 | 1 | 470 µF / 16 V, radial Ø8 mm, passo 3,5 mm | `CP_Radial_D8.0mm_P3.50mm` | Entrada de 5V. |
| C2, C3 | 2 | 1 µF cerâmico X7R, passo 5 mm | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | Entrada e saída do U2. |
| C4 | 1 | 100 nF cerâmico, passo 5 mm | idem | VCC do slot (pinos 9 e 34). |

Sem PIC (o dumper não usa o CIC do N64) e sem pontos de teste.

## Pinos e mecânica

| Item | Qtd | Observação |
|---|---|---|
| Pinos macho 2,54 mm, **cauda longa** (≥ 10 mm abaixo, ≥ 5 mm acima) | **85 posições** | Todos os pads do shield, inclusive os sem sinal (2 tiras 1x40 e 1 tira 2x20, corte em 2x18). |
| Espaçador M3 + pé de borracha | 4 (cantos) | Só apoio. |
| Espaçador M3 | 6 (furos do Mega) | Seguram o shield no Mega. |
| Cabo USB-C | 1 | Interface com o PC. |

## Bloco de troca de cartucho (v1.1, D126)

Circuito e motivo: `docs/referencia/bloco-troca.md` (na raiz do repositório). Peças novas desta placa:

| Ref. | Valor | Função |
|---|---|---|
| Q1 | IRF9540N (P-MOSFET, TO-220) | chave de alta do 5V dos slots (`+5V_CART`); comando no D19 (nível baixo liga) |
| R3 | 100 kΩ | gate do Q1 ao 5V (desligado com o Mega em reset) |
| R4 | 100 Ω | D19 ao gate do Q1 |
| R5, D2 | 1 kΩ, LED verde 3 mm | `+5V_CART` presente |
| Q2, R6 e R7 | 2N7000 (TO-92), 330 Ω (o R7 descarrega o 3,3 V) | descarga do rail quando o Q1 abre |
| Q3, R8, R9, R10, D3 | 2N7000, 100 kΩ, 1 kΩ, 1 kΩ, LED amarelo 3 mm | sensor do rail: D3 aceso = seguro trocar; R10 leva o nó ao D53 |

Os pinos de 5V dos slots e dos circuitos que a placa tiver (Si5351, PIC, pull-up, entrada do regulador de 3,3 V) e os capacitores deles ficam em `+5V_CART`. O Q1 (TO-220) fica em pé na placa, sem dissipador (a corrente do cartucho é baixa).

Peças a comprar a mais por placa: 1 × IRF9540N, 2 × 2N7000, 1 LED verde e 1 LED amarelo de 3 mm, resistores axiais 1/4 W (pequenos, 0204 ou 0207 em pé): 100 kΩ × 2, 100 Ω × 1, 1 kΩ × 3, 330 Ω × 2.

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

Peças opcionais a comprar a mais por placa:

| Ref. | Peça | Qtd | Onde |
|---|---|---|---|
| F1 | PTC de furo passante 0,35 a 0,5 A (Bourns MF-RHT050) | 1 | todas as versões (v1.0 e v1.1) |

**F1** (PTC de furo passante, Bourns MF-RHT050 ou equivalente de 0,35 a 0,5 A de retenção, passo de 5,1 mm), em série com o 5 V que a placa recebe do Mega (nas versões com bloco de troca, antes do Q1). Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 e v1.1 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o F1, ponha um fio ou uma ponte de solda entre os dois furos dele**, senão a placa fica sem 5 V.
