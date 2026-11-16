# Spec: pendências que não precisam de placa em mãos

Data: 2026-11-14. Estado (2026-11-14): **aprovada**; o usuário delegou as decisões D-B a D-E ("pode decidir conforme achar melhor") e decidiu D-A. **Onda 0 do plano feita** (D161) e **Onda 1 feita** (D162; falta embutir os `.hex` no instalador, H-7, e o teste automático do diálogo da GUI). Plano de execução: `docs/planos/pendencias-sem-placa-plano.md`.

Origem: levantamento de `docs/continuacao.md`, `docs/referencia/funcoes-oscr.md`, `docs/historico/pesquisa-comunidade.md` (P-01 a P-17), D160 e os planos em `docs/planos/`.

## 1. Objetivo

Fechar tudo o que pode ser **escrito, compilado e testado no PC** sem uma placa montada: firmware (núcleos do OSCR ligados pelas costuras de `src/dumper/`), protocolo, CLIs Python e Kotlin, GUI, documentação, scripts de verificação das placas KiCad e empacotamento.

**Critério de "pronto" de qualquer item** (o mesmo de D157/D158):

1. `make -C firmware/oscr/pc-tests test`, `cd host && python3 -m pytest -q` e `cd gui && ./gradlew --offline :shared:jvmTest :desktopApp:compileKotlin :cliApp:compileKotlin` verdes.
2. `pio run -e SerialASCII` compila e o uso de flash fica **dentro do orçamento** (seção 3).
3. Protocolo documentado em `docs/referencia/protocolo.md` **antes** de implementar; `host/tests/test_docs_sync.py` e `I18nTest` verdes (4 idiomas).
4. Entrada nova em `docs/decisoes.md` e atualização de `docs/referencia/funcoes-oscr.md`.
5. Texto honesto: "**nada rodou em hardware**" em cada entrada. Item de firmware sem placa nunca vira ✅ de "funciona", só de "compila e passa nos testes do protocolo".
6. Regra do CLAUDE.md: chamar as funções do OSCR direto; código próprio só nas costuras; divergência justificada em `docs/decisoes.md`.

## 2. Fora do escopo (precisa de placa, cartucho ou pessoa)

| Item | Por quê |
|---|---|
| Qualquer validação de hardware (`selftest`, primeiro dump, CRC contra No-Intro, gravação de flash) | placa não montada |
| MD-9, MD-14, MD-15 (mapeadores, cartucho de 8 MiB, Open EverDrive) | cartucho em mãos |
| P6 `peek` | adiado de propósito na D160: sem placa um valor errado pareceria bom |
| Medir slots, direção da etiqueta do SMS, corrente do U3 com N64, furos de fixação no Mega | medição física |
| Teste do `firmware-flash` com Mega real; serial a 1.000.000 baud nos três sistemas; leitor de tela real | equipamento |
| N64 Controller Pak e teste de controle | a placa não tem o conector do controle |
| Calibração real do Si5351 (precisa de frequencímetro) | só o código entra; a calibração é da bancada |
| Bancada do RP2040 (v1.3) | hardware |
| Revisão nativa de ru e zh | falante nativo |
| Revisão **visual** do layout no KiCad | os olhos do usuário; aqui entra só a verificação automática (K-1) |
| Encomendas | decisão do usuário (ordem na D159) |
| CI do GitHub | conta bloqueada por cobrança |

## 3. Restrição central: orçamento de flash do Mega

`SerialASCII` já usa **194.466 B de flash (76,6 %)** e 4.129 B de RAM (50,4 %) com N64, SMS, flash e selftest ligados. Sobram cerca de **59 KB**; `HAS_FLASH` sozinho custou ~27 KB. Os núcleos pendentes (SF Memory, Satellaview, Sufami Turbo, GPRAM, Test RAM, flash repro do N64, mais mappers do NES, Sega CD, RTC, GB Smart, NPower etc.) provavelmente **não cabem juntos**.

**Decisão do usuário (2026-11-14): imagem única primeiro; variantes só se for impossível caber tudo.** O firmware completo (`SerialASCII`) continua sendo o alvo. Só se a medição provar que um núcleo não cabe junto dos outros é que ele entra numa variante separada. Em qualquer caso, **o programa grava a variante certa sozinho** quando o usuário escolhe uma placa e o firmware que está no Arduino não dá suporte ao que a placa precisa.

