# famicom — componentes que podem ser retirados e o que se perde

Placa só Famicom (`boards/famicom/`, 60 pinos): slot, LED e dois capacitores. Sem Si5351, PIC, R2 nem regulador de 3,3 V. O Famicom não tem pino de clock nem CIC do SNES no `pinmap.md`.

> **Nada aqui foi testado em hardware.**

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade | Nenhum |
| **C2** 100 nF (VCC do slot, pinos 30 e 31) | Não recomendado | Desacoplamento do cartucho; leituras podem sair erradas | Mappers que consomem mais e os com bateria. Inferência |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |

Não há chip opcional. Cartuchos Famicom com chip de áudio extra (VRC6, VRC7, Namco 163, Sunsoft 5B) leem como os outros: o áudio não passa pelo dumper. Limites de mappers: `docs/limites-nes.md`.

> Quando a v1.1 com o bloco de troca de cartucho existir (Q1, Q2, Q3 e o LED de "seguro trocar"; **sem chave física**, D123), acrescentar aqui.
