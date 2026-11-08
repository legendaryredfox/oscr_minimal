# megadrive_sms — Mega Drive e Master System

Versão mínima de dois slots em shield para Arduino Mega 2560 R3, 100% THT, só USB, **5 V** fixo: **Mega Drive** (64p, 2,54 mm) e **Master System / Mark III** (50p, 2,54 mm). Um cartucho por vez.

**Estado:** fases 1 e 2 (pinagem e footprint `SMS_Slot` em `boards/_lib/`); **sem projeto KiCad ainda**. Pedido do usuário em 2026-11-08 ("mega drive + sms").

## Pinagem

Os dois slots dividem endereço (`A0..A14`), dados de 8 bits (`D30..D37`) e os controles `D6`, `D8`, `D9`, `D17` e `D48`. O SMS vem do `mastersystem_adapter` do OSCR (`vendor/oscr/legacy/hardware/`), conferido com `pinout.ods` e `SMS.cpp`. Detalhes e pendências: [`docs/pinmap.md`](docs/pinmap.md).

## Decisões (2026-11-08)

- Pino 47 (Clock) do SMS sem ligação; sem Si5351.
- Slot SMS de 50p a 2,54 mm (2 × 25), o mesmo tipo de item que o slot Mega Drive (wiki de peças do OSCR). Medir o slot recebido.
- Game Gear e SG-1000 por adaptador de terceiros, fora da placa.
- **v1.0 sem o bloco de troca** (a mais barata que funciona; desligar o USB para trocar). Versão com bloco só depois, como v1.1.

Próximas fases (`CLAUDE.md` seção 7): esquemático (da `megadrive` v1.0), posicionamento, roteamento, fabricação.