- **F-0a. Medir antes de decidir.** Tabela "sistema → B de flash e de RAM" medida com `pio run`, ligando um núcleo por vez. Cada núcleo novo é medido antes de entrar.
- **F-0b. Capacidades no `INFO`.** O firmware informa os sistemas e recursos que tem (hoje o `INFO` já tem bits; o bit 6 é o `SELFTEST`). Firmware antigo sem os bits: o PC assume o que existia até então.
- **F-0c. Troca automática de firmware.** O PC conhece, por placa (`boards/versoes.json`), quais sistemas e recursos ela precisa. Ao escolher a placa (combo da GUI, `--board` na CLI), compara com as capacidades do `INFO`. Se faltar algo, escolhe a menor imagem que cobre a placa e grava com o `firmware-flash` (avrdude, já existente). Antes de gravar, **pede confirmação** (diálogo na GUI; `--yes` ou `--auto-flash` na CLI), porque gravar apaga o firmware atual e reinicia o Mega. Depois de gravar, lê o `INFO` de novo e confere. Se não houver imagem que cubra a placa, avisa e não grava.
- **F-0d. Imagens.** Enquanto couber tudo, existe uma imagem só e a F-0c apenas grava o firmware ausente ou antigo. Variantes (`Board_<placa>` ou `Sistemas_<grupo>`) só são criadas se o teste de orçamento falhar; elas ficam em `firmware/oscr/` e o `.hex` de cada uma é embutido (H-7).
- **F-0e. Relatório de tamanho no teste** (`tools/check_flash_budget.py`): falha se alguma imagem passar de 95 % do flash ou 80 % da RAM (a pilha precisa de folga).

Decisão D-A: **resolvida** como acima (a recomendação de "uma imagem por placa" da primeira versão desta spec foi trocada).

## 4. Itens (cada um com critério de aceitação)

Legenda de tamanho: S = menos de um dia, M = 1 a 3 dias, L = mais de 3 dias. "Núcleo" = função já existente no OSCR.

### 4.1 Infraestrutura (bloqueia o resto)

| Id | Item | Aceitação | Tam. |
|---|---|---|---|
| F-0a..e | **Feito (D162), com limites.** Orçamento de flash e troca automática de firmware (seção 3) | tabela medida; `INFO` traz as capacidades; escolher a placa na GUI ou `--board` na CLI grava a imagem que cobre a placa, com confirmação; teste de tamanho falha ao estourar | M |
| H-0 | ~~Dispositivo falso na CLI Kotlin~~ **já existe** (`SimDevice`, `MdBoardLimitCliTest`, D157); a nota "não há dispositivo falso lá" estava defasada | nada a fazer | feito |
| H-0b | **Feito (D161)** `tools/gui_smoke.sh` (janela larga e estreita, captura não em branco; ainda não cobre diálogos, base de dados nem busca do NES). Testes de GUI sem hardware: Xvfb + `SimDevice`, janela estreita, diálogos, base de dados, busca NES | script `tools/gui_smoke.sh` gera capturas e falha se a janela não abrir | M |

### 4.2 Protocolo e comandos novos (mudam protocolo e firmware; D-B (decidida))

| Id | Item | Aceitação | Tam. |
|---|---|---|---|
| F-1 | `PROGRESSO` (0x88): etapas vindas do firmware (apagando, gravando, conferindo, esperando) | barra e `--json` mostram a etapa; protocolo versionado; simulador emite as etapas | M |
| F-2 | Forçar o **tipo** do SNES (P-06): campo novo no protocolo, sem reusar `mapper` | `--type lorom|hirom|exhirom` em `detect`, `dump` e `save-read` nas duas CLIs e na GUI; `pc-tests` cobrem; o firmware chama `snesProbe` do OSCR com o tipo forçado | M |
| F-3 | Calibrar o relógio do Si5351 (P-03): comando que aplica o fator medido e grava no EEPROM do Mega, chamando o `ClockGen` do OSCR; alvos 3.072.000, 4.000.000 e 1.000.000 Hz | `dumper clock-cal` nas duas CLIs e GUI; texto mostra os alvos; sem frequencímetro o comando só lê e mostra o fator | M |
| H-1 | Conversão de ordem de bytes dos saves (P-08: Mega Drive ímpar/par, N64, GB) para emulador | `dumper save-convert`; testes com vetores; só PC | S |

### 4.3 Núcleos do OSCR ainda não ligados (todos de `funcoes-oscr.md` com ⬜)

