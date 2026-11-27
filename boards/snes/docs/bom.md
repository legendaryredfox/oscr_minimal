# BOM — placa snes (só SNES) v1.0

Montagem **manual**. Lista gerada de `boards/snes/fab/bom-v1.0.csv` mais as peças sem símbolo (pinos e espaçadores).

> **Pendências antes de comprar:** medidas reais do slot SNES e do módulo Si5351 (D17, D23); direção da etiqueta (D27).

## Placa (JLCPCB)

| Item | Valor |
|---|---|
| Arquivo | `boards/snes/fab/dumper-v1.0-jlcpcb.zip` |
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
| SNES1 | 1 | Slot de cartucho SNES/SFC 62 pinos, passo 2,5 mm | `SNES_Slot` | Igual ao do OSCR. |
| U1 | 1 | Módulo Si5351 (CJMCU-5351, 25 MHz) + header fêmea 1x7 | `PinSocket_1x07_P2.54mm_Vertical` | Pinos: VIN, GND, SDA, SCL, 2, 1, 0. |
| U2 | 1 | PIC12F629-I/P (DIP-8) gravado com `snescic-lock-resync.hex` + soquete DIP-8 tradicional | `DIP-8_W7.62mm` | Sempre no soquete; fora dele até o teste de tensão. |
| D1 | 1 | LED 3 mm | `LED_D3.0mm` | Ativo em nível baixo (cátodo em D38). |
| R1 | 1 | 220 Ω 1/4 W | `R_Axial_DIN0207...P10.16mm` | Resistor do LED. |
| R2 | 1 | 1 kΩ 1/4 W | idem | Pull-up do D7 (`/IRQ` do SNES). |
| C1 | 1 | 470 µF / 16 V, radial Ø8 mm, passo 3,5 mm | `CP_Radial_D8.0mm_P3.50mm` | Entrada de 5V. |
| C2, C3 | 2 | 100 nF cerâmico, passo 5 mm | `C_Disc_D5.0mm_W2.5mm_P5.00mm` | C2 no slot (pino 27), C3 no PIC. |
| TP1, TP2, TP3, TP4, TP5 | 5 | Pontos de teste, pad de 2 mm, furo 1 mm | só cobre | `5V`, `GND`, `/RD`, `/WR`, `/IRQ`. Opcional: tira de pinos macho 1x5 de 2,54 mm (furos a 2,54 mm um do outro). |

## Pinos e mecânica

| Item | Qtd | Observação |
|---|---|---|
| Pinos macho 2,54 mm, **cauda longa** (≥ 10 mm abaixo, ≥ 5 mm acima) | **85 posições** | Todos os pads do shield, inclusive os sem sinal (2 tiras 1x40 e 1 tira 2x20, corte em 2x18). |
| Espaçador M3 + pé de borracha | 4 | Furos de canto; só apoio. |
| Cabo USB-C | 1 | Interface com o PC. |

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

Peças opcionais a comprar a mais por placa:

| Ref. | Peça | Qtd | Onde |
|---|---|---|---|
| F1 | suporte de clipes para fusível 5×20 mm (Littelfuse série 100, 2 clipes) e fusível de vidro 5×20 mm de 500 mA, ação rápida | 1 + 1 (compre fusíveis de reserva) | todas as versões (v1.0) |

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.

## Componentes que podem ser retirados e o que se perde

Placa só SNES/Super Famicom (`boards/snes/`). Esta tabela diz o que acontece se uma peça **não for montada** ou for retirada depois. Vale para quem quer montar uma versão mais barata ou simples.

> **Nada aqui foi testado em hardware.** A coluna "o que se perde" vem da leitura do firmware (`firmware/oscr/src/cores/SNES.cpp`), de `docs/decisoes.md` (D54, D55) e de `pinmap.md`. Onde a conclusão é inferência, está dito.

