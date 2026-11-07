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

## Bloco de troca de cartucho (v1.1)

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| Q1, R2, R3 | **Não** (sem o Q1 o 5V dos slots não chega: pôr uma ponte do 5V ao `+5V_CART` se quiser abrir mão do `POWER`) | `POWER on/off` em software; a troca segura do cartucho |
| R4, D2 (LED verde) | Sim | só a indicação visual de 5V dos slots |
| Q2, R5 | Sim | descarga rápida do rail: o firmware espera 2 s em vez de 500 ms |
| Q3, R6, R7, R8, D3 (sensor e LED amarelo) | Sim | o LED amarelo e a leitura do D53 (`POWER_RESP.rail` fica `0xFF`) |

Nenhuma peça do bloco afeta quais cartuchos podem ser lidos; todas atuam só na troca de cartucho e no ciclo de energia do SA-1.
