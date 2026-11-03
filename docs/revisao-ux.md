# Revisão de UX/UI

Data: 2026-11-02. Escopo: a GUI (Compose Desktop), a CLI (`dumper.py`), os textos de ajuda e o guia de uso, e a experiência física do hardware (silkscreen e montagem). A revisão de código está em `docs/revisao-codigo.md`.

**Método:** a GUI foi aberta num display virtual (Xvfb, renderização por software) e percorrida: troca de idioma, escolha de sistema, opções do NES, painel de ajuda. As capturas estão em `docs/img/`. A conexão com o Mega não pôde ser exercitada (sem porta serial no Xvfb), então o fluxo de leitura e gravação foi avaliado **pelo código** (`Main.kt`) e não ao vivo. A avaliação segue as heurísticas de Nielsen e o que importa para este produto: quem usa lê um cartucho que não se refaz (bateria que acaba, jogo raro) e **grava** em memória que não se desfaz.

| Captura | Arquivo |
|---|---|
| Tela principal (PT) | `docs/img/gui-principal-pt.png` |
| Opções do NES/Famicom | `docs/img/gui-nes-pt.png` |
| Ajuda embutida | `docs/img/gui-ajuda-pt.png` |

## 1. Resumo

| Gravidade | Qtd |
|---|---|
| Alta | 3 |
| Média | 10 |
| Baixa | 7 |

Nada abaixo foi corrigido nesta revisão (os ajustes de texto e do chip GB feitos antes já estão no código). As três de gravidade alta envolvem **perda de dados ou ação irreversível**; recomendo corrigi-las antes do primeiro teste com hardware.

## 2. Pontos fortes

- **Quatro idiomas** (pt-BR, en, ru, zh) com troca na própria janela e padrão vindo do sistema; um teste garante que nenhuma chave fica sem tradução.
- **Ajuda embutida** com casos de uso e solução de problemas, sem sair do programa.
- Botões **desabilitados** durante a operação e sem conexão; botão **Cancelar** só ativo quando faz sentido.
- Avisos de tensão em vermelho para GBA e GB; "um cartucho por vez, desligue o USB" no topo.
- **Verificação do checksum do cabeçalho** (SNES, Mega Drive, GBA) com mensagem clara, e CRC32 sempre exibido para comparar com o No-Intro.
- Dica do tipo de save do GBA achada **na própria ROM** depois do dump (poupa o usuário de adivinhar).

## 3. Achados

### Alta

**U-01 — Cancelar o "Salvar como" depois de uma leitura descarta tudo.**
`Main.kt`: depois de **Ler ROM** (ou **Ler save**) a GUI abre o diálogo de arquivo; se o usuário cancela, só aparece o CRC32 e os dados lidos são perdidos. Um dump de 4 MB leva ~1 minuto e a leitura de um save de bateria só deve ser repetida o mínimo possível.
*Recomendação:* escolher o arquivo **antes** de ler, ou guardar o resultado na memória com um botão **Salvar...** que continua disponível; nunca descartar uma leitura bem-sucedida.

**U-02 — Gravar o save não pede confirmação nem faz backup.**
**Gravar save** executa direto depois de escolher o arquivo. A operação sobrescreve a SRAM, a EEPROM ou **apaga a Flash do GBA**, e escolher o tipo errado altera bytes de comando no save (D48). O botão tem a mesma aparência de **Detectar**.
*Recomendação:* diálogo de confirmação com o resumo (sistema, tipo, arquivo, tamanho) e uma caixa "ler o save atual antes e guardar como `.bak`" marcada por padrão; botão destrutivo com cor e posição próprias (U-20).

**U-03 — O resultado fica fora da tela.**
A janela abre com 800×600 e o log (única forma de ver "CRC32", "salvo em...", erros) está **no fim** da coluna, depois do progresso, então só aparece rolando. Uma falha pode passar despercebida.
*Recomendação:* barra de status fixa no rodapé com a última mensagem; log em painel próprio, ao lado ou abaixo com altura fixa; janela maior por padrão e tamanho lembrado (U-21).

### Média

**U-04 — O log não pode ser copiado nem salvo.** O roteiro de testes com hardware pede "logs" ao usuário, mas as linhas são `Text` simples (não selecionáveis) e somem ao fechar. *Recomendação:* `SelectionContainer` mais botões **Copiar** e **Salvar log**, incluindo a versão do app, o `INFO` do firmware (versão, `flags`, sistemas) e a data.

**U-05 — Erros técnicos, sem tradução e sem ação.** O usuário vê `erro 0x0004 ()` ou `sem resposta ao comando 0x3`. A ajuda explica os códigos, mas a GUI não faz a ligação (ver também C-10 em `revisao-codigo.md`). *Recomendação:* mapear cada código para uma mensagem localizada com a causa provável e o que fazer ("0x0004: tamanho ou mapper inválido para este cartucho; confira PRG e CHR"), com atalho para o item da ajuda.

