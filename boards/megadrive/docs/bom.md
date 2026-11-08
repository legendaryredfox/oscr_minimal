# BOM — placa megadrive (só Mega Drive) v1.1

Montagem **manual**. Lista gerada de `boards/megadrive/fab/bom-v1.1.csv` mais as peças sem símbolo (pinos e espaçadores).

> **Pendências antes de comprar:** medidas reais do slot Mega Drive (D17, D23); direção da etiqueta (D27).

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `boards/megadrive/fab/dumper-v1.1-jlcpcb.zip` |
| Camadas | 2 |
| Dimensões | 107,1 × 65,1 mm (acima de 100 mm de largura: faixa de preço maior) |
| Espessura / acabamento | 1,6 mm, HASL |
| Quantidade | 5 |
| Furos | metalizados (inclui as vias de costura do GND) e 4 não metalizados (3,2 mm, cantos) |
| Demais | trilha/espaço mín. 0,2 mm; sem montagem; sem stencil |

## Componentes

| Ref. | Qtd | Valor | Footprint | Observação |
|---|---|---|---|---|
| A1 | 1 | Arduino Mega 2560 R3 (do usuário, USB-C) | `Mega2560_R3_Shield` | Não vai na compra da placa. |
| MD1 | 1 | Slot de cartucho Mega Drive/Genesis 64 pinos, 2,54 mm | `MD_Slot` | Igual ao do OSCR. |
| D1 | 1 | LED 3 mm | `LED_D3.0mm` | Ativo em nível baixo (cátodo em D38). |
| R1 | 1 | 220 Ω 1/4 W | `R_Axial_DIN0207...P10.16mm` | Resistor do LED. |
| C1 | 1 | 470 µF / 16 V, radial Ø8 mm, passo 3,5 mm | `CP_Radial_D8.0mm_P3.50mm` | Entrada de 5V. |
| C2, C3, C4 | 3 | 100 nF cerâmico, passo 5 mm | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | C2 no meio do slot; C3 junto ao A31; C4 junto ao A2. |
| TP1 a TP6 | 6 | Pontos de teste, pad de 2 mm, furo 1 mm | só cobre | `/UWR`, `/CE`, `5V`, `GND`, `/OE`, `/WE`. Opcional: tira de pinos macho 1x6 de 2,54 mm (os furos de 1 mm ficam a 2,54 mm um do outro). |

Sem Si5351, sem PIC, sem soquete DIP-8, sem R2.

## Pinos e mecânica

| Item | Qtd | Observação |
|---|---|---|
| Pinos macho 2,54 mm, **cauda longa** (≥ 10 mm abaixo, ≥ 5 mm acima) | **85 posições** | Todos os pads do shield, inclusive os sem sinal (2 tiras 1x40 e 1 tira 2x20, corte em 2x18). |
| Espaçador M3 + pé de borracha | 4 | Furos de canto; só apoio. |
| Cabo USB-C | 1 | Interface com o PC. |

## Bloco de troca de cartucho (v1.1, D126)

Circuito e motivo: `docs/referencia/bloco-troca.md` (na raiz do repositório). Peças novas desta placa:

| Ref. | Valor | Função |
|---|---|---|
| Q1 | IRF9540N (P-MOSFET, TO-220) | chave de alta do 5V dos slots (`+5V_CART`); comando no D19 (nível baixo liga) |
| R2 | 100 kΩ | gate do Q1 ao 5V (desligado com o Mega em reset) |
| R3 | 100 Ω | D19 ao gate do Q1 |
| R4, D2 | 1 kΩ, LED verde 3 mm | `+5V_CART` presente |
| Q2, R5 | 2N7000 (TO-92), 330 Ω | descarga do rail quando o Q1 abre |
| Q3, R6, R7, R8, D3 | 2N7000, 100 kΩ, 1 kΩ, 1 kΩ, LED amarelo 3 mm | sensor do rail: D3 aceso = seguro trocar; R8 leva o nó ao D53 |

Os pinos de 5V dos slots e dos circuitos que a placa tiver (Si5351, PIC, pull-up, entrada do regulador de 3,3 V) e os capacitores deles ficam em `+5V_CART`. O Q1 (TO-220) fica em pé na placa, sem dissipador (a corrente do cartucho é baixa).

Peças a comprar a mais por placa: 1 × IRF9540N, 2 × 2N7000, 1 LED verde e 1 LED amarelo de 3 mm, resistores axiais 1/4 W (pequenos, 0204 ou 0207 em pé): 100 kΩ × 2, 100 Ω × 1, 1 kΩ × 3, 330 Ω × 1.

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

Peças opcionais a comprar a mais por placa:

| Ref. | Peça | Qtd | Onde |
|---|---|---|---|
| F1 | PTC de furo passante 0,35 a 0,5 A (Bourns MF-RHT050) | 1 | todas as versões (v1.0 e v1.1) |
| J1 | cabeçalho de 2 pinos de 2,54 mm e um jumper ("TRAVA 3,3 V") | 1 | v1.1 |
| LDO | LD1117V33 (TO-220) | 1 | v1.1 |
| Q4 | IRF9540N (P-MOSFET, TO-220) | 1 | v1.1 |
| Q5 | 2N7000 (TO-92) | 1 | v1.1 |
| RN1 a RN7 | rede isolada de 8 resistores de 470 Ω, DIP-16 | 7 | v1.1 |
| C (2) | 100 nF cerâmico e 10 µF/16 V eletrolítico (entrada e saída do LDO) | 2 | v1.1 |
| R (3) | 100 kΩ, 1 kΩ e 220 Ω, axiais 1/4 W | 3 | v1.1 |

**F1** (PTC de furo passante, Bourns MF-RHT050 ou equivalente de 0,35 a 0,5 A de retenção, passo de 5,1 mm), em série com o 5 V que a placa recebe do Mega (nas versões com bloco de troca, antes do Q1). Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 e v1.1 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o F1, ponha um fio ou uma ponte de solda entre os dois furos dele**, senão a placa fica sem 5 V.

Seletor 3,3 V/5 V nos slots Mega Drive (resto da placa sempre em 5 V). Preço aproximado das peças extras: menos de US$ 3 por placa (estimativa de varejo, não cotada).
