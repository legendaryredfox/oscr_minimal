# BOM — placa completa (SNES, NES, Famicom, Mega Drive, Master System, N64 e GBA) v1.1

Montagem **manual** (sem montagem pela JLCPCB). Esta lista vem de `boards/completa/fab/bom-v1.1.csv` (gerado do esquemático) mais as peças que não têm símbolo (pinos, espaçadores, cabo).

> **Pendências antes de comprar (conferir quando as peças chegarem):**
> - Medidas reais dos slots e do módulo Si5351 (estimadas: `docs/decisoes.md` D17, D23).
> - Direção da etiqueta de cada slot (D27) e do GBA (D28).
> - Footprint do slot GBA é o do OSCR (SMD). Conferir se o slot comprado tem os mesmos 32 pads de 1,5 mm e os 2 furos-guia de 2,2 mm.

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `boards/completa/fab/dumper-v1.1-jlcpcb.zip` (v1.1) ou `dumper-v1.0-jlcpcb.zip` (v1.0) |
| Camadas | 2 |
| Dimensões | v1.0: 144,1 × 152,1 mm; v1.1: 144,1 × 168,1 mm (acima de 100 × 100 mm: faixa de preço maior) |
| Espessura | 1,6 mm |
| Acabamento | HASL (com chumbo ou sem; sem chumbo é mais comum) |
| Quantidade | 5 |
| Cor / máscara | tanto faz (padrão verde) |
| Cobre | 1 oz |
| Furos | metalizados (inclui as vias de costura do GND) e não metalizados de 3,2 mm (4 de canto) e os do Mega |
| Demais | trilha/espaço mín. 0,2 mm / 0,2 mm; sem borda castelada; sem montagem; sem stencil |

## Componentes

| Ref. | Qtd | Valor | Footprint | Observação |
|---|---|---|---|---|
| A1 | 1 | Arduino Mega 2560 R3 (placa do usuário, USB-C) | `Mega2560_R3_Shield` | **Não vai na compra da placa.** Os pads do shield pedem pinos macho longos (abaixo). |
| SNES1 | 1 | Slot de cartucho SNES/SFC 62 pinos, passo 2,5 mm | `SNES_Slot` | Igual ao do OSCR. |
| NES1 | 1 | Slot de cartucho NES 72 pinos, passo 2,5 mm | `NES_Slot` | Igual ao do OSCR. |
| FC1 | 1 | Slot de cartucho Famicom 60 pinos, passo 2,54 mm | `FC_Slot` | Igual ao do OSCR. |
| MD1 | 1 | Slot de cartucho Mega Drive/Genesis 64 pinos, passo 2,54 mm | `MD_Slot` | Igual ao do OSCR. |
| N64_1 | 1 | Slot de cartucho N64, 50 pinos, passo 2,5 mm, duas fileiras de 25 | `N64_Slot` | Footprint do OSCR. **3,3 V** (do U3). Medir o slot recebido. |
| SMS1 | 1 | Slot de cartucho Master System 50 pinos (2 × 25), passo 2,54 mm | `SMS_Slot` | Igual ao do OSCR (wiki de peças). **Medir o slot recebido.** |
| GBA1 | 1 | Slot de cartucho GBA 32 pinos, passo 1,5 mm | `GBA_Slot` | **SMD**, única peça SMD. 3,3 V apenas. |
| U1 | 1 | Módulo Si5351 (CJMCU-5351, 25 MHz) | header fêmea 1x7 2,54 mm | Pinos: VIN, GND, SDA, SCL, 2, 1, 0. |
| U1 (header) | 1 | Header fêmea 1x7, 2,54 mm | `PinSocket_1x07_P2.54mm_Vertical` | |
| U2 | 1 | PIC12F629-I/P (DIP-8), gravado com `snescic-lock-resync.hex` | | Fora do soquete até o teste de tensão. |
| U2 (soquete) | 1 | Soquete DIP-8 (7,62 mm) | `DIP-8_W7.62mm_Socket` | |
| U3 | 1 | MCP1700-3302E/TO (3,3 V, 250 mA, TO-92) | `TO-92` | Para os slots GBA e N64 (um cartucho por vez). Corrente do N64 não conferida. |
| D1 | 1 | LED 3 mm, qualquer cor | `LED_D3.0mm` | Ativo em nível baixo (cátodo no D38). |
| R1 | 1 | 220 Ω 1/4 W | `R_Axial_DIN0207...P10.16mm` | Resistor do LED. |
| R2 | 1 | 1 kΩ 1/4 W | idem | Pull-up do D7 (IRQ do SNES e EEPROM_DATA do N64), **para 5 V**. |
| C1 | 1 | 470 µF / 16 V eletrolítico, radial, Ø8 mm, passo 3,5 mm | `CP_Radial_D8.0mm_P3.50mm` | Entrada de 5V. |
| C2 a C6, C9 a C11 | 8 | 100 nF cerâmico, passo 5 mm | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | Um por slot (C2 SNES, C3 NES, C4 Famicom, C5 Mega Drive, C10 SMS, C11 N64), PIC (C6) e GBA (C9). |
| C7, C8 | 2 | 1 µF cerâmico multicamada X7R, passo 5 mm | idem | Entrada/saída do U3. Precisa ser 1 µF ou mais, cerâmico ou tântalo. |

