# famicom_nes — componentes que podem ser retirados e o que se perde

Placa Famicom + NES (`boards/famicom_nes/`). Tem Si5351 (só o NES usa); sem PIC, R2 nem regulador de 3,3 V.

> **Nada aqui foi testado em hardware.** Conclusões vêm de `pinmap.md` e do firmware (`NES.cpp` não chama o Si5351).

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U1** módulo Si5351 + header | Sim, sem perda conhecida | O `CLK0` só vai ao pino 37 do NES; o firmware atual não o usa. O Famicom não tem pino de clock | Nenhum conhecido |
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade | Nenhum |
| **C2**, **C3** 100 nF (VCC do NES e do Famicom) | Não recomendado | Desacoplamento de cada slot | Mappers que consomem mais e os com bateria. Inferência |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |

Um cartucho por vez (os dois slots dividem os mesmos barramentos). Sem o Si5351, a placa vira uma `famicom` com um slot NES a mais.

> Quando a v1.1 com o bloco de troca de cartucho existir (Q1, Q2, Q3 e o LED de "seguro trocar"; **sem chave física**, D123), acrescentar aqui.
