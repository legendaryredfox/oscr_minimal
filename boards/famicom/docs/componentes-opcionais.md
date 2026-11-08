# famicom — componentes que podem ser retirados e o que se perde

Placa só Famicom (`boards/famicom/`, 60 pinos): slot, LED e dois capacitores. Sem Si5351, PIC, R2 nem regulador de 3,3 V. O Famicom não tem pino de clock nem CIC do SNES no `pinmap.md`.

> **Nada aqui foi testado em hardware.**

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **D1** LED + **R1** 220 Ω | Sim | Some a indicação de atividade | Nenhum |
| **C2** 100 nF (VCC do slot, pinos 30 e 31) | Não recomendado | Desacoplamento do cartucho; leituras podem sair erradas | Mappers que consomem mais e os com bateria. Inferência |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |

Não há chip opcional. Cartuchos Famicom com chip de áudio extra (VRC6, VRC7, Namco 163, Sunsoft 5B) leem como os outros: o áudio não passa pelo dumper. Limites de mappers: `docs/referencia/limites-nes.md`.

## Bloco de troca de cartucho (v1.1)

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| Q1, R2, R3 | **Não** (sem o Q1 o 5V dos slots não chega: pôr uma ponte do 5V ao `+5V_CART` se quiser abrir mão do `POWER`) | `POWER on/off` em software; a troca segura do cartucho |
| R4, D2 (LED verde) | Sim | só a indicação visual de 5V dos slots |
| Q2, R5 | Sim | descarga rápida do rail: o firmware espera 2 s em vez de 500 ms |
| Q3, R6, R7, R8, D3 (sensor e LED amarelo) | Sim | o LED amarelo e a leitura do D53 (`POWER_RESP.rail` fica `0xFF`) |

Nenhuma peça do bloco afeta quais cartuchos podem ser lidos; todas atuam só na troca de cartucho e no ciclo de energia do SA-1.
