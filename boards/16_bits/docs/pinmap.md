# Mapa de pinos — slot do cartucho → pino do Arduino Mega 2560

**FONTE DA VERDADE.** Gerado por `tools/gen_pinmap.py` (não edite à mão; edite o script ou `docs/decisoes.md`).

Cruza três fontes do OSCR HW5 (repositório `sanni/cartreader`, clone em `vendor/oscr/legacy/`):

- `ods` = `pinout.ods` (coluna do sistema; Famicom usa a coluna NES)
- `sch` = esquemático KiCad do adaptador (`hardware/<sistema>_adapter`) + `main_pcb_hw5`
- `six` = `hardware/six_slot_adapter` (mesma net no mesmo pino do header; não existe para o GBA)
- `fw`  = porta/bit AVR usado no `.ino` do sistema (`SNES.ino`, `NES.ino`, `MD.ino`, `GBA.ino`)

Convenção: a coluna **Arduino** é o nome da net no HW5 (`A0..A15`, `D2..D53`, `CLK0..2`). Na placa HW5, cada net vai do Mega ao header J3/J4 (pino de mesmo número no adaptador) e daí ao slot. Neste projeto o slot liga direto ao pino do Mega.

`-fw` no Mega Drive para `D2/D3/D5` (/YS, /CAS2, EDCLK): `MD.ino` não toca esses bits (deixa-os como entrada); o HW5 os liga mesmo assim e o `ods` os lista. Mantidos.

Marcas: `ods`/`sch`/`six`/`fw` = fonte concorda; `-` = fonte não cobre (ver nota); `!` = fonte discorda (ver `docs/decisoes.md`). `fw` é checado só no nível da porta/bit (o firmware não usa nomes de sinal).

Pinos do Mega **não usados** por nenhum slot: `D0`/`D1` (serial USB; o HW5 leva ao header mas os adaptadores deixam sem ligação), `D10..D13`, `D18`, `D19`, `D39`, `D50..D53`. `D0`/`D1` nunca podem ir a um slot.


## SNES (ref. `J3` em `snes_adapter`, 62 pinos)

