# 8_bits — componentes que podem ser retirados e o que se perde

Placa NES + Famicom + Master System (`boards/8_bits/`). Tem Si5351 (só o NES usa); sem PIC, R2 nem regulador de 3,3 V (o LDO da v1.1 é do seletor).

> **Nada aqui foi testado em hardware.** Conclusões vêm de `pinmap.md` e do firmware (`NES.cpp` não chama o Si5351).

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U1** módulo Si5351 + header | Sim, sem perda conhecida | O `CLK0` só vai ao pino 37 do NES; o firmware atual não o usa. O Famicom não tem pino de clock | Nenhum conhecido |
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade | Nenhum |
| **C2**, **C3**, **C4** 100 nF (VCC do NES, do Famicom e do SMS) | Não recomendado | Desacoplamento de cada slot | Mappers que consomem mais e os com bateria. Inferência |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |

Um cartucho por vez (os três slots dividem os mesmos barramentos). Sem o Si5351, a placa lê Famicom e Master System e só os mappers do NES que não usam o clock.

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| F1 (suporte e fusível 5×20 mm, 500 mA) | **Sim**, mas sem o fusível no suporte a placa não tem 5 V (um fio no lugar dele também serve) | só a proteção contra curto no cartucho (placa, Mega e USB) |
| J1 (jumper TRAVA 3,3 V) | **Sim** | a defesa independente do firmware contra o 5 V num cartucho de 3,3 V; deixe aberto para usar o seletor |
| U2 (LDO), Q1, Q2, R2 a R4, C5 e C6 | Não, se quiser 3,3 V | sem eles o slot fica só em 5 V; o seletor é a tensão padrão (5 V) com o Q1 |

> **Tensão do cartucho (D140):** a placa não tem resistores em série entre o Mega e os slots (as redes RN saíram em D140). Mesmo com o seletor em 3,3 V, as saídas do Mega continuam em 5 V; o seletor só baixa o VCC do cartucho. **Confira a tensão que o cartucho suporta antes de inserir**: um cartucho só de 3,3 V pode ser danificado.

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 e v1.1 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.
