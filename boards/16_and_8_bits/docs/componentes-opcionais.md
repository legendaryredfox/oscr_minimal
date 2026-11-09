# 16_and_8_bits — componentes que podem ser retirados e o que se perde

Placa de 5 slots v1.0: SNES, NES, Famicom, Mega Drive e GBA (`boards/16_and_8_bits/`). Sem chave de 5 V (Q1) nem proteção das linhas. Um cartucho por vez.

> **Nada aqui foi testado em hardware.** Fontes: `docs/bom.md`, `pinmap.md`, firmware, D54 e `docs/referencia/limites-gb.md`.

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

Sobre GB/GBC a 3,3 V: ver `docs/referencia/limites-gb.md` (alguns GB antigos podem falhar; jumper para 5 V só para GB/GBC, nunca GBA).

## F1, J1 e seletor de tensão (D138)

<!-- d138 -->

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| F1 (suporte e fusível 5×20 mm, 500 mA) | **Sim**, mas sem o fusível no suporte a placa não tem 5 V (um fio no lugar dele também serve) | só a proteção contra curto no cartucho (placa, Mega e USB) |

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. Vale para as versões v1.0 (exceção declarada à regra "a v1.0 é a mais barata que funciona", D138). **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.
