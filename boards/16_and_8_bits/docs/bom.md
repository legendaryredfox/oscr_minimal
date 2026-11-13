# BOM — oscr_minimal (16_and_8_bits) v1.0 e v1.1

Montagem **manual** (sem montagem pela JLCPCB). Esta lista vem de `boards/16_and_8_bits/fab/bom-v1.0.csv` ou `bom-v1.1.csv` (gerados do esquemático) mais as peças que não têm símbolo (pinos, espaçadores, cabo).

> **Pendências antes de comprar (conferir quando as peças chegarem):**
> - Medidas reais dos slots e do módulo Si5351 (estimadas: `docs/decisoes.md` D17, D23).
> - Direção da etiqueta de cada slot (D27) e do GBA (D28).
> - Footprint do slot GBA é o do OSCR (SMD). Conferir se o slot comprado tem os mesmos 32 pads de 1,5 mm e os 2 furos-guia de 2,2 mm.

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `boards/16_and_8_bits/fab/dumper-v1.1-jlcpcb.zip` (v1.1) ou `dumper-v1.0-jlcpcb.zip` (v1.0, mínima) |
| Camadas | 2 |
| Dimensões | v1.0: 144,05 × 118,05 mm; v1.1: 144,05 × 134,05 mm (acima de 100 × 100 mm: preço maior) |
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
| Espaçador M2 (nylon ou metal) + parafuso M2 | 2 | Para os 2 furos de 2,2 mm ao lado do módulo Si5351 (MH5, MH6, 20 mm entre eles). Altura = a do header fêmea (~8,5 mm). Posição estimada: conferir com os furos do módulo. |
| Cabo USB-C para USB-C (ou USB-A) | 1 | Interface com o PC (D30). |

## Ferramentas e consumíveis
Ver `boards/16_and_8_bits/docs/montagem.md`.

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

Peças opcionais a comprar a mais por placa:

| Ref. | Peça | Qtd | Onde |
|---|---|---|---|
| F1 | suporte de clipes para fusível 5×20 mm (Littelfuse série 100, 2 clipes) e fusível de vidro 5×20 mm de 500 mA, ação rápida | 1 + 1 (compre fusíveis de reserva) | todas as versões (v1.0) |

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.

**Só na v1.1 (seletor 3,3 V/5 V nos slots NES, Famicom e Mega Drive; D138, D147):**

| Ref. | Peça | Qtd | Observação |
|---|---|---|---|
| U4 | LD1117V33 (TO-220) | 1 | LDO de 3,3 V |
| Q1 | IRF9540N (P-MOSFET, TO-220) | 1 | bypass do LDO: 5 V |
| Q2 | 2N7000 (TO-92) | 1 | comando pelo D18 |
| R3, R4, R5 | 100 kΩ, 1 kΩ e 220 Ω, axiais 1/4 W | 3 | |
| C10, C11 | 100 nF cerâmico e 10 µF/16 V eletrolítico | 2 | entrada e saída do LDO |
| J1 | cabeçalho de 2 pinos de 2,54 mm e um jumper ("TRAVA 3,3 V") | 1 | |

O **SNES fica sempre em 5 V** (o SA-1 não funciona a 3,3 V), assim como o PIC e o Si5351; o GBA tem o seu próprio regulador (U3). Preço aproximado das peças extras da v1.1: menos de US$ 3 por placa (estimativa de varejo, não cotada).
