# Mapa de pinos — placa megadrive (só Mega Drive) → pino do Arduino Mega 2560

> Recorte de `boards/16_bits/docs/pinmap.md` (mesma pinagem do OSCR HW5): só a tabela do Mega Drive. Sem SNES, NES, Famicom e GBA; sem Si5351, PIC e regulador de 3,3 V.

**FONTE DA VERDADE da placa `megadrive`.** Recorte à mão do pinmap da `16_bits` (que vem de `tools/gen_pinmap.py`); `tools/check_netlist.py --board megadrive` confere o esquemático contra este arquivo.

Cruza três fontes do OSCR HW5 (repositório `sanni/cartreader`, clone em `vendor/oscr/legacy/`):

- `ods` = `pinout.ods` (coluna do sistema; Famicom usa a coluna NES)
- `sch` = esquemático KiCad do adaptador (`hardware/<sistema>_adapter`) + `main_pcb_hw5`
- `six` = `hardware/six_slot_adapter` (mesma net no mesmo pino do header; não existe para o GBA)
- `fw`  = porta/bit AVR usado no `.ino` do sistema (`SNES.ino`, `NES.ino`, `MD.ino`, `GBA.ino`)

Convenção: a coluna **Arduino** é o nome da net no HW5 (`A0..A15`, `D2..D53`, `CLK0..2`). Na placa HW5, cada net vai do Mega ao header J3/J4 (pino de mesmo número no adaptador) e daí ao slot. Neste projeto o slot liga direto ao pino do Mega.

`-fw` no Mega Drive para `D2/D3/D5` (/YS, /CAS2, EDCLK): `MD.ino` não toca esses bits (deixa-os como entrada); o HW5 os liga mesmo assim e o `ods` os lista. Mantidos.

Marcas: `ods`/`sch`/`six`/`fw` = fonte concorda; `-` = fonte não cobre (ver nota); `!` = fonte discorda (ver `docs/decisoes.md`). `fw` é checado só no nível da porta/bit (o firmware não usa nomes de sinal).

Pinos do Mega **não usados** por nenhum slot: `D0`/`D1` (serial USB; o HW5 leva ao header mas os adaptadores deixam sem ligação), `D10..D13`, `D18`, `D19`, `D39`, `D51..D53` (`D50` é `/CART`; `D39` é o pino do botão no `main.cpp` do OSCR e não deve ser usado). `D0`/`D1` nunca podem ir a um slot.


## Mega Drive (ref. `U1` em `megadrive_adapter`, 64 pinos)