Cada um entra **depois** de F-0 e só se couber no orçamento da placa que o tem. Ordem por valor e risco (detalhe no plano).

| Id | Item | Núcleo OSCR | Tam. |
|---|---|---|---|
| F-10 | SNES: Test RAM, Game Processor RAM, Sufami Turbo (slot A e B) | `SNES.cpp` | M |
| F-11 | SNES: SF Memory (SFM) e Satellaview BS-X (Memory Pack e SRAM) | `SNES.cpp`, `SFM`, `BSX` | L |
| F-12 | SNES: chips raros (Derby Stallion 96, S-RTC, OBC1, ST018, MSU-1, RTC do SPC7110) | `SNES.cpp` | M |
| F-13 | NES: leitura raw (PRG e CHR separados) — **feito** (D173) | `NES.cpp` | S |
| F-14 | NES: EEPROM dos mappers 16 e 159, saves de Namco 163 e Sunsoft/Taito, mais mappers (os do upstream além dos 37), flash de CHR em outros chips | `NES.cpp` | L |
| F-15 | NES: detecção de cartucho ausente melhor que a heurística de 64 bytes iguais — **feito** (D173; só a regra, validação em bancada) | `NES.cpp` + costura | S |
| F-16 | Mega Drive: Sega CD RAM (BRAM), Realtec, Sharp LH28F320BJE, 2 chips no mesmo cartucho, 29F800, gravar por CFI, detectar o limite de 2 MiB pelo padrão de leitura (resto do MD-13), conjunto de chips MD-1 a MD-8 que ainda faltarem | `MegaDrive.cpp`, `Flash.cpp` | L |
| F-17 | GB/GBC: RTC do MBC3, flash do MBC6, ROM do TAMA5; GB Smart, NPower, Mega Memory, GameShark, Datel, Codebreaker, Pelican | `GBX`, `Flash.cpp` | L |
| F-18 | GBA: 369-in-1 (ler 256 MB e por offset), GBA repro via slot GB | `GBA.cpp` | M |
| F-19 | N64: gravar ROM em flash repro (`flashRepro`), Gameshark, Xplorer 64 | `N64.cpp` | M |
| F-20 | Outros sistemas (os 41 stubs: Atari, PC Engine, WonderSwan, MSX etc.) | um núcleo por sistema | L, em lotes |

D-C (decidida): a F-20 é a maior e a que mais gasta flash. Proposta: **só** os sistemas que cabem nos slots das placas existentes (via adaptador do slot SNES ou GBA) e só como um lote por vez; o restante fica registrado como "precisa de adaptador próprio".

### 4.4 PC: CLIs, GUI e empacotamento

| Id | Item | Aceitação | Tam. |
|---|---|---|---|
| H-2 | Link do NESCartDB na GUI e nota em `limites-nes.md` (P-10) | link abre; texto nos 4 idiomas | S |
| H-3 | Baud intermediário de 500000 no fallback (P-14) | CLI e GUI tentam 1.000.000, 500000, 115200; teste com porta falsa | S |
| H-4 | Aviso e checagem: `-s auto` e `detect` sugerem o sistema certo para adaptadores 3,3 V (P-16) | `tools/check_adaptadores.py` cruza adaptadores da pesquisa com `boards/*/docs/pinmap.md` e lista conflitos | M |
| H-5 | **Feito (D161)** `host/tests/test_guia_sync.py`. Guia passo a passo: conferir ru e zh (arquivos já existem; a nota da D157 está desatualizada) e travar a paridade | `test_docs_sync` compara títulos e números de passos nos 4 | S |
| H-6 | Empacotamento: `.deb` e AppImage geráveis aqui; **dmg e msi só em runner macOS e Windows** | `.deb` e AppImage embutem `.hex` por placa e o avrdude; dmg e msi com receita pronta e não testada | L |
| H-7 | Embutir os `.hex` (imagem completa e variantes, se existirem) e o avrdude no instalador; o arquivo do firmware que o usuário já tem é só uma segunda opção | `firmware-flash` e a troca automática da F-0c funcionam sem PlatformIO instalado, no simulador do bootloader | M |

D-D (decidida): dmg e msi precisam de CI com runner macOS e Windows. O GitHub está bloqueado por cobrança. Alternativas: Codeberg (Forgejo Actions, runners próprios) ou deixar só as receitas.

### 4.5 Hardware sem tocar em hardware (KiCad, scripts)

