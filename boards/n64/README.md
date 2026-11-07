# n64 — Nintendo 64

**Slots:** N64 (50 pinos, cartucho de 3,3 V; footprint `N64_Slot` do OSCR, a trazer para `_lib/`)

**Estado:** esqueleto, sem projeto KiCad. **Fase 1 do `CLAUDE.md` feita:** `docs/pinmap.md` gerado por `tools/n64/gen_pinmap.py` cruzando `pinout.ods`, `n64_adapter` + `six_slot_adapter` e `N64.ino`: 50 pinos, 0 divergências entre as fontes. **Aguarda aprovação do usuário** para seguir.

## O que o pinmap mostra

- Sinais: `AD0` a `AD15` em A0 a A15 (portas F e K), `/READ` em D9, `/WRITE` em D8, `ALE_L` em D37, `ALE_H` em D36, `RESET` em D17, `EEPROM_DATA` em D7 (com pull-up de 1 kΩ para o 3,3 V no adaptador do OSCR). `EEPROM_CLK` (pino 19) vem do `CLK1` do Si5351 (2 MHz).
- Tensão: `VCC` (pinos 9, 17, 34, 42) em **3,3 V**. Mesmo regulador do GBA (MCP1700, `gb_gba/`) e sinais do Mega em 5 V, como o OSCR HW5 e a família já fazem no slot GBA.
- Sem ligação (como no OSCR): `12V` (13, 38), `NC` (14, 39), `CIC_to_PIF` (18), `L_AUDIO` (24), `PIF_to_CIC` (43), `R4300_CLK` (44), `NMI` (45), `Video_CLK` (46), `R_AUDIO` (49). O CIC do N64 **não** é lido por esta placa.

## O que a placa levaria e o que cada peça faz

Detalhe em `docs/componentes-opcionais.md`. Resumo:

| Peça | Sem ela |
|---|---|
| Regulador 3,3 V + 2 capacitores | Slot sem energia: nada lê |
| Si5351 (só `CLK1`) | Não lê as **EEPROMs** de save (4K e 16K); ROM e SRAM/Flash seguem |
| Pull-up de 1 kΩ no D7 | EEPROM não lê com confiança |

## Pendências para seguir

1. Aprovação do `pinmap.md` e das escolhas acima (CLAUDE.md, seção 3, passo 5).
2. Medidas reais do slot N64 comprado (CLAUDE.md, seção 5) e direção da etiqueta.
3. Firmware: religar o núcleo em `firmware/oscr/user.ini` (`n64 = true`), id no protocolo, host e GUI.
4. Footprint `N64_Slot` e símbolo em `boards/_lib/` (do OSCR: `vendor/oscr/legacy/hardware/footprints`).

O `CLAUDE.md` (seção 4) deixava o N64 fora das placas atuais; esta pasta nasce a pedido do usuário (2026-11-07).

Regras gerais: `CLAUDE.md`. Layout da pasta: `boards/README.md`.
