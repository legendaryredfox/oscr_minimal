# megadrive_sms — Mega Drive e Master System

Versão mínima de dois slots em shield para Arduino Mega 2560 R3, 100% THT, só USB, **5 V** fixo: **Mega Drive** (64p, 2,54 mm) e **Master System / Mark III** (50p, 2,54 mm). Um cartucho por vez.

**Estado:** fase 1 (referência). Só o `docs/pinmap.md` existe; **sem projeto KiCad ainda**. Pedido do usuário em 2026-11-08 ("mega drive + sms").

## Pinagem

Os dois slots dividem endereço (`A0..A14`), dados de 8 bits (`D30..D37`) e os controles `D6`, `D8`, `D9`, `D17` e `D48`. O SMS vem do `mastersystem_adapter` do OSCR (`vendor/oscr/legacy/hardware/`), conferido com `pinout.ods` e `SMS.cpp`. Detalhes e pendências: [`docs/pinmap.md`](docs/pinmap.md).

## Pendências (precisam do usuário)

1. Pino 47 (Clock) do SMS: sem ligação (proposta) ou `CLK0`/`D16`.
2. Slot SMS de 50 pinos: medidas e modelo do slot comprado (footprint e posição).
3. Game Gear e SG-1000: só por adaptador, ou fora?
4. Com ou sem o bloco de troca de cartucho (versão separada, D128).

Próximas fases (`CLAUDE.md` seção 7): footprints em `boards/_lib/`, esquemático (derivado da `megadrive`), posicionamento, roteamento, fabricação.
