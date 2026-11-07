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

## Bloco de troca de cartucho (v1.1)

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| Q1, R2, R3 | **Não** (sem o Q1 o 5V dos slots não chega: pôr uma ponte do 5V ao `+5V_CART` se quiser abrir mão do `POWER`) | `POWER on/off` em software; a troca segura do cartucho |
| R4, D2 (LED verde) | Sim | só a indicação visual de 5V dos slots |
| Q2, R5 | Sim | descarga rápida do rail: o firmware espera 2 s em vez de 500 ms |
| Q3, R6, R7, R8, D3 (sensor e LED amarelo) | Sim | o LED amarelo e a leitura do D53 (`POWER_RESP.rail` fica `0xFF`) |

Nenhuma peça do bloco afeta quais cartuchos podem ser lidos; todas atuam só na troca de cartucho e no ciclo de energia do SA-1.
