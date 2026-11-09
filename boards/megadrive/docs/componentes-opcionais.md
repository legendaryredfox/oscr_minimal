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

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| F1 (suporte e fusível 5×20 mm, 500 mA) | **Sim**, mas sem o fusível no suporte a placa não tem 5 V (um fio no lugar dele também serve) | só a proteção contra curto no cartucho (placa, Mega e USB) |
| J1 (jumper TRAVA 3,3 V) | **Sim** | a defesa independente do firmware contra o 5 V num cartucho de 3,3 V; deixe aberto para usar o seletor |
| LDO, Q1, Q2, C do LDO | Não, se quiser 3,3 V | sem eles o slot fica só em 5 V; o seletor é a tensão padrão (5 V) com o Q1 |

> **Tensão do cartucho (D140):** a placa não tem resistores em série entre o Mega e os slots (as redes RN saíram em D140). Mesmo com o seletor em 3,3 V, as saídas do Mega continuam em 5 V; o seletor só baixa o VCC do cartucho. **Confira a tensão que o cartucho suporta antes de inserir**: um cartucho só de 3,3 V pode ser danificado.

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 e v1.1 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.
