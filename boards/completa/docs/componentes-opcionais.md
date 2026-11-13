# completa — componentes que podem ser retirados e o que se perde

Placa de 7 slots: SNES, NES, Famicom, Mega Drive, Master System, N64 e GBA (`boards/completa/`). Um cartucho por vez.

> **Nada aqui foi testado em hardware.** Fontes: `docs/bom.md`, `pinmap.md`, firmware, D54 e `docs/referencia/limites-gb.md`.

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| **U2** PIC12F629 (CIC) + soquete | **Perde o SA-1** | O PIC emula o CIC do SNES; o SA-1 só responde com ele rodando | Só **SA-1** (Super Mario RPG, Kirby Super Star, Kirby's Dream Land 3, Jikkyou Oshaberi Parodius, Dragon Ball Z: Hyper Dimension e outros; lista não exaustiva em `snes/docs/componentes-opcionais.md`). NES, Famicom, Mega Drive, Master System e GBA não usam |
| **U1** módulo Si5351 | **Perde o SA-1**; o PIC fica sem clock | SNES: clock mestre (pino 1), CPU (57) e CIC (56). NES: o `CLK0` vai ao pino 37, mas o firmware atual não o usa | SA-1; futuros Satellaview e SF Memory. NES: nenhum conhecido |
| **R2** 1 kΩ (pull-up de D7, `/IRQ` do SNES) | Sim, com cuidado | `/IRQ` solta. D7 também é o `/UWR` do Mega Drive (pino B29); o pull-up estava no HW5 | Nenhum conhecido. Inferência |
| **U3** MCP1700-3302E + **C7**, **C8** (1 µF) + **C9**, **C11** | **Perde o GBA, o GB, o GBC e o N64** | Os slots GBA e N64 só têm 3,3 V, vindo do U3. Sem ele, sem energia nos slots. Nunca ligar o GBA ou o N64 ao 5 V | Todos os GBA, GB e GBC. SNES, NES, Famicom, Mega Drive e Master System não dependem |
| **D1** LED + **R1** 220 Ω | Sim | Indicação de atividade | Nenhum |
| **C2** SNES, **C3** NES, **C4** Famicom, **C5** Mega Drive, **C10** Master System, **C9** GBA, **C11** N64, **C6** PIC (100 nF) | Não recomendado | Desacoplamento do slot ou do PIC. Sem eles, leitura errada possível (CRC variável) | Mais provável: SA-1, ROM grande (SSF2), GBA com Flash. Inferência |
| **C1** 470 µF | Não recomendado | Reserva do 5 V | Todos |

## Montagens parciais

Como os slots dividem os mesmos barramentos, pode-se montar só os slots que o usuário vai usar; os demais ficam vazios sem prejuízo, **menos** o desacoplamento de cada slot (montar o capacitor do slot usado). Sem PIC e sem Si5351 a placa lê tudo menos SA-1. Sem U3 e seus capacitores perde-se tudo do GBA (inclusive GB/GBC por adaptador) e do N64, mas os slots podem continuar vazios.

Sobre GB/GBC a 3,3 V: ver `docs/referencia/limites-gb.md` (alguns GB antigos podem falhar; jumper para 5 V só para GB/GBC, nunca GBA).

## F1, J1 e seletor de tensão (D138)

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| F1 (suporte e fusível 5×20 mm, 500 mA) | **Sim**, mas sem o fusível no suporte a placa não tem 5 V (um fio no lugar dele também serve) | só a proteção contra curto no cartucho (placa, Mega e USB) |
| J1 (jumper TRAVA 3,3 V), v1.1 | **Sim** | a defesa independente do firmware contra o 5 V num cartucho de 3,3 V; deixe aberto para usar o seletor |
| U4 (LDO), Q1, Q2, R3 a R5, C11 e C12, v1.1 | Não, se quiser 3,3 V | sem eles os slots NES, Famicom, Mega Drive e SMS ficam só em 5 V (com o Q1 no lugar). Se o seletor não for montado, ligue os pads de dreno e fonte do Q1 com um fio |

> **Tensão do cartucho (D140):** a placa não tem resistores em série entre o Mega e os slots. Mesmo com o seletor em 3,3 V, as saídas do Mega continuam em 5 V; o seletor só baixa o VCC do cartucho. **Confira a tensão que o cartucho suporta antes de inserir.** O SNES nunca recebe 3,3 V.

**F1**: fusível de vidro **5×20 mm, 500 mA, ação rápida**, em suporte de clipes de furo passante (Littelfuse série 100 ou equivalente): o fusível queimado se troca **sem solda**. Fica em série com o 5 V que a placa recebe do Mega. Queda de 0,1 a 0,2 V a 200 mA. **Sem o fusível no suporte, a placa fica sem 5 V**: use um fusível de 500 mA (ou um pedaço de fio na falta) e confira o valor ao trocar.