#### Resumo

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U2** PIC12F629 (CIC) + soquete | **Perde o SA-1** | O PIC emula o CIC do console; o SA-1 só responde com o CIC rodando (D54). O resto da leitura segue | Só cartuchos **SA-1** (lista abaixo). LoROM, HiROM, ExHiROM, SuperFX, S-DD1, SPC7110 e Cx4 não dependem dele |
| **U1** módulo Si5351 | **Perde o SA-1** e o PIC fica sem clock | Sai o clock mestre (pino 1, 21,477 MHz), o do CPU (pino 57) e o do CIC (pino 56). O PIC recebe o CLK2 do Si5351: sem módulo, o PIC também não roda, mesmo montado | Os mesmos SA-1. Futuros: **Satellaview (BS-X)** e **SF Memory Cassette**, que o OSCR lê com o clock mestre (ainda não portados, `docs/referencia/funcoes-oscr.md`). Os demais cartuchos comuns não dependem |
| **R2** 1 kΩ (pull-up do `/IRQ`, D7) | Sim, sem perda conhecida | A linha `/IRQ` (pino 18 do slot) fica solta. O firmware atual só configura o pino como entrada na abertura e não o lê depois | Nenhum conhecido. Inferência: o OSCR HW5 tem o resistor; não achei uso dele nos cores ligados |
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade (D38) | Nenhum |
| **TP1 a TP5** pontos de teste | Sim | Só o acesso para medir `5V`, `GND`, `/RD`, `/WR`, `/IRQ` | Nenhum |
| **C2** 100 nF (VCC do slot) | Não recomendado | Desacoplamento do cartucho. Sem ele, ruído de alimentação pode dar leitura errada (CRC diferente a cada tentativa) | Pior nos que puxam mais corrente: SA-1, SuperFX. Inferência; não medido |
| **C3** 100 nF (PIC) | Não recomendado | Desacoplamento do PIC. Sem ele o CIC pode travar ou reiniciar | Só SA-1 |
| **C1** 470 µF | Não recomendado | Reserva de carga na entrada de 5 V; sem ela, picos do cartucho derrubam o 5 V do Mega e podem reiniciá-lo | Todos, na pior hora (início da leitura) |
| **SNES1**, pinos macho longos, A1 | Não | Sem eles não há placa | — |

#### Cartuchos SA-1 (afetados por U1 ou U2 ausentes)

Lista de jogos que usam o chip SA-1, para conferir antes de montar sem o PIC ou sem o Si5351. **Não é exaustiva** (vem da memória, não de uma lista do OSCR): Super Mario RPG, Kirby Super Star (Kirby's Fun Pak), Kirby's Dream Land 3, Jikkyou Oshaberi Parodius, Dragon Ball Z: Hyper Dimension, SD Gundam G NEXT, Marvelous: Another Treasure Island, Masters New: Harukanaru Augusta 3, Pebble Beach no Hotou, PGA Tour 96, PGA European Tour, Power Rangers Zeo: Battle Racers, Itoi Shigesato no Bass Tsuri No. 1, J.League '96 Dream Stadium, Daisenryaku Expert WWII e outros jogos de shogi. O byte de chips do cabeçalho (`$34` ou `$35`, mapa `$23`) mostra se é SA-1.

#### Combinações práticas

| Montagem | Lê | Não lê |
|---|---|---|
| Completa (U1 + U2) | Tudo que o firmware suporta, inclusive SA-1 | — |
| Sem PIC, com Si5351 | LoROM, HiROM, ExHiROM, SuperFX, S-DD1, SPC7110, Cx4 | SA-1 |
| Sem Si5351, sem PIC | os mesmos | SA-1 e, quando portados, Satellaview e SF Memory |
| Sem Si5351, com PIC | os mesmos | SA-1 (o PIC não tem clock) |

Dá para montar o soquete do PIC e do Si5351 vazios e completar depois: ambos são removíveis.

#### Limites que não dependem de peça

Chips especiais que o dumper ainda recusa (S-RTC, OBC1, ST018, MSU-1, RTC do SPC7110) valem para qualquer montagem: `docs/decisoes.md` D55.

#### F1, J1 e seletor de tensão (D138)

<!-- d138 -->

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| F1 (suporte e fusível 5×20 mm, 500 mA) | **Sim**, mas sem o fusível no suporte a placa não tem 5 V (um fio no lugar dele também serve) | só a proteção contra curto no cartucho (placa, Mega e USB) |

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.
