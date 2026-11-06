# Placa perfurada: tabelas geradas por `scripts/perfboard.py`

Furo = letra da linha + numero da coluna (ver o desenho `perfboard.png`). Vale para uma placa de 22 colunas x 14 linhas ou maior.

## Pecas

| Ref | Peca | Furos |
|---|---|---|
| J3 | Barra de 6 pinos macho (vai ao Uno por cabos Dupont) | GND: A5, D2: A6, D4: A7, D7: A8, A1: A9, A5: A10 |
| J1 | Borne de parafuso 5,08 mm (entrada de 13 V) | 1: C2, 2: C4 |
| U2 | Soquete DIP-8 (entalhe para cima = pino 1 em cima a esquerda) | 1: D13, 2: E13, 3: F13, 4: G13, 8: D16, 7: E16, 6: F16, 5: G16 |
| C1 | 100 nF | 1: D11, 2: F11 |
| R1 | 10 k | 1: I6, 2: I10 |
| R4 | 1 k | 1: K6, 2: K10 |
| D2 | LED vermelho (perna curta = catodo = K) | A: K12, K: K13 |
| Q1 | BC547 (C, B, E da esquerda para a direita, lado chato para cima) | C: I13, B: I14, E: I15 |
| R2 | 4,7 k | 1: K18, 2: K14 |
| R3 | 220 | 1: C21, 2: G21 |
| D3 | LED amarelo (perna curta = catodo = K) | A: H21, K: I21 |

## Fios (todos isolados, no lado da solda; solde nos furos das pontas e dobre nos furos indicados)

| Net | Caminho |
|---|---|
| GND | A5 > C5 > N5 |
| GND | C4 > C5 |
| GND | N5 > N11 > N13 > N15 > N19 > N21 |
| GND | F11 > N11 |
| GND | K13 > N13 |
| GND | I15 > N15 |
| GND | D16 > D19 > N19 |
| GND | I21 > N21 |
| VDD | A6 > D6 > D11 > D13 |
| CLK | A7 > C7 > C18 > F18 > F16 |
| DAT | A8 > B8 > B17 > E17 > E16 |
| VPP_CTL | A9 > L9 > L18 > K18 |
| BASE | I14 > K14 |
| MCLR | G13 > I13 |
| MCLR | I10 > I13 |
| V13 | C2 > E2 |
| V13 | E2 > I2 |
| V13 | I2 > I6 > K6 |
| LED13_A | K10 > K12 |
| LED_ATIVO | A10 > A21 > C21 |
| LEDA_A | G21 > H21 |
