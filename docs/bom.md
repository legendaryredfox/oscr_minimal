# BOM — oscr_minimal v1.0

Montagem **manual** (sem montagem pela JLCPCB). Esta lista vem de `hardware/fab/bom.csv` (gerado do esquemático) mais as peças que não têm símbolo (pinos, espaçadores, cabo).

> **Pendências antes de comprar (conferir quando as peças chegarem):**
> - Medidas reais dos slots e do módulo Si5351 (estimadas: `docs/decisoes.md` D17, D23).
> - Direção da etiqueta de cada slot (D27) e do GBA (D28).
> - Footprint do slot GBA é o do OSCR (SMD). Conferir se o slot comprado tem os mesmos 32 pads de 1,5 mm e os 2 furos-guia de 2,2 mm.

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `hardware/fab/dumper-v1.0-jlcpcb.zip` |
| Camadas | 2 |
| Dimensões | 144,05 × 108,05 mm (acima de 100 × 100 mm: preço maior) |
| Espessura | 1,6 mm |
| Acabamento | HASL (com chumbo ou sem; sem chumbo é mais comum) |
| Quantidade | 5 |
| Cor / máscara | tanto faz (padrão verde) |
| Cobre | 1 oz |
| Furos | 915 metalizados (mín. 0,3 mm), 12 não metalizados (2,2 e 3,2 mm) |
| Demais | trilha/espaço mín. 0,2 mm / 0,2 mm; sem borda castelada; sem montagem; sem stencil |

## Componentes

| Ref. | Qtd | Valor | Footprint | Observação |
|---|---|---|---|---|
| A1 | 1 | Arduino Mega 2560 R3 (placa do usuário, USB-C) | `Mega2560_R3_Shield` | **Não vai na compra da placa.** Os pads do shield pedem pinos macho longos (abaixo). |
| SNES1 | 1 | Slot de cartucho SNES/SFC 62 pinos, passo 2,5 mm | `SNES_Slot` | Igual ao do OSCR. |
| NES1 | 1 | Slot de cartucho NES 72 pinos, passo 2,5 mm | `NES_Slot` | Igual ao do OSCR. |
| FC1 | 1 | Slot de cartucho Famicom 60 pinos, passo 2,54 mm | `FC_Slot` | Igual ao do OSCR. |
| MD1 | 1 | Slot de cartucho Mega Drive/Genesis 64 pinos, passo 2,54 mm | `MD_Slot` | Igual ao do OSCR. |
| GBA1 | 1 | Slot de cartucho GBA 32 pinos, passo 1,5 mm | `GBA_Slot` | **SMD**, única peça SMD. 3,3 V apenas. |
| U1 | 1 | Módulo Si5351 (CJMCU-5351, 25 MHz) | header fêmea 1x7 2,54 mm | Pinos: VIN, GND, SDA, SCL, 2, 1, 0. |
| U1 (header) | 1 | Header fêmea 1x7, 2,54 mm | `PinSocket_1x07_P2.54mm_Vertical` | |
| U2 | 1 | PIC12F629-I/P (DIP-8), gravado com `snescic-lock-resync.hex` | | Fora do soquete até o teste de tensão. |
| U2 (soquete) | 1 | Soquete DIP-8 (7,62 mm) | `DIP-8_W7.62mm_Socket` | |
| U3 | 1 | MCP1700-3302E/TO (3,3 V, 250 mA, TO-92) | `TO-92` | Só para o slot GBA. |
| D1 | 1 | LED 3 mm, qualquer cor | `LED_D3.0mm` | Ativo em nível baixo (cátodo no D38). |
| R1 | 1 | 220 Ω 1/4 W | `R_Axial_DIN0207...P10.16mm` | Resistor do LED. |
| R2 | 1 | 1 kΩ 1/4 W | idem | Pull-up do D7 (IRQ do SNES). |
| C1 | 1 | 470 µF / 16 V eletrolítico, radial, Ø8 mm, passo 3,5 mm | `CP_Radial_D8.0mm_P3.50mm` | Entrada de 5V. |
| C2 a C6, C9 | 6 | 100 nF cerâmico, passo 5 mm | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | Um por slot (C2 a C5), PIC (C6) e GBA (C9). |
| C7, C8 | 2 | 1 µF cerâmico multicamada X7R, passo 5 mm | idem | Entrada/saída do U3. Precisa ser 1 µF ou mais, cerâmico ou tântalo. |

## Pinos e mecânica (sem símbolo no esquemático)

| Item | Qtd | Observação |
|---|---|---|
| Pinos macho 2,54 mm, **cauda longa** (≥ 10 mm abaixo do plástico, ≥ 5 mm acima) | **85 posições** | Todos os pads do shield, inclusive os sem sinal. Sugestão: 2 tiras 1x40 e 1 tira 2x20 (corte em 2x18). |
| Espaçador M3 fêmea-fêmea, ~12 mm | 6 | Nos 6 furos do Mega (3,2 mm). Conferir a altura com o USB e o jack do Mega. |
| Parafuso M3 (comprimento a medir) | 6 | Por baixo do Mega, até o espaçador. Sem parafuso por cima. |
| Espaçador M3 + pé de borracha | 4 | Furos de canto da placa. Comprimento a definir (fase 7: o Mega fica sob o shield). |
| Cabo USB-C para USB-C (ou USB-A) | 1 | Interface com o PC (D30). |

## Ferramentas e consumíveis
Ver `docs/montagem.md`.