## Pinos e mecânica (sem símbolo no esquemático)

| Item | Qtd | Observação |
|---|---|---|
| Pinos macho 2,54 mm, **cauda longa** (≥ 10 mm abaixo do plástico, ≥ 5 mm acima) | **85 posições** | Todos os pads do shield, inclusive os sem sinal. Sugestão: 2 tiras 1x40 e 1 tira 2x20 (corte em 2x18). |
| Espaçador M3 + pé de borracha | 4 | Furos de canto da placa. Comprimento a definir: o Mega fica sob o shield. A placa não tem furos de fixação no Mega: fica presa pelos pinos dos headers e pelos pés. |
| Cabo USB-C para USB-C (ou USB-A) | 1 | Interface com o PC (D30). |

## Ferramentas e consumíveis
Ver `boards/completa/docs/montagem.md`.

## F1, J1 e seletor de tensão (D138)

**F1 (v1.0 e v1.1):** suporte de clipes para fusível 5×20 mm (Littelfuse série 100, 2 clipes) e fusível de vidro 5×20 mm de 500 mA, ação rápida (compre reservas). Em série com o 5 V que a placa recebe do Mega. **Sem o fusível no suporte, a placa fica sem 5 V** (um fio no lugar dele também serve).

**Só na v1.1 (seletor 3,3 V/5 V nos slots NES, Famicom, Mega Drive e SMS; D138, D147):**

| Ref. | Peça | Qtd | Observação |
|---|---|---|---|
| U4 | LD1117V33 (TO-220) | 1 | LDO de 3,3 V |
| Q1 | IRF9540N (P-MOSFET, TO-220) | 1 | bypass do LDO: 5 V |
| Q2 | 2N7000 (TO-92) | 1 | comando pelo D18 |
| R3, R4, R5 | 100 kΩ, 1 kΩ e 220 Ω, axiais 1/4 W | 3 | |
| C12, C13 | 100 nF cerâmico e 10 µF/16 V eletrolítico | 2 | entrada e saída do LDO |
| J1 | cabeçalho de 2 pinos de 2,54 mm e um jumper ("TRAVA 3,3 V") | 1 | |

O **SNES fica sempre em 5 V** (o SA-1 não funciona a 3,3 V), assim como o PIC e o Si5351; o GBA tem o seu próprio regulador (U3). Preço aproximado das peças extras da v1.1: menos de US$ 3 por placa (estimativa de varejo, não cotada).

## Componentes que podem ser retirados e o que se perde

Placa de 7 slots: SNES, NES, Famicom, Mega Drive, Master System, N64 e GBA (`boards/completa/`). Um cartucho por vez.

