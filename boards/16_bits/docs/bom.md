# BOM — placa 16_bits (SNES e Mega Drive) v. 1.2

Montagem **manual** (sem montagem pela JLCPCB). Esta lista vem de `boards/16_bits/fab/bom.csv` (gerado do esquemático) mais as peças que não têm símbolo (pinos, espaçadores, cabo).

> **Pendências antes de comprar (conferir quando as peças chegarem):**
> - Medidas reais dos slots e do módulo Si5351 (estimadas: `docs/decisoes.md` D17, D23).
> - Direção da etiqueta de cada slot (D27).

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `boards/16_bits/fab/dumper-v1.2-jlcpcb.zip` (cópia idêntica: `dumper-v1.2-gerbers-jlcpcb.zip`) |
| Camadas | 2 |
| Dimensões | 108,1 × 86,1 mm (largura acima de 100 mm: faixa de preço maior) |
| Espessura | 1,6 mm |
| Acabamento | HASL (com chumbo ou sem; sem chumbo é mais comum) |
| Quantidade | 5 |
| Cor / máscara | tanto faz (padrão verde) |
| Cobre | 1 oz |
| Furos | 343 metalizados (mín. 0,3 mm; 93 deles são vias), 4 não metalizados (3,2 mm, os de canto) |
| Demais | trilha/espaço mín. 0,2 mm / 0,2 mm; sem borda castelada; sem montagem; sem stencil |

## Componentes

| Ref. | Qtd | Valor | Footprint | Observação |
|---|---|---|---|---|
| A1 | 1 | Arduino Mega 2560 R3 (placa do usuário, USB-C) | `Mega2560_R3_Shield` | **Não vai na compra da placa.** Os pads do shield pedem pinos macho longos (abaixo). |
| SNES1 | 1 | Slot de cartucho SNES/SFC 62 pinos, passo 2,5 mm | `SNES_Slot` | Igual ao do OSCR. |
| MD1 | 1 | Slot de cartucho Mega Drive/Genesis 64 pinos, passo 2,54 mm | `MD_Slot` | Igual ao do OSCR. |
| U1 | 1 | Módulo Si5351 (CJMCU-5351, 25 MHz) | header fêmea 1x7 2,54 mm | Pinos: VIN, GND, SDA, SCL, 2, 1, 0. |
| U1 (header) | 1 | Header fêmea 1x7, 2,54 mm | `PinSocket_1x07_P2.54mm_Vertical` | |
| U2 | 1 | PIC12F629-I/P (DIP-8), gravado com `snescic-lock-resync.hex` | | Fora do soquete até o teste de tensão. |
| U2 (soquete) | 1 | Soquete DIP-8 tradicional (7,62 mm), de preferência de pino torneado | `DIP-8_W7.62mm` | **O PIC é removível:** vai sempre no soquete (troca, regravação e manutenção sem dessoldar). O footprint é o do CI; o soquete encaixa nos mesmos 8 furos. |
| D1 | 1 | LED 3 mm, qualquer cor | `LED_D3.0mm` | Ativo em nível baixo (cátodo no D38). |
| R1 | 1 | 220 Ω 1/4 W | `R_Axial_DIN0207...P10.16mm` | Resistor do LED. |
| R2 | 1 | 1 kΩ 1/4 W | idem | Pull-up do D7 (IRQ do SNES). |
| C1 | 1 | 470 µF / 16 V eletrolítico, radial, Ø8 mm, passo 3,5 mm | `CP_Radial_D8.0mm_P3.50mm` | Entrada de 5V. |
| C2, C3, C4, C5, C6 | 5 | 100 nF cerâmico, passo 5 mm | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | Um por slot (C2 SNES, C3 Mega Drive), um no PIC (C4) e, na v. 1.2, dois extras no slot Mega Drive: C5 junto ao pino A31 e C6 junto ao A2 (5V). |
| TP1 a TP6 | 6 | Pontos de teste: pad de 2 mm, furo de 1 mm (`TestPoint_THTPad_D2.0mm_Drill1.0mm`) | só cobre | Na placa, sem peça: `5V`, `GND`, `/CE`, `/OE`, `/WE`, `/UWR`. Opcional: tira de pinos macho 1x6 de 2,54 mm (os furos ficam a 2,54 mm um do outro). Fora da BOM de compra. |

## Pinos e mecânica (sem símbolo no esquemático)

| Item | Qtd | Observação |
|---|---|---|
| Pinos macho 2,54 mm, **cauda longa** (≥ 10 mm abaixo do plástico, ≥ 5 mm acima) | **85 posições** | Todos os pads do shield, inclusive os sem sinal. Sugestão: 2 tiras 1x40 e 1 tira 2x20 (corte em 2x18). |
| Espaçador M3 + pé de borracha | 4 | Furos de canto da placa; só apoio, não prendem o Mega. Comprimento a definir (o Mega fica sob o shield). |
| Cabo USB-C para USB-C (ou USB-A) | 1 | Interface com o PC (D30). |

## Ferramentas e consumíveis
Ver `boards/16_bits/docs/montagem.md`.