| pino do slot | sinal | net / pino Arduino | porta/bit AVR | fonte |
|---|---|---|---|---|
| A1 | GND_A1 | GND | - | sch six |
| A2 | VCC_A2 | 5V (fixo) | - | sch six |
| A3 | A8_A3 | A7 | PF7 | sch ods fw six |
| A4 | A11_A4 | A10 | PK2 | sch ods fw six |
| A5 | A7_A5 | A6 | PF6 | sch ods fw six |
| A6 | A12_A6 | A11 | PK3 | sch ods fw six |
| A7 | A6_A7 | A5 | PF5 | sch ods fw six |
| A8 | A13_A8 | A12 | PK4 | sch ods fw six |
| A9 | A5_A9 | A4 | PF4 | sch ods fw six |
| A10 | A14_A10 | A13 | PK5 | sch ods fw six |
| A11 | A4_A11 | A3 | PF3 | sch ods fw six |
| A12 | A15_A12 | A14 | PK6 | sch ods fw six |
| A13 | A3_A13 | A2 | PF2 | sch ods fw six |
| A14 | A16_A14 | A15 | PK7 | sch ods fw six |
| A15 | A2_A15 | A1 | PF1 | sch ods fw six |
| A16 | A17_A16 | D49 | PL0 | sch ods fw six |
| A17 | A1_A17 | A0 | PF0 | sch ods fw six |
| A18 | GND_A18 | GND | - | sch six |
| A19 | D7_A19 | D30 | PC7 | sch ods fw six |
| A20 | D0_A20 | D37 | PC0 | sch ods fw six |
| A21 | D8_A21 | D22 | PA0 | sch ods fw six |
| A22 | D6_A22 | D31 | PC6 | sch ods fw six |
| A23 | D1_A23 | D36 | PC1 | sch ods fw six |
| A24 | D9_A24 | D23 | PA1 | sch ods fw six |
| A25 | D5_A25 | D32 | PC5 | sch ods fw six |
| A26 | D2_A26 | D35 | PC2 | sch ods fw six |
| A27 | D10_A27 | D24 | PA2 | sch ods fw six |
| A28 | D4_A28 | D33 | PC4 | sch ods fw six |
| A29 | D3_A29 | D34 | PC3 | sch ods fw six |
| A30 | D11_A30 | D25 | PA3 | sch ods fw six |
| A31 | VCC_A31 | 5V (fixo) | - | sch six |
| A32 | GND_A32 | GND | - | sch six |
| B1 | SL1_B1 | NC (sem ligação) | - | sch |
| B2 | /MRES_B2 | D17 | PH0 | sch ods fw six |
| B3 | SR1_B3 | NC (sem ligação) | - | sch |
| B4 | A9_B4 | A8 | PK0 | sch ods fw six |
| B5 | A10_B5 | A9 | PK1 | sch ods fw six |
| B6 | A18_B6 | D48 | PL1 | sch ods fw six |
| B7 | A19_B7 | D47 | PL2 | sch ods fw six |
| B8 | A20_B8 | D46 | PL3 | sch ods fw six |
| B9 | A21_B9 | D45 | PL4 | sch ods fw six |
| B10 | A22_B10 | D44 | PL5 | sch ods fw six |
| B11 | A23_B11 | D43 | PL6 | sch ods fw six |
| B12 | /YS_B12 | D2 | PE4 | sch ods -fw six |
| B13 | /VSYNC_B13 | NC (sem ligação) | - | sch |
| B14 | /HSYNC_B14 | NC (sem ligação) | - | sch |
| B15 | EDCLK_B15 | D5 | PE3 | sch ods -fw six |
| B16 | /CAS0_B16 | D9 | PH6 | sch ods fw six |
| B17 | /CE_0_B17 | D6 | PH3 | sch ods fw six |
| B18 | /AS_B18 | D14 | PJ1 | sch ods fw six |
| B19 | VCLK_B19 | D16 | PH1 | sch ods fw six |
| B20 | /DTACK_B20 | NC (sem ligação) | - | sch |
| B21 | /CAS2_B21 | D3 | PE5 | sch ods -fw six |
| B22 | D15_B22 | D29 | PA7 | sch ods fw six |
| B23 | D14_B23 | D28 | PA6 | sch ods fw six |
| B24 | D13_B24 | D27 | PA5 | sch ods fw six |
| B25 | D12_B25 | D26 | PA4 | sch ods fw six |
| B26 | /ASEL_B26 | D4 | PG5 | sch ods fw six |
| B27 | /VRES_B27 | D17 | PH0 | sch ods fw six |
| B28 | /LWR_B28 | D8 | PH5 | sch ods fw six |
| B29 | /UWR_B29 | D7 | PH4 | sch ods fw six |
| B30 | /M3_B30 | NC (sem ligação) | - | sch |
| B31 | /TIME_B31 | D15 | PJ0 | sch ods fw six |
| B32 | /CART_B32 | D50 | PB3 | **v. 1.2**: detecção de cartucho (o cartucho liga B32 ao GND; no Mega, `INPUT_PULLUP`; baixo = cartucho presente). D50 não é usado pelo OSCR neste fork (sem SD); fora do HW5 |

## Placa principal — o que esta placa liga além do slot

| item | pino Arduino | fonte |
|---|---|---|
| LED de status (cátodo via 220Ω, ânodo em VCC; **ativo em nível baixo**) | D38 (PD7) | sch main D1/R1 + fw `statusLED()` |
| Reset do Mega | RESET → J4.35 (adaptadores não usam) | sch main |
