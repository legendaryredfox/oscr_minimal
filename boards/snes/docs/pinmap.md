# Mapa de pinos — placa snes (só SNES) → pino do Arduino Mega 2560

> Recorte de `boards/16_bits/docs/pinmap.md` (mesma pinagem do OSCR HW5): só a tabela do SNES, o Si5351 e o CIC (PIC12F629). Sem Mega Drive, NES, Famicom e GBA; sem regulador de 3,3 V.

**FONTE DA VERDADE da placa `snes`.** Recorte à mão do pinmap da `16_bits` (que vem de `tools/gen_pinmap.py`); `tools/check_netlist.py --board snes` confere o esquemático contra este arquivo.

Cruza três fontes do OSCR HW5 (repositório `sanni/cartreader`, clone em `vendor/oscr/legacy/`):

- `ods` = `pinout.ods` (coluna do sistema; Famicom usa a coluna NES)
- `sch` = esquemático KiCad do adaptador (`hardware/<sistema>_adapter`) + `main_pcb_hw5`
- `six` = `hardware/six_slot_adapter` (mesma net no mesmo pino do header; não existe para o GBA)
- `fw`  = porta/bit AVR usado no `.ino` do sistema (`SNES.ino`, `NES.ino`, `MD.ino`, `GBA.ino`)

Convenção: a coluna **Arduino** é o nome da net no HW5 (`A0..A15`, `D2..D53`, `CLK0..2`). Na placa HW5, cada net vai do Mega ao header J3/J4 (pino de mesmo número no adaptador) e daí ao slot. Neste projeto o slot liga direto ao pino do Mega.

Marcas: `ods`/`sch`/`six`/`fw` = fonte concorda; `-` = fonte não cobre (ver nota); `!` = fonte discorda (ver `docs/decisoes.md`). `fw` é checado só no nível da porta/bit (o firmware não usa nomes de sinal).

Pinos do Mega **não usados** por nenhum slot: `D0`/`D1` (serial USB; o HW5 leva ao header mas os adaptadores deixam sem ligação), `D10..D13`, `D18`, `D19`, `D39`, `D51..D53` (`D50` não é usado nesta placa; `D39` é o pino do botão no `main.cpp` do OSCR e não deve ser usado). `D0`/`D1` nunca podem ir a um slot.


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

