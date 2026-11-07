# snes — componentes que podem ser retirados e o que se perde

Placa só SNES/Super Famicom (`boards/snes/`). Esta tabela diz o que acontece se uma peça **não for montada** ou for retirada depois. Vale para quem quer montar uma versão mais barata ou simples.

> **Nada aqui foi testado em hardware.** A coluna "o que se perde" vem da leitura do firmware (`firmware/oscr/src/cores/SNES.cpp`), de `docs/decisoes.md` (D54, D55) e de `pinmap.md`. Onde a conclusão é inferência, está dito.

## Resumo

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U2** PIC12F629 (CIC) + soquete | **Perde o SA-1** | O PIC emula o CIC do console; o SA-1 só responde com o CIC rodando (D54). O resto da leitura segue | Só cartuchos **SA-1** (lista abaixo). LoROM, HiROM, ExHiROM, SuperFX, S-DD1, SPC7110 e Cx4 não dependem dele |
| **U1** módulo Si5351 | **Perde o SA-1** e o PIC fica sem clock | Sai o clock mestre (pino 1, 21,477 MHz), o do CPU (pino 57) e o do CIC (pino 56). O PIC recebe o CLK2 do Si5351: sem módulo, o PIC também não roda, mesmo montado | Os mesmos SA-1. Futuros: **Satellaview (BS-X)** e **SF Memory Cassette**, que o OSCR lê com o clock mestre (ainda não portados, `docs/funcoes-oscr.md`). Os demais cartuchos comuns não dependem |
| **R2** 1 kΩ (pull-up do `/IRQ`, D7) | Sim, sem perda conhecida | A linha `/IRQ` (pino 18 do slot) fica solta. O firmware atual só configura o pino como entrada na abertura e não o lê depois | Nenhum conhecido. Inferência: o OSCR HW5 tem o resistor; não achei uso dele nos cores ligados |
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade (D38) | Nenhum |
| **TP1 a TP5** pontos de teste | Sim | Só o acesso para medir `5V`, `GND`, `/RD`, `/WR`, `/IRQ` | Nenhum |
| **C2** 100 nF (VCC do slot) | Não recomendado | Desacoplamento do cartucho. Sem ele, ruído de alimentação pode dar leitura errada (CRC diferente a cada tentativa) | Pior nos que puxam mais corrente: SA-1, SuperFX. Inferência; não medido |
| **C3** 100 nF (PIC) | Não recomendado | Desacoplamento do PIC. Sem ele o CIC pode travar ou reiniciar | Só SA-1 |
| **C1** 470 µF | Não recomendado | Reserva de carga na entrada de 5 V; sem ela, picos do cartucho derrubam o 5 V do Mega e podem reiniciá-lo | Todos, na pior hora (início da leitura) |
| **SNES1**, pinos macho longos, A1 | Não | Sem eles não há placa | — |

## Cartuchos SA-1 (afetados por U1 ou U2 ausentes)

Lista de jogos que usam o chip SA-1, para conferir antes de montar sem o PIC ou sem o Si5351. **Não é exaustiva** (vem da memória, não de uma lista do OSCR): Super Mario RPG, Kirby Super Star (Kirby's Fun Pak), Kirby's Dream Land 3, Jikkyou Oshaberi Parodius, Dragon Ball Z: Hyper Dimension, SD Gundam G NEXT, Marvelous: Another Treasure Island, Masters New: Harukanaru Augusta 3, Pebble Beach no Hotou, PGA Tour 96, PGA European Tour, Power Rangers Zeo: Battle Racers, Itoi Shigesato no Bass Tsuri No. 1, J.League '96 Dream Stadium, Daisenryaku Expert WWII e outros jogos de shogi. O byte de chips do cabeçalho (`$34` ou `$35`, mapa `$23`) mostra se é SA-1.

## Combinações práticas

| Montagem | Lê | Não lê |
|---|---|---|
| Completa (U1 + U2) | Tudo que o firmware suporta, inclusive SA-1 | — |
| Sem PIC, com Si5351 | LoROM, HiROM, ExHiROM, SuperFX, S-DD1, SPC7110, Cx4 | SA-1 |
| Sem Si5351, sem PIC | os mesmos | SA-1 e, quando portados, Satellaview e SF Memory |
| Sem Si5351, com PIC | os mesmos | SA-1 (o PIC não tem clock) |

Dá para montar o soquete do PIC e do Si5351 vazios e completar depois: ambos são removíveis.

## Limites que não dependem de peça

Chips especiais que o dumper ainda recusa (S-RTC, OBC1, ST018, MSU-1, RTC do SPC7110) valem para qualquer montagem: `docs/decisoes.md` D55.

## Bloco de troca de cartucho (v1.1)

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| Q1, R3, R4 | **Não** (sem o Q1 o 5V dos slots não chega: pôr uma ponte do 5V ao `+5V_CART` se quiser abrir mão do `POWER`) | `POWER on/off` em software; a troca segura do cartucho |
| R5, D2 (LED verde) | Sim | só a indicação visual de 5V dos slots |
| Q2, R6 | Sim | descarga rápida do rail: o firmware espera 2 s em vez de 500 ms |
| Q3, R7, R8, R9, D3 (sensor e LED amarelo) | Sim | o LED amarelo e a leitura do D53 (`POWER_RESP.rail` fica `0xFF`) |

Nenhuma peça do bloco afeta quais cartuchos podem ser lidos; todas atuam só na troca de cartucho e no ciclo de energia do SA-1.
