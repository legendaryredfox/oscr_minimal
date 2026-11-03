# Limites do suporte a NES / Famicom

Levantamento de 2026-11-03, feito lendo `vendor/oscr/legacy/Cart_Reader/NES.ino` (`readPRG`, linhas ~2011-3430, e `readCHR`, ~3436 em diante) e `firmware/oscr_serial/oscr_carts_nes.cpp`. Tudo aqui é leitura de código: **nada foi testado em hardware**, e os modelos dos testes (`SimMapper`) são a minha leitura dos registradores, não os chips.

A leitura do `readCHR` parou por volta do mapper 19 (a lista de CHR dos mappers 21 e acima **não foi lida**). Onde isso importa, está marcado.

## 1. O que o firmware faz hoje

Mappers de ROM: 0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 33, 48, 66, 69, 70, 71, 75, 78, 79, 87, 118, 206. São 22 de mais de 100 que o OSCR trata. Saves (PRG-RAM de 8 KB, mais 16/32 KB no 1 e no 5): mappers 1, 4, 5, 69 e 118. Detalhes: `docs/protocolo.md` e D50, D57.

## 2. Limites de tamanho dos mappers já suportados

Vêm do tamanho do registrador de banco e estão em `probe_nes`. Acima deles o firmware responde `ERRO 0x0002` em vez de truncar em silêncio.

| Mapper | PRG máx. | CHR máx. | Observação |
|---|---|---|---|
| 1 (MMC1) | 256 KB | 128 KB | acima de 256 KB (SUROM e afins) não feito: o firmware recusa |
| 4 (MMC3) | 512 KB | 256 KB | registradores de 8 bits (CHR de 1 KB) |
| 5 (MMC5) | 1 MB | sem teto no código | modo 3 de PRG e modo 0 de CHR; o `$5130` fica em 0 (ver D50) |
| 9 (MMC2) | 128 KB | 128 KB | |
| 10 (MMC4) | 256 KB | 128 KB | |
| 11 | 128 KB | 128 KB | PRG múltiplo de 32 KB |
| 33, 48 | 256 KB | 256 KB | |
| 66 | 128 KB | 32 KB | |
| 69 (FME-7) | 512 KB | 256 KB | |
| 70 | 256 KB | 128 KB | |
| 75 (VRC1) | 128 KB | 128 KB | |
| 78 | 128 KB | 128 KB | |
| 79 | 64 KB | 64 KB | |
| 87 | 32 KB | 32 KB | |
| 118 | 512 KB | 256 KB | |
| 206 | 128 KB | 64 KB | |
| 2, 7, 71 | n/d | 0 | só com CHR-RAM |

Regras gerais: PRG múltiplo de 16 KB, CHR múltiplo de 8 KB. Mappers 79, 87, 78, 75, 70, 33, 48, 118 e 206 exigem CHR-ROM.

## 3. Limites do formato e do jeito de operar

- O cartucho de NES não tem cabeçalho: o usuário informa `mapper`, `prg_kb` e `chr_kb` (a menos que seja NROM, que se detecta por espelhamento). Informar errado dá um arquivo errado, e o CRC32 não avisa; só a comparação com o No-Intro mostra.
- O iNES gerado é sintético: só tem tamanhos e mapper (nibbles dos bytes 6 e 7). **Sem** espelhamento, bateria, submapper nem NES 2.0.
- CHR-RAM não é lida (não há o que ler).
- Cada leitura usa o `NesBus` com a sequência de porta copiada do OSCR (`oscr_avr_buses.h`): o teste no PC confere as sequências, mas **não** os tempos (M2, /ROMSEL, ~33 ns na escrita segura de D57).
- Só um cartucho por vez, e os que mantêm estado entre operações (MMC1, MMC5, VRC) são reinicializados em `nes_setup_mapper`; o OSCR assume alimentação nova a cada leitura.

## 4. O que o OSCR faz e o firmware ainda não, por motivo

### 4.1 Falta uma primitiva no `NesBus`

| Mapper | O que o OSCR usa | O que falta |
|---|---|---|
| 34 (BxROM/NINA-001) | `delay(200)` depois de cada troca de banco ("NINA seems slow to switch banks") | espera em milissegundos no `NesBus` (o `SnesBus` tem `wait_ms`; o `NesBus` e o `GbBus` não) |
| 60 | `delay(500)` depois de cada escrita | idem |
| 57 | `write_prg_pulsem2` e `dumpPRG_pulsem2` (pulsa M2 de outro jeito) | variante de leitura/escrita com pulso de M2 |
| 59 | `write_reg_m59` | escrita própria |
| 19, 532 (Namco 163) | `write_ram_byte`, 64 escritas de inicialização no registrador | escrita na RAM/registrador sem conflito |
| 67 | `write_reg_byte` em `$F800` | já existe como `reg_write_safe`: só falta ler a parte de CHR |

