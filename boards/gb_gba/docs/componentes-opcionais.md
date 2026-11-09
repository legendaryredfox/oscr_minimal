# gb_gba — componentes que podem ser retirados e o que se perde

Placa só GBA (`boards/gb_gba/`); GB e GBC entram pelo mesmo slot, com adaptador. O VCC do slot é **3,3 V**, vindo do regulador. Sem Si5351, PIC nem R2.

> **Nada aqui foi testado em hardware.** Conclusões vêm de `pinmap.md`, do esquemático e de `docs/referencia/limites-gb.md`.

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U1** MCP1700-3302E (regulador 3,3 V) | **Não** | O slot fica sem alimentação: nada lê. Nunca ligar o VCC do slot ao 5 V do GBA | **Todos**: GBA, GB e GBC |
| **C2** (entrada) e **C3** (saída) 1 µF | **Não** | O MCP1700 precisa de 1 µF ou mais em cada lado; sem eles pode oscilar e dar tensão instável | Todos |
| **C4** 100 nF (VCC do slot) | Não recomendado | Desacoplamento do cartucho; leituras podem sair erradas | GBA com Flash e saves; repros. Inferência |
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade | Nenhum |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |

## Efeito de 3,3 V nos cartuchos antigos (não é peça, mas limita)

O OSCR lê GB a 5 V; aqui todos saem do regulador a 3,3 V. A maioria dos cartuchos GB lê bem, mas **alguns GB antigos podem falhar** (bits trocados, CRC diferente a cada tentativa). A saída prevista é um jumper de solda do VCC do slot ao 5 V (`docs/referencia/limites-gb.md`, seção 2), que **só vale para GB/GBC**: nunca para GBA, que se danifica com 5 V.

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| F1 (suporte e fusível 5×20 mm, 500 mA) | **Sim**, mas sem o fusível no suporte a placa não tem 5 V (um fio no lugar dele também serve) | só a proteção contra curto no cartucho (placa, Mega e USB) |

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.