| pino do slot | sinal | net / pino Arduino | porta/bit AVR | fonte |
|---|---|---|---|---|
| 1 | 21.477MHz_Clock_1 | CLK0 (Si5351) | (Si5351) | sch ods six |
| 2 | Expand_2 | D4 | PG5 | sch ods fw six |
| 3 | PA6_3 | D28 | PA6 | sch ods fw six |
| 4 | /PARD_4 | D15 | PJ0 | sch ods fw six |
| 5 | GND_5 | GND | - | sch six |
| 6 | A11_6 | A11 | PK3 | sch ods fw six |
| 7 | A10_7 | A10 | PK2 | sch ods fw six |
| 8 | A9_8 | A9 | PK1 | sch ods fw six |
| 9 | A8_9 | A8 | PK0 | sch ods fw six |
| 10 | A7_10 | A7 | PF7 | sch ods fw six |
| 11 | A6_11 | A6 | PF6 | sch ods fw six |
| 12 | A5_12 | A5 | PF5 | sch ods fw six |
| 13 | A4_13 | A4 | PF4 | sch ods fw six |
| 14 | A3_14 | A3 | PF3 | sch ods fw six |
| 15 | A2_15 | A2 | PF2 | sch ods fw six |
| 16 | A1_16 | A1 | PF1 | sch ods fw six |
| 17 | A0_17 | A0 | PF0 | sch ods fw six |
| 18 | /IRQ_18 | D7 | PH4 | sch ods fw six |
| 19 | D0_19 | D37 | PC0 | sch ods fw six |
| 20 | D1_20 | D36 | PC1 | sch ods fw six |
| 21 | D2_21 | D35 | PC2 | sch ods fw six |
| 22 | D3_22 | D34 | PC3 | sch ods fw six |
| 23 | /RD_23 | D9 | PH6 | sch ods fw six |
| 24 | CIC_out_data_(p1)_24 | CIC DATA 1 → PIC12F629 | - | sch six |
| 25 | CIC_in_data_(p7)_25 | CIC RESET → PIC12F629 | - | sch six |
| 26 | /RESET_26 | D17 | PH0 | sch ods fw six |
| 27 | VCC_27 | 5V (fixo) | - | sch six |
| 28 | PA0_28 | D22 | PA0 | sch ods fw six |
| 29 | PA2_29 | D24 | PA2 | sch ods fw six |
| 30 | PA4_30 | D26 | PA4 | sch ods fw six |
| 31 | Left_Audio_Input_31 | NC (sem ligação) | - | sch |
| 32 | /WRAM_32 | D2 | PE4 | sch ods fw six |
| 33 | Refresh_33 | D3 | PE5 | sch ods fw six |
| 34 | PA7_34 | D29 | PA7 | sch ods fw six |
| 35 | /PAWR_35 | D14 | PJ1 | sch ods fw six |
| 36 | GND_36 | GND | - | sch six |
| 37 | A12_37 | A12 | PK4 | sch ods fw six |
| 38 | A13_38 | A13 | PK5 | sch ods fw six |
| 39 | A14_39 | A14 | PK6 | sch ods fw six |
| 40 | A15_40 | A15 | PK7 | sch ods fw six |
| 41 | BA0_41 | D49 | PL0 | sch ods fw six |
| 42 | BA1_42 | D48 | PL1 | sch ods fw six |
| 43 | BA2_43 | D47 | PL2 | sch ods fw six |
| 44 | BA3_44 | D46 | PL3 | sch ods fw six |
| 45 | BA4_45 | D45 | PL4 | sch ods fw six |
| 46 | BA5_46 | D44 | PL5 | sch ods fw six |
| 47 | BA6_47 | D43 | PL6 | sch ods fw six |
| 48 | BA7_48 | D42 | PL7 | sch ods fw six |
| 49 | /Cart_49 | D6 | PH3 | sch ods fw six |
| 50 | D4_50 | D33 | PC4 | sch ods fw six |
| 51 | D5_51 | D32 | PC5 | sch ods fw six |
| 52 | D6_52 | D31 | PC6 | sch ods fw six |
| 53 | D7_53 | D30 | PC7 | sch ods fw six |
| 54 | /WR_54 | D8 | PH5 | sch ods fw six |
| 55 | CIC_data_out_(p2)_55 | CIC DATA 0 → PIC12F629 | - | sch six |
| 56 | CIC_clock_in_(p6)_56 | CLK2 (Si5351) | (Si5351) | sch ods six |
| 57 | CPU_Clock_57 | CLK1 (Si5351) | (Si5351) | sch ods six |
| 58 | VCC_58 | 5V (fixo) | - | sch six |
| 59 | PA1_59 | D23 | PA1 | sch ods fw six |
| 60 | PA3_60 | D25 | PA3 | sch ods fw six |
| 61 | PA5_61 | D27 | PA5 | sch ods fw six |
| 62 | Right_Audio_Input_62 | NC (sem ligação) | - | sch |

## NES (ref. `U1` em `nes_adapter`, 72 pinos)

