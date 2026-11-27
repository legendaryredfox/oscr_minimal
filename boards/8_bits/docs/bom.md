# BOM — placa 8_bits (NES, Famicom e Master System) v1.1

Montagem **manual**. Lista gerada de `boards/8_bits/fab/bom-v1.1.csv` mais as peças sem símbolo (pinos e espaçadores).

> **Pendências antes de comprar:** medidas reais dos slots e do módulo Si5351 (D17, D23); direção da etiqueta (D27).

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `boards/8_bits/fab/dumper-v1.1-jlcpcb.zip` |
| Camadas | 2 |
| Dimensões | 117,1 × 109,1 mm na v1.1 e 117,1 × 97,1 mm na v1.0 (acima de 100 mm: faixa de preço maior) |
| Espessura / acabamento | 1,6 mm, HASL |
| Quantidade | 5 |
| Furos | metalizados (inclui as vias de costura do GND) e 4 não metalizados de 3,2 mm (cantos) |
| Demais | trilha/espaço mín. 0,2 mm; sem montagem; sem stencil |

## Componentes

| Ref. | Qtd | Valor | Footprint | Observação |
|---|---|---|---|---|
| A1 | 1 | Arduino Mega 2560 R3 (do usuário, USB-C) | `Mega2560_R3_Shield` | Não vai na compra da placa. |
| NES1 | 1 | Slot de cartucho NES 72 pinos, passo 2,5 mm | `NES_Slot` | Igual ao do OSCR. |
| FC1 | 1 | Slot de cartucho Famicom 60 pinos, passo 2,54 mm | `FC_Slot` | Igual ao do OSCR. |
| SMS1 | 1 | Slot de cartucho Master System 50 pinos (2 × 25), passo 2,54 mm | `SMS_Slot` | Igual ao do OSCR (wiki de peças: "50 pin 2.54mm Master System slot"). **Medir o slot recebido.** |
| U1 | 1 | Módulo Si5351 (CJMCU-5351, 25 MHz) + header fêmea 1x7 | `PinSocket_1x07_P2.54mm_Vertical` | Pinos: VIN, GND, SDA, SCL, 2, 1, 0. Só o CLK0 (pino 0) vai ao slot NES. Soquete na vertical. |
| D1 | 1 | LED 3 mm | `LED_D3.0mm` | Ativo em nível baixo (cátodo em D38). |
| R1 | 1 | 220 Ω 1/4 W | `R_Axial_DIN0207...P10.16mm` | Resistor do LED. |
| C1 | 1 | 470 µF / 16 V, radial Ø8 mm, passo 3,5 mm | `CP_Radial_D8.0mm_P3.50mm` | Entrada de 5V. |
| C2, C3, C4 | 3 | 100 nF cerâmico, passo 5 mm | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | C2 no NES (pino 36), C3 no Famicom (pinos 30 e 31), C4 no SMS (pinos 1 e 35). Na v1.1, C5 e C6 são os do LDO (abaixo). |

Sem PIC, R2, regulador nem pontos de teste.

## Pinos e mecânica

| Item | Qtd | Observação |
|---|---|---|
| Pinos macho 2,54 mm, **cauda longa** (≥ 10 mm abaixo, ≥ 5 mm acima) | **85 posições** | Todos os pads do shield, inclusive os sem sinal (2 tiras 1x40 e 1 tira 2x20, corte em 2x18). |
| Espaçador M3 + pé de borracha | 4 (cantos) | Só apoio. A placa não tem furos de fixação no Mega: ela fica presa pelos pinos dos headers e pelos pés (a força de inserir o cartucho passa pelos pinos). |
| Cabo USB-C | 1 | Interface com o PC. |

## F1, J1 e seletor de tensão (D138)

**F1 (v1.0 e v1.1):** suporte de clipes para fusível 5×20 mm (Littelfuse série 100, 2 clipes) e fusível de vidro 5×20 mm de 500 mA, ação rápida (compre reservas). Em série com o 5 V que a placa recebe do Mega. **Sem o fusível no suporte, a placa fica sem 5 V** (um fio no lugar dele também serve).

**Só na v1.1 (seletor 3,3 V/5 V nos três slots; D138, D147):**

| Ref. | Peça | Qtd | Observação |
|---|---|---|---|
| U2 | LD1117V33 (TO-220) | 1 | LDO de 3,3 V |
| Q1 | IRF9540N (P-MOSFET, TO-220) | 1 | bypass do LDO: 5 V |
| Q2 | 2N7000 (TO-92) | 1 | comando pelo D18 |
| R2, R3, R4 | 100 kΩ, 1 kΩ e 220 Ω, axiais 1/4 W | 3 | |
| C5, C6 | 100 nF cerâmico e 10 µF/16 V eletrolítico | 2 | entrada e saída do LDO |
| J1 | cabeçalho de 2 pinos de 2,54 mm e um jumper ("TRAVA 3,3 V") | 1 | |

Preço aproximado das peças extras da v1.1: menos de US$ 3 por placa (estimativa de varejo, não cotada). Os três slots (NES, Famicom e SMS) ficam no VCC do seletor; Si5351 e o resto, sempre em 5 V.

## Componentes que podem ser retirados e o que se perde

Placa NES + Famicom + Master System (`boards/8_bits/`). Tem Si5351 (só o NES usa); sem PIC, R2 nem regulador de 3,3 V (o LDO da v1.1 é do seletor).

> **Nada aqui foi testado em hardware.** Conclusões vêm de `pinmap.md` e do firmware (`NES.cpp` não chama o Si5351).

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U1** módulo Si5351 + header | Sim, sem perda conhecida | O `CLK0` só vai ao pino 37 do NES; o firmware atual não o usa. O Famicom não tem pino de clock | Nenhum conhecido |
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade | Nenhum |
| **C2**, **C3**, **C4** 100 nF (VCC do NES, do Famicom e do SMS) | Não recomendado | Desacoplamento de cada slot | Mappers que consomem mais e os com bateria. Inferência |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |

Um cartucho por vez (os três slots dividem os mesmos barramentos). Sem o Si5351, a placa lê Famicom e Master System e só os mappers do NES que não usam o clock.

#### F1, J1 e seletor de tensão (D138)

<!-- d138 -->

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| F1 (suporte e fusível 5×20 mm, 500 mA) | **Sim**, mas sem o fusível no suporte a placa não tem 5 V (um fio no lugar dele também serve) | só a proteção contra curto no cartucho (placa, Mega e USB) |
| J1 (jumper TRAVA 3,3 V) | **Sim** | a defesa independente do firmware contra o 5 V num cartucho de 3,3 V; deixe aberto para usar o seletor |
| U2 (LDO), Q1, Q2, R2 a R4, C5 e C6 | Não, se quiser 3,3 V | sem eles o slot fica só em 5 V; o seletor é a tensão padrão (5 V) com o Q1 |

> **Tensão do cartucho (D140):** a placa não tem resistores em série entre o Mega e os slots (as redes RN saíram em D140). Mesmo com o seletor em 3,3 V, as saídas do Mega continuam em 5 V; o seletor só baixa o VCC do cartucho. **Confira a tensão que o cartucho suporta antes de inserir**: um cartucho só de 3,3 V pode ser danificado.

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 e v1.1 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.
