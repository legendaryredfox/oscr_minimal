# Pesquisa em fóruns, wikis e repositórios da comunidade (2026-11-07)

Objetivo (pedido do usuário): ver o que a comunidade de modders e de dumping de cartuchos sabe que ajude a **melhorar, otimizar ou corrigir** este projeto, considerando os 41 consoles do OSCR que ainda não temos, e **juntar links de adaptadores existentes para a nossa documentação** (não vamos refazê-los).

## Limites desta pesquisa (leia antes de confiar)

- Feita com busca na web e leitura de páginas por agentes de busca; o texto foi **resumido por modelo**. Os números, valores e citações abaixo precisam ser **conferidos na fonte** antes de virar decisão de projeto.
- **Reddit:** nenhuma busca devolveu thread de r/consolemods, r/snes ou parecidos sobre o OSCR (só resultados de outros assuntos). O **Discord** da comunidade não é acessível. As conversas úteis estão no **GitHub (issues e discussions do `sanni/cartreader`)**, no **fórum do Arduino**, no **NESdev** e no **Retrode**.
- Falhas de leitura: `issues.ecosyste.ms` devolveu 403; a discussão #354 (adaptadores) foi lida só em parte (o resto veio resumido); os links marcados "só índice" não foram abertos.
- Nada aqui foi testado em hardware.

## 1. O que muda para nós, em ordem de valor

