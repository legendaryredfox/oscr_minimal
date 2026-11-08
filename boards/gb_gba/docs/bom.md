# BOM — placa gb_gba (GBA; GB e GBC por adaptador) v1.1

Montagem **manual**. Lista gerada de `boards/gb_gba/fab/bom-v1.1.csv` mais as peças sem símbolo (pinos e espaçadores).

> **Pendências antes de comprar:** medidas reais do slot GBA; direção do cartucho (D28); adaptador de GB/GBC (D56).

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `boards/gb_gba/fab/dumper-v1.1-jlcpcb.zip` |
| Camadas | 2 |
| Dimensões | 138,1 × 67,1 mm (acima de 100 mm de largura: faixa de preço maior) |
| Espessura / acabamento | 1,6 mm, HASL |
| Quantidade | 5 |
| Furos | metalizados (inclui as vias de costura do GND) e 10 não metalizados de 3,2 mm (4 do lado do Mega e 6 do Mega); os 2 furos-guia do slot GBA são não metalizados de 2,2 mm |
| Demais | trilha/espaço mín. 0,2 mm; sem montagem; sem stencil |

## Componentes

| Ref. | Qtd | Valor | Footprint | Observação |
|---|---|---|---|---|
| A1 | 1 | Arduino Mega 2560 R3 (do usuário, USB-C) | `Mega2560_R3_Shield` | Não vai na compra da placa. |
| GBA1 | 1 | Slot de cartucho GBA 32 pads, SMD, 1,5 mm | `GBA_Slot` | Igual ao do OSCR; única peça SMD. |
| U1 | 1 | MCP1700-3302E/TO, 3,3 V, TO-92 | `TO-92` | Só alimenta o slot GBA. |
| C2, C3 | 2 | 1 µF cerâmico, passo 5 mm | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | Entrada e saída do U1. |
| C4 | 1 | 100 nF cerâmico, passo 5 mm | idem | VCC do slot. |
| D1 | 1 | LED 3 mm | `LED_D3.0mm` | Ativo em nível baixo (cátodo em D38). |
| R1 | 1 | 220 Ω 1/4 W | `R_Axial_DIN0207...P10.16mm` | Resistor do LED. |
| C1 | 1 | 470 µF / 16 V, radial Ø8 mm, passo 3,5 mm | `CP_Radial_D8.0mm_P3.50mm` | Entrada de 5V. |

Sem Si5351, PIC, R2 e pontos de teste.

## Pinos e mecânica

| Item | Qtd | Observação |
|---|---|---|
| Pinos macho 2,54 mm, **cauda longa** (≥ 10 mm abaixo, ≥ 5 mm acima) | **85 posições** | Todos os pads do shield, inclusive os sem sinal (2 tiras 1x40 e 1 tira 2x20, corte em 2x18). |
| Espaçador M3 + pé de borracha | 4 | Furos do lado do Mega; só apoio. |
| Espaçador M3 | 6 | Furos do Mega; seguram o shield no Mega, como na `16_and_8_bits`. |
| Cabo USB-C | 1 | Interface com o PC. |

## Bloco de troca de cartucho (v1.1, D126)

Circuito e motivo: `docs/referencia/bloco-troca.md` (na raiz do repositório). Peças novas desta placa:

| Ref. | Valor | Função |
|---|---|---|
| Q1 | IRF9540N (P-MOSFET, TO-220) | chave de alta do 5V dos slots (`+5V_CART`); comando no D19 (nível baixo liga) |
| R2 | 100 kΩ | gate do Q1 ao 5V (desligado com o Mega em reset) |
| R3 | 100 Ω | D19 ao gate do Q1 |
| R4, D2 | 1 kΩ, LED verde 3 mm | `+5V_CART` presente |
| Q2, R5 e R6 | 2N7000 (TO-92), 330 Ω (o R6 descarrega o 3,3 V) | descarga do rail quando o Q1 abre |
| Q3, R7, R8, R9, D3 | 2N7000, 100 kΩ, 1 kΩ, 1 kΩ, LED amarelo 3 mm | sensor do rail: D3 aceso = seguro trocar; R9 leva o nó ao D53 |

Os pinos de 5V dos slots e dos circuitos que a placa tiver (Si5351, PIC, pull-up, entrada do regulador de 3,3 V) e os capacitores deles ficam em `+5V_CART`. O Q1 (TO-220) fica em pé na placa, sem dissipador (a corrente do cartucho é baixa).

Peças a comprar a mais por placa: 1 × IRF9540N, 2 × 2N7000, 1 LED verde e 1 LED amarelo de 3 mm, resistores axiais 1/4 W (pequenos, 0204 ou 0207 em pé): 100 kΩ × 2, 100 Ω × 1, 1 kΩ × 3, 330 Ω × 2.