### 4.2 Depende de variante, de submapper ou de ligação dos pinos

- **VRC2/VRC4 (21, 22, 23, 25) e VRC6 (24, 26):** os registradores mudam de endereço conforme a placa (linhas A0/A1 ligadas de formas diferentes). O OSCR resolve com escritas "para ver se pega" (`$9002`, `$9008`, `$9005`, `$9004`) e escolhe pelo número do mapper. Sem submapper no protocolo, o firmware não sabe qual variante o usuário tem. Não li a parte de CHR desses mappers.
- **16/159 (Bandai FCG):** o OSCR escreve em dois endereços (`$6000` e `$8000`) para cobrir os submappers 4 e 5. As placas com EEPROM serial (save) são outro assunto: o save desses mappers usa I²C.
- **80/82 (Taito X1-005/017), 207:** o PRG usa `$7EFA`; o OSCR avisa que o 207 "às vezes precisa de power cycle".

### 4.3 Clones de MMC3 com registradores de bloco externo

Mappers 12, 37, 44, 45, 47, 49, 52, 115, 116, 126, 134, 176, 224, 245, 268, 315, 351, 366, 422, 534, 995-999. O OSCR trata o PRG e o CHR como MMC3 e escolhe o bloco externo (A18-A21) com uma escrita específica por mapper (`$6000`, `$6800`, `$5000`, `$4100`, `$A001`...), em ordens diferentes. Cada um é uma sequência própria, sem teste real possível sem o cartucho. Já temos o 118 e o 206 porque são o MMC3 puro.

### 4.4 Multicartuchos

15, 28, 31, 35/90/209/211, 36, 38, 40, 41, 42, 43, 46, 50, 55, 56, 58/213, 59, 60, 61, 62, 63, 104, 105, 107, 111, 112, 113, 114/182, 120, 125, 142, 148, 153, 157, 162, 163, 168, 174, 175, 178 e semelhantes. São, em geral, registradores de bloco escritos em endereços que dependem do valor (`$8000 + i`, `$FFB0 + i`...), com tamanho total fora do padrão (o 63 tem 3 MB e 192 bancos de 16 KB). O mapper 105 (NES-EVENT, 256 KB) exige a sequência de reset do MMC1 em duas fases. Nenhum foi portado.

### 4.5 Mappers pequenos e provavelmente seguros, mas ainda não portados

Todos com o PRG já lido; falta ler o CHR e escrever os modelos de teste:

- **13 (CPROM)**: PRG como NROM, CHR-RAM de 16 KB (nada de CHR para ler).
- **180**: UNROM invertido (primeiro banco fixo, troca em `$C000`) — PRG: `dumpBankPRG(0x0, 0x4000)` e depois `write(0x8000, i)` com conflito de barramento.
- **97** (primeiro banco fixo, igual ao 180), **93**, **94** (conflito de barramento, banco fixo no fim), **73** (VRC3, `$F000`), **68** (Sunsoft 4, `$F000`), **67** (Sunsoft 3, `$F800`, escrita segura), **72**, **92** (escrita dupla `i|0x80` e `i`), **140**, **86** (`$6000`, bits 4-5), **152**, **184**, **146/79** (`$4100`).
- **34**: depende da espera de 4.1.

## 5. O que o simulador não prova

O `SimMapper` foi escrito por mim, a partir do mesmo código do OSCR e das descrições de registradores que lembro dos chips. Ele pega erro de lógica (banco errado, tamanho, ordem de escrita, conflito de barramento modelado). **Não pega:** erro de transcrição de bit ou de endereço copiado igual nos dois lados, tempos, diferenças entre revisões do chip (por exemplo MMC1A e MMC1B), e cartuchos que respondem diferente do documentado.

## 6. Como escolher o próximo lote

Ordem sugerida, do menor risco para o maior:
1. Mappers de 4.5 que não precisam de primitiva nova (13, 180, 97, 93, 94, 73, 68, 72, 92, 140, 86, 152, 184).
2. Mapper 34, acrescentando `NesBus::wait_ms` (padrão sem efeito, `delay` no AVR).
3. VRC2/VRC4/VRC6 só se o usuário informar a variante (precisa de um campo novo no protocolo).
4. Clones de MMC3 e multicartuchos: só com o cartucho na mão, um de cada vez.