| # | Achado | Ação sugerida | Fonte |
|---|---|---|---|
| P-01 | **Base de dados nova e aberta do OSCR:** `oscartreader/oscr-databases` tem `data/*.json` (CRC32 + nome) para **quase todos os sistemas**: `nes` (1,5 MB), `snes`, `md`, `gba`, `gb`, `n64`, `pce`, `sms`, `gg`, `32x`, `sg`, `lnx`, `a26/a52/a78`, `c64`, `col`, `int`, `msx`, `vb`... Formato simples (`records: [{name, crc32}]`). O binário CRDB é só a versão compilada. | **Resolve a pendência do item 8 sem ler CRDB**: estender `tools/importar_base_oscr.py` para ler esses JSON (hoje usamos os `.txt` do legado, 11 sistemas, 24 007 jogos). **Licença conferida em 2026-11-07: o repositório `oscartreader/oscr-databases` não tem arquivo de licença (a API devolve 404), então a importação ficou parada à espera de decisão do usuário** (o legado que já importamos é GPL v3). | https://github.com/oscartreader/oscr-databases |
| P-02 | **Tensão do VCC no SA-1:** relato de que cartuchos SA-1 "não destravam" se o VCC do cartucho passa de ~5,2 V (hub USB a 5,28 V falhou; 5,0 V limpo funcionou; 5,3 V no HW5 falhou sempre). | Medir o 5V dos slots na primeira energização (nossa 5V vem do USB) e registrar em `montagem.md`; aceitar ≤ 5,2 V. | issue #734 (comentário de 8 dez 2023) e `Voltage.Report.pdf` anexo |
| P-03 | **Clock e SA-1:** a falha intermitente do SA-1 foi atribuída a **frequência do clock** (calibração do Si5351) e a **gerador barato de AliExpress**; a wiki tem o procedimento de calibração: pino 56 do SNES (clock do CIC) **3.072.000 Hz**, pino 1 (EXT) **4.000.000 Hz**, pino 57 (CPU) **1.000.000 Hz**, medidos com frequencímetro. Alternativa ao PIC12F629: **PIC16F630 + `supercic-lock_p16F630.hex`** (um relato diz que dá mais sucesso). | Implementar "Calibrar o relógio" (⬜ em `docs/funcoes-oscr.md`) usando esses alvos; pontos de teste no clock (v1.3); documentar a alternativa PIC16F630 em `tools/pic/`. | wiki `Calibrating-the-ClockGen`, `Flashing-the-snesCIC`; issue #734; fórum Arduino |
| P-04 | **Ligar e desligar o 5V do cartucho ajuda no SA-1** (os relatos falam em "esperar os capacitores descarregarem"; um capacitor grande no VCC do cartucho atrapalha o tempo do destravamento). Nossa v1.2 já tem a chave de 5V (Q1, D108). | Comando `POWER` no protocolo (hoje falta) + **ciclo de energia automático antes de cada tentativa de SA-1** + resistor de descarga. Ver `docs/troca-de-cartucho.md`. | issue #734; D108 |
| P-05 | **Ler duas vezes e comparar.** O CRC contra a base só confere jogos conhecidos; o checksum do cabeçalho do SNES é fraco; um usuário de GBA relatou **1 bit trocado a cada ~1000 palavras** (tempo ou integridade de sinal; sem solução no fórum). O dumping.guide recomenda limpar, ler, e se não achar na base, limpar e ler de novo comparando SHA-256. | Opção `dump --twice` (**feita nas CLIs, D125**) / caixa na GUI "Ler a ROM 2 vezes e comparar" (**feita**). Barata e útil sem base. | dumping.guide; fórum Arduino post 1401 |
| P-06 | **Forçar tipo e tamanho no SNES** (hoje só ExHiROM aceita tamanho): CRC errado de SF2 Turbo foi corrigido forçando 20 Mbit; repros multijogo (Retro-Bit/JNNEX) só saem forçando "4MB LoROM 256K SRAM"; cabeçalhos mentem (SuperFX tem 64 KB de RAM com cabeçalho 0, Game Genie 0 KB vs 64 KB, Sufami Turbo 0 KB vs 1 MB). | Permitir `--prg` e tipo para todos os tipos de SNES na CLI e na GUI. **Conferido em 2026-11-07:** o firmware (`snesProbe(sizeKb)`) já aplica `prg_kb` a todos os tipos, não só ao ExHiROM; falta só liberar o campo no host (`NesRules.kt` e `parser.py` ainda dizem "só ExHiROM") e, para o **tipo**, um campo novo (o `mapper` do SNES já é o código do chip em `WRITE_ROM`, então não serve sem separar os caminhos). Não feito: exige firmware que não rodou em hardware. | discussions #525, issue #1001; dumping.guide (SNES) |
| P-07 | **Aviso de 3,3 V.** Algumas placas aftermarket, não licenciadas e flashcarts só aceitam 3,3 V; 5 V pode danificá-las **e o dumper**. As páginas de Mega Drive, NES e GB do dumping.guide avisam. Nossos slots de SNES, NES, Famicom e Mega Drive são 5 V fixos (decisão do projeto). | Aviso em `docs/uso.md` e na GUI antes de ler flashcart ou cartucho não licenciado. | dumping.guide |
| P-08 | **Conversor de ordem de bytes dos saves** para emulador (Genesis, N64, GB): utilitário da comunidade existe. | Ver se o save do Mega Drive (ímpar/par) já sai na ordem certa; oferecer conversão. | discussion #593 |
| P-09 | **Mega Drive, EEPROM e chips especiais:** carteiras Acclaim "Type 2" têm PAL antes da EEPROM e exigem init; cartuchos Codemasters usam PAL e precisam de **CLK** (o shield de MD do OSCR não tem pino CLK; o autor ligou CLK ao `/C_CE`); vários Codemasters repetem o checksum do Micro Machines 96 (separar pelo primeiro DWORD); só as versões **J-Cart** do Micro Machines têm EEPROM serial; **EEPROM só em originais, repros não**; NBA Jam T.E. rev 0 apaga o próprio save. | Conferir no `MegaDrive.cpp` do upstream o que já está tratado (38 checksums) e documentar os casos que não. | fórum Arduino, posts 857 a 860 |
| P-10 | **NES:** o cabeçalho iNES do OSCR vem de uma base "que pode estar incompleta"; fontes de mapper e tamanho: nescartdb.com, bootgod, nes.dnsabr.com. Cartuchos de FamicomBox exigem ligar os pinos 69-71 e 70-36 do conector NES e **não se deve usar adaptador FC-NES que ligue os pinos de som de expansão**. Conectores de 72 pinos gastos voltam a funcionar entortando os pinos. | Link do NESCartDB na GUI (pendente); nota em `docs/limites-nes.md`. | dumping.guide; fórum Arduino post 1540; NESdev |
| P-11 | **Flash do GB e do GBA:** o FlashGBX (lesserkuma) é referência independente com a lista mais completa de chips e sequências. Armadilhas confirmadas: **D0 e D1 trocados** em muitos carts (escrever 0x56 onde a folha diz 0x55; CFI "QRY" aparece como "R,Q,Z" se trocado), apagamento **por setor**, espera por DQ7, regiões de setor lidas do CFI. Sempre "analisar o cartucho" antes de gravar. | Usar as listas de chips do FlashGBX para **conferir** as nossas (29F, 39SF, CFI, Intel 4000/4400, MX29GL128E, MSP55LV128, M29W128GH); conferir que nossa gravação lê de volta tudo (já fazemos). A frase "chips 6600/4050M não funcionam" veio de busca e **o README do FlashGBX os lista como suportados**: não confiar. | https://github.com/lesserkuma/FlashGBX ; gbadoc |
| P-12 | **Autoteste do OSCR:** o firmware original tem um "Self Test" (sem cartucho) que acha curto para GND e curtos entre pinos e diz quais ("Pin A12 + D49"). | Considerar um comando `SELFTEST` no protocolo + botão na GUI: ajuda muito na montagem (`montagem.md` seção 5). Avaliar se o núcleo do upstream dá para chamar direto. | wiki `Troubleshooting` |
| P-13 | **Si5351:** a wiki avisa para alinhar o conector (o pino "3V BAT" não pode ligar; não usar header de 8 pinos; **ligar ao contrário queima o módulo**) e que módulos baratos variam. O módulo Adafruit tem regulador e conversor de nível no I²C; genéricos podem não ter (o Mega põe 5 V nas linhas). | Reforçar em `montagem.md`: orientação do módulo e conferir o nível do SDA/SCL antes de ligar (já era C-15). | wiki `Build-Guide`; Adafruit |
| P-14 | **Serial USB:** relatos de 1 Mbaud funcionando em Mega com 16U2; nada específico sobre CH340. Problemas de alta velocidade costumam ser do lado do PC (Windows). | Nosso protocolo já tem CRC32 e ACK. Opcional: baud intermediário de 500000 na rotina de fallback. | fórum Arduino (vários) |
| P-15 | **Upstream:** `sanni/cartreader` foi **arquivado em 15 jun 2026** (somente leitura). O desenvolvimento está em `github.com/oscartreader`. O nosso fork (`firmware/oscr`) está no commit `d9cb26a`, que era o **topo do `oscr-firmware` em 28 jul 2026**. `oscartreader/oscr-hardware` estava **vazio** na consulta. | Acompanhar `oscr-firmware`; os projetos KiCad dos adaptadores oficiais continuam em `sanni/cartreader/hardware/`. | API do GitHub |
| P-16 | **Adaptadores de slot SNES da comunidade funcionam no slot SNES das nossas placas?** Quase todos os adaptadores dos consoles extras (tabela da seção 3) encaixam no slot de SNES do OSCR HW5, em PCB de **1,2 mm**. Nossas placas com slot de SNES herdam a pinagem do HW5 (regra de ouro). **Mas** os de **3,3 V** (Leapster, V.Smile, Pokémon Mini, Little Jammer Pro) **não podem** ir no nosso slot de 5 V fixo, e o PIC/CIC usa pinos do slot. | Antes de recomendar qualquer adaptador, conferir pino a pino com `boards/*/docs/pinmap.md`. Para 3,3 V, só com a placa `completa` (a definir) ou o slot GBA. | discussão #354 |
| P-17 | **Projetos parecidos com o nosso** (USB, sem SD): `niwakazoider/Serial_CartDumper` ("Cartridge Dumper for CartReader", 2022), `DragonBox-Shop/retrode3-oscr` ("adaptação em linha de comando para Linux do OSCR e da retrode.lib", ago 2026), `Gand46/MegaBurner_MX29L3211_HTLM` (Web Serial no navegador para MX29L3211 com Arduino Mega, out 2026). | Ler o que eles fizeram no protocolo e na gravação do MX29L3211 e comparar. | seção 4 |

