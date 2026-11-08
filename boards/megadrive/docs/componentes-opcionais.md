# megadrive — componentes que podem ser retirados e o que se perde

Placa só Mega Drive/Genesis (`boards/megadrive/`): slot, LED e capacitores. Não tem Si5351, PIC, regulador de 3,3 V nem R2.

> **Nada aqui foi testado em hardware.** Conclusões vêm de `pinmap.md` e do firmware (`firmware/oscr/src/cores/MegaDrive.cpp`, sem uso de clock externo).

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade (D38) | Nenhum |
| **TP1 a TP6** pontos de teste | Sim | Só o acesso para medir `/UWR`, `/CE`, `5V`, `GND`, `/OE`, `/WE` | Nenhum |
| **C2** (meio do slot), **C3** (junto ao A31), **C4** (junto ao A2) 100 nF | Não recomendado | Desacoplamento do cartucho. Sem eles, ruído pode dar leitura errada (CRC diferente a cada tentativa) | Mais provável nos de ROM grande (Super Street Fighter II com mapper SSF2, até 8 MB) e nos com SRAM/EEPROM (saves). Inferência; não medido |
| **C1** 470 µF | Não recomendado | Reserva de carga do 5 V; sem ela, picos podem reiniciar o Mega | Todos |

Não há chip opcional: o Mega Drive não usa clock do console, CIC nem tensão diferente de 5 V no dumper.

## Bloco de troca de cartucho (v1.1)

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| Q1, R2, R3 | **Não** (sem o Q1 o 5V dos slots não chega: pôr uma ponte do 5V ao `+5V_CART` se quiser abrir mão do `POWER`) | `POWER on/off` em software; a troca segura do cartucho |
| R4, D2 (LED verde) | Sim | só a indicação visual de 5V dos slots |
| Q2, R5 | Sim | descarga rápida do rail: o firmware espera 2 s em vez de 500 ms |
| Q3, R6, R7, R8, D3 (sensor e LED amarelo) | Sim | o LED amarelo e a leitura do D53 (`POWER_RESP.rail` fica `0xFF`) |

Nenhuma peça do bloco afeta quais cartuchos podem ser lidos; todas atuam só na troca de cartucho e no ciclo de energia do SA-1.

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| F1 (PTC) | **Sim**, mas ponha um fio ou ponte de solda nos furos dele | só a proteção contra curto no cartucho (placa, Mega e USB); sem o fio a placa não tem 5 V |
| J1 (jumper TRAVA 3,3 V) | **Sim** | a defesa independente do firmware contra o 5 V num cartucho de 3,3 V; deixe aberto para usar o seletor |
| LDO, Q4, Q5, C do LDO | Não, se quiser 3,3 V | sem eles o slot fica só em 5 V; o seletor é a tensão padrão (5 V) com o Q4 |
| RN1 a RN7 (470 Ω) | Não, se quiser proteger cartuchos de 3,3 V | sem os resistores (ponte de fio nos furos) o 3,3 V deixa de proteger contra as saídas de 5 V do Mega |

**F1** (PTC de furo passante, Bourns MF-RHT050 ou equivalente de 0,35 a 0,5 A de retenção, passo de 5,1 mm), em série com o 5 V que a placa recebe do Mega (nas versões com bloco de troca, antes do Q1). Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 e v1.1 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o F1, ponha um fio ou uma ponte de solda entre os dois furos dele**, senão a placa fica sem 5 V.
