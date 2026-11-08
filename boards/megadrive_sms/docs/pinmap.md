# Mapa de pinos — placa `megadrive_sms` (Mega Drive + Master System)

**Estado: pinagem aprovada pelo usuário em 2026-11-08 (pendências resolvidas abaixo).** Gerado por `tools/boards/megadrive_sms/gen_pinmap_sms.py` (seção SMS) e copiado da seção Mega Drive de `boards/16_and_8_bits/docs/pinmap.md` (fonte da verdade do Mega Drive).

Fontes do Master System (cruzadas):

- `sch` = `vendor/oscr/legacy/hardware/mastersystem_adapter` (J1/J2 = os headers do Mega, `U1` = slot de 50 pinos a 2,54 mm). As nets são os nomes de pino do Arduino (`A0..A15`, `D2..D53`).
- `ods` = `pinout.ods`, coluna "Master System".
- `fw` = `vendor/oscr/firmware/src/cores/SMS.cpp` (modos Raphnet e Retron, que usam a pinagem do adaptador do OSCR): endereço `PORTF` (A0-A7) e `PORTK` (A8-A14), A15 / M0-7 em `PH3`, dados `PORTC`, WR `PH5`, OE/RD `PH6`, CE `PL1`, RESET `PH0`. O modo Retrode usa outros pinos (adaptador de terceiros, fora desta placa).

Os dois slots ficam em paralelo nos mesmos pinos do Mega, como no `six_slot_adapter`. **Um cartucho por vez.** Pinos compartilhados entre os dois slots: `A0..A14`, `D30..D37` (dados de 8 bits), `D6` (`/CE_0` no Mega Drive, A15/M0-7 no SMS), `D8`, `D9`, `D17`, `D48`. Só um slot tem cartucho, o outro fica em alta impedância.

## Divergências e decisões

1. **Pino 47 do SMS (Clock): sem ligação** (decisão de 2026-11-08, depois de pesquisa). O esquemático do adaptador do OSCR liga ao `CLK0` e o `pinout.ods` diz `D16`, mas nem `SMS.cpp` (novo) nem `SMS.ino` (legado) usam clock. O smspower.org descreve o pino como saída do console ("Not clock", 3,5 MHz), opcional nos adaptadores. Esta placa não tem Si5351 (como a `megadrive`). Se algum cartucho precisar, é por jumper no adaptador, não na placa.
2. **Pinos do slot SMS sem ligação no OSCR** (mantidos sem ligação): 3, 5, 34, 37 a 45, 47 a 50.
3. **Slot SMS 50p, 2,54 mm, 2 × 25:** o wiki do OSCR (Parts-needed) lista "50 pin 2.54mm Master System slot (2x25)" e o link de compra é o mesmo item de AliExpress do slot Mega Drive de 64p e do Famicom de 60p. O footprint é o `SMS_Slot` do OSCR (CC BY 4.0, 50 pads de 1,524 mm, furo 0,762 mm, fileiras a 5,08 mm), em `boards/_lib/`. O corpo (courtyard 12 mm de largura) é estimado como nos outros slots (D17); **medir o slot recebido**.
4. **Game Gear e SG-1000: por adaptador, fora desta placa.** Pesquisa (2026-11-08): o OSCR os suporta por adaptadores de terceiros (Retrode, Retron 3in1, Raphnet), comerciais; não achei adaptador com arquivos abertos (o `oscartreader/oscr-hardware` está vazio; o `sanni/cartreader` não tem pasta de Game Gear). Mark III usa o slot SMS (modo "SMS/MarkIII Raphnet" do firmware).
5. **Versão 1.0: sem o bloco de troca de cartucho** (decisão do usuário): a v1.0 de qualquer placa é a mais barata que funciona; para trocar de cartucho, desligar o USB.

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

## Master System (ref. `U1` em `mastersystem_adapter`, 50 pinos)

| pino do slot | sinal | net / pino Arduino | porta/bit AVR | fonte |
|---|---|---|---|---|
| 1 | 5V | 5V (fixo) | - | sch |
| 2 | WR | D8 | PH5 | sch ods fw |
| 3 | MReq | NC (sem ligação) | - | sch |
| 4 | RD | D9 | PH6 | sch ods fw |
| 5 | M8-B | NC (sem ligação) | - | sch |
| 6 | A14 | A14 | PK6 | sch ods fw |
| 7 | A13 | A13 | PK5 | sch ods fw |
| 8 | A8 | A8 | PK0 | sch ods fw |
| 9 | A9 | A9 | PK1 | sch ods fw |
| 10 | A11 | A11 | PK3 | sch ods fw |
| 11 | M0-7 | D6 | PH3 | sch ods fw |
| 12 | A10 | A10 | PK2 | sch ods fw |
| 13 | CE | D48 | PL1 | sch ods fw |
| 14 | D7 | D30 | PC7 | sch ods fw |
| 15 | D6 | D31 | PC6 | sch ods fw |
| 16 | D5 | D32 | PC5 | sch ods fw |
| 17 | D4 | D33 | PC4 | sch ods fw |
| 18 | D3 | D34 | PC3 | sch ods fw |
| 19 | GND | GND | - | sch |
| 20 | GND | GND | - | sch |
| 21 | GND | GND | - | sch |
| 22 | D2 | D35 | PC2 | sch ods fw |
| 23 | D1 | D36 | PC1 | sch ods fw |
| 24 | D0 | D37 | PC0 | sch ods fw |
| 25 | A0 | A0 | PF0 | sch ods fw |
| 26 | A1 | A1 | PF1 | sch ods fw |
| 27 | A2 | A2 | PF2 | sch ods fw |
| 28 | A3 | A3 | PF3 | sch ods fw |
| 29 | A4 | A4 | PF4 | sch ods fw |
| 30 | A5 | A5 | PF5 | sch ods fw |
| 31 | A6 | A6 | PF6 | sch ods fw |
| 32 | A7 | A7 | PF7 | sch ods fw |
| 33 | A12 | A12 | PK4 | sch ods fw |
| 34 | CONT | NC (sem ligação) | - | sch |
| 35 | 5V | 5V (fixo) | - | sch |
| 36 | A15 | D6 | PH3 | sch ods fw |
| 37 | M1 | NC (sem ligação) | - | sch |
| 38 | IOReq | NC (sem ligação) | - | sch |
| 39 | Refresh | NC (sem ligação) | - | sch |
| 40 | Halt | NC (sem ligação) | - | sch |
| 41 | Wait | NC (sem ligação) | - | sch |
| 42 | Int | NC (sem ligação) | - | sch |
| 43 | JyDs | NC (sem ligação) | - | sch |
| 44 | BusReq | NC (sem ligação) | - | sch |
| 45 | BusAck | NC (sem ligação) | - | sch |
| 46 | Reset | D17 | PH0 | sch ods fw |
| 47 | Clock | NC (sem ligação; sch: CLK0, ods: D16, ver divergência 1) | - | sch ! ods |
| 48 | JRead | NC (sem ligação) | - | sch |
| 49 | MC-F | NC (sem ligação) | - | sch |
| 50 | NMI | NC (sem ligação) | - | sch |