## 2. Detalhes por tema (com fonte)

### SNES e SA-1
- Issue #734 (aberta desde mar 2023, ainda aberta): cartuchos SA-1 como PGA Tour 96 dão "Rom header corrupt or missing". Causas citadas: PIC12F629 + `snescic-lock-resync.hex` (trocar por PIC16F630 resolveu em um caso), clock do gerador diferente do console real, cartucho com contatos sujos (limpar com removedor de adesivo e limpa-contato), tensão do VCC acima de 5,2 V, gerador de clock barato. Sanni: os SA-1 dele eram "temperamentais"; esperar os capacitores descarregarem ajudou. Um relato mede 5.000 tentativas com < 1 % de falha com PIC16F630. Último comentário (nov 2024): refazer a calibração do clock resolveu.
- A wiki permite pular o PIC fechando as ilhas de solda do CIC ("destravar o SA-1 pelas ilhas, pode levar mais tentativas").
- Cartuchos da Nintendo Power (SFM): um usuário relata que o SF Memory deu timeout até desligar o VSELECT; outro, que o firmware antigo `NP.ino` lia sem o gerador de clock.
- Saves "não gravam" em repro chinês: o mantenedor diz que SRAM escreve a 5 V; o caso real foi um resistor fora do lugar na placa do usuário (discussão #499).

### Energia, tensão e troca de cartucho
- A wiki do OSCR manda ligar o leitor, inserir o cartucho e então escolher o sistema; a restrição "não ligar com cartucho de 3,3 V" foi retirada no firmware V13.2 (discussão #906, não lida). O dumping.guide ainda avisa que cartuchos só de 3,3 V podem ser danificados e danificar o dumper.
- Slot de N64 exige espaçamento de 2,5 mm; muitos slots de AliExpress são 2,54 mm. (Os nossos NES/SNES são 2,5 mm e Famicom/Mega Drive 2,54 mm por decisão do projeto.)
- Retrode (fórum): slots de 2,54 mm têm alto risco de curto entre contatos; adaptadores de PCB precisam de **1,2 mm** exatos.
- Nossa pergunta sobre desligar o shield para trocar cartucho: ver `docs/troca-de-cartucho.md`.

### NES / Famicom
- O dumping.guide lista fontes de mapper/tamanho: `nes.dnsabr.com`, `bootgod.dyndns.org:7777`, `nescartdb.com`, `tuxnes nesmapper.txt`. O RetroBlaster não detecta mapper (o usuário informa), como a nossa GUI.
- Erros de cabeçalho: uma base incompleta exige corrigir o iNES à mão (ferramentas inestool e "INES header fixer"). Revisões diferentes do mesmo jogo têm CRCs diferentes (Mega Man 4): CRC fora da base nem sempre é dump ruim.

### Mega Drive
- Ver P-09. Também: 32X lê como cartucho comum; Sega CD é outro assunto (disco). Projetos de dumper próprios: Sega4ever MD-Dumper (STM32, USB), GenDumper (tonyp7), MDreader.

### Game Boy e GBA
- FlashGBX 3.37 (última encontrada) inclui firmware R42+L11 do GBxCart RW v1.4/1.4a. Notas úteis: velocidade de gravação de MSP55LV128M e S29GL128 depende do firmware R23+; chips Sharp exigem R25+; um problema de gravação em hardware antigo v1.3 foi corrigido na 3.29.
- GBA bootleg: sem bateria, o save vai para a própria flash (apaga setores com 0xFFFF); "analisar o cartucho" antes de ler ou gravar; contato instável é a causa mais comum de erro de leitura/gravação; limpar com IPA 99,9 %.
- A página de GBA do dumping.guide **não cobre OSCR** (só GBxCart RW, Joey Jr, RetroBlaster e métodos por DS).

### Serial USB
- Relatos soltos de 1 Mbaud estável em Mega 2560 com 16U2; nenhuma fonte sobre CH340 a 1 Mbaud; recomendação geral: medir perda com checksum/sequência e testar 500000 se houver erro.

## 3. Os 41 consoles: adaptadores existentes (links)

Origem: discussão `sanni/cartreader#354` ("User-contributed PCBs and adapters", lida por agente; só a parte inicial é texto original). **Quase todos são para o slot de SNES do OSCR HW5, PCB de 1,2 mm.** Autores: `sakman55` (maioria), `partlyhuman`, `Cephiros`, `splash5`, `herzmx`, `SAVE-THE-HERO`. Os arquivos `.zip` de gerbers estão hospedados no GitHub do `sanni/cartreader` (anexos de comentário). "—" = nenhum adaptador encontrado. Os oficiais ficam em https://github.com/sanni/cartreader/tree/master/hardware (`cic_adapter`, `famicom_adapter`, `loopy_adapter`, `main_pcb_hw5`, `mastersystem_adapter`, `megadrive_adapter`, `n64_adapter`, `nes_adapter`, `six_slot_adapter`, `snes_adapter`, `vselect`).

| Id no projeto | Console | Tensão | Adaptador (link) |
|---|---|---|---|
| `a2600` | Atari 2600 | 5 V | https://github.com/sanni/cartreader/files/10367698/Atari.2600.Adapter.zip |
| `a5200` | Atari 5200 | 5 V | https://github.com/sanni/cartreader/files/12571079/Atari.5200.Adapter.zip |
| `a7800` | Atari 7800 | 5 V | v0.1 https://github.com/sanni/cartreader/files/12571080/Atari.7800.Adapter.zip ; v0.2 (bankset) https://github.com/sanni/cartreader/files/14680657/Atari.7800.Adapter.v0.2.zip |
| `a8bit` | Atari 8-bit | 5 V | https://github.com/sanni/cartreader/files/15445470/Atari.8bit.Adapter.zip |
| `jaguar` | Atari Jaguar | — | https://github.com/user-attachments/files/16446406/Atari.Jaguar.Adaptor.zip (precisa de fio de correção ou dois adaptadores) |
| `lynx` | Atari Lynx | — | https://github.com/partlyhuman/cartreader/tree/adapter-snes-atari-lynx/hardware/lynx_snes_adapter/ (CC-BY-4.0; precisa de conector SMD de reposição) |
| `astrocade` | Bally Astrocade | — | https://github.com/sanni/cartreader/files/14234223/Bally.Astrocade.Adapter.zip |
| `loopy` | Casio Loopy | — | oficial: https://github.com/sanni/cartreader/tree/master/hardware/loopy_adapter ; alternativa https://github.com/partlyhuman/cartreader/tree/loopy-adapter-makeshift/hardware/loopy_adapter/loopy_adapter_makeshift/ (liga direto no OSCR; `#define ENABLE_LOOPY`) |
| `pv1000` | Casio PV-1000/PV-2000 | — | https://github.com/sanni/cartreader/files/14234224/Casio.PV-1000.Adapter.zip |
| `channelf` | Fairchild Channel F | — | https://github.com/sanni/cartreader/files/10367705/Fairchild.Channel.F.Adapter.zip |
| `coleco` | ColecoVision | — | https://github.com/sanni/cartreader/files/10367702/Colecovision.Adapter.zip ; 3 em 1: https://github.com/sanni/cartreader/files/10460184/IPC2S_RC1.zip (**VCC/GND ligados errado segundo um comentário de fev 2025: não confiar**) |
| `c64` | Commodore 64 | — | https://github.com/sanni/cartreader/files/12571081/Commodore.64.Adapter.zip |
| `vic20` | Commodore VIC-20 | — | https://github.com/sanni/cartreader/files/14234225/Commodore.VIC-20.Adapter.zip |
| `cps3` | Capcom CPS3 | — | https://github.com/herzmx/CPS3-OSCR-Adapter (KiCad, BOM, gerbers) |
| `intellivision` | Intellivision | — | https://github.com/sanni/cartreader/files/10367707/Mattel.Intellivision.Adapter.zip ; 3 em 1 (mesma ressalva): https://github.com/sanni/cartreader/files/10460184/IPC2S_RC1.zip |
| `leapster` | Leapster / L-MAX | **3,3 V** | https://github.com/sanni/cartreader/files/15445471/Leapster.Adapter.zip |
| `jammer` | Little Jammer | 5 V | https://github.com/sanni/cartreader/files/14736867/Bandai.Little.Jammer.Adapter.zip |
| `jammerpro` | Little Jammer Pro | **3,3 V** | https://github.com/sanni/cartreader/files/14736869/Bandai.Little.Jammer.Pro.Adapter.zip |
| `n64` | Nintendo 64 | 3,3 V | oficial: https://github.com/sanni/cartreader/tree/master/hardware/n64_adapter ; projeto só N64: https://github.com/jgazeley/n64cartreader ; dumper USB para N64 (GitLab): https://gitlab.com/wolfre/usb-cart-reader |
| `vb` | Virtual Boy | — | https://github.com/sanni/cartreader/files/10367709/Nintendo.VirtualBoy.Adapter.zip |
| `pokemini` | Pokémon Mini | **3,3 V** | https://github.com/sanni/cartreader/files/11717129/Pokemon.Mini.Adapter.zip (usa conector de console doador) |
| `ngp` | Neo Geo Pocket | — | só índice (não aberto): https://github.com/sanni/cartreader/discussions/614 |
| `odyssey2` | Odyssey 2 / Videopac | — | https://github.com/sanni/cartreader/files/10367706/Magnavox.Odyssey.2.Adapter.zip |
| `pce` | PC Engine / TurboGrafx-16 | — | só índice (não aberto): https://github.com/sanni/cartreader/discussions/345 ; também no 3 em 1 acima |
| `pcw` | Pocket Challenge W | — | https://github.com/sanni/cartreader/files/10367699/Benesse.Pocket.Challenge.W.Adapter.zip |
| `rca2` | RCA Studio II | — | **nenhum adaptador encontrado** (o firmware tem o núcleo) |
| `satellaview` | Satellaview (BS-X) | 5 V | sem adaptador: usa o slot de SNES (cartucho BS-X; precisa do gerador de clock). Regravar 8M: wiki `Reflashing-BSX-8M-carts` |
| `sfm` | SF Memory (Nintendo Power) | 5 V | sem adaptador: slot de SNES, precisa de clock. Wiki `Reflashing-NP-carts` |
| `sms` | Master System | 5 V | oficial: https://github.com/sanni/cartreader/tree/master/hardware/mastersystem_adapter ; Mark III/SG-1000 pelo adaptador da Raphnet |
| `supercan` | Super A'can | — | https://github.com/sanni/cartreader/pull/715 (slot de NES de 72 pinos modificado, cartucho com a etiqueta para cima) |
| `supervision` | Watara Supervision | — | https://github.com/sanni/cartreader/files/10367710/Watara.Supervision.Adapter.zip |
| `ti99` | TI-99/4A | — | https://github.com/sanni/cartreader/files/14234227/TI-99.Adapter.zip |
| `pyuuta` | Tomy Pyuuta | — | https://github.com/sanni/cartreader/files/14234228/Tomy.Pyuuta.Adapter.zip |
| `trs80` | TRS-80 Color Computer | — | https://github.com/sanni/cartreader/files/14234230/TRS-80.Color.Computer.Adapter.zip |
| `vectrex` | Vectrex | — | v0.1 https://github.com/sanni/cartreader/files/12571082/Vectrex.Adapter.zip ; v0.2 https://github.com/sanni/cartreader/files/13757714/Vectrex.Adapter.v0.2.zip |
| `vsmile` | V.Smile | **3,3 V** | https://github.com/sanni/cartreader/files/15445474/V.Smile.Adapter.zip |
| `ws` | WonderSwan | — | só índice (não aberto): https://github.com/sanni/cartreader/pull/337 ; página da wiki: `WonderSwan-(Color)` |
| `msx` | MSX | — | https://github.com/sanni/cartreader/files/11717120/MSX.Adapter.zip |
| `arcadia` | Arcadia 2001 | — | https://github.com/sanni/cartreader/files/10367703/Emerson.Arcadia.2001.Adapter.zip |
| `gbsmart` | Game Boy Smart Card (EMS) | 5 V | sem adaptador: slot de GB do adaptador GBx do OSCR (wiki: `Writing-custom-flashcarts`) |
| `gbmem` | Game Boy Memory (Nintendo Power) | 5 V | sem adaptador: slot de GB; wiki `Reflashing-NP-GB-Memory-carts` |

Outros consoles que o OSCR cobre e **não** estão nos 41 (já suportados por nós ou por adaptador): Game Gear (https://github.com/StarshadeRETRO/KiCadFiles/tree/main/GameSystems/Adapters/SMS-to-GG e `gg_adapter.zip` https://github.com/sanni/cartreader/files/10682784/gg_adapter.zip), Mark III e SG-1000 (adaptador da Raphnet).

**Avisos sobre esta tabela:** (1) os `.zip` são anexos de comentário do GitHub e podem sumir; baixe uma cópia antes de depender deles; (2) a licença de cada adaptador é a do autor (os de `partlyhuman` são CC-BY-4.0; os oficiais seguem a licença do repositório, CC BY 4.0 no hardware); (3) "só índice" significa que o link veio de uma lista e não foi aberto.

## 4. Outros projetos encontrados (GitHub, GitLab, Codeberg)

Buscas pelas APIs públicas: **GitHub** (várias consultas), **GitLab** (`/api/v4/projects?search=`), **Codeberg** (`/api/v1/repos/search`). Na **Codeberg** nenhum resultado relevante (a busca devolve ruído); no **GitLab** só os dois da tabela.

| Projeto | O que é | Relevância |
|---|---|---|
| https://github.com/oscartreader/oscr-firmware | firmware atual do OSCR (org nova) | upstream do nosso fork |
| https://github.com/oscartreader/oscr-databases | JSONs de CRC32/nome de todos os sistemas | P-01 |
| https://github.com/oscartreader/oscr-hardware | "arquivos de projeto de hardware" (vazio na consulta) | acompanhar |
| https://github.com/makhowastaken/cartreader | "versão menor, mais portátil e modular" do cartreader (Makho) | outra variante mínima |
| https://github.com/herzmx/CPS3-OSCR-Adapter | adaptador CPS3 | tabela |
| https://github.com/jgazeley/n64cartreader | versão só N64 do OSCR | tabela |
| https://github.com/DragonBox-Shop/retrode3-oscr | adaptação em linha de comando para Linux do OSCR | P-17 |
| https://github.com/niwakazoider/Serial_CartDumper | "Cartridge Dumper for CartReader" (serial) | P-17, parecido com o nosso |
| https://github.com/Gand46/MegaBurner_MX29L3211_HTLM | HTML/Web Serial para programar MX29L3211 com Arduino Mega | P-17 |
| https://github.com/Diplomatic-Entertainment/JustAnotherCartridgeReader | "derivado do OSCR" | ver |
| https://gitlab.com/wolfre/usb-cart-reader | leitor USB de N64 e saves, "foco em estrutura limpa e documentação" | N64 |
| https://gitlab.com/FermataRest/SanniOSCR | repositório sem descrição (GitLab) | não aberto |
| https://github.com/lesserkuma/FlashGBX | software de GBxCart RW/Joey Jr/GBFlash | P-11 |
| https://github.com/ClusterM/famicom-dumper-writer | dumper de Famicom (STM32 + CPLD), mappers em scripts C# | referência de mappers |
| https://github.com/tonyp7/GenDumper | dumper de Mega Drive de código aberto | referência |

## 5. Fontes principais (links)

Ver também o arquivo `links-oscr-foruns-e-projetos.md` (mesma lista, em formato de consulta) que o usuário pediu na área de trabalho.

- Wiki do OSCR: https://github.com/sanni/cartreader/wiki (páginas: Troubleshooting, Build-Guide, Calibrating-the-ClockGen, Flashing-the-snesCIC, Automatic-Voltage-Selection, Supported-Systems, List-of-user-created-Adapters, Designing-your-own-Adapters). A wiki é um repositório Git público: `git clone https://github.com/sanni/cartreader.wiki.git`.
- Fórum do Arduino (thread longa do sanni, mais de 80 páginas): https://forum.arduino.cc/t/rom-reader-for-super-nintendo-super-famicom-game-cartridges/155260
- dumping.guide: https://dumping.guide/carts/nintendo/snes , /nes , /gba , /gameboy , /n64 , https://dumping.guide/carts/sega/mega-drive-genesis , /master-system , https://dumping.guide/carts/nec , https://dumping.guide/tools/hardware . O site **não tem páginas** para os consoles Atari, Bally, Casio, Fairchild, ColecoVision, Commodore, Intellivision, Leapster, Pokémon Mini, Neo Geo Pocket, Odyssey 2, Super A'can, Watara, TI-99, TRS-80, Vectrex, V.Smile, WonderSwan, MSX, Arcadia (`/carts/atari` é um espaço vazio) e tem só rascunho de Virtual Boy e Game Gear.
- NESdev (dump de NES): https://nesdev.nes.science/f9/t14131.xhtml (BennVenn's NES Cart Dumper), https://archive.nes.science/nesdev-forums/f10/t2857.xhtml (NES cartridge dumping), https://nesdev.nes.science/f5/t15210.xhtml (revisões e dumps).
- Retrode: https://forum.retrode.com/index.php?msg=2833 (SSF2 e SRAM do Mega Drive).
- Issues e discussões do OSCR: #734 (SA-1), #1001 (repros multijogo), #525 (SF2 Turbo), #499 (saves), #593 (conversão de save), #913 (SF Memory), #354 (adaptadores).

## 6. Não encontrado

- Conteúdo de r/consolemods e similares (ver "Limites").
- Orientação de ESD/hot-swap específica para dumpers de NES (a NESdev só fala de conector desgastado).
- Dado sobre CH340 a 1 Mbaud.
- Nível do I²C do Si5351 em módulos genéricos (a wiki só diz "Adafruit ou AliExpress").
- Valor de correção do Si5351 usado por quem consertou o SA-1 (ninguém publica o número; é por unidade).
