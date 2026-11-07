# n64 — componentes que podem ser retirados e o que se perde

Tabela a partir de `pinmap.md` e de `firmware/oscr/src/cores/N64.cpp`; vale a mesma ressalva das outras placas: **nada testado em hardware**.

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| Regulador 3,3 V (MCP1700) + 2 capacitores de 1 µF | **Não** | O slot N64 não tem outra fonte; sem ele, nada lê | Todos |
| Si5351 (`CLK1` = clock de 2 MHz da EEPROM, pino 19) | Sim, se só ROM interessa | Sem o clock, o firmware põe a linha em nível alto e **a EEPROM não é lida nem gravada** (`N64.cpp`, ramo sem `ENABLE_CLOCKGEN`) | Jogos com save em **EEPROM**: p. ex. Super Mario 64 (4K), Mario Kart 64 (4K) e Banjo-Kazooie (16K). Jogos com SRAM, FlashRAM ou Controller Pak não dependem; a ROM de todos lê |
| Pull-up de 1 kΩ no D7 (`EEPROM_DATA`) | Não, se houver Si5351 | EEPROM instável ou ilegível | Os mesmos de EEPROM |
| LED de status, capacitores de 100 nF, 470 µF | LED sim; capacitores não recomendado | LED: indicação. Capacitores: leitura errada possível | — |

Chips de segurança do N64 (CIC) ficam no cartucho e na própria placa do console; o dumper não os usa (pinos 18 e 43 sem ligação).

## Bloco de troca de cartucho (v1.1)

| Peça | Opcional? | O que se perde sem ela |
|---|---|---|
| Q1, R3, R4 | **Não** (sem o Q1 o 5V dos slots não chega: pôr uma ponte do 5V ao `+5V_CART` se quiser abrir mão do `POWER`) | `POWER on/off` em software; a troca segura do cartucho |
| R5, D2 (LED verde) | Sim | só a indicação visual de 5V dos slots |
| Q2, R6, R7 | Sim | descarga rápida do rail: o firmware espera 2 s em vez de 500 ms |
| Q3, R8, R9, R10, D3 (sensor e LED amarelo) | Sim | o LED amarelo e a leitura do D53 (`POWER_RESP.rail` fica `0xFF`) |

Nenhuma peça do bloco afeta quais cartuchos podem ser lidos; todas atuam só na troca de cartucho e no ciclo de energia do SA-1.
