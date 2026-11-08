# BOM — placa megadrive_sms (Mega Drive + Master System) v1.0

Montagem **manual**. Lista gerada de `boards/megadrive_sms/fab/bom-v1.0.csv` mais as peças sem símbolo (pinos e espaçadores).

> **Pendências antes de comprar:** medidas reais dos slots Mega Drive e Master System (D17, D23, D136); direção da etiqueta de cada um (D27; a do SMS ainda não está no silk).

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `boards/megadrive_sms/fab/dumper-v1.0-jlcpcb.zip` |
| Camadas | 2 |
| Dimensões | 107,1 × 83,1 mm (acima de 100 mm de largura: faixa de preço maior) |
| Espessura / acabamento | 1,6 mm, HASL |
| Quantidade | 5 |
| Furos | metalizados (inclui as vias de costura do GND) e 6 não metalizados (3,2 mm, cantos) |
| Demais | trilha/espaço mín. 0,2 mm; sem montagem; sem stencil |

## Componentes

| Ref. | Qtd | Valor | Footprint | Observação |
|---|---|---|---|---|
| A1 | 1 | Arduino Mega 2560 R3 (do usuário, USB-C) | `Mega2560_R3_Shield` | Não vai na compra da placa. |
| MD1 | 1 | Slot de cartucho Mega Drive/Genesis 64 pinos, 2,54 mm | `MD_Slot` | Igual ao do OSCR. |
| SMS1 | 1 | Slot de cartucho Master System / Mark III 50 pinos (2 × 25), 2,54 mm | `SMS_Slot` | "50 pin 2.54mm Master System slot (2x25)" do wiki de peças do OSCR; mesmo item de AliExpress do slot MD. |
| D1 | 1 | LED 3 mm | `LED_D3.0mm` | Ativo em nível baixo (cátodo em D38). |
| R1 | 1 | 220 Ω 1/4 W | `R_Axial_DIN0207...P10.16mm` | Resistor do LED. |
| C1 | 1 | 470 µF / 16 V, radial Ø8 mm, passo 3,5 mm | `CP_Radial_D8.0mm_P3.50mm` | Entrada de 5V. |
| C2, C3, C4, C5 | 4 | 100 nF cerâmico, passo 5 mm | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | C2 no meio do slot MD; C3 junto ao A31; C4 junto ao A2; C5 junto ao 5V (pino 1) do slot SMS. |
| TP1 a TP6 | 6 | Pontos de teste, pad de 2 mm, furo 1 mm | só cobre | `/UWR`, `/CE`, `5V`, `GND`, `/OE`, `/WE`. Opcional: tira de pinos macho 1x6 de 2,54 mm (os furos de 1 mm ficam a 2,54 mm um do outro). |

Sem Si5351, sem PIC, sem soquete DIP-8, sem R2 e **sem o bloco de troca de cartucho** (v1.0 é a mais barata que funciona: para trocar o cartucho, desligue o USB).

## Pinos e mecânica

| Item | Qtd | Observação |
|---|---|---|
| Pinos macho 2,54 mm, **cauda longa** (≥ 10 mm abaixo, ≥ 5 mm acima) | **85 posições** | Todos os pads do shield, inclusive os sem sinal (2 tiras 1x40 e 1 tira 2x20, corte em 2x18). |
| Espaçador M3 + pé de borracha | 6 | Furos de canto; só apoio. |
| Cabo USB-C | 1 | Interface com o PC. |
