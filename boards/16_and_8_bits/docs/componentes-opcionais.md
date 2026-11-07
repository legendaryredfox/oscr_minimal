# 16_and_8_bits — componentes que podem ser retirados e o que se perde

Placa de 5 slots v1.0: SNES, NES, Famicom, Mega Drive e GBA (`boards/16_and_8_bits/`). Sem chave de 5 V (Q1) nem proteção das linhas. Um cartucho por vez.

> **Nada aqui foi testado em hardware.** Fontes: `docs/bom.md`, `pinmap.md`, firmware, D54 e `docs/limites-gb.md`.

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U2** PIC12F629 (CIC) + soquete | **Perde o SA-1** | O PIC emula o CIC do SNES; o SA-1 só responde com ele rodando | Só **SA-1** (Super Mario RPG, Kirby Super Star, Kirby's Dream Land 3, Jikkyou Oshaberi Parodius, Dragon Ball Z: Hyper Dimension e outros; lista não exaustiva em `snes/docs/componentes-opcionais.md`). NES, Famicom, Mega Drive e GBA não usam |
| **U1** módulo Si5351 | **Perde o SA-1**; o PIC fica sem clock | SNES: clock mestre (pino 1), CPU (57) e CIC (56). NES: o `CLK0` vai ao pino 37, mas o firmware atual não o usa | SA-1; futuros Satellaview e SF Memory. NES: nenhum conhecido |
| **R2** 1 kΩ (pull-up de D7, `/IRQ` do SNES) | Sim, com cuidado | `/IRQ` solta. D7 também é o `/UWR` do Mega Drive (pino B29); o pull-up estava no HW5 | Nenhum conhecido. Inferência |
| **U3** MCP1700-3302E + **C7**, **C8** (1 µF) + **C9** | **Perde o GBA, o GB e o GBC** | O slot GBA só tem 3,3 V, vindo do U3. Sem ele, sem energia no slot. Nunca ligar o GBA ao 5 V | Todos os GBA, GB e GBC. SNES, NES, Famicom e Mega Drive não dependem (5 V direto) |
| **D1** LED + **R1** 220 Ω | Sim | Indicação de atividade | Nenhum |
| **C2** SNES, **C3** NES, **C4** Famicom, **C5** Mega Drive, **C9** GBA, **C6** PIC (100 nF) | Não recomendado | Desacoplamento do slot ou do PIC. Sem eles, leitura errada possível (CRC variável) | Mais provável: SA-1, ROM grande (SSF2), GBA com Flash. Inferência |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |

## Montagens parciais

Como os slots dividem os mesmos barramentos, pode-se montar só os slots que o usuário vai usar; os demais ficam vazios sem prejuízo, **menos** o desacoplamento de cada slot (montar o capacitor do slot usado). Sem PIC e sem Si5351 a placa lê tudo menos SA-1. Sem U3 e seus capacitores perde-se tudo do GBA (inclusive GB/GBC por adaptador), mas o slot GBA pode continuar vazio.

Sobre GB/GBC a 3,3 V: ver `docs/limites-gb.md` (alguns GB antigos podem falhar; jumper para 5 V só para GB/GBC, nunca GBA).

## Bloco de troca de cartucho (v1.1)

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| Q1, R3, R4 | **Não** (sem o Q1 o 5V dos slots não chega: pôr uma ponte do 5V ao `+5V_CART` se quiser abrir mão do `POWER`) | `POWER on/off` em software; a troca segura do cartucho |
| R5, D2 (LED verde) | Sim | só a indicação visual de 5V dos slots |
| Q2, R6, R7 | Sim | descarga rápida do rail: o firmware espera 2 s em vez de 500 ms |
| Q3, R8, R9, R10, D3 (sensor e LED amarelo) | Sim | o LED amarelo e a leitura do D53 (`POWER_RESP.rail` fica `0xFF`) |

Nenhuma peça do bloco afeta quais cartuchos podem ser lidos; todas atuam só na troca de cartucho e no ciclo de energia do SA-1.
