# Mapa de pinos — placa famicom (só Famicom) → pino do Arduino Mega 2560

> Recorte de `boards/16_and_8_bits/docs/pinmap.md` (mesma pinagem do OSCR HW5): só a tabela do Famicom. Sem SNES, NES, Mega Drive e GBA; sem Si5351 (o slot Famicom não tem pino de clock), sem PIC (CIC), sem R2 e sem regulador de 3,3 V.

**FONTE DA VERDADE da placa `famicom`.** Recorte à mão do pinmap da `16_and_8_bits` (que vem de `tools/gen_pinmap.py`); `tools/check_netlist.py --board famicom` confere o esquemático contra este arquivo.

Cruza três fontes do OSCR HW5 (repositório `sanni/cartreader`, clone em `vendor/oscr/legacy/`):

- `ods` = `pinout.ods` (o Famicom usa a coluna do NES)
- `sch` = esquemático KiCad do adaptador (`hardware-v1.1/famicom_adapter`) + `main_pcb_hw5`
- `six` = `hardware/six_slot_adapter` (mesma net no mesmo pino do header)
- `fw`  = porta/bit AVR usado no `NES.ino` (o Famicom é lido pelo mesmo código do NES)

Marcas: `ods`/`sch`/`six`/`fw` = fonte concorda; `-` = fonte não cobre (ver nota); `!` = fonte discorda (ver `docs/decisoes.md`). `fw` é checado só no nível da porta/bit (o firmware não usa nomes de sinal).

Pinos do Mega **não usados** pela placa: `D0`/`D1` (serial USB, nunca ligar a slot), `D10..D13`, `D18`, `D19`, `D39`, `D50..D53`, `D20`/`D21` (I²C do Si5351, que não existe aqui) e os que só outros sistemas usam.

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

## Placa principal — o que a placa famicom liga além do slot

| item | pino Arduino | fonte |
|---|---|---|
| LED de status (cátodo via 220Ω, ânodo em VCC; **ativo em nível baixo**) | D38 (PD7) | sch main D1/R1 + fw `statusLED()` |

## Pinos do slot sem ligação no OSCR (mantidos sem ligação)

- Famicom: `EXP_45` e `EXP_46`. Os pinos 30 (`5V_30`) e 31 (`VCC_31`) vão ambos ao 5V.
