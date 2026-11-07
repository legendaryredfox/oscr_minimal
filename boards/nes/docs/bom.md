# BOM — placa nes (só NES) v1.0

Montagem **manual**. Lista gerada de `boards/nes/fab/bom.csv` mais as peças sem símbolo (pinos e espaçadores).

> **Pendências antes de comprar:** medidas reais do slot NES e do módulo Si5351 (D17, D23); direção da etiqueta (D27).

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `boards/nes/fab/dumper-v1.0-jlcpcb.zip` (cópia idêntica: `dumper-v1.0-gerbers-jlcpcb.zip`) |
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
| NES1 | 1 | Slot de cartucho NES 72 pinos, passo 2,5 mm | `NES_Slot` | Igual ao do OSCR. |
| U1 | 1 | Módulo Si5351 (CJMCU-5351, 25 MHz) + header fêmea 1x7 | `PinSocket_1x07_P2.54mm_Vertical` | Pinos: VIN, GND, SDA, SCL, 2, 1, 0. Só o CLK0 (pino 0) vai ao slot. |
| D1 | 1 | LED 3 mm | `LED_D3.0mm` | Ativo em nível baixo (cátodo em D38). |
| R1 | 1 | 220 Ω 1/4 W | `R_Axial_DIN0207...P10.16mm` | Resistor do LED. |
| C1 | 1 | 470 µF / 16 V, radial Ø8 mm, passo 3,5 mm | `CP_Radial_D8.0mm_P3.50mm` | Entrada de 5V. |
| C2 | 1 | 100 nF cerâmico, passo 5 mm | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | No slot NES (pino 36, VCC). |

Sem PIC (o NES não usa CIC do SNES), sem R2 e sem pontos de teste.

## Pinos e mecânica

| Item | Qtd | Observação |
|---|---|---|
| Pinos macho 2,54 mm, **cauda longa** (≥ 10 mm abaixo, ≥ 5 mm acima) | **85 posições** | Todos os pads do shield, inclusive os sem sinal (2 tiras 1x40 e 1 tira 2x20, corte em 2x18). |
| Espaçador M3 + pé de borracha | 4 (cantos) | Só apoio. |
| Espaçador M3 | 6 (furos do Mega) | Seguram o shield no Mega, como na `16_and_8_bits`. |
| Cabo USB-C | 1 | Interface com o PC. |
