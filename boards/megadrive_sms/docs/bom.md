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

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

Peças opcionais a comprar a mais por placa:

| Ref. | Peça | Qtd | Onde |
|---|---|---|---|
| F1 | suporte de clipes para fusível 5×20 mm (Littelfuse série 100, 2 clipes) e fusível de vidro 5×20 mm de 500 mA, ação rápida | 1 + 1 (compre fusíveis de reserva) | todas as versões (v1.0 e v1.1) |
| J1 | cabeçalho de 2 pinos de 2,54 mm e um jumper ("TRAVA 3,3 V") | 1 | v1.1 |
| LDO | LD1117V33 (TO-220) | 1 | v1.1 |
| Q1 | IRF9540N (P-MOSFET, TO-220) | 1 | v1.1 |
| Q2 | 2N7000 (TO-92) | 1 | v1.1 |
| C (2) | 100 nF cerâmico e 10 µF/16 V eletrolítico (entrada e saída do LDO) | 2 | v1.1 |
| R (3) | 100 kΩ, 1 kΩ e 220 Ω, axiais 1/4 W | 3 | v1.1 |

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 e v1.1 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.

Seletor 3,3 V/5 V nos slots Mega Drive, Master System (resto da placa sempre em 5 V). Preço aproximado das peças extras: menos de US$ 3 por placa (estimativa de varejo, não cotada).

## Componentes que podem ser retirados e o que se perde

Placa Mega Drive + Master System (`boards/megadrive_sms/`): dois slots, LED e capacitores. Não tem Si5351, PIC, regulador de 3,3 V, R2 nem bloco de troca de cartucho.

> **Nada aqui foi testado em hardware.** Conclusões vêm de `pinmap.md` e do firmware (`firmware/oscr/src/cores/MegaDrive.cpp`; o núcleo `SMS.cpp` do OSCR não usa clock e está ligado no fork desde a D137).

| Peça | Retirar? | O que deixa de funcionar | Cartuchos afetados |
|---|---|---|---|
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade (D38) | Nenhum |
| **TP1 a TP6** pontos de teste | Sim | Só o acesso para medir `/UWR`, `/CE`, `5V`, `GND`, `/OE`, `/WE` | Nenhum |
| **C2, C3, C4** 100 nF (slot Mega Drive) | Não recomendado | Desacoplamento do cartucho; sem eles, ruído pode dar leitura errada | Mais provável nos de ROM grande |
| **C5** 100 nF (slot SMS) | Não recomendado | Desacoplamento do cartucho de Master System | Todos os do SMS |
| **C1** 470 µF | Não recomendado | Reserva de carga do 5 V; sem ela, picos podem reiniciar o Mega | Todos |

Não há chip opcional. O pino 47 (Clock) do slot SMS fica sem ligação (D136); se algum cartucho exigir o clock do console, só um adaptador com o sinal resolve.

#### F1, J1 e seletor de tensão (D138)

<!-- d138 -->

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| F1 (suporte e fusível 5×20 mm, 500 mA) | **Sim**, mas sem o fusível no suporte a placa não tem 5 V (um fio no lugar dele também serve) | só a proteção contra curto no cartucho (placa, Mega e USB) |
| J1 (jumper TRAVA 3,3 V) | **Sim** | a defesa independente do firmware contra o 5 V num cartucho de 3,3 V; deixe aberto para usar o seletor |
| LDO, Q1, Q2, C do LDO | Não, se quiser 3,3 V | sem eles o slot fica só em 5 V; o seletor é a tensão padrão (5 V) com o Q1 |

> **Tensão do cartucho (D140):** a placa não tem resistores em série entre o Mega e os slots (as redes RN saíram em D140). Mesmo com o seletor em 3,3 V, as saídas do Mega continuam em 5 V; o seletor só baixa o VCC do cartucho. **Confira a tensão que o cartucho suporta antes de inserir**: um cartucho só de 3,3 V pode ser danificado.

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 e v1.1 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.
