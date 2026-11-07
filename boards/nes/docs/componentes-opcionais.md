# nes — componentes que podem ser retirados e o que se perde

Placa só NES (`boards/nes/`, 72 pinos). Tem Si5351; não tem PIC, R2 nem regulador de 3,3 V. Famicom não entra aqui (placas `famicom/` e `famicom_nes/`).

> **Nada aqui foi testado em hardware.** Conclusões vêm de `pinmap.md` e do firmware: `NES.cpp` não chama o Si5351 (conferido por busca de `ClockGen` nos cores).

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U1** módulo Si5351 + header | Sim, sem perda conhecida | O `CLK0` vai ao pino 37 do slot NES, como no OSCR HW5. O firmware atual não usa esse clock para ler NES | Nenhum conhecido. Se aparecer um cartucho que precise de clock externo, a falta seria nele; não achei nenhum no código |
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade | Nenhum |
| **C2** 100 nF (VCC do slot, pino 36) | Não recomendado | Desacoplamento do cartucho. Sem ele, leituras podem sair erradas | Mappers que consomem mais (MMC5, FME-7) e os com bateria. Inferência |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |

Como o Si5351 é a peça mais cara e mais difícil de achar certa, **a placa funciona para NES sem ele**. Se a meta for só NES, `boards/famicom/` (sem Si5351) é a versão sem nada opcional. As limitações de mappers estão em `docs/limites-nes.md` e valem para qualquer montagem.

> Quando a v1.1 com a chave física de troca de cartucho existir (D115, D118), acrescentar aqui Q1/Q2/Q3, a chave e o LED amarelo.