**U-06 — Estado compartilhado entre sistemas.** `prgKb` é um único campo usado como "Tamanho da ROM" no SNES e no Mega Drive e como "PRG" no NES. O valor digitado no NES aparece no SNES e é enviado: num ExHiROM isso **força o tamanho** sem o usuário perceber. *Recomendação:* estado por sistema, ou limpar ao trocar de sistema.

**U-07 — Opções do NES são o ponto mais frágil do fluxo.** O usuário precisa informar mapper, PRG e CHR de uma fonte externa; errar dá um arquivo com CRC errado, sem aviso. A tela só dá uma dica em texto pequeno. *Recomendação:* lista de mappers com nome (`4 — MMC3`), validação em tempo real ("PRG deve ser múltiplo de 16 KB", campo destacado), valores padrão por mapper e link para o NESCartDB.

**U-08 — Campos numéricos sem unidade nem validação inline.** Os rótulos dizem "(KB)", mas aceitam qualquer dígito e o erro só vem do firmware depois do envio. *Recomendação:* validar ao digitar com os limites da seção "Opções de DUMP_ROM" do `protocolo.md`.

**U-09 — Conexão pouco comunicada.** A porta escolhida é a primeira da lista; os chips mostram nomes crus (`ttyACM0`); o estado conectado/desconectado e o firmware só existem como linha no log; desligar o USB não é detectado (as operações falham e a GUI continua "conectada"). *Recomendação:* indicador permanente (ponto verde com "Mega — firmware 0.1.0"), nome amigável da porta quando o sistema fornece, desconexão automática ao perder a porta e botão **Reconectar**.

**U-11 — Nome de arquivo e saída pouco úteis.** Sugere `rom_snes.sfc`, mesmo depois de **Detectar** ter lido o título. Jogos de GBC saem `.gb`. *Recomendação:* usar o título detectado (`TITULO_(CRC).sfc`), `.gbc` quando o cabeçalho for CGB, e oferecer gravar um `.txt` com o CRC32 e o resultado das verificações.

**U-12 — Progresso sem contexto.** Só uma barra. Operações como ligar clocks e CIC do SA-1 (~1 s), apagar a Flash do GBA (até 5 s) ou gravar uma EEPROM de 8 KB (~2 min no Mega Drive) parecem travadas. *Recomendação:* texto da etapa ("lendo cabeçalho", "apagando Flash"), velocidade e tempo restante; o tipo `PROGRESSO` já está reservado no protocolo para o firmware informar etapas.

**U-15 — Aviso de segurança física pequeno.** "Um cartucho por vez. Desligue o USB antes de trocar" é `bodySmall` no topo e some do campo de visão. Inserir cartucho com o USB ligado é o erro de maior consequência. *Recomendação:* lembrete proeminente ao **Detectar** e antes de **Gravar**, e na ajuda de primeiro uso.

**U-19 — Sem onboarding.** Nada guia a primeira execução (instalar driver, entrar no grupo `dialout`, testar com `MOCK` antes de colocar cartucho). A mensagem sobre `dialout` só aparece quando **nenhuma** porta existe. *Recomendação:* assistente curto na primeira vez: porta, **Testar conexão** (`INFO`), teste `MOCK`, depois cartucho; detectar permissão negada e explicar.

### Baixa

**U-10 — Baud como números crus.** Dois chips (`1000000`, `115200`) sem explicação; 115200 é o "plano B". *Recomendação:* tentar 1.000.000 e cair sozinho para 115.200 com aviso; esconder a escolha em "Avançado".

**U-13 — Acessibilidade.** Erro só em vermelho (sem ícone), texto de 12 sp em toda a ajuda, sem atalhos de teclado nem rótulos para leitor de tela, tema só claro. *Recomendação:* ícone e prefixo "Erro:", tamanho de fonte ajustável, atalhos (Ctrl+D detectar, Ctrl+R ler), tema escuro seguindo o sistema.

**U-14 — Textos fixos e traduções.** Nomes de sistema, "bytes" e "CRC32" fixos (aceitável para nomes próprios e siglas; "bytes" não). Traduções ru e zh sem revisão nativa. *Recomendação:* revisão por falantes, como já previsto em `continuacao.md`.

**U-16 — Ajuda em bloco único.** Duas listas longas, sem busca, sem links para `docs/uso.md`. *Recomendação:* seções recolhíveis e link para o guia completo.

**U-17 — CLI.** `save-write` não pede confirmação nem tem `--yes`; mensagens de erro misturam português e termos do protocolo; sem `--json` para automação. *Recomendação:* confirmação interativa (`--yes` para scripts), mensagens padronizadas e saída JSON opcional.

**U-20 — Hierarquia dos botões.** Detectar, Ler ROM, Ler save, **Gravar save** e Cancelar numa linha só, com o mesmo peso. *Recomendação:* separar leitura (segura) de gravação (destrutiva), destacar **Cancelar** durante a operação.

