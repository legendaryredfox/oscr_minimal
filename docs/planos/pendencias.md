# Pendências: o que falta e o que cada id quer dizer

A spec e o plano de 2026-11-14 ("pendências que não precisam de placa", D161) foram executados em seis ondas e fechados na D191 (2026-11-20); a F-20 (outros sistemas) seguiu depois, um sistema por incremento (D201 em diante). Este arquivo guarda o significado dos ids que aparecem em `docs/decisoes.md` e no código, e **só o que ainda falta**. O que cada sistema faz hoje: `docs/referencia/uso.md` seção 3 e `docs/referencia/funcoes-oscr.md`.

## Critério de pronto (vale para todo item novo)

1. `make -C firmware/oscr/pc-tests test`, `cd host && python3 -m pytest -q` e `cd gui && ./gradlew --offline :shared:jvmTest :desktopApp:compileKotlin :cliApp:compileKotlin` verdes; `tools/gui_smoke.sh` abre a janela.
2. `pio run -e SerialASCII` compila e `python3 tools/flash_budget.py check` passa (limites: 95 % do flash, 80 % da RAM). Imagem única enquanto couber; variante só se a medição provar que não cabe (decisão do usuário, 2026-11-14, D162).
3. Protocolo documentado em `docs/referencia/protocolo.md` antes de implementar; textos da GUI e da CLI nos 4 idiomas.
4. Entrada nova em `docs/decisoes.md` e `docs/referencia/funcoes-oscr.md` atualizado.
5. Regra do `CLAUDE.md`: chamar as funções do OSCR direto; código próprio só nas costuras de `src/dumper/`; divergência justificada em `decisoes.md`.
6. Texto honesto: "nunca rodou em hardware" em cada entrada até rodar.

## Ids e estado

| Id | O quê | Estado |
|---|---|---|
| F-0a a F-0e | Orçamento de flash, capacidades no `INFO`, troca automática de firmware pela placa, imagens, teste de tamanho | feito (D162) |
| F-1 | `PROGRESSO` com etapa (apagando, gravando, lendo, autoteste) | feito (D165) |
| F-2 | Tipo de ROM do SNES forçado (`--type`) | feito (D164) |
| F-3 | `clock-cal` do Si5351 | feito (D167); calibrar de verdade é da bancada |
| F-10 | SNES: Test RAM, GPRAM, Sufami Turbo | feito (D178) |
| F-11 | SNES: SF Memory e Satellaview (BS-X) | feito (D187, D190) |
| F-12 | SNES: chips raros | nada a ligar (D187) |
| F-13, F-15 | NES: leitura raw; detecção de cartucho ausente | feito (D173) |
| F-14 | NES: EEPROM dos mappers 16 e 159, saves e mappers novos, VRC2/4/6 | feito (D184, D185) |
| F-16 | Mega Drive: BRAM, Realtec, lock-on, bancos, Sharp, Am29F800, gravar por CFI | feito o que não precisa de cartucho (D179 a D183); falta o da seção abaixo |
| F-17 | GB/GBC: acessórios (Pelican, Mega Memory, GameShark, GB Memory, GB Smart), RTC do MBC3 | feito (D186, D188, D189, D192, D193) |
| F-18 | GBA: 369-in-1; repro pelo slot GB | feito (D174, D175) |
| F-19 | N64: flash repro, Gameshark, Xplorer 64 | feito (D176, D177) |
| F-20 | Outros sistemas do OSCR, um por vez, só os que cabem num slot existente com adaptador (D-C) | 19 feitos (D201 a D228, `docs/planos/adaptadores.md`); faltam os da seção abaixo |
| H-0, H-0b | Dispositivo falso na CLI Kotlin; `tools/gui_smoke.sh` | feito (D157, D161) |
| H-1 | `save-convert` | feito (D163); qual operação cada emulador pede não foi conferido |
| H-2, H-3 | Link do NESCartDB; baud de 500.000 no fallback | feito (D166) |
| H-4 | `tools/check_adaptadores.py` (adaptadores de 3,3 V da comunidade) | feito (D172), sem cruzar pino a pino |
| H-5 | Paridade dos guias nos 4 idiomas (`test_guia_sync.py`) | feito (D161) |
| H-6, H-7 | Instalador com as imagens do firmware e o avrdude; `.deb` e AppImage | feito em parte (D169): `.deb` gerado e nunca instalado; dmg e msi só com CI |
| K-1, K-2, K-4 | `tools/check_all_boards.py`; ligações abertas; resumo das placas no `CLAUDE.md` | feito (D161) |
| K-3 | Corrente do U3 com GBA e N64 | estimativa (D171, `docs/historico/pesquisas-2026-11.md#estimativa-corrente-u3`); medir na bancada |
| K-5 | Área livre sobre o USB-B do Mega: R1.1 (LED) e, na `16_bits` e na `snes`, R2.1 (**+5V**) ficam sobre a carcaça do USB-B (GND); na `megadrive` e na `megadrive_sms`, C4.1 (5V) também. 16 das 22 versões; só `16_and_8_bits`, `completa` e `gb_gba` estão livres (D238). Mover as peças e pôr no `tools/check_all_boards.py` a verificação da área | **pendente** |
| D-1, D-2 | `continuacao.md` curto; registro da D159 | feito (D159, D161) |
| D-3 | Diff do upstream `oscr-firmware` | feito (D168) |
| D-4 | Pesquisar de novo Little Jammer, Little Jammer Pro, Super A'Can, SF Memory, Pocket Challenge W e PV-1000 nos repositórios | **pendente** (trabalho de rede e leitura longa) |
| D-5, D-6 | P-09 do Mega Drive contra o código; aviso do Si5351 na montagem | feito (D170) |
| P-01 a P-17 | Achados da pesquisa da comunidade | `docs/historico/pesquisa-comunidade.md` |
| MD-1 a MD-15, HW-MD-1 a HW-MD-8 | Mega Drive: flash, mapeadores, 8 MiB e hardware | `docs/planos/melhorias-megadrive.md` |