| pino do slot | sinal | net / pino Arduino | porta/bit AVR | fonte |
|---|---|---|---|---|
| 1 | GND_1 | GND | - | sch six |
| 2 | PRG_A11_2 | D25 | PA3 | sch ods fw six |
| 3 | PRG_A10_3 | D24 | PA2 | sch ods fw six |
| 4 | PRG_A9_4 | D23 | PA1 | sch ods fw six |
| 5 | PRG_A8_5 | D22 | PA0 | sch ods fw six |
| 6 | PRG_A7_6 | D42 | PL7 | sch ods fw six |
| 7 | PRG_A6_7 | D43 | PL6 | sch ods fw six |
| 8 | PRG_A5_8 | D44 | PL5 | sch ods fw six |
| 9 | PRG_A4_9 | D45 | PL4 | sch ods fw six |
| 10 | PRG_A3_10 | D46 | PL3 | sch ods fw six |
| 11 | PRG_A2_11 | D47 | PL2 | sch ods fw six |
| 12 | PRG_A1_12 | D48 | PL1 | sch ods fw six |
| 13 | PRG_A0_13 | D49 | PL0 | sch ods fw six |
| 14 | PRG_RW_14 | A7 | PF7 | sch ods fw six |
| 15 | IRQ_15 | A6 | PF6 | sch ods fw six |
| 16 | EXP_0_16 | NC (sem ligação) | - | sch |
| 17 | EXP_1_17 | NC (sem ligação) | - | sch |
| 18 | EXP_2_18 | NC (sem ligação) | - | sch |
| 19 | EXP_3_19 | NC (sem ligação) | - | sch |
| 20 | EXP_4_20 | NC (sem ligação) | - | sch |
| 21 | CHR_RD_21 | A5 | PF5 | sch ods fw six |
| 22 | CIRAM_A10_22 | D35 | PC2 | sch ods fw six |
| 23 | CHR_A6_23 | D43 | PL6 | sch ods fw six |
| 24 | CHR_A5_24 | D44 | PL5 | sch ods fw six |
| 25 | CHR_A4_25 | D45 | PL4 | sch ods fw six |
| 26 | CHR_A3_26 | D46 | PL3 | sch ods fw six |
| 27 | CHR_A2_27 | D47 | PL2 | sch ods fw six |
| 28 | CHR_A1_28 | D48 | PL1 | sch ods fw six |
| 29 | CHR_A0_29 | D49 | PL0 | sch ods fw six |
| 30 | CHR_D0_30 | A8 | PK0 | sch ods fw six |
| 31 | CHR_D1_31 | A9 | PK1 | sch ods fw six |
| 32 | CHR_D2_32 | A10 | PK2 | sch ods fw six |
| 33 | CHR_D3_33 | A11 | PK3 | sch ods fw six |
| 34 | Security3_34 | NC (sem ligação) | - | sch |
| 35 | Security4_35 | NC (sem ligação) | - | sch |
| 36 | VCC_36 | 5V (fixo) | - | sch six |
| 37 | CLK_37 | CLK0 (Si5351) | (Si5351) | sch -ods six |
| 38 | M2_38 | A0 | PF0 | sch ods fw six |
| 39 | PRG_A12_39 | D26 | PA4 | sch ods fw six |
| 40 | PRG_A13_40 | D27 | PA5 | sch ods fw six |
| 41 | PRG_A14_41 | D28 | PA6 | sch ods fw six |
| 42 | PRG_D7_42 | A15 | PK7 | sch ods fw six |
| 43 | PRG_D6_43 | A14 | PK6 | sch ods fw six |
| 44 | PRG_D5_44 | A13 | PK5 | sch ods fw six |
| 45 | PRG_D4_45 | A12 | PK4 | sch ods fw six |
| 46 | PRG_D3_46 | A11 | PK3 | sch ods fw six |
| 47 | PRG_D2_47 | A10 | PK2 | sch ods fw six |
| 48 | PRG_D1_48 | A9 | PK1 | sch ods fw six |
| 49 | PRG_D0_49 | A8 | PK0 | sch ods fw six |
| 50 | PRG_CE_50 | A1 | PF1 | sch ods fw six |
| 51 | EXP_9_51 | NC (sem ligação) | - | sch |
| 52 | EXP_8_52 | NC (sem ligação) | - | sch |
| 53 | EXP_7_53 | NC (sem ligação) | - | sch |
| 54 | EXP_6_54 | NC (sem ligação) | - | sch |
| 55 | EXP_5_55 | NC (sem ligação) | - | sch |
| 56 | CHR_WR_56 | A2 | PF2 | sch ods fw six |
| 57 | CIRAM_CE_57 | A3 | PF3 | sch ods fw six |
| 58 | CHR_/A13_58 | A4 | PF4 | sch ods fw six |
| 59 | CHR_A7_59 | D42 | PL7 | sch ods fw six |
| 60 | CHR_A8_60 | D22 | PA0 | sch ods fw six |
| 61 | CHR_A9_61 | D23 | PA1 | sch ods fw six |
| 62 | CHR_A11_62 | D25 | PA3 | sch ods fw six |
| 63 | CHR_A10_63 | D24 | PA2 | sch ods fw six |
| 64 | CHR_A12_64 | D26 | PA4 | sch ods fw six |
| 65 | CHR_A13_65 | D27 | PA5 | sch ods fw six |
| 66 | CHR_D7_66 | A15 | PK7 | sch ods fw six |
| 67 | CHR_D6_67 | A14 | PK6 | sch ods fw six |
| 68 | CHR_D5_68 | A13 | PK5 | sch ods fw six |
| 69 | CHR_D4_69 | A12 | PK4 | sch ods fw six |
| 70 | Security1_70 | NC (sem ligação) | - | sch |
| 71 | Security2_71 | NC (sem ligação) | - | sch |
| 72 | GND_72 | GND | - | sch six |

