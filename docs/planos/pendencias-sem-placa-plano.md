# Plano: pendências que não precisam de placa em mãos

Data: 2026-11-14. Spec (itens, aceitação, decisões): `docs/planos/pendencias-sem-placa-spec.md`. Os ids (F-, H-, K-, D-) são os da spec.

## Princípios de execução

- **Uma onda por vez.** Ao fim de cada onda: testes verdes, `pio run` dentro do orçamento, docs e `decisoes.md` atualizados, commit. Push nos dois remotos só com o `git log --format=%B origin/main..HEAD | grep -iE 'co-authored|claude|generated with'` vazio (regra 0 do CLAUDE.md).
- **Perguntar antes de cada onda que muda protocolo ou hardware** (regra da D160: "antes de adicionar, me pergunte").
- **Chamar o OSCR, não reescrever.** Cada item de firmware começa lendo a função em `firmware/oscr/src/cores/*.cpp`, liga o núcleo em `user.ini` e escreve só a costura em `src/dumper/`.
- **Ordem dentro de cada item:** protocolo documentado → `oscr_proto.h` → costura do firmware → `pc-tests` → Python → Kotlin (CLI e GUI, 4 idiomas) → simuladores → docs.
- **Sem hardware, sem afirmar.** Toda entrada termina com "nada rodou em hardware".

## Onda 0: organizar o terreno (sem mudar firmware) — FEITA em 2026-11-14 (D161)

Feita: itens 1 a 6 abaixo, com K-2 sem trabalho (nenhuma ligação aberta). Fica de fora, por ser maior, a parte de diálogos, base de dados e busca do NES no `gui_smoke.sh`.

1. **D-1** reescrever `docs/continuacao.md` (estado, retomada, pendências; história para `docs/historico/continuacao-2026-11.md`). Corrige o que está defasado: SMS ligado, guia ru e zh existentes.
2. **K-4** corrigir `CLAUDE.md` seção 2 e `boards/README.md` contra `boards/versoes.json`.
3. **K-1** `tools/check_all_boards.py` (ERC, DRC, `check_netlist`, SHA-256 dos zips, silk em pt-BR) e rodar uma vez; o resultado vira a lista real de ligações abertas.
4. **H-0b** `tools/gui_smoke.sh` (Xvfb + simulador). H-0 (dispositivo falso na CLI Kotlin) já existia.
5. **H-5** paridade do guia nos 4 idiomas no `test_docs_sync`.
6. **D-2** D159: só depois de o usuário confirmar o texto.

Saída: `continuacao.md` curto, relatório de todas as placas, testes de CLI e GUI sem hardware. Nenhuma decisão de protocolo.

## Onda 1: orçamento de flash e troca automática de firmware (bloqueia a Onda 4)

Regra do usuário (2026-11-14): imagem única sempre que couber; variantes só se for impossível.

1. **Medir** (F-0a): `pio run` com um sistema ligado por vez; tabela "sistema → B de flash e RAM" em `docs/referencia/fork-oscr.md`. Medir também a imagem completa de hoje (`SerialASCII`).
2. **Capacidades** (F-0b): bits no `INFO` com sistemas e recursos; firmware antigo sem os bits = o que existia.
3. **Mapa placa → necessidades** em `boards/versoes.json` (ou arquivo vizinho): sistemas por placa, lido por Python e Kotlin (um só arquivo, com teste de paridade).
4. **Troca automática** (F-0c): GUI (combo de placa, diálogo de confirmação, barra de progresso) e CLI (`--board`, `--yes`/`--auto-flash`) gravam a imagem que cobre a placa pelo `firmware-flash`, conferem o `INFO` depois e recusam se nenhuma imagem cobre. Testado com o simulador do bootloader e o `SimDevice`, **sem Mega real**.
5. **Variantes** (F-0d) só se a medição mostrar que a imagem completa não comporta o plano da Onda 4. Nesse caso o teste de orçamento (F-0e) indica quais núcleos saem da imagem completa e quais variantes nascem.
6. **Teste de orçamento** (F-0e): `tools/check_flash_budget.py`, falha acima de 95 % de flash ou 80 % de RAM.

Saída: tabela medida, capacidades visíveis, troca automática funcionando contra o simulador. **Gate:** nenhuma onda de núcleo começa sem esta tabela.

## Onda 2: protocolo e comandos novos (após D-B)

Ordem por risco crescente:

