# Mapa de pinos — placa gb_gba (GBA; GB e GBC por adaptador) → pino do Arduino Mega 2560

> Recorte de `boards/16_and_8_bits/docs/pinmap.md` (mesma pinagem do OSCR HW5): só a tabela do GBA. Sem SNES, NES, Famicom, Mega Drive, Si5351 e PIC. O regulador de 3,3 V (U1) fica: VCC do slot GBA = 3V3, nunca 5V.

**FONTE DA VERDADE da placa `gb_gba`.** Recorte à mão do pinmap da `16_and_8_bits` (que vem de `tools/gen_pinmap.py`); `tools/check_netlist.py --board gb_gba` confere o esquemático contra este arquivo.

Cruza três fontes do OSCR HW5 (repositório `sanni/cartreader`, clone em `vendor/oscr/legacy/`):

- `ods` = `pinout.ods` (coluna do sistema; Famicom usa a coluna NES)
- `sch` = esquemático KiCad do adaptador (`hardware/<sistema>_adapter`) + `main_pcb_hw5`
- `six` = `hardware/six_slot_adapter` (mesma net no mesmo pino do header; não existe para o GBA)
- `fw`  = porta/bit AVR usado no `.ino` do sistema (`SNES.ino`, `NES.ino`, `MD.ino`, `GBA.ino`)

Convenção: a coluna **Arduino** é o nome da net no HW5 (`A0..A15`, `D2..D53`, `CLK0..2`). Na placa HW5, cada net vai do Mega ao header J3/J4 (pino de mesmo número no adaptador) e daí ao slot. Neste projeto o slot liga direto ao pino do Mega.

`-fw` no Mega Drive para `D2/D3/D5` (/YS, /CAS2, EDCLK): `MD.ino` não toca esses bits (deixa-os como entrada); o HW5 os liga mesmo assim e o `ods` os lista. Mantidos.

Marcas: `ods`/`sch`/`six`/`fw` = fonte concorda; `-` = fonte não cobre (ver nota); `!` = fonte discorda (ver `docs/decisoes.md`). `fw` é checado só no nível da porta/bit (o firmware não usa nomes de sinal).

Pinos do Mega **não usados** por nenhum slot: `D0`/`D1` (serial USB; o HW5 leva ao header mas os adaptadores deixam sem ligação), `D10..D13`, `D18`, `D19`, `D39`, `D50..D53`. `D0`/`D1` nunca podem ir a um slot.


## GBA (ref. `J10` em `main_pcb_hw5`, 34 pinos)

| pino do slot | sinal | net / pino Arduino | porta/bit AVR | fonte |
|---|---|---|---|---|
| 1 | VCC_1 | 3V3 (regulador U1) | - | sch |
| 2 | CLK_2 | D16 | PH1 | sch ods -fw |
| 3 | WR_3 | D8 | PH5 | sch ods fw |
| 4 | RD_4 | D9 | PH6 | sch ods fw |
| 5 | CS1_5 | D6 | PH3 | sch ods fw |
| 6 | AD0_6 | A0 | PF0 | sch ods fw |
| 7 | AD1_7 | A1 | PF1 | sch ods fw |
| 8 | AD2_8 | A2 | PF2 | sch ods fw |
| 9 | AD3_9 | A3 | PF3 | sch ods fw |
| 10 | AD4_10 | A4 | PF4 | sch ods fw |
| 11 | AD5_11 | A5 | PF5 | sch ods fw |
| 12 | AD6_12 | A6 | PF6 | sch ods fw |
| 13 | AD7_13 | A7 | PF7 | sch ods fw |
| 14 | AD8_14 | A8 | PK0 | sch ods fw |
| 15 | AD9_15 | A9 | PK1 | sch ods fw |
| 16 | AD10_16 | A10 | PK2 | sch ods fw |
| 17 | AD11_17 | A11 | PK3 | sch ods fw |
| 18 | AD12_18 | A12 | PK4 | sch ods fw |
| 19 | AD13_19 | A13 | PK5 | sch ods fw |
| 20 | AD14_20 | A14 | PK6 | sch ods fw |
| 21 | AD15_21 | A15 | PK7 | sch ods fw |
| 22 | D0_A16_22 | D37 | PC0 | sch ods fw |
| 23 | D1_A17_23 | D36 | PC1 | sch ods fw |
| 24 | D2_A18_24 | D35 | PC2 | sch ods fw |
| 25 | D3_A19_25 | D34 | PC3 | sch ods fw |
| 26 | D4_A20_26 | D33 | PC4 | sch ods fw |
| 27 | D5_A21_27 | D32 | PC5 | sch ods fw |
| 28 | D6_A22_28 | D31 | PC6 | sch ods fw |
| 29 | D7_A23_29 | D30 | PC7 | sch ods fw |
| 30 | RST_CS2_30 | D17 | PH0 | sch ods fw |
| 31 | AUD_IRQ_31 | NC (sem ligação) | - | sch |
| 32 | GND_32 | GND | - | sch |
| SHIELD_3 | SHIELD_3_33 | GND | - | sch |
| SHIELD_4 | SHIELD_4_34 | GND | - | sch |

## Placa principal — o que esta placa liga além do slot

| item | pino Arduino | fonte |
|---|---|---|
| LED de status (cátodo via 220Ω, ânodo em VCC; **ativo em nível baixo**) | D38 (PD7) | sch main D1/R1 + fw `statusLED()` |
| Reset do Mega | RESET → J4.35 (adaptadores não usam) | sch main |
| Regulador U1 (MCP1700-3302E), C2 (1 µF, 5V), C3 (1 µF, 3V3), C4 (100 nF, VCC do slot) | 5V → 3V3 | D22 em `docs/decisoes.md` |
| Pino 31 do slot GBA (AUD_IRQ) | sem ligação (no HW5 vai ao D7) | D22 |