## Famicom (ref. `U1` em `famicom_adapter`, 60 pinos)

| pino do slot | sinal | net / pino Arduino | porta/bit AVR | fonte |
|---|---|---|---|---|
| 1 | GND_1 | GND | - | sch six |
| 2 | PRG_A11_2 | D25 | PA3 | sch ods fw six |
| 3 | PRG_A10_3 | D24 | PA2 | sch ods fw six |
| 4 | PRG_A9_4 | D23 | PA1 | sch ods fw six |
| 5 | PRG_A8_5 | D22 | PA0 | sch ods fw six |
| 6 | PRG_A7_6 | D42 | PL7 | sch ods fw six |
| 7 | PRG_A6_7 | D43 | PL6 | sch ods fw six |
| 8 | PRG_A5_8 | D44 | PL5 | sch ods fw six |
| 9 | PRG_A4_9 | D45 | PL4 | sch ods fw six |
| 10 | PRG_A3_10 | D46 | PL3 | sch ods fw six |
| 11 | PRG_A2_11 | D47 | PL2 | sch ods fw six |
| 12 | PRG_A1_12 | D48 | PL1 | sch ods fw six |
| 13 | PRG_A0_13 | D49 | PL0 | sch ods fw six |
| 14 | PRG_RW_14 | A7 | PF7 | sch ods fw six |
| 15 | IRQ_15 | A6 | PF6 | sch ods fw six |
| 16 | GND_16 | GND | - | sch six |
| 17 | CHR_RD_17 | A5 | PF5 | sch ods fw six |
| 18 | CIRAM_A10_18 | D35 | PC2 | sch ods fw six |
| 19 | CHR_A6_19 | D43 | PL6 | sch ods fw six |
| 20 | CHR_A5_20 | D44 | PL5 | sch ods fw six |
| 21 | CHR_A4_21 | D45 | PL4 | sch ods fw six |
| 22 | CHR_A3_22 | D46 | PL3 | sch ods fw six |
| 23 | CHR_A2_23 | D47 | PL2 | sch ods fw six |
| 24 | CHR_A1_24 | D48 | PL1 | sch ods fw six |
| 25 | CHR_A0_25 | D49 | PL0 | sch ods fw six |
| 26 | CHR_D0_26 | A8 | PK0 | sch ods fw six |
| 27 | CHR_D1_27 | A9 | PK1 | sch ods fw six |
| 28 | CHR_D2_28 | A10 | PK2 | sch ods fw six |
| 29 | CHR_D3_29 | A11 | PK3 | sch ods fw six |
| 30 | 5V_30 | 5V (fixo) | - | sch six |
| 31 | VCC_31 | 5V (fixo) | - | sch six |
| 32 | M2_32 | A0 | PF0 | sch ods fw six |
| 33 | PRG_A12_33 | D26 | PA4 | sch ods fw six |
| 34 | PRG_A13_34 | D27 | PA5 | sch ods fw six |
| 35 | PRG_A14_35 | D28 | PA6 | sch ods fw six |
| 36 | PRG_D7_36 | A15 | PK7 | sch ods fw six |
| 37 | PRG_D6_37 | A14 | PK6 | sch ods fw six |
| 38 | PRG_D5_38 | A13 | PK5 | sch ods fw six |
| 39 | PRG_D4_39 | A12 | PK4 | sch ods fw six |
| 40 | PRG_D3_40 | A11 | PK3 | sch ods fw six |
| 41 | PRG_D2_41 | A10 | PK2 | sch ods fw six |
| 42 | PRG_D1_42 | A9 | PK1 | sch ods fw six |
| 43 | PRG_D0_43 | A8 | PK0 | sch ods fw six |
| 44 | PRG_CE_44 | A1 | PF1 | sch ods fw six |
| 45 | EXP_45 | NC (sem ligação) | - | sch |
| 46 | EXP_46 | NC (sem ligação) | - | sch |
| 47 | CHR_WR_47 | A2 | PF2 | sch ods fw six |
| 48 | CIRAM_CE_48 | A3 | PF3 | sch ods fw six |
| 49 | CHR_/A13_49 | A4 | PF4 | sch ods fw six |
| 50 | CHR_A7_50 | D42 | PL7 | sch ods fw six |
| 51 | CHR_A8_51 | D22 | PA0 | sch ods fw six |
| 52 | CHR_A9_52 | D23 | PA1 | sch ods fw six |
| 53 | CHR_A10_53 | D24 | PA2 | sch ods fw six |
| 54 | CHR_A11_54 | D25 | PA3 | sch ods fw six |
| 55 | CHR_A12_55 | D26 | PA4 | sch ods fw six |
| 56 | CHR_A13_56 | D27 | PA5 | sch ods fw six |
| 57 | CHR_D7_57 | A15 | PK7 | sch ods fw six |
| 58 | CHR_D6_58 | A14 | PK6 | sch ods fw six |
| 59 | CHR_D5_59 | A13 | PK5 | sch ods fw six |
| 60 | CHR_D4_60 | A12 | PK4 | sch ods fw six |

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
| B32 | /CART_B32 | NC (sem ligação) | - | sch |