## O que falta sem placa

- **F-20, sistemas restantes (19):** Casio Loopy, Commodore 64, VIC-20, Capcom CPS3, Intellivision, Leapster (3,3 V), Little Jammer, Little Jammer Pro (3,3 V), Virtual Boy, PC Engine / TurboGrafx-16, Pocket Challenge W, Satellaview e SF Memory como sistemas próprios (os cartuchos já são lidos pelo SNES, F-11), Super A'can, TI-99/4A, TRS-80, WonderSwan, Game Boy Smart Card e Game Boy Memory (já gravados pelo GB, F-17). Lista idêntica em `host/oscr_host/planned.py` e `PlannedSystems.kt` (`test_planned.py`). A máscara `systems()` do firmware tem 64 bits desde a D232: o próximo id é 32, e cabem até o 63.
- **MSX (D230), resto:** busca do jogo por nome na GUI e na CLI pela base `database/oscr/json/msx.json` (traz mapper, índice do tamanho e da SRAM, sem CRC32), como o NES faz com a base dele; /IORQ, /M1 e /RFSH do adaptador (pull-up?).
- **F-16, resto:** dois chips no mesmo cartucho e detectar o limite de 2 MiB pelo padrão de leitura (resto do MD-13).
- **D-4** (acima).
- Teste automático do diálogo de troca de firmware da GUI; dmg e msi (precisam de CI com runner macOS e Windows; o GitHub está bloqueado por cobrança).

## Só com hardware, cartucho, medição, pessoa ou CI

- **Bancada da `16_bits` v1.0 (D242 a D245), o que ficou aberto:**
  - `detect -s md` com o slot vazio dá falso positivo (D242). A correção foi proposta e não foi feita.
  - Chip do DKC2 regravável de SNES: o `rom-write` responde "chip não reconhecido". Falta a marcação do chip, que o usuário vai ler.
  - Gravar a SRAM no SNES: nunca rodou.
  - Gravar ROM no MD com chips que não o S29GL064N: nunca rodou.
  - Gravar no GBA e no N64: nunca rodou, e a `16_bits` não tem esses slots.
  - O Yu Yu Hakusho lê `FF` (cartucho de funcionamento desconhecido).


Validação de tudo (roteiro em `docs/referencia/uso.md` seção 7 e `docs/referencia/teste-de-bancada.md`, na ordem de risco da D191); MD-9, MD-14 e MD-15; o comando `peek` (P6, adiado de propósito na D160: sem placa um valor errado pareceria bom); medir os slots, a direção da etiqueta do SMS, a corrente do U3 com o N64 e os furos de fixação no Mega; `firmware-flash` com o Mega real nos três sistemas operacionais; Controller Pak do N64 (a placa não tem o conector do controle); calibração do Si5351 com frequencímetro; bancada do RP2040 (`docs/planos/placa-v1.3-rp2040.md`); revisão nativa de ru e zh; revisão visual dos layouts no KiCad; montar e testar os adaptadores da F-20; encomendas (ordem na D159: validar a `16_bits` v1.0 já encomendada antes de comprar outra).