1. **H-1** `save-convert` (só PC, não depende de nada).
2. **F-2** tipo forçado do SNES. Ler `snesProbe` e o fluxo de `SNES.cpp`; campo novo no `DETECT`/`DUMP_ROM`/`READ_SAVE`; `--type` e campo na GUI.
3. **F-1** `PROGRESSO` (0x88): o firmware emite a etapa onde já há laços longos (`rom_prepare`, apagar, gravar, conferir); o PC passa a mostrar a etapa em vez de só porcentagem.
4. **F-3** `clock-cal`: chamar o `ClockGen` do OSCR; só mostra e grava o fator; calibrar de verdade é da bancada.
5. **H-3** baud intermediário, **H-2** link do NESCartDB.

Saída: protocolo versionado com testes de compatibilidade (host novo + firmware velho, e o contrário).

## Onda 3: PC, empacotamento e pesquisa (paralela à 2)

1. **H-7** embutir os `.hex` (imagem completa e variantes, se houver) e avrdude no instalador; teste com o simulador do bootloader.
2. **H-6** `.deb` e AppImage gerados nesta máquina; receitas de dmg e msi escritas, **marcadas como não testadas** até haver runner (D-D).
3. **H-4** `tools/check_adaptadores.py`.
4. **D-3** diff do upstream `oscr-firmware` contra `d9cb26a` e lista do que trazer.
5. **D-4, D-5, D-6, K-3** pesquisa e docs; **K-2** fechar ligações abertas com confirmação por item.

## Onda 4: núcleos do OSCR, em lotes (depois das ondas 1 e 2)

Regra do lote: medir flash **antes** de ligar; se passar do orçamento da placa, o núcleo entra só na imagem das placas que o usam. Cada lote termina com uma entrada de decisão e `funcoes-oscr.md` atualizado.

| Lote | Itens | Motivo da ordem |
|---|---|---|
| 4.1 | F-13, F-15, F-18 (369-in-1), F-19 (flash repro do N64) | pouca superfície nova, funções do OSCR já mapeadas |
| 4.2 | F-10 (Test RAM, GPRAM, Sufami Turbo) | SNES, costura simples |
| 4.3 | F-16 (Mega Drive) | continua o trabalho do MD-1 a MD-8; núcleo `MdFlashCore` já tem modelo no PC |
| 4.4 | F-14 (NES: mappers e EEPROM) | exige atualizar listas de mappers em vários arquivos (ver armadilhas da `continuacao.md`) |
| 4.5 | F-17 (GB/GBC) | muitos acessórios; cada um separado |
| 4.6 | F-12, F-11 (SNES raro, SFM, BS-X) | maiores e de menor uso |
| 4.7 | F-20 (outros sistemas), por sistema | por último; só os que cabem nos slots existentes (D-C) |

Em cada item: ler o menu do OSCR, mapear os `case`/`_clk`/pinos contra `boards/*/docs/pinmap.md` (nunca inventar pino; `PENDENTE` e perguntar), seguir a ordem de camadas dos princípios.

## Onda 5: fechamento

1. Rodar a suíte completa e `tools/check_all_boards.py`.
2. Atualizar `docs/referencia/cobertura-testes.md`.
3. Atualizar `continuacao.md` (D-1) com o que sobrou: só o que depende de placa, cartucho, medição, falante nativo ou CI.
4. Entrada final em `decisoes.md` com a lista "o que rodou em hardware: nada" e o roteiro de bancada na ordem de risco do `uso.md` seção 7.

## Ordem sugerida e dependências

```
Onda 0 ──► Onda 1 ──► Onda 4 ──► Onda 5
   │          ▲
   └─► Onda 2 ┘   (F-0b antes de F-1/F-2/F-3 para usar o INFO novo)
   └─► Onda 3 (independente; H-7 depende de F-0c)
```

## Primeira entrega proposta (cabe numa sessão)

Onda 0 inteira, menos D-2: `continuacao.md` enxuto, `check_all_boards.py` com o relatório, teste de CLI Kotlin com dispositivo falso e smoke da GUI. Sem mudança de protocolo, firmware nem hardware, então não pede aprovação de D-A a D-E.

## Critério de encerramento do plano

Tudo da spec seção 4 está feito, ou virou item em `funcoes-oscr.md` / `continuacao.md` com o motivo exato (placa, cartucho, medição, falante nativo, CI), ou foi recusado pelo usuário em D-A a D-E.
