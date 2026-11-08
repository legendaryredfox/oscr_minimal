# Mapa de pinos — slot N64 → pino do Arduino Mega 2560

**FONTE DA VERDADE.** Gerado por `tools/boards/n64/gen_pinmap.py` (não edite à mão). Mesmas fontes e convenções de `boards/16_and_8_bits/docs/pinmap.md`:

- `ods` = `pinout.ods` (colunas `N64 ROM` e `N64 EEP`)
- `sch` = `hardware/n64_adapter` (ref. `J1`)
- `six` = `hardware/six_slot_adapter` (ref. `N64`; mesma net no mesmo pino do header)
- `fw`  = porta/bit AVR usado em `legacy/Cart_Reader/N64.ino`

Marcas: `-` = fonte não cobre; `!` = fonte discorda. `fw` é checado só no nível da porta/bit.

**Tensão:** o cartucho N64 é de 3,3 V. Os pinos `VCC` (9, 17, 34, 42) vão a 3,3 V; o Mega continua com sinais de 5 V, como o OSCR HW5 faz no modo 3V e como esta família já faz no slot GBA (D3, D22). Nenhuma decisão nova de tensão foi tomada: **aguarda aprovação** (ver `README.md`).

Pinos `12V` (13 e 38): o adaptador do OSCR os deixa sem ligação (o six-slot liga ao +12V do HW5, que não existe aqui). Ficam sem ligação.

## N64 (ref. `J1` em `n64_adapter`, 50 pinos)

| pino do slot | sinal | net / pino Arduino | porta/bit AVR | fonte |
|---|---|---|---|---|
| 1 | GND_1 | GND | - | sch six |
| 2 | GND_2 | GND | - | sch six |
| 3 | AD15_3 | A15 | PK7 | sch ods fw six |
| 4 | AD14_4 | A14 | PK6 | sch ods fw six |
| 5 | AD13_5 | A13 | PK5 | sch ods fw six |
| 6 | GND_6 | GND | - | sch six |
| 7 | AD12_7 | A12 | PK4 | sch ods fw six |
| 8 | /WRITE_8 | D8 | PH5 | sch ods fw six |
| 9 | VCC_9 | 3V3 (regulador) | - | sch six |
| 10 | /READ_10 | D9 | PH6 | sch ods fw six |
| 11 | AD11_11 | A11 | PK3 | sch ods fw six |
| 12 | AD10_12 | A10 | PK2 | sch ods fw six |
| 13 | 12V_13 | NC (sem ligação) | - | sch |
| 14 | NC_14 | NC (sem ligação) | - | sch |
| 15 | AD9_15 | A9 | PK1 | sch ods fw six |
| 16 | AD8_16 | A8 | PK0 | sch ods fw six |
| 17 | VCC_17 | 3V3 (regulador) | - | sch six |
| 18 | CIC_to_PIF_18 | NC (sem ligação) | - | sch |
| 19 | EEPROM_CLK_19 | CLK1 (Si5351) | (Si5351) | sch ods six |
| 20 | RESET_20 | D17 | PH0 | sch ods fw six |
| 21 | EEPROM_DATA_21 | D7 | PH4 | sch ods fw six |
| 22 | GND_22 | GND | - | sch six |
| 23 | GND_23 | GND | - | sch six |
| 24 | L_AUDIO_24 | NC (sem ligação) | - | sch |
| 25 | GND_25 | GND | - | sch six |
| 26 | GND_26 | GND | - | sch six |
| 27 | GND_27 | GND | - | sch six |
| 28 | AD0_28 | A0 | PF0 | sch ods fw six |
| 29 | AD1_29 | A1 | PF1 | sch ods fw six |
| 30 | AD2_30 | A2 | PF2 | sch ods fw six |
| 31 | GND_31 | GND | - | sch six |
| 32 | AD3_32 | A3 | PF3 | sch ods fw six |
| 33 | ALE_L_33 | D37 | PC0 | sch ods fw six |
| 34 | VCC_34 | 3V3 (regulador) | - | sch six |
| 35 | ALE_H_35 | D36 | PC1 | sch ods fw six |
| 36 | AD4_36 | A4 | PF4 | sch ods fw six |
| 37 | AD5_37 | A5 | PF5 | sch ods fw six |
| 38 | 12V_38 | NC (sem ligação) | - | sch |
| 39 | NC_39 | NC (sem ligação) | - | sch |
| 40 | AD6_40 | A6 | PF6 | sch ods fw six |
| 41 | AD7_41 | A7 | PF7 | sch ods fw six |
| 42 | VCC_42 | 3V3 (regulador) | - | sch six |
| 43 | PIF_to_CIC_43 | NC (sem ligação) | - | sch |
| 44 | R4300_CLK_44 | NC (sem ligação) | - | sch |
| 45 | NMI_45 | NC (sem ligação) | - | sch |
| 46 | Video_CLK_46 | NC (sem ligação) | - | sch |
| 47 | GND_47 | GND | - | sch six |
| 48 | GND_48 | GND | - | sch six |
| 49 | R_Audio_49 | NC (sem ligação) | - | sch |
| 50 | GND_50 | GND | - | sch six |

## Fora do slot

| item | pino Arduino | fonte |
|---|---|---|
| Si5351 CLK1 → EEPROM_CLK (pino 19) | CLK1 (2 MHz, `set_freq(200000000, CLK1)`) | sch + fw `N64.cpp` (`ENABLE_CLOCKGEN`) |
| EEPROM_DATA (pino 21) | D7 (PH4), pull-up de 1 kΩ para o 3,3 V (R1 do adaptador) | sch + ods |
| Si5351 SDA / SCL | D20 / D21 | igual às outras placas |
| Sem Si5351 no firmware | `PH1` (D16) vira saída em nível alto; o adaptador não leva D16 ao slot, então o EEPROM não é lido | fw `N64.cpp` |

Pinos do slot sem ligação no OSCR (mantidos): 12V (13, 38), NC (14, 39), CIC_to_PIF (18), L_AUDIO (24), PIF_to_CIC (43), R4300_CLK (44), NMI (45), Video_CLK (46), R_AUDIO (49).

