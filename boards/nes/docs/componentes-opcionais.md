# nes — componentes que podem ser retirados e o que se perde

Placa só NES (`boards/nes/`, 72 pinos). Tem Si5351; não tem PIC, R2 nem regulador de 3,3 V. Famicom não entra aqui (placas `famicom/` e `famicom_nes/`).

> **Nada aqui foi testado em hardware.** Conclusões vêm de `pinmap.md` e do firmware: `NES.cpp` não chama o Si5351 (conferido por busca de `ClockGen` nos cores).

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U1** módulo Si5351 + header | Sim, sem perda conhecida | O `CLK0` vai ao pino 37 do slot NES, como no OSCR HW5. O firmware atual não usa esse clock para ler NES | Nenhum conhecido. Se aparecer um cartucho que precise de clock externo, a falta seria nele; não achei nenhum no código |
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade | Nenhum |
| **C2** 100 nF (VCC do slot, pino 36) | Não recomendado | Desacoplamento do cartucho. Sem ele, leituras podem sair erradas | Mappers que consomem mais (MMC5, FME-7) e os com bateria. Inferência |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |

Como o Si5351 é a peça mais cara e mais difícil de achar certa, **a placa funciona para NES sem ele**. Se a meta for só NES, `boards/famicom/` (sem Si5351) é a versão sem nada opcional. As limitações de mappers estão em `docs/referencia/limites-nes.md` e valem para qualquer montagem.

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| F1 (suporte e fusível 5×20 mm, 500 mA) | **Sim**, mas sem o fusível no suporte a placa não tem 5 V (um fio no lugar dele também serve) | só a proteção contra curto no cartucho (placa, Mega e USB) |
| J1 (jumper TRAVA 3,3 V) | **Sim** | a defesa independente do firmware contra o 5 V num cartucho de 3,3 V; deixe aberto para usar o seletor |
| LDO, Q4, Q5, C do LDO | Não, se quiser 3,3 V | sem eles o slot fica só em 5 V; o seletor é a tensão padrão (5 V) com o Q4 |
| RN1 a RN4 (470 Ω) | Não, se quiser proteger cartuchos de 3,3 V | sem os resistores (ponte de fio nos furos) o 3,3 V deixa de proteger contra as saídas de 5 V do Mega |

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 e v1.1 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.
