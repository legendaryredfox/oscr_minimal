# Sessão de 2026-11-17: Onda 4, lotes 4.3 a 4.6

Tudo abaixo está na `main` (github e codeberg). **Nada rodou em hardware.** Detalhes de cada item: `docs/decisoes.md` (D179 a D188).

| Lote | Item | Decisão | O que entrou |
|---|---|---|---|
| 4.3 | F-16 Mega Drive | D179 a D183 | BRAM do Sega CD, Realtec, lock-on do Sonic & Knuckles no DETECT, leitura por banco (`--mapper 1\|2\|3`: Lion King 3, Pokémon Stadium, Star Odyssey), Sharp LH28F320BJE, Am29F800, gravar chip fora da tabela pelo CFI (só AMD, mapa de setores que fecha) |
| 4.4 | F-14 NES | D184, D185 | EEPROM dos mappers 16 e 159, saves de 19, 80, 82, 155, 21, 25, 26, 68, 85, 153; 19 mappers de ROM novos, incluindo VRC2/4/6 (21 a 26) sem campo novo no protocolo |
| 4.5 | F-17 GB/GBC | D186, D188 | leitura dos acessórios (`dump -s gb --mapper 1..6`: Pelican, Mega Memory, GameShark, GB Memory, mapeamento, GB Smart); gravar Pelican, Mega Memory e GameShark (`rom-write --chip gb-pelican\|gb-megamem\|gb-gameshark`) com backup e conferência |
| 4.6 | F-11, F-12 SNES | D187 | BS-X (Memory Pack e SRAM) e SF Memory (flash, mapeamento, jogos 0 a 6) pelo `--accessory`; F-12 sem nada a ligar |

Pier Solar: pesquisa e plano do adaptador passante em `docs/historico/2026-11-17-pesquisa-pier-solar-e-piratas-md.md` e `docs/planos/adaptador-passante-pier-solar.md`, depois do RP2040.

## Erros achados e corrigidos na sessão
- Tamanho da leitura do Mega Memory: 540.672 bytes (bancos de 16 KB), não 278.528 (D188).
- A hipótese de que os VRC precisavam de campo novo no protocolo estava errada: o OSCR escolhe a variante pelo número e por leituras (D185).
- `uso.md` dizia que o save do MBC6 não era aceito; o firmware já gravava (D186).

## Estado ao encerrar
Flash 224.512 B (88,4 %, limite 95 %), RAM 4596 B. Testes: host 362, Kotlin verde, `pc-tests` 12 binários.

## Próximos
1. **GB Memory Module** (`GameBoyMem`: apagar, gravar, mapeamento) e **GB Smart** (`GameBoySmart::writeFlash`, menus de jogo): mesmo molde do D188 (seam em `GbFlash.cpp`, esperas limitadas, backup e conferência pela leitura de D186, tamanho conferido antes de apagar). Fluxos com mais de um arquivo.
2. RTC do MBC3 (o OSCR não tem; código novo e formato de arquivo).
3. Gravar o Memory Pack do BS-X e a flash e o mapeamento do SFM.
4. Lote 4.7 (F-20, outros sistemas) e Onda 5 (fechamento).
5. Conferir os pinos dos adaptadores BS-X e SFM contra o `pinmap` antes de montar.