**U-21 — Preferências não persistem.** Idioma, porta, baud, sistema, último diretório e tamanho da janela voltam ao padrão a cada execução. *Recomendação:* guardar em arquivo de configuração do usuário.

## 4. Hardware e montagem (UX físico)

| Item | Situação |
|---|---|
| Silkscreen: "UM CARTUCHO POR VEZ", nome do sistema em cada slot, pino 1, versão e data, créditos do OSCR | Presentes (D24, D29). O slot GBA agora diz "GBA/GB 3V3" e "GBA E GB (ADAPTADOR) - 3,3 V". |
| Direção de entrada e lado da etiqueta de cada cartucho | **Pendente de conferir com o slot físico** (D27, D28): o texto do silk pode estar ao contrário. É a pendência de UX mais barata de errar e mais cara de descobrir depois da fabricação. |
| `docs/montagem.md` | Ordem de solda e testes antes de ligar são claros. Falta uma foto ou desenho da placa pronta com as referências (`R1`, `C2`...) e uma checklist imprimível. |
| Cartuchos de 3,3 V e 5 V no mesmo conjunto de slots | Só um aviso no silk e na GUI protege quem insere um cartucho de 5 V no slot GBA; o hardware não impede. Considerar um chanfro físico ou batente no slot GBA. |

## 5. Ordem sugerida

1. **U-01, U-02 e U-03** (perda de dados, gravação sem confirmação, resultado fora da tela): pequenos e com maior efeito; fazer antes do primeiro teste real.
2. **U-04 e U-05**: o primeiro teste com hardware vai gerar logs e erros; precisam ser legíveis, copiáveis e localizados.
3. **U-06, U-07, U-08**: reduzem erros de operação do NES.
4. **U-09, U-12, U-19**: conexão, progresso e primeira execução.
5. O restante, junto com o empacotamento.

## 6. Estado depois das correções (2026-11-02)

Verificação: a GUI foi aberta de novo no display virtual (layout e troca de idioma); **o fluxo com o Mega ligado continua sem teste** (sem porta serial nesta máquina).

| Achado | Estado |
|---|---|
| U-01 cancelar o "Salvar como" perde a leitura | **Corrigido**: a leitura fica na memória com **Salvar como...** e **Descartar** |
| U-02 gravar sem confirmação nem backup | **Corrigido**: diálogo de confirmação e backup do save atual em `~/oscr_backups` (marcado por padrão); a CLI também pergunta (`--yes`) e faz backup |
| U-03 resultado fora da tela | **Corrigido**: barra fixa embaixo com estado, progresso, última mensagem e registro |
| U-04 registro não copiável | **Corrigido**: selecionável, **Copiar** e **Salvar registro**, com versão do programa e do firmware |
| U-05 erros técnicos | **Corrigido**: mensagem traduzida com causa e ação para cada código |
| U-06 estado compartilhado | **Corrigido**: os campos zeram ao trocar de sistema |
| U-07 opções do NES | **Em parte**: nome do mapper e validação enquanto digita; **faltam** presets por jogo e o link para o NESCartDB |
| U-08 validação inline | **Corrigido** (NES, SNES ExHiROM e Mega Drive) |
| U-09 conexão | **Corrigido**: indicador permanente, nome amigável da porta, desconexão detectada, botão Reconectar |
| U-10 baud | **Corrigido**: tenta o escolhido e cai para o outro sozinho; a escolha fica em **Avançado** |
| U-11 nome do arquivo e saída | **Corrigido**: título detectado no nome, `.gbc`, relatório `.txt` opcional |
| U-12 progresso sem contexto | **Em parte**: etapa, velocidade, tempo restante e aviso de operação demorada; **faltam** as etapas que o firmware informaria (`PROGRESSO`) |
| U-13 acessibilidade | **Em parte**: ícones nos avisos, tema escuro, atalhos, texto maior; **faltam** rótulos para leitor de tela e ajuste de fonte |
| U-14 textos fixos e traduções | **Em parte**: "bytes" traduzido; revisão nativa de ru e zh pendente |
| U-15 aviso de segurança | **Corrigido**: cartão de destaque no topo e aviso no diálogo de gravação |
| U-16 ajuda | **Em parte**: seções recolhíveis e indicação do guia; sem busca |
| U-17 CLI | **Corrigido**: confirmação, `--yes`, backup, `--json`, mensagens com dica |
| U-18 hardware físico | **Aberto**: confirmar com o slot físico o lado da etiqueta e a direção de entrada (D27, D28) |
| U-19 primeira execução | **Corrigido**: cartão de primeiros passos; dica do grupo `dialout` na falha de abertura |
| U-20 hierarquia dos botões | **Corrigido**: leitura e gravação em seções separadas, gravação destacada, Cancelar em vermelho |
| U-21 preferências | **Corrigido**: idioma, porta, baud, sistema, pasta e tamanho da janela |