## GBA (ref. `J10` em `main_pcb_hw5`, 34 pinos)

| pino do slot | sinal | net / pino Arduino | porta/bit AVR | fonte |
|---|---|---|---|---|
| 1 | VCC_1 | 3V3 (regulador U3) | - | sch |
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

## Placa principal — o que o HW5 liga além dos slots (referência)

| item | pino Arduino | fonte |
|---|---|---|
| Si5351 SDA / SCL | D20 (PD1) / D21 (PD0) | sch main J7.3/J7.4 + ods |
| Si5351 CLK0 / CLK1 / CLK2 | 3 saídas do Si5351 (não vão ao Mega); CLK0→SNES 21.477MHz (pino 1), CLK1→SNES CPU clock (57), CLK2→CIC clock (56) e PIC pino 2 | sch |
| LED de status (cátodo via 220Ω, ânodo em VCC; **ativo em nível baixo**) | D38 (PD7) | sch main D1/R1 + fw `statusLED()` |
| Pull-up 1kΩ VCC→D7 (linha /IRQ do SNES) | D7 (PH4) | sch six_slot R1 + ods `D7 (1K Pullup)` |
| Reset do Mega | RESET → J4.35 (adaptadores não usam) | sch main |

## CIC SNES (PIC12F629 DIP-8) — `cic_adapter/PIC_adapter`

| pino do PIC | net | liga em | fonte |
|---|---|---|---|
| 1 | VCC | 5V | sch(PIC_adapter + six_slot JCIC1) + ods(snesCIC) + fw SNES.ino (PG0/PG1) |
| 2 | CLK2 | Si5351 CLK2 (mesma net do SNES pino 56) | sch(PIC_adapter + six_slot JCIC1) + ods(snesCIC) + fw SNES.ino (PG0/PG1) |
| 3 | D41 | Mega D41 (PG0) — Reset Out Host | sch(PIC_adapter + six_slot JCIC1) + ods(snesCIC) + fw SNES.ino (PG0/PG1) |
| 4 | D40 | Mega D40 (PG1) — Reset In | sch(PIC_adapter + six_slot JCIC1) + ods(snesCIC) + fw SNES.ino (PG0/PG1) |
| 5 | CIC RESET | SNES slot pino 25 (CIC_in_data p7) | sch(PIC_adapter + six_slot JCIC1) + ods(snesCIC) + fw SNES.ino (PG0/PG1) |
| 6 | CIC DATA 1 | SNES slot pino 24 (CIC_out_data p1) | sch(PIC_adapter + six_slot JCIC1) + ods(snesCIC) + fw SNES.ino (PG0/PG1) |
| 7 | CIC DATA 0 | SNES slot pino 55 (CIC_data_out p2) | sch(PIC_adapter + six_slot JCIC1) + ods(snesCIC) + fw SNES.ino (PG0/PG1) |
| 8 | GND | GND | sch(PIC_adapter + six_slot JCIC1) + ods(snesCIC) + fw SNES.ino (PG0/PG1) |

Nota: o PIC12F629 usa a pinagem do `JCIC1` (1=VCC, 2=CLK2, 3=D41, 4=D40, 5=RESET, 6=DATA1, 7=DATA0, 8=GND).

## Pinos do slot sem ligação no OSCR (mantidos sem ligação)

- SNES: pino 31 (Left Audio), pino 62 (Right Audio).
- NES: `EXP_0..EXP_9` (16-20, 51-55), `Security1..4` (70, 71, 34, 35).
- Famicom/Mega Drive: ver pinos ausentes na tabela de cada sistema.

