# n64 — Nintendo 64

**Slots:** N64 (cartucho de 3,3 V; conector de borda a levantar)

**Estado:** esqueleto, sem projeto KiCad.

**Pendências:** levantar a pinagem do N64 em `vendor/oscr/` (`pinout.ods`, `hardware/` e `Cart_Reader/N64.ino`) e cruzar as três fontes; escolher o slot e o adaptador; definir a tensão do slot (o N64 não é de 5 V); conferir se o OSCR pede +12 V para o N64 no `six_slot_adapter` (ver D3 em `docs/decisoes.md`); firmware: o núcleo N64 está desligado (`n64 = false`) em `firmware/oscr/user.ini`.

O `CLAUDE.md` (seção 4) deixou o N64 fora das placas atuais; esta pasta só reserva o lugar para uma variante futura, a pedido do usuário. Nenhum pino foi levantado ainda.

Regras de hardware (THT, JLCPCB 2 camadas, pinagem idêntica ao OSCR HW5): `CLAUDE.md`. Layout da pasta: `boards/README.md`.