| Id | Item | Aceitação | Tam. |
|---|---|---|---|
| K-1 | **Feito (D161)** `tools/check_all_boards.py`. Verificação automática de todas as placas e versões: ERC, DRC (sem ligação aberta), `check_netlist --board`, SHA-256 dos zips contra `PEDIDO.md`, silk em pt-BR, versões em `versoes.json` | `tools/check_all_boards.py` roda tudo e lista ligações abertas (as da `famicom_nes` v1.1 e `16_bits` v1.3 da D139); sai com 1 se algo estiver errado | M |
| K-2 | **Sem trabalho:** o K-1 não achou nenhuma ligação aberta (as da D139 já estavam fechadas). Fechar à mão as ligações abertas que o K-1 achar (com confirmação do usuário antes de qualquer `delete_*` do MCP) | DRC sem ligação aberta nas placas atuais | M |
| K-3 | Estimar a corrente do U3 (MCP1700, 250 mA) com GBA e N64 a partir de folhas de dados e medidas publicadas | cálculo em `docs/historico/`; **a medição fica para a bancada** | S |
| K-4 | **Feito (D161)**. Atualizar o resumo de `boards/README.md` e `CLAUDE.md` seção 2 (`gb_gba` ainda aparece como esqueleto) | texto bate com `boards/versoes.json` | S |

### 4.6 Documentação e pesquisa

| Id | Item | Aceitação | Tam. |
|---|---|---|---|
| D-1 | **Feito (D161)**. Reescrever `docs/continuacao.md`: hoje tem 300 linhas em ordem cronológica inversa, seções 2 a 5 descrevem o firmware arquivado e há texto defasado (o SMS **já está ligado**, `sms = true`; o guia em ru e zh já existe) | arquivo curto: estado, como retomar, pendências; história vai para `docs/historico/` | M |
| D-2 | **Feito (D159)**. Registrar **D159** (ordem de encomenda, etiqueta do SMS, furos no Mega, R2/U3 do N64) **somente depois da confirmação do usuário** | entrada em `decisoes.md` | S |
| D-3 | P-15: acompanhar `oscartreader/oscr-firmware` e trazer correções do upstream para o fork | diff do topo atual contra `d9cb26a`; lista do que vale trazer; nada aplicado sem OK | M |
| D-4 | PC-1 a PC-6: pesquisar de novo Little Jammer, Little Jammer Pro, Super A'Can, SF Memory, Pocket Challenge W, PV-1000 **e conferir nos repositórios** o que hoje é só resumo de busca | `docs/planos/placas-cartuchos-...md` com fonte e licença conferidas | M |
| D-5 | P-09 (Mega Drive: PAL, Codemasters, EEPROM só em originais) conferido contra `MegaDrive.cpp` | tabela "tratado / não tratado" em `limites-md.md` (novo) | S |
| D-6 | P-13 (Si5351: orientação, nível do I²C) em `montagem.md` de cada placa que tem o módulo | texto igual em todas, conferido por script | S |

## 5. Decisões que dependem do usuário

| Id | Pergunta | Recomendação |
|---|---|---|
| D-A | ~~Uma imagem por placa?~~ **Resolvida pelo usuário:** imagem única; variantes só se não couber; troca automática ao escolher a placa | feito |
| D-B | Campos novos do protocolo (PROGRESSO, tipo SNES, clock-cal) | **Decidido:** aprovados; F-1 e F-2 primeiro, F-3 por último. Cada campo é documentado em `protocolo.md` antes de implementar |
| D-C | Escopo da F-20 (41 sistemas) | **Decidido:** só os que cabem em slots existentes, um lote por vez |
| D-D | Onde rodar o CI para dmg e msi | **Decidido:** receita pronta agora, marcada não testada; CI depois |
| D-E | Registrar D159 | **Feito** (D159 em `decisoes.md`) |

## 6. Riscos

- **Código sem hardware:** cada núcleo do OSCR roda só no AVR. Teste no PC cobre protocolo e regras puras (`include/dumper/*Core.h`), nunca o barramento. Risco aceito, registrado em cada decisão.
- **Flash estourado** (seção 3): mitigado por F-0.
- **Protocolo:** campos novos exigem versão do protocolo e compatibilidade com firmware antigo (o host deve ler o `INFO` e recusar o comando que o firmware não tem).
- **Sobrecarga de revisão:** muitas decisões D-xx em sequência; agrupar por onda e perguntar uma vez por onda.
