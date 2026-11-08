# Mapa de pinos — placa nes (só NES) → pino do Arduino Mega 2560

> Recorte de `boards/16_and_8_bits/docs/pinmap.md` (mesma pinagem do OSCR HW5): só a tabela do NES e o Si5351. Sem SNES, Famicom, Mega Drive e GBA; sem PIC (CIC), sem R2 e sem regulador de 3,3 V.

**FONTE DA VERDADE da placa `nes`.** Recorte à mão do pinmap da `16_and_8_bits` (que vem de `tools/gen_pinmap.py`); `tools/check_netlist.py --board nes` confere o esquemático contra este arquivo.

Cruza três fontes do OSCR HW5 (repositório `sanni/cartreader`, clone em `vendor/oscr/legacy/`):

- `ods` = `pinout.ods` (coluna do sistema)
- `sch` = esquemático KiCad do adaptador (`hardware-v1.1/nes_adapter`) + `main_pcb_hw5`
- `six` = `hardware/six_slot_adapter` (mesma net no mesmo pino do header)
- `fw`  = porta/bit AVR usado no `NES.ino`

Marcas: `ods`/`sch`/`six`/`fw` = fonte concorda; `-` = fonte não cobre (ver nota); `!` = fonte discorda (ver `docs/decisoes.md`). `fw` é checado só no nível da porta/bit (o firmware não usa nomes de sinal).

Pinos do Mega **não usados** pela placa: `D0`/`D1` (serial USB, nunca ligar a slot), `D10..D13`, `D18`, `D19`, `D39`, `D50..D53`, e os que só outros sistemas usam (`D2..D9`, `D14..D17`, `D29..D34`, `D36`, `D37`, `D40`, `D41`).

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

## Placa principal — o que a placa nes liga além do slot

| item | pino Arduino | fonte |
|---|---|---|
| Si5351 SDA / SCL | D20 (PD1) / D21 (PD0) | sch main J7.3/J7.4 + ods |
| Si5351 CLK0 | saída do Si5351 (não vai ao Mega); vai ao pino 37 (CLK) do slot NES. CLK1 e CLK2 ficam sem uso | sch |
| LED de status (cátodo via 220Ω, ânodo em VCC; **ativo em nível baixo**) | D38 (PD7) | sch main D1/R1 + fw `statusLED()` |

## Pinos do slot sem ligação no OSCR (mantidos sem ligação)

- NES: `EXP_0..EXP_9` (16-20, 51-55), `Security1..4` (70, 71, 34, 35).
