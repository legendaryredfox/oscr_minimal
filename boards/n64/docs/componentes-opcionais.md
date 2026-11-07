# n64 — componentes que podem ser retirados e o que se perde

Tabela a partir de `pinmap.md` e de `firmware/oscr/src/cores/N64.cpp`; vale a mesma ressalva das outras placas: **nada testado em hardware**.

| Peça | Retirar? | O que deixa de funcionar | Jogos afetados |
|---|---|---|---|
| Regulador 3,3 V (MCP1700) + 2 capacitores de 1 µF | **Não** | O slot N64 não tem outra fonte; sem ele, nada lê | Todos |
| Si5351 (`CLK1` = clock de 2 MHz da EEPROM, pino 19) | Sim, se só ROM interessa | Sem o clock, o firmware põe a linha em nível alto e **a EEPROM não é lida nem gravada** (`N64.cpp`, ramo sem `ENABLE_CLOCKGEN`) | Jogos com save em **EEPROM**: p. ex. Super Mario 64 (4K), Mario Kart 64 (4K) e Banjo-Kazooie (16K). Jogos com SRAM, FlashRAM ou Controller Pak não dependem; a ROM de todos lê |
| Pull-up de 1 kΩ no D7 (`EEPROM_DATA`) | Não, se houver Si5351 | EEPROM instável ou ilegível | Os mesmos de EEPROM |
| LED de status, capacitores de 100 nF, 470 µF | LED sim; capacitores não recomendado | LED: indicação. Capacitores: leitura errada possível | — |

Chips de segurança do N64 (CIC) ficam no cartucho e na própria placa do console; o dumper não os usa (pinos 18 e 43 sem ligação).