> **Nada aqui foi testado em hardware.** Fontes: a lista acima, `pinmap.md`, firmware, D54 e `docs/referencia/limites.md`.

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U2** PIC12F629 (CIC) + soquete | **Perde o SA-1** | O PIC emula o CIC do SNES; o SA-1 só responde com ele rodando | Só **SA-1** (Super Mario RPG, Kirby Super Star, Kirby's Dream Land 3, Jikkyou Oshaberi Parodius, Dragon Ball Z: Hyper Dimension e outros; lista não exaustiva em `snes/docs/bom.md`). NES, Famicom, Mega Drive, Master System e GBA não usam |
| **U1** módulo Si5351 | **Não**: parte fixa da placa (D231) | SNES: clock mestre (pino 1), CPU (57) e CIC (56). NES: o `CLK0` vai ao pino 37, mas o firmware atual não o usa | SA-1; futuros Satellaview e SF Memory. NES: nenhum conhecido |
| **R2** 1 kΩ (pull-up de D7, `/IRQ` do SNES) | Sim, com cuidado | `/IRQ` solta. D7 também é o `/UWR` do Mega Drive (pino B29); o pull-up estava no HW5 | Nenhum conhecido. Inferência |
| **U3** MCP1700-3302E + **C7**, **C8** (1 µF) + **C9**, **C11** | **Perde o GBA, o GB, o GBC e o N64** | Os slots GBA e N64 só têm 3,3 V, vindo do U3. Sem ele, sem energia nos slots. Nunca ligar o GBA ou o N64 ao 5 V | Todos os GBA, GB e GBC. SNES, NES, Famicom, Mega Drive e Master System não dependem |
| **D1** LED + **R1** 220 Ω | Sim | Indicação de atividade | Nenhum |
| **C2** SNES, **C3** NES, **C4** Famicom, **C5** Mega Drive, **C10** Master System, **C9** GBA, **C11** N64, **C6** PIC (100 nF) | Não recomendado | Desacoplamento do slot ou do PIC. Sem eles, leitura errada possível (CRC variável) | Mais provável: SA-1, ROM grande (SSF2), GBA com Flash. Inferência |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |

#### Montagens parciais

Como os slots dividem os mesmos barramentos, pode-se montar só os slots que o usuário vai usar; os demais ficam vazios sem prejuízo, **menos** o desacoplamento de cada slot (montar o capacitor do slot usado). Sem PIC e sem Si5351 a placa lê tudo menos SA-1. Sem U3 e seus capacitores perde-se tudo do GBA (inclusive GB/GBC por adaptador) e do N64, mas os slots podem continuar vazios.

Sobre GB/GBC a 3,3 V: ver `docs/referencia/limites.md` (alguns GB antigos podem falhar; jumper para 5 V só para GB/GBC, nunca GBA).

#### F1, J1 e seletor de tensão (D138)

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| F1 (suporte e fusível 5×20 mm, 500 mA) | **Sim**, mas sem o fusível no suporte a placa não tem 5 V (um fio no lugar dele também serve) | só a proteção contra curto no cartucho (placa, Mega e USB) |
| J1 (jumper TRAVA 3,3 V), v1.1 | **Sim** | a defesa independente do firmware contra o 5 V num cartucho de 3,3 V; deixe aberto para usar o seletor |
| U4 (LDO), Q1, Q2, R3 a R5, C11 e C12, v1.1 | Não, se quiser 3,3 V | sem eles os slots NES, Famicom, Mega Drive e SMS ficam só em 5 V (com o Q1 no lugar). Se o seletor não for montado, ligue os pads de dreno e fonte do Q1 com um fio |

> **Tensão do cartucho (D140):** a placa não tem resistores em série entre o Mega e os slots. Mesmo com o seletor em 3,3 V, as saídas do Mega continuam em 5 V; o seletor só baixa o VCC do cartucho. **Confira a tensão que o cartucho suporta antes de inserir.** O SNES nunca recebe 3,3 V.

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.
