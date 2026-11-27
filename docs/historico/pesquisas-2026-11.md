# Pesquisas de 2026-11 (registro)

Pesquisas datadas, guardadas como registro: o que se achou, de onde veio e o que se decidiu na hora. O que virou trabalho está em `docs/decisoes.md` e nos planos; a pesquisa da comunidade (P-01 a P-17), que o `tools/check_adaptadores.py` confere, fica em `docs/historico/pesquisa-comunidade.md`.

- [Repositórios de referência baixados e o que aprender deles (2026-11-13)](#pesquisa-repos-referencia)
- [Placas de cartucho open source e ROMs especiais (pendências futuras)](#placas-cartuchos-open-source)
- [Upstream `oscartreader/oscr-firmware`: o que mudou desde `d9cb26a` (D-3, P-15)](#upstream-oscr-firmware)
- [Corrente do regulador de 3,3 V (MCP1700) com GBA e N64 (K-3)](#estimativa-corrente-u3)
- [Pesquisa: Pier Solar e mappers piratas do Mega Drive (2026-11-17)](#pier-solar)

<a id="pesquisa-repos-referencia"></a>

## Repositórios de referência baixados e o que aprender deles (2026-11-13)

Pedido do usuário: achar mais repositórios e projetos open source de dumpers de cartucho, baixar os mais promissores para `references/`, analisar o firmware deles e dizer que melhorias ou recursos cabem aqui. **Nada foi adicionado ao projeto a partir desta análise: cada item da seção 3 espera a aprovação do usuário.**

### 1. O que foi baixado

Cópias rasas (`git clone --depth 1`) em `references/repos/` (pasta ignorada pelo git; já existia `references/REFERENCES.md`, de 2026-11-04, com um índice de outros projetos). Nada do que veio foi executado nem compilado. A licença abaixo é a que a API do GitHub informou; conferir o arquivo `LICENSE` de cada um antes de copiar qualquer código.

| Pasta | Origem | Commit | Licença | O que é |
|---|---|---|---|---|
| `FlashGBX` | github.com/Lesserkuma/FlashGBX | `5b2398b` | GPL-3.0 | Software (Python) para GBxCart RW, GBFlash, Joey Jr e Game Bub: ROM, save, flash repro de GB e GBA, **bases de dados** de jogos e **tabelas de comandos de flash** |
| `GBxCart-RW` | github.com/insidegadgets/GBxCart-RW | `7fca4aa` | não declarada | Firmware (PIC/AVR) e software do GBxCart RW |
| `famicom-dumper-writer` | github.com/ClusterM/famicom-dumper-writer | `5590062` | GPL-3.0 | Firmware STM32 + CPLD e hardware do dumper de Famicom/NES |
| `famicom-dumper-client` | github.com/ClusterM/famicom-dumper-client | `3188bd0` | GPL-3.0 | Cliente em C# do dumper acima: mappers em **scripts**, FDS, COOLBOY/COOLGIRL, gRPC |
| `INL-retro-progdump` | gitlab.com/InfiniteNesLives/INL-retro-progdump | `7f21176` | (ver o repositório) | Firmware (AVR e STM32) e host em Lua do INL-retro / Kazzo: mappers de NES em scripts |
| `SNES_Dumper` | github.com/X-death25/SNES_Dumper | `922232c` | GPL-3.0 (software; firmware do hardware vendido é fechado) | Dumper USB-C de SNES: LoROM, HiROM, ExHiROM, DSP, Super FX, S-DD1; SA-1 em andamento |
| `UMDv3` | github.com/db-electronics/UMDv3 | `430d501` | não declarada | Firmware STM32F407 do Universal Mega Dumper v3 (em estágio inicial, abr/2024) |
| `Universal-Mega-Dumper` | github.com/db-electronics/Universal-Mega-Dumper | `e610d9e` | GPL-3.0 | Versão anterior do UMD (2021) |
| `n64cartreader` | github.com/jgazeley/n64cartreader | `e27beb9` | não declarada (ver `LICENSES/`) | "N64 Pico Cart Reader V2": Raspberry Pi Pico, ROM, saves, Controller Pak, GameShark, **interface Web Serial**, validação com referências "douradas" |
| `Dreamdumper` e `drmdmp64_mass` | github.com/khill25 e nopjne | `a5cb514`, `195e2c2` | não declarada | Leitores de N64 (o segundo aparece como **disco USB**) |
| `retrode3-oscr` | github.com/DragonBox-Shop/retrode3-oscr | `3bbc215` | GPL-3.0 | Adaptação do OSCR em **linha de comando no Linux** para o Retrode3 (parecida com o nosso rumo, sem protocolo próprio) |
| `GenDumper` | github.com/tonyp7/GenDumper | `f049c3f` | (ver o repositório) | Dumper de Mega Drive em USB |
| `pico_rom_dump` | github.com/queueRAM/pico_rom_dump | `5508d41` | MIT | Pico lendo uma ROM paralela genérica |
| `shawazu-gb-dumper-hardware` | github.com/tihmstar/shawazu-gb-dumper-hardware | `57f34ca` | não declarada | Hardware de um dumper de GB/GBC/GBA |

Não achei: o firmware do **Retrode 2** (só binários; o autor não publicou o código) e o projeto "Tuna" do norix-v (o endereço dava 404).

### 2. O que cada um mostra

- **FlashGBX** é o mais rico. `FlashGBX/config/db_AGB.json` (2.948 jogos de GBA) e `db_DMG.json` (3.136 de GB) dão, para cada jogo, o **tipo de save (`st`) e o tamanho do save (`ss`)**, o tamanho da ROM e o CRC32; a chave é o **SHA-1 dos primeiros 0x180 bytes do cabeçalho** (`RomFileAGB.py`, linha 197 e seguintes). Hoje, no GBA, o nosso programa só adivinha o tipo de save procurando a cadeia da biblioteca de save na ROM (`FLASH1M_V`, `EEPROM_V`). Há também `fc_*.txt` (sequências de comando de dezenas de flash carts), "Dump Report" (relatório de preservação com hashes), decodificação de fotos do Game Boy Camera, leitor de e-Reader, backup de RTC e de saves "sem bateria", e uma lista de mappers de GB bem mais longa que a do OSCR (MBC1M, MMM01, M161, HuC-3, TAMA5, Sachen, Wisdom Tree, Datel...). O firmware L16 do GBxCart traz uma opção de **controle de fluxo** com janelas de 64 bytes por confirmação, para estabilidade.
- **famicom-dumper-client**: mappers descritos em **scripts C#** no PC (o firmware só faz leitura e escrita de barramento), então um mapper novo não exige regravar o firmware; leitura e gravação de **FDS**; saída em **NES 2.0** e **UNIF** (com `--battery`, tamanhos de PRG/CHR RAM e NVRAM); `--verify`, `--lock` (proteção de setores da flash depois de gravar), `--reset` (simula o reset do console) e `--sound` (aviso sonoro no fim); modo **servidor gRPC** para qualquer linguagem. O `INL-retro-progdump` faz o mesmo com Lua.
- **UMDv3**: cada adaptador de cartucho tem um **MCP23008** que **identifica o console** pelo I²C, e o firmware configura o barramento sozinho. O `SNES_Dumper` oferece `-read auto` ("modo automático"). Em ambos, o usuário não escolhe o sistema.
- **n64cartreader**: (1) **catálogo embutido** que identifica jogo, tamanho de ROM e tipo de save (o que fizemos agora na D158, pelo CRC1); (2) **interface Web Serial**: uma página HTML + JavaScript que fala com o dumper direto pelo Chrome ou Edge, sem instalar nada; (3) **matriz de validação** (`n64_validation_matrix.py`, `n64_cart_verify.py`): cada cartucho "dourado" tem hashes SHA-256 conhecidos, exporta-se, grava-se, relê-se e compara-se; (4) **procedimento de teste de fabricação** (`docs/MANUFACTURING_TEST.md`) para a placa recém-montada; (5) limitações conhecidas: **contenção do Joybus** quando cartucho e controle dividem o fio de dados, e reencaixar o cartucho antes de repetir a leitura da EEPROM depois de trocar o cartucho.
- **retrode3-oscr**: confirma o caminho que seguimos (OSCR com linha de comando no PC), mas sem protocolo de blocos com CRC nem GUI; as nossas camadas (CRC32 por bloco, ACK, JSON) vão além.

### 3. Propostas (todas aguardam aprovação do usuário)

| # | Proposta | Origem | Esforço | Valor | Risco |
|---|---|---|---|---|---|
| P1 | **MD5 e SHA-1 além do CRC32** nos `dump` (CLI, JSON, GUI e relatório), porque o No-Intro e o Redump catalogam por SHA-1 | FlashGBX (relatório), prática de preservação | baixo | médio | nenhum |
| P2 | **Tipo de save do GBA e do GB pela base do FlashGBX**: depois do dump, o SHA-1 do cabeçalho acha `st` e `ss` e o programa sugere `--mapper` e o tamanho do save (hoje é manual) | `db_AGB.json`, `db_DMG.json` (GPL-3.0) | baixo a médio (carregador como o do N64) | alto para GBA | baixo (só sugere) |
| P3 | **Suíte de bancada com cartuchos "dourados"** para todos os sistemas (hoje só o Mega Drive tem `hwtest_md.py`): hashes SHA-256 conhecidos, leitura duas vezes, gravação e releitura de save, relatório; mais o **procedimento de teste de fabricação** da placa (autoteste, 5 V e 3,3 V, primeiro dump) | `n64cartreader` | baixo | alto na primeira montagem | nenhum (só leitura por padrão) |
| P4 | **Aviso ao terminar** (sinal sonoro na CLI com `--sound`, notificação na GUI) em operações longas (gravar 8 MB, ler N64 de 64 MB) | `famicom-dumper-client` | baixo | médio | nenhum |
| P5 | **Detecção automática do sistema** (`detect` sem `-s`, "Automático" na GUI): tenta cada sistema em ordem e diz o que está no slot | UMDv3 (ID do adaptador), `SNES_Dumper` (`-read auto`) | médio | médio | **médio**: sondar o sistema errado põe os sinais do Mega (5 V) nos pinos de um cartucho de 3,3 V (N64, GBA); só valeria com ordem segura (3,3 V por último, só leitura) |
| P6 | **Comando `peek` somente leitura** (lê N bytes de um endereço num sistema) para diagnóstico na primeira montagem, sem escrever nada | `INL-retro`, `famicom-dumper-client` (script) | médio (protocolo + firmware + CLIs) | médio | baixo se for só leitura |
| P7 | **Interface Web Serial** (uma página que fala com o dumper pelo navegador, sem instalar) | `n64cartreader/host-tools/web` | alto (uma terceira implementação do protocolo, além da CLI e da GUI) | médio | baixo, mas custo de manutenção |
| P8 | **Mappers de NES descritos em scripts no PC** (firmware só com leitura e escrita de barramento), para passar dos 37 mappers do OSCR sem regravar o Mega | `famicom-dumper-client`, `INL-retro-progdump` | muito alto (muda a arquitetura do NES) | alto a longo prazo | alto |
| P9 | **Extrair as fotos do Game Boy Camera** de um save (arquivo `.sav` do cartucho de câmera) para PNG | `FlashGBX/PocketCamera.py` | médio | baixo | nenhum |
| P10 | **Mais mappers e chips de GB/GBA**: tabelas `fc_*.txt` e lista de mappers (MBC1M, MMM01, M161, HuC-3, TAMA5, Sachen...) para ampliar o `rom-write` do GB e do GBA | FlashGBX | alto (vem do núcleo do OSCR em C++; é código novo no firmware) | médio | médio |

Itens que **não** recomendo agora: leitor de e-Reader e visualizador da câmera ao vivo (exigem hardware próprio), disco USB (o Mega 2560 não faz armazenamento em massa), servidor gRPC (a CLI com `--json` e `--progress jsonl` já serve a qualquer linguagem), controle de fluxo em janelas de 64 bytes (já temos ACK e CRC32 por bloco).

### 4. Notas de licença

`FlashGBX`, `famicom-dumper-*` e `SNES_Dumper` (software) são GPL-3.0, a mesma licença do firmware daqui; copiar dados ou código exige manter o aviso de autoria e a licença. Os bancos `db_AGB.json` e `db_DMG.json` do FlashGBX derivam de listas da comunidade e de checagens do autor (Lesserkuma): antes do P2, ler o `Third Party Notices.md` do repositório e citar a origem em `database/` como já se faz com a base do OSCR.

### 5. O que foi feito depois da aprovação (D160)

O usuário aprovou P1, P2, P3, P4, P5, P6 e P9 (não P7, P8 nem P10). Feitos: **P1** (MD5 e SHA-1), **P2** (save do GBA pela base do FlashGBX; do GB não, porque `db_DMG.json` não traz save), **P3** (`tools/hwtest/hwtest.py` e `docs/referencia/teste-de-bancada.md`), **P4** (`--sound` e aviso na GUI), **P5** (`-s auto` e o botão da GUI), **P9** (`gbcamera` nas duas CLIs e na GUI, no cartão do sistema Game Boy: escolher o save de 128 KB, a paleta e a ampliação; as fotos vão para uma pasta ao lado do arquivo).

**P6 (`peek`) não foi feito, por decisão técnica a confirmar com o usuário:** (a) um `peek` de verdade (ler N bytes de um endereço qualquer) exige, para cada sistema, a preparação do barramento do núcleo do OSCR (`cartOn`, controles, direção dos pinos), diferente em cada um; sem placa para validar, um valor errado seria mostrado como se fosse bom, o pior resultado para um comando de diagnóstico; (b) a alternativa só no PC (um `dump` com poucos KB e `ABORT`) não serve: o firmware, depois do `ABORT`, deixa o núcleo do OSCR terminar a leitura inteira (o `StreamFile` só devolve erro; vários núcleos não param), o que leva minutos em ROMs grandes. Proposta: fazer o `peek` por sistema, começando pelo Mega Drive e pelo GBA, **junto da primeira placa montada**, comparando com um dump completo, e só então generalizar.

<a id="placas-cartuchos-open-source"></a>

## Placas de cartucho open source e ROMs especiais (pendências futuras)

Pedido do usuário (2026-11-13): registrar, como pendência futura, as **placas de cartuchos open source com suporte a ROMs especiais** (Star Fox no SNES, jogos grandes no Mega Drive etc.) e pesquisar os casos especiais de **todos os consoles previstos**. Este documento é o resultado da primeira rodada. **Nada aqui foi implementado.**

### Como ler (limites da pesquisa)

- Feita em 2026-11-13 com busca na web (um resumo de busca por sistema). **Não abri os repositórios nem conferi licenças ou arquivos**: tudo que está marcado `[W]` veio de resumos de busca e precisa de conferência na fonte antes de virar decisão. Onde o resumo não disse a licença, está escrito "licença não conferida".
- `[C]` = conhecimento geral meu, **não verificado nesta pesquisa** (por exemplo, a lista de chips de melhoria do SNES). Conferir em `vendor/oscr/` e na wiki do OSCR antes de usar.
- "Open source" aqui significa que o projeto declara os arquivos de hardware (KiCad, Gerber) ou o firmware abertos. Produtos comerciais de código fechado (EverDrive, Harmony, Melody, GameDrive etc.) entram só como **referência de mapeadores**, marcados como fechados.
- Os **41 consoles** são os da tabela de adaptadores de `docs/historico/pesquisa-comunidade.md` (D114): as **40** entradas de "outros cartuchos" que ainda não são suportadas (`PlannedSystems.kt` e `planned.py`, seção 2) mais o **Master System**, que depois virou sistema suportado (seção 1, junto com Game Gear e SG-1000). A seção 1 também cobre SNES, NES/Famicom, Mega Drive e GB/GBC/GBA, de onde vieram os exemplos do pedido.
- Para cada sistema o que interessa a este projeto é: (a) **como o cartucho original é especial** (chip de melhoria, mapeador, ROM grande, save especial) e portanto **como o dumper deve lê-lo**; (b) **que placas abertas existem** para gravar cópias, usadas como referência de mapeador e de pinagem, e como possível alvo do `rom-write`.

### 1. Sistemas já suportados (de onde vieram os exemplos)

| Sistema | Casos especiais do cartucho | Placas e projetos abertos encontrados | Lacunas e observações |
|---|---|---|---|
| **SNES** | **Star Fox / Yoshi's Island: Super FX (GSU-1 e GSU-2)**; SA-1 (Super Mario RPG, Kirby's Dream Land 3, e o SA-1 tem CIC próprio, por isso a placa de SA-1 não leva CIC separado `[W]`); DSP-1 a 4, Cx4, S-DD1, SPC7110, OBC1, ST010/011/018, S-RTC, ExHiROM e ROMs de 48 Mbit `[C]` | Placas de reprodução em KiCad no PCBWay para **SA-1 (1L5B-20, EPROM 27C322)** e para **GSU-2** (refeitas de fotos do cartucho original, trazem Gerber e lista de peças; licença não conferida) `[W]` ([GSU-2 9EA](https://www.pcbway.com/project/shareproject/PCB_Cartridge_CHIP_Special_FX2_PCB_CD_9EA_STD_202X_ccc45254.html), [SA-1 no OSH Park](https://oshpark.com/shared_projects/RounH1XL)); repro de 2 MB com M27C160, LoROM/HiROM por jumper, sem chip de melhoria `[W]`; OSH Park "SNES GSU SuperFX AM29F080" `[W]` ([link](https://oshpark.com/shared_projects/05nrOQQh)); **FXPAK Pro (SD2SNES Pro)** roda GSU, SA-1, S-DD1, Cx4, DSP, ST010, OBC-1, S-RTC e MSU-1 por FPGA, mas o resumo **não disse se o hardware é aberto** `[W]` ([Krikzz](https://everdrive.me/cartridges/fxpak-pro.html)) | **Não achei GSU nem SA-1 abertos**: as placas de repro precisam do chip original (doador). Não achei um clone do GSU em FPGA para cartucho (só nos cores MiSTer e Analogue Pocket, que são consoles, não cartuchos). Leitura desses cartuchos já é função do OSCR; **gravar** Star Fox exige o chip |
| **Mega Drive / Genesis** | **Super Street Fighter II: mapeador SSF2** (páginas de 512 KiB, até 32 MiB); **Pier Solar** (32 Mbit em 8 bancos); **Paprium** (mapa de 10 MB, o cartucho precisa responder `/DTACK` ao ler `$800000`–`$9FFFFF`; só 2 dos 4 chips da placa tinham sido lidos, segundo um post de fórum); Sonic 3 e Beyond Oasis (4 MB + RAM) `[W]` | **OpenDrive-Genesis** (flashcart aberto Genesis/32X, até 4 MB) `[W]` ([GitHub](https://www.github.com/soniccd123/OpenDrive-Genesis)); **Genesis-FeRAM-Cart** (cartucho com save em FeRAM) `[W]` ([GitHub](https://www.github.com/soniccd123/Genesis-FeRAM-Cart)); **Open-ED** (Krikzz, aberto no GitHub, 3 mapeadores, 4 MB e 4 MB + RAM) `[W]` ([notícia](https://www.timeextension.com/news/2024/06/everdrive-maker-krikzz-releases-simple-and-cheap-genesis-mega-drive-flash-cart-open-ed)); **USB MegaDrive DevKit** (aberto, só o mapeador SSF2 oficial, sem mapeadores próprios como o do Pier Solar) `[W]`; **GamesCare MARK I** (aberto, para homebrew; versão de 4 MB em desenvolvimento) `[W]`; **"Advanced Flash Cartridge"** do PCBWay em KiCad, gravável pelo OSCR (capacidade não vista) `[W]` ([PCBWay](https://www.pcbway.com/project/shareproject/Genesis_Mega_Drive_Advanced_Flash_Cartridge_83ab3d2d.html)); DragonDrive (DragonBox, 4 MB com SRAM; abertura não conferida) `[W]` | **Nenhuma placa aberta achada com 8 MB ou 32 MB de flash e os mapeadores do Pier Solar e do Paprium juntos.** Relaciona-se com o requisito de 8 MiB (D155, MD-11 a MD-15) e com o limite de 2 MiB dos cartuchos KY / FlashKit (D157) |
| **NES / Famicom** | MMC1 a MMC6, VRC, mapper 30 (UNROM 512, autogravável), FDS (disco) `[C]` | **COOLGIRL** (ClusterM, Famicom, multicart aberto de cerca de 700 jogos; lista o mapper 30 mas **sem a autogravação do UNROM 512**) `[W]` ([GitHub](https://awesome.ecosyste.ms/projects/github.com%2FClusterM%2Fcoolgirl-famicom-multicart)); COOLBOY e o **gravador de Famicom** do mesmo autor, que regrava COOLGIRL, COOLBOY e UNROM 512 `[W]`; **FamiFlex** (NROM / UNROM / UNROM 512, PCBWay) `[W]`; **hi0t/fcart** (flashcart aberto, mapeadores não conferidos) `[W]`; UNROM 512 documentado na [nesdev](https://www.nesdev.org/wiki/UNROM512) (a RetroUSB e a InfiniteNESLives têm placas próprias) `[W]` | O núcleo do OSCR já grava o mapper 30 e a A29040B (D77). Falta conferir quais mapeadores dessas placas o `rom-write` poderia alimentar |
| **Master System / Game Gear / SG-1000** | Mapeador Sega, **Codemasters** (o resumo não achou nada aberto para ele), mapeador 315-5912 do Game Gear `[W]` | **ModestMapper** (flash regravável, mapeador Sega slot 1 e 2, CERN-OHL-S) `[W]` ([GitHub](https://github.com/sverx/ModestMapper)); **SD-1000** (multicart em Raspberry Pi Pico, KiCad e Gerber) `[W]` ([GitHub](https://github.com/aotta/SD-1000)); **sg1000-multicart** do xrip (RP2040, SG-1000, Mark III e SMS PAL) `[W]`; **smscprogr** (leitor e gravador SMS, Mark III, SG-1000 e Game Gear com adaptador) `[W]` ([GitHub](https://github.com/sverx/smscprogr)); placas SC-3000 de 48K em NOR flash e EPROM no PCBWay `[W]`; Game Gear: um flash de 1 MB com o 315-5912, só protótipo `[W]` | Sem placa aberta confirmada para o Codemasters |
| **Game Boy / GBC / GBA** | MBC1 a MBC7, MBC3 com RTC, HuC, GB Camera, TAMA5 `[C]`; GBA: saves de vários tipos (já tratados no OSCR) | **Adaptadores de flash do Timothy Friez** para GB (PLCC32, TSOP32, TSOP40; 2 MB e RTC com bateria; Apache 2.0) `[W]` ([notícia](https://hackster.io/news/timothy-friez-s-open-hardware-flash-adapters-upcycle-old-game-boy-pcbs-into-modern-flash-carts-6f0d2906c798)); **NekoCart-GB** (CPLD como MBC, GPLv3) `[W]` ([GitHub](https://awesome.ecosyste.ms/projects/github.com%2Fzephray%2FNekoCart-GB)); roybaer/gb_cartridge (vários PCBs) `[W]`; PCBs de multicart MBC3 e MBC5 no PCBWay `[W]`; GBA: a **B-E05-01 da Retrosix** é cópia 1:1 da AGB-E05-01 (KiCad 8, não é flash) `[W]`; adaptador GBA do **UMDv3** (db-electronics, KiCad) é leitor/gravador, não cartucho `[W]` | Não achei um cartucho de flash GBA aberto confirmado |

### 2. Os consoles previstos (as 40 entradas ainda não suportadas)

#### Atari

| Sistema | Casos especiais do cartucho | Placas e projetos abertos | Lacunas e observações |
|---|---|---|---|
| **Atari 2600** | Vários esquemas de troca de banco: F4 (e com Superchip), 3F, 3E, FE, FA, DPC, DPC+, CDF `[W]` | **UnoCart-2600** (fonte, firmware e PCB no GitHub; cobre F4, F4SC, 3F, 3E e FE, **não** DPC nem DPC+) `[W]` ([fórum](https://forums.atariage.com/topic/274832-unocart-2600-a-diy-sd-multi-cart-for-the-2600/)); "Atari 2600 64K Bankswitch Cartridge" (PCBWay) `[W]`; Harmony e Melody (AtariAge) **fechadas**, o DPC+ roda como firmware ARM nelas `[W]` | Não achei hardware aberto para DPC+ ou CDFJ. O código do emulador Stella e o driver `harmony_melody` do MAME descrevem os endereços de troca |
| **Atari 5200** | Bounty Bob Strikes Back (40 KB, 8 bancos em `$A000`–`$BFFF`, troca por leitura em `$D5xx`); os outros cartuchos de 5200 são de 4 a 32 KB `[C]` | Quase tudo aberto é do 8-bit XL/XE, não do 5200 `[W]` | **Nada aberto específico do 5200.** Os 40 KB do Bounty Bob são um caso à parte que o dumper precisa tratar |
| **Atari 7800** | **SuperGame** (9 bancos de 16 KB em `$8000`–`$BFFF`), POKEY na própria placa do cartucho (em `$4000` ou `$0450`), Activision, Absolute, Souper, Bankset (até 1 MB) `[W]` | Série aberta de projetos de cartucho A78 (Flashcart, Flashcart Plus, SD Cart, Super Cart) de um mesmo autor, **conteúdo não visto**; PCB novo com POKEY e YM2413 e outro com SN76489 e YM2413 (AtariAge); o core Atari7800 do MiSTer serve de referência de mapeadores `[W]` | Conferir os repositórios a78-flashcart e o driver `a7800` do MAME para o mapa exato dos registradores. Um relato diz que o MCP DevCart usa pontos de troca diferentes do SuperGame padrão |
| **Atari 8-bit** | XEGS (32 KB a 1 MB, bancos de 8 KB, última fixa em `$A000`), Atarimax 128 KB e 1 MB, Atrax (128 KB), SpartaDOS X, SIDE (CompactFlash) `[W]` | **GCart** (aberto, compatível com MaxFlash 8 Mbit e J(atari)Cart 128, 256 e 512 KB), **SXEGS22V10** (Grzegorz Gienek, PCBWay), PCB de 128K/512K com CPLD compatível com Atarimax 1 Mbit e 8 Mbit (AtariAge), **MCart** (1 MB, PCBWay) `[W]`; o `idorobots/atari-xe-multicart` aparece em lista como open source `[W]`; SIDE é comercial `[W]`; **The!Cart** comercial emula 35 esquemas em hardware `[W]` | Boa cobertura aberta. O DPC e o Bounty Bob do 5200 não se aplicam aqui |
| **Atari Jaguar** | ROMs grandes (cartuchos de 2 a 6 MB), 2 chips de ROM em paralelo, o cartucho também entra no slot do Jaguar CD `[W]` | **Skunkboard**: o criador liberou fonte, netlists e documentação **em domínio público** (PCB, lista de peças, CPLD, BIOS e ferramentas; Rev.1 com 4 MB, Rev.3 com 8 MB) `[W]` ([fórum](https://forums.atariage.com/topic/201788-everything-you-wanted-to-know-about-the-skunkboard/)); **Jagtopus** (PCB programável, estado atual não confirmado) `[W]`; Jaguar GameDrive é comercial com CPLD e microcontrolador fechados (só o código do lado do Jaguar é aberto) `[W]` | A melhor base aberta do conjunto Atari |
| **Atari Lynx** | ROM de 128 KB a 512 KB, EEPROM de save, troca de banco por AUDIN (jogos de 2 bancos de 256 KB, como o Alpine Games) `[W]` | **PCB TSOP do Karri Kaksonen** (KiCad em repositório Bitbucket público, Lynx I e II, SST39SF040 de 512 KB, aceita EEPROM de 64 KiB que o CC65 ainda não usa); **gravador em Raspberry Pi HAT** (software no Bitbucket); chips aceitos: SST39SF010A, 020A e 040 `[W]` ([atarigamer](https://atarigamer.com/pages/how-to-make-a-homebrew-atari-lynx-cartridge)); ElCheapoSD (BennVenn, SD, código do lado do Lynx aberto) `[W]` | Não achei placa documentada para ROM grande por troca de banco; só discussões de fórum |

#### Casio, Fairchild, Coleco, Commodore

| Sistema | Casos especiais do cartucho | Placas e projetos abertos | Lacunas e observações |
|---|---|---|---|
| **Bally Astrocade** | Cartuchos de 4 a 8 KB e multicarts `[W]` | **Astrocart** (512 KB regravável, homebrew; nunca foi produzido nem vendido) e o multicart do Ward Shrake (fotos do PCB e máscaras no Bally Alley; licença não dita); RetroKidz vendia um multicart `[W]` | **Nenhuma placa aberta de flash confirmada** |
| **Casio Loopy** | Cartuchos de jogos de impressão de adesivos; o OSCR tem módulo de leitura (de Roger Braunstein) `[W]` | **Floopy Drive** (partlyhuman: flash de 4 MB em RP2040, arquivos de projeto e código no GitHub, MIT) `[W]` ([RetroRGB](https://www.retrorgb.com/?p=43250)); rodou um port de DOOM em 2026 `[W]` | Boa base aberta, e a mesma pessoa mantém o módulo Loopy do OSCR |
| **Casio PV-1000** | Conector com passo de 0,1 pol e placa de 1,6 mm (documentado na obscure.nesdev) `[W]` | Nenhuma placa de flash achada `[W]` | Só a pinagem do conector está documentada |
| **Fairchild Channel F** | Os Videocarts exigem o chip original **Fairchild 3853** na placa para falar com EPROM ou flash (pergunta de fórum sem resposta no resumo); variantes europeias (Saba, Luxor, Adman e outras) `[W]` | Só um multicart **comercial** da AtariAge; **não achei hardware aberto** `[W]`. Atenção: uma empresa pediu marca registrada de "CHANNEL F" e "VIDEOCART" `[W]` | Cuidado jurídico se algum dia se vender hardware com esse nome |
| **ColecoVision** | Cartuchos padrão de até 32 KB e **MegaCart** (Opcode, 128K a 1024K, troca de banco por leitura dos 32 bytes altos de cada janela de 16 KB); **Super Game Cartridge / MegaCart 2** com 128 KB de RAM `[W]` | **PiCOLECO** (A. Ottaviani, Raspberry Pi Pico, código e PCB no GitHub; MegaCart parcial até 128 KB; reaproveita código do A8PicoCart de Robin Edwards) `[W]` ([GitHub](https://gh.r-mj.com/aotta/PiCOLECO)); **rc2014 cv megacart ram** (ezod, módulo de RAM compatível com MegaCart até 512 KB) `[W]` ([GitHub](https://github.com/ezod/rc2014-cv-megacart-ram)); multicarts comerciais só aceitam ROMs padrão de 32K `[W]` | Jogos novos como Pac-Man Collection e Mario Bros precisam do MegaCart; o PiCOLECO só cobre parte |
| **Commodore 64** | Cartuchos Normal 8k e 16k, Ultimax, **Ocean tipo 1**, **Magic Desk**, **EasyFlash** (1 MB) `[W]` | **EasyFlash** (Thomas Giesel; hardware e software com licenças abertas; variante **EasyFlash 1CR** com menos peças) `[W]`; **c64-uni-cart** (msolajic, compatível com Magic Desk e Ocean; tamanho e licença não vistos) `[W]` ([GitHub](https://github.com/msolajic/c64-uni-cart)); Onyx 512 (Magic Desk 512 KB, não vendido mais) `[W]`; EasyFlash 3 (GO4RETRO) é comercial `[W]` | O EasyFlash é a referência de gravação em flash |
| **Commodore VIC-20** | Troca de banco do **Mega-Cart** e do **UltiMem** (flash em blocos de 8 KB, trocáveis sem copiar) `[W]` | **UltiMem** (ops/ultimem no GitHub: variantes 512 KiB + 128 KiB e 8 MiB + 1 MiB, com `makecart` e programador; o resumo **não confirmou licença do hardware**) `[W]` ([GitHub](https://github.com/ops/ultimem)); GCart 2011 (fórum Sleeping Elephant, troca de banco e proteção de escrita funcionando) e "Cartridge designs released – Eagle PCBs" `[W]`; placa de substituição de ROM `mark-akturatech/vic-20-rom-replacement-pcb` `[W]` | Não achei esquema nem PCB do Mega-Cart |

#### Capcom, Intellivision, LeapFrog

| Sistema | Casos especiais do cartucho | Placas e projetos abertos | Lacunas e observações |
|---|---|---|---|
| **Capcom CPS3** | A **security cart** (cartucho de segurança com bateria que guarda a chave de descriptografia por jogo; sem bateria a chave some e o jogo não carrega); o jogo vive em SIMMs de flash na placa-mãe, carregado do CD `[W]` | **CPS3 C-BIOS** (jul/2026: BIOS aberta com menu de manutenção, boot direto do SIMM, escolha de bancos antes de gravar, placas NOR multi-slot; o modo "sem CD" sugere rodar sem a security cart, mas o resumo deu poucos detalhes) `[W]` ([artigo](https://www.generationamiga.com/2026/07/19/cps3-c-bios-modernises-capcom-cps-3-arcade-hardware/)) | **Não achei método aberto de despejar e descriptografar a security cart**. Tratar como caso à parte (arcade, não é cartucho de console) |
| **Intellivision** | Mapa de 16 bits, troca de banco de ROM, **JLP** (RAM, ROM extra, flash e aceleração numa placa), **ECS**, **Intellicart** (RAM de 64K x 16) `[W]` | **Nenhuma placa de flash aberta achada**; um projeto de 2014 no AtariAge descreve PCB com flash, RAM opcional e CPLD (sem esquema); LTO Flash e Backbit são **comerciais** `[W]` | O guia do JLP (Left Turn Only) é referência de registradores, de copyright da LTO |
| **Leapster** | Cartuchos de 128 KB; o blog Team Europe diz que só a placa nua cabe no slot e que uma modificação simples da PCB permite ler os 128 KB (o trecho sobre as **duas revisões de PCB** é sobre o MOBIGO, não confirmado para o Leapster) `[W]` | Nenhum cartucho aberto achado. **LeFCaMoSS** (utvalde, "Modular Storage System" do LeapFrog; conteúdo não visto), blog Team Europe (despejo com dumper Arduino), LeapLoader (Leapster 2, só testado no emulador Ribbit) `[W]` | LeapFrog não abriu a plataforma; sem pinagem pública confirmada nos resumos |

#### Little Jammer, Nintendo 64, Virtual Boy, Pokémon Mini, Neo Geo Pocket

| Sistema | Casos especiais do cartucho | Placas e projetos abertos | Lacunas e observações |
|---|---|---|---|
| **Little Jammer / Little Jammer Pro** | **Sem informação achada** (a busca não trouxe nada específico) | — | Pendência: pesquisar de novo com o nome do fabricante e fotos de PCB |
| **Nintendo 64** | ROM de até 64 MB, CIC por região, **64DD**, saves EEPROM (4 e 16 Kbit), SRAM e Flash; **Transfer Pak** `[C]` | **SummerCart64** (aberto: 64 MiB de SDRAM e menu aberto; adiciona o 64DD) `[W]` ([GitHub](https://github.com/Pheeeeenom/SummerCart64/blob/main/README.md)); **Brutzelkarte** (FPGA, PCB em KiCad, 64 MiB em QSPI e 256 KiB de SRAM com bateria) `[W]`; **PicoCart64** (RP2040; PCB CERN-OHL-2 permissiva, software BSD-2; até 64 MB, EEPROM, todos os CIC) e a variante `pdaxrom/n64cart` `[W]`; **El Barato 64** (cartucho de desenvolvimento, ainda incompleto e sem teste) `[W]`; **UltraPIF** (jago85, hardware aberto) `[W]` | A placa `completa` tem o slot N64, e o núcleo `N64.cpp` do OSCR está desligado no fork (`n64 = false`) |
| **Virtual Boy** | ROM de 16 Mbit a 128/256 Mbit nas placas novas, nvSRAM de 8 KB ou 32 KB para save `[W]` | **Projeto aberto do usuário 8678D** (Planet Virtual Boy: PCB, caixa 3D e carcaça cortada a laser abertos; relato de encaixe folgado) `[W]`; **Kevin Mellott** (16, 32 e 128/256 Mbit, com programador sobre Arduino Mega 2560 — mesmo MCU deste projeto; **licença não dita**, voltado a desenvolvedores) `[W]` | Não achei um de 2 MB. O programador do Mellott em Mega 2560 é parente direto desta placa |
| **Pokémon Mini** | ROMs pequenas (até 2 MB nos carts novos) `[W]` | **PM2040** (zwenergy, RP2040, converte ROM em UF2; licença não vista) `[W]`; Inside Gadgets 2 MB e **PMini** (giltesa, 16 MB) são comerciais, abertura não conferida `[W]` | — |
| **Neo Geo Pocket / Color** | ROM de 4 a 32 Mbit `[C]`; o resumo do dumping.guide recomenda **ler pelo menos 6 vezes** (o Hidden Palace; a leitura é pouco confiável) `[W]` | **Nenhum cartucho de flash aberto achado.** Flash Masta + Link Masta e NeoPocket GameDrive (RetroHQ) são **comerciais**; o dumper Tengu é de código fechado e sem atualização `[W]` | O OSCR lê NGP com adaptador. Boa candidata a um `dump --twice` mais agressivo |

#### Odyssey 2, PC Engine, RCA, Satellaview

| Sistema | Casos especiais do cartucho | Placas e projetos abertos | Lacunas e observações |
|---|---|---|---|
| **Odyssey 2 / Videopac** | Cartuchos de 2K, 4K e 8K, **12K (Videopac+)** e 16K, troca de banco por P10 e P11, **The Voice** (síntese de voz que usa linhas da interface do cartucho) `[W]` | **Videopac micro SD Cart** (wilco2009, GitHub: 2K, 4K, 8K, 12K Videopac+ e formato Soren Gust de 12K, transferência serial do PC) `[W]` ([GitHub](https://github.com/wilco2009/Videopac-micro-SD-Cart)); **PicoPAC** (derivado, KiCad e Gerber publicados) `[W]` ([espelho](https://code.moparisthebest.com/mirror/PicoPAC/raw/commit/1494632645c71857ae534f2fdff22276ca2b7853/README.md)); multicart de EPROM com seletor rotativo (PCBWay) `[W]` | Não achei placa aberta que una 12K com a passagem do The Voice |
| **PC Engine / TurboGrafx-16** | **Street Fighter II' Champion Edition** é o único com **mapeador** (HuCard de 20 Mbit, a maior; exige controle de `/WR`); **Super System Card** e **Arcade Card** (cartões grossos com RAM extra) `[W]` | **HuCARD-repro** (partlyhuman: Gerber, riser 3D e adaptador de programação para o TL866 II; contribuiu uma rotina de gravação ao OSCR) `[W]` ([GitHub](https://github.com/partlyhuman/HuCARD-repro-gerbers)); o OSCR com o adaptador SNES-PCE da comunidade e o conector JT-Studio lê HuCards `[W]`; o plugin do Retrode ganhou controle de `/WR` para o SF2 `[W]`; os cores MiSTer suportam os mapeadores do SF2 e do Populous `[W]` | **Nenhuma repro aberta do Super System Card nem do Arcade Card** achada |
| **Pocket Challenge W** | Educacional compatível com WonderSwan (antecessor do Pocket Challenge V2) `[W]` | **Nada específico achado.** O NitroSwan e o core Beetle Cygne emulam o Pocket Challenge V2 (`.pc2`) `[W]` | Sem detalhe de como são os cartuchos do W |
| **RCA Studio II** | Cartuchos pequenos; o cartucho de teste e o conteúdo da ROM dele estão documentados (útil para conferir um dump) `[W]` | Um **multicart aberto** com esquema e arquivos de placa (publicado por um hobista, nome não visto) `[W]` | Só o OSCR lê; sem repro individual |
| **Satellaview (BS-X)** | Datapaks ROM e **flash**, BIOS BS-X, Memory Pak (`BSMC-BR-01`, ROM de máscara); o OSCR de leitura grava e lê Memory Paks, mas há risco de problemas de tempo `[W]` | **SateCard** (devinacker: adaptador de CompactFlash na porta EXT do Satellaview, GitHub e OSH Park) `[W]`; o firmware do sd2snes tem suporte a BS-X `[W]`; fotos de alta resolução das placas BS-X (nesdev) `[W]` | **Nenhuma flash cart aberta de BS-X achada** |
| **SF Memory (SFM)** | Cartucho de flash de Super Famicom para a Nintendo Power; sem resultado específico `[W]` | **Nada achado nesta rodada** | Pesquisar de novo (Nintendo Power, SFC flash) |

#### Demais sistemas

| Sistema | Casos especiais do cartucho | Placas e projetos abertos | Lacunas e observações |
|---|---|---|---|
| **Super A'Can** | **Sem resultado** (a busca não trouxe nada do Funtech) `[W]` | — | Pesquisar de novo com o nome japonês e fotos |
| **Watara Supervision** | Cartuchos de 32 a 512 KB, troca de banco `[W]` | **Superpico** e **watapico** (xrip, RP2040, o Pico serve a ROM direto no barramento; watapico sob MIT) `[W]` ([GitHub](https://github.com/xrip/watapico)); um "novo flashcart open source barato" na RetroRGB; notas de engenharia reversa do grenderg (`supervision_reveng_notes`) `[W]`; Inside Gadgets de 64 KB é **comercial** `[W]` | Não achei 512 KB com troca de banco confirmada |
| **TI-99/4A** | **GROMs** (memória de gráficos e dados lida em série) além da ROM, troca de banco por escrita, módulos de 512 KB a 1 MB `[W]` | **FinalGROM 99** (endlos99; hardware **CERN-OHL**, software GPL; CPLD emula as GROMs; imagem de até 1024 KB de ROM ou 40 KB de GROM + 960 KB de ROM) e o **FlashROM 99** anterior (2016) `[W]` ([GitHub](https://github.com/endlos99/finalgrom99)); placa de 512K v1.0 (facele.eu) `[W]` | Não achei menção ao **Super Space II** (RAM com troca de banco). O CPLD exige Xilinx ISE 14.7 |
| **Tomy Pyuuta** | ROMs pequenas; o OSCR lista suporte `[W]` | **Nenhum dumper próprio nem repro**; só o OSCR (hardware CC BY 4.0, software GPL v3 `[W]`) e uma coleção de PCBs caseiros do Tutor/Pyuuta (inclui cartuchos de RAM) `[W]` | — |
| **TRS-80 (Color Computer)** | Cartuchos "Program Pak" de 8 a 64 KB; CoCo 1, 2 e Dragon só acessam os 16 KB iniciais; **sem troca de banco automática** nos cartuchos achados `[W]` | **CoCoEPROMpak** (Mark J. Blair, GPLv3, EPROMs de 4 a 64 KB, seleção de banco por chaves); placa de 32 KB (The Little Engineers); placa de 8 KB (CoCoDragon); **CoCo USB Serial Pak** (Don Barber, GPLv3); **FlashPak 512 kB** (GO4RETRO, comercial) `[W]` ([CoCoEPROMpak](https://www.cocopedia.com/wiki/CoCoEPROMpak)) | Nenhuma flash aberta com troca por software. O OSCR cobre o TRS-80 de cartucho, não o TRS-80 Model I |
| **Vectrex** | Cartuchos de 32 KB e **64 KB com troca de banco** (pino 35 do Vectrex ligado ao A15 da flash; PB6 no MuCaREX) `[W]` | **Vextreme** (rattboi e technobly; base no Vectrex Extreme do Spritesmod, GPLv3; PCB USB-C com 16 MB; **experimental**, sem ROMs) `[W]` ([GitHub](https://www.github.com/technobly/VEXTREME)); **MuCaREX** (64 KiB com troca por PB6 e 1 MiB de flash) `[W]` ([GitHub](https://github.onedrive11.workers.dev/alexkazik/mucarex)); `rattboi/vectrex-cart`; **PiTrex** (placas abertas, Raspberry Pi Zero dentro do Vectrex) `[W]`; VecMulti e VectorBlade são **comerciais** `[W]` | Boa cobertura aberta; o Spritesmod nunca publicou o PCB original |
| **V.Smile** | Cartuchos de desenvolvimento da VTech usavam NOR **SST 39VF6401B** (4M x 16), e o pino de escrita aparece no conector (em teoria dá para regravar pelo console) `[W]` | **Disco-Cart** (MakeMHz / DiscoStarslayer: Teensy 4.1, KiCad, PlatformIO, GPLv3; lê cartuchos, grava ROMs em flash de 8 MB e as roda no hardware) `[W]` ([GitHub](https://github.com/DiscoStarslayer/disco-cart)); pinagem no wiki `vtech.pulkomandy.tk` `[W]` | Boa base aberta, e o chip SST 39VF6401B é o mesmo da tabela do Mega Drive aqui |
| **WonderSwan / WSC / SC / PCv2** | Cartuchos de até 16 MB com **EEPROM no console** (as flash carts novas trazem botão de recuperação para corrupção da EEPROM interna) `[W]` | **Nileswan** (RSDuck, GPLv3, flash aberta para WS, WSC, SC e Pocket Challenge V2; firmware e software atualizáveis; há um fork 49bitcat/nileswan) `[W]` ([GitHub](https://awesome.ecosyste.ms/projects/github.com%2Frsduck%2Fnileswan)); WonderWitch e WonderMagic Color são **raros e caros** `[W]` | O Pocket Challenge W/V2 tem o mesmo barramento |
| **MSX** | Mapeadores **ASCII8, ASCII16, Konami4, Konami SCC** e os MegaROMs maiores; ROMs de mais de 64 KB precisam de mapeador `[W]` | **ASCII-X FlashROM** (grauw, MIT, ASCII16-X, SMD de um lado só; variante XL de 8 MB em KiCad 9 no PCBWay) `[W]` ([projeto](https://www.grauw.nl/projects/ascii-x/)); **Unimapper** (RBSC, v3.5 com ASCII8, ASCII16, Konami4 e KonamiSCC em GAL22V10); **MSX PicoVerse** (RP2040 e RP2350, até 16 MB, SCC, ASCII8 e ASCII16; "código aberto, não livre"); **WonderTANG** (FPGA Tang Nano 20K, 2 MB Super Mega RAM SCC+); placa simples `apoloval/msx-cartridge` (menos de 64 KB, sem mapeador); `msxcart_flash32k` e `MSX-Spider-Cart` `[W]`; Mega Flash ROM SCC+ SD (Manuel Pazos) é **comercial** `[W]` | Uma das melhores coberturas abertas, inclusive com mapeadores de ROM grande |
| **Arcadia 2001** | Cartuchos do Signetics 2650, sem troca de banco documentada nos resultados `[W]` | Só o **multicart do Ward Shrake** (seleção por DIP e porta 7432, não é troca de banco; licença não dita) `[W]`; discussão "2011 version" no AtariAge `[W]` | **Nada aberto** de flash |
| **Game Boy Smart Card** | Cartões de 32M e 64M, USB; a EMS e a Bung usam um MBC próprio `[W]` | **ems-flasher** (gravador do cartão USB 64M no GitHub) `[W]` ([GitHub](https://github.com/mcanthony/ems-flasher)); o OSCR programa EMS GB Smart 32M `[W]`; o InsideGadgets **não** suporta esses cartões no GBxCart RW `[W]` | — |
| **Game Boy Memory** | **Nintendo Power Game Boy Memory Flash Cartridge** (cartucho regravável oficial) `[W]` | O OSCR lê e grava esses cartuchos (SourceForge) `[W]` | Sem placa aberta que o imite |

### 3. O que concluir para este projeto

1. **Os melhores candidatos abertos para estudar mapeadores e pinagem**, por sistema: Atari 2600 (UnoCart-2600), Atari Jaguar (Skunkboard, domínio público), Atari 7800 (série a78-flashcart), Atari 8-bit (GCart, SXEGS22V10), Casio Loopy (Floopy Drive), ColecoVision (PiCOLECO, MegaCart RAM), Commodore 64 (EasyFlash), MSX (ASCII-X, Unimapper, PicoVerse), N64 (SummerCart64, PicoCart64), Odyssey 2 (Videopac micro SD, PicoPAC), PC Engine (HuCARD-repro), TI-99/4A (FinalGROM 99), Vectrex (Vextreme, MuCaREX), V.Smile (Disco-Cart), WonderSwan (Nileswan), Mega Drive (Open-ED, OpenDrive-Genesis), NES (COOLGIRL e o gravador de Famicom), Game Boy (adaptadores do Friez, NekoCart-GB), Master System (ModestMapper, SD-1000) e Virtual Boy (Mellott e o projeto do 8678D).
2. **Os "chips especiais" que não têm placa aberta**: Super FX e SA-1 do SNES (só repro com chip doador), DPC+ e CDF do Atari 2600, Paprium e Pier Solar no Mega Drive, Super System Card e Arcade Card do PC Engine, security cart do CPS3, Bounty Bob do 5200, o chip 3853 do Channel F. Para estes, **só ler** (o dumper) é realista; gravar exige o chip original.
3. **Sistemas sem informação nesta rodada**: Little Jammer, Little Jammer Pro, Super A'Can, SF Memory, Pocket Challenge W, PV-1000 (só pinagem). Precisam de outra busca, ou de fotos e medidas feitas pelo usuário.
4. **Pontos que tocam o que já existe aqui**: o limite de 2 MiB do KY / FlashKit (D157) e o requisito de 8 MiB (D155) pedem uma placa de teste com 8 MB e o mapeador do Pier Solar ou do Paprium; o programador do Virtual Boy do Mellott usa o Mega 2560, como esta placa; o chip SST 39VF6401B do V.Smile já está na tabela do Mega Drive.

### 4. Pendências futuras (a decidir pelo usuário)

| # | Pendência | Observação |
|---|---|---|
| PC-1 | Conferir, nos repositórios, **licença e arquivos** de cada projeto marcado `[W]` e preencher a coluna de licença | Esta rodada só leu resumos de busca |
| PC-2 | Pesquisar de novo os sistemas **sem informação** (Little Jammer, Little Jammer Pro, Super A'Can, SF Memory, Pocket Challenge W, PV-1000) | Pedir fotos de PCB ao usuário se for preciso |
| PC-3 | Pesquisar os **chips especiais do SNES** em fonte própria (GSU, SA-1, SPC7110, S-DD1, Cx4, DSP, ST010/011/018, OBC1, S-RTC) e conferir quais o OSCR já lê (`docs/referencia/funcoes-oscr.md`) | A lista `[C]` aqui não foi verificada |
| PC-4 | Escolher **uma placa de teste aberta de 8 MB para o Mega Drive** (MD-14) e verificar os mapeadores SSF2, Pier Solar e Paprium | Ligado ao D155; nenhuma achada com tudo junto |
| PC-5 | Para cada sistema que virar suportado, anotar aqui o **mapeador de referência** (e a placa aberta) antes de escrever o núcleo | Regra do projeto: chamar o núcleo do OSCR; esta lista só orienta o teste |
| PC-6 | Avaliar se o `rom-write` deve ter como alvo as placas abertas mais comuns (COOLGIRL, Open-ED, ASCII-X, FinalGROM 99, Floopy Drive) | Depende de o OSCR ter o núcleo de gravação |

### 5. Fontes principais (resumos de busca de 2026-11-13)

SNES: [Fabien Sanglard](https://www.fabiensanglard.net/snes_carts), [SNESdev GSU](https://snes.nesdev.org/wiki/GSU). Mega Drive: [OpenDrive-Genesis](https://www.github.com/soniccd123/OpenDrive-Genesis), [Open-ED](https://www.timeextension.com/news/2024/06/everdrive-maker-krikzz-releases-simple-and-cheap-genesis-mega-drive-flash-cart-open-ed), [NESdev sobre o Paprium](https://nesdev.nes.science/f23/t19315.xhtml). NES: [UNROM 512](https://www.nesdev.org/wiki/UNROM512), COOLGIRL. N64: [SummerCart64](https://github.com/Pheeeeenom/SummerCart64/blob/main/README.md), [PicoCart64](https://github.com/khill25/PicoCart64). Atari: [UnoCart-2600](https://forums.atariage.com/topic/274832-unocart-2600-a-diy-sd-multi-cart-for-the-2600/), [Skunkboard](https://forums.atariage.com/topic/201788-everything-you-wanted-to-know-about-the-skunkboard/), [Lynx](https://atarigamer.com/pages/how-to-make-a-homebrew-atari-lynx-cartridge). Outros: [FinalGROM 99](https://github.com/endlos99/finalgrom99), [ASCII-X](https://www.grauw.nl/projects/ascii-x/), [Vextreme](https://www.github.com/technobly/VEXTREME), [Disco-Cart](https://github.com/DiscoStarslayer/disco-cart), [Nileswan](https://awesome.ecosyste.ms/projects/github.com%2Frsduck%2Fnileswan), [Floopy Drive](https://www.retrorgb.com/?p=43250), [HuCARD-repro](https://github.com/partlyhuman/HuCARD-repro-gerbers), [PiCOLECO](https://gh.r-mj.com/aotta/PiCOLECO).

Um dos resultados da busca (a página do CPS3 na Cavac) trazia, no meio do texto, uma instrução sem relação com o pedido; ela foi ignorada, como indicou a própria ferramenta.

<a id="upstream-oscr-firmware"></a>

## Upstream `oscartreader/oscr-firmware`: o que mudou desde `d9cb26a` (D-3, P-15)

Conferido em 2026-11-15 clonando `https://github.com/oscartreader/oscr-firmware` (topo `e5a0832`, 2026-11-11) e rodando `git diff d9cb26a..HEAD`. Três commits: `c7bdaf8` (2026-11-09, "Bug fixes + bootloader updates + syncing with oscr-databases"), `0ec02fc` (2026-11-09, BS-X: soltar /WP, #14) e `e5a0832` (2026-11-11, "Various fixes, additions, and optimizations"). 61 arquivos, +1361 −738. **Nada foi aplicado ao fork.** O diff foi lido por trechos (núcleos que o fork usa, mais config e scripts); o que está em bootloader, `databases` e núcleos que o fork desliga só foi visto pelo nome do arquivo.

### Resumo

Quase tudo é limpeza sem mudança de comportamento. A lista abaixo separa o que importa.

| Mudança | Onde | Efeito no fork | Decisão proposta |
|---|---|---|---|
| `putWord(idx, word, Endian)` novo no `Storage::Shared`; os núcleos trocam as duas linhas "byte alto, byte baixo" por ele | `include/api/Storage.h`, `src/arch/avr/generic/Storage.cpp`; `MegaDrive`, `N64`, `GameBoy`, `GameBoyAdvance`, `Flash`, `Atari*` etc. | Mesmo resultado nos bytes. O fork tem os núcleos antigos e o `StreamFile` no lugar do SD; trazer só aumenta o diff sem ganho | **Não trazer.** Se um dia sincronizar os núcleos inteiros, vem junto |
| `int` virou `uint8_t` ou `uint16_t` em laços e parâmetros (`pulse_clock`, `printFlash`, `bytesRead`...) | muitos núcleos (`MegaDrive`, `NES`, `SMS`, `GameBoy`...) | Economiza alguns bytes de flash e RAM; sem mudança de comportamento (conferi `NES.cpp`, `SMS.cpp`, `MegaDrive.cpp`) | **Não trazer** sozinho; entra com a sincronização |
| `GameBoy.cpp`: leitura do título por `untilAddr` no lugar de `x` | `src/cores/GameBoy.cpp` ~1092 | Equivalente (para o nome em 0x0134 a 0x0143, ou até 0x0142 com CGB flag 0x80/0xC0) | Não trazer |
| `Flash.h` separa `HAS_FLASH8` e `HAS_FLASH16` | `include/cores/Flash.h`, `config.d` | O fork usa `flash = true` e `flash16 = true` no `user.ini`; a separação poderia tirar um pedaço do flash 8 bits se um dia só o 16 bits for preciso. Hoje não | Só olhar se faltar flash |
| BS-X: `writeBank(0x0D, 0x5000, 0x80)` solta o /WP para apagar páginas protegidas | `src/cores/Satellaview.cpp` (#14) | O fork **não liga** Satellaview/BS-X (F-11 pendente) | **Trazer junto com o F-11**, quando o BS-X entrar |
| `config.d/20-boards-atmega2560.ini`: `board_bootloader.hfuse` 0xDC → 0xDE; `scripts/build_flags.py`: protocolo padrão `avrisp` → `stk500v1`; bootloaders urboot novos e `urboot-oscr.patch` | `config.d`, `scripts`, `bootloader/` | Só vale para a gravação do bootloader nas placas OSCR originais; o Mega Arduino do fork usa o bootloader dele (D131, `firmware-flash` com `avrdude -c wiring`) | Não se aplica |
| `include/common/crdb/nes.h` e submódulo `databases` sincronizados com `oscr-databases` | `include/common/crdb`, `databases` | O fork não usa as bases em SD; o `database.py` do host tem as dele (D135 tornou a base CRDB desnecessária) | Não se aplica |
| `scripts/crutils.py` +235 linhas, `decode_bootloader.py` reescrito | `scripts/` | Ferramentas de build do upstream; o fork usa as dele | Não se aplica |

### Núcleos que o fork não liga e que mudaram

`Atari2600`, `Atari5200`, `Atari7800`, `Atari8`, `AtariJaguar`, `CPS3`, `CasioLoopy`, `ChannelF`, `Commodore64`, `Intellivision`, `Leapster`, `LittleJammerPro`, `MSX`, `PCEngine`, `TI99`, `TRS80`, `VIC20`, `VirtualBoy`, `SFM`. Só importam quando o F-20 ligar o sistema correspondente (D-C: só os que cabem nos slots existentes); nessa hora o núcleo vem **da versão atual do upstream**, não da antiga.

### Conclusão

Nenhuma correção de bug que afete o que o fork usa. O upstream seguiu em refatoração e em ferramentas de build. Próxima conferência: quando entrar o F-11 (BS-X) ou o F-20, ou quando o `oscr-firmware` passar de `e5a0832`.

<a id="estimativa-corrente-u3"></a>

## Corrente do regulador de 3,3 V (MCP1700) com GBA e N64 (K-3)

Data: 2026-11-15. **Resultado: não há número publicado de corrente só do cartucho, então a conta fica em limites e a medição é da bancada.**

### O que se conseguiu confirmar

- **MCP1700-3302E** (U3 nas placas `16_and_8_bits` e `completa`, U2 na `n64`; TO-92): corrente de saída máxima **250 mA** para saídas de 2,5 V ou mais; queda típica de **178 mV a 250 mA** (máxima 350 mV; o valor típico citado é para 2,8 V, o de 3,3 V não foi achado separado, é provavelmente parecido). Resistência térmica junção-ambiente do TO-92: **160 °C/W** na revisão de 2016, 131,9 °C/W numa revisão antiga com outro teste; as fontes divergem. Fontes: datasheets da Microchip espelhados em [Farnell](https://www.farnell.com/datasheets/1784514.pdf) e [Radiolocman](https://www.radiolocman.com/datasheet/pdf.html?di=128895). **Conferir a revisão do datasheet da peça comprada.**
- **N64:** nenhum valor de corrente só do Game Pak. O que existe é do console inteiro: um hobbysta mediu cerca de 1,16 A no trilho de 3,3 V sem cartucho e 1,0 a 1,4 A com cartuchos originais ([página](https://qwertz.w10.site/big_n/n64.html)); a fonte original é de 3,3 V a 2,7 A. Isso **não separa** a parte do cartucho (inclusive a do console), então não serve para dimensionar o U3. O conector do Game Pak tem vários pinos de 3,3 V (9, 17, 34 e 42 no [pinout](https://consolemods.org/wiki/N64:Connector_Pinouts)); a pinagem não dá corrente.
- **GBA:** não achei medida publicada nesta busca. Não vou usar número de memória.

### A conta que dá para fazer (só regulador)

Queda de tensão no regulador linear: 5 V − 3,3 V = 1,7 V. Potência dissipada = 1,7 V × I. Subida de temperatura = potência × θJA (usando 160 °C/W, o caso pior dos dois):

| Corrente do cartucho | Potência no U3 | Subida da junção (160 °C/W) |
|---|---|---|
| 50 mA | 0,085 W | cerca de 14 °C |
| 100 mA | 0,17 W | cerca de 27 °C |
| 150 mA | 0,255 W | cerca de 41 °C |
| 250 mA (limite) | 0,425 W | cerca de 68 °C |

Com 25 °C ambiente, 250 mA daria junção perto de 93 °C: dentro da faixa do componente, mas sem folga para a proteção de curto (o datasheet fala de limite de corrente, e não de uma corrente de operação segura contínua além dos 250 mA). Se o cartucho puxar perto disso, o regulador esquenta e a tensão cai.

### O que medir na bancada

1. Multímetro em série no 3,3 V entre U3 e o slot (ou fio de teste), com o cartucho parado (só inserido) e **durante a leitura**; anotar o pico.
2. Cartuchos diferentes: N64 de mask ROM, N64 com SRAM/FlashRAM, repro; GBA de mask ROM e repro com flash.
3. Medir a tensão de saída do U3 sob carga (cai muito perto de 250 mA).
4. Se algum passar de cerca de 150 mA: pensar em regulador maior (a mesma pinagem TO-92 não serve) antes de encomendar a `completa`.

Registrado também em `docs/continuacao.md` (só com hardware: corrente do U3 com o N64).

<a id="pier-solar"></a>

## Pesquisa: Pier Solar e mappers piratas do Mega Drive (2026-11-17)

Pedido do usuário: procurar repositórios para basear o suporte (MD-9). Nada foi implementado no firmware: faltam dados que só um cartucho ou um dump confirmado dão (ver "Lacunas"). Tudo abaixo vem de emuladores, não de medição em cartucho.

### Fontes e licenças

| Fonte | Licença | Uso |
|---|---|---|
| MAME `src/devices/bus/megadrive/cart/t5740.cpp` e `rom.cpp` (github.com/mamedev/mame) | BSD-3-Clause | pode servir de base (só os fatos de registrador; o código é nosso) |
| Genesis Plus GX `core/cart_hw/md_cart.c` (github.com/ekeeke/Genesis-Plus-GX) | própria, **proíbe uso comercial** | só leitura de referência; **não copiar código**, incompatível com a GPL v3 do projeto |
| PicoDrive / pico-genesisPlus (`gwpier.c`) | não conferida | citada em PR do pico-genesisPlus; não lida |
| Sega Retro, SpritesMind (threads 37429 e 37433), nesdev | | Sega Retro bloqueou o acesso automático, SpritesMind deu timeout, nesdev deu 404: **não lidos** |
| GitLab, Codeberg, Bitbucket | | nada útil (Bitbucket só tem o repositório do Genesis Plus GX) |

### Pier Solar (T-5740, WaterMelon), segundo o MAME

- 8 janelas de 512 KiB no espaço do cartucho (`0x000000` a `0x3FFFFF`); no reset a janela *i* mostra a página *i*.
- Janelas 0 a 4 fixas. Janelas 5, 6 e 7 trocam de página com escrita de 8 bits, valor `& 0xF` (16 páginas possíveis), nos offsets `0x03`, `0x05` e `0x07` do bloco de E/S "TIME" (`$A130xx`; **a base absoluta não está no arquivo**).
- Offset `0x01`: escrita sem efeito no MAME (comentários: habilita SPI e troca de banco). Offset `0x09`: SPI (bit 0 SI, 1 SCK, 2 HOLD, 3 CS); offset `0x0B`: leitura de SO. EEPROM M95320 (4 KiB).
- Proteção: "no início cada banco aparece espelhado em 32 KiB e uma condição não especificada libera o banco inteiro"; o MAME só tem um *hack* para a leitura de `$018100`-`$0181FF`. **A condição de desbloqueio é desconhecida.**
- Detecção por cabeçalho (Genesis Plus GX): produto `T-5740`.

### Mappers piratas (MAME `rom.cpp`): o que muda para quem só lê a ROM

A maioria só devolve valores de proteção em leituras fora da ROM (Soul Blade, Bug's Life, KOF98/99, Super Mario Bros, Rockman X3, Smart Mouse, Elf Wor, Mahjong...); a ROM é linear, então o `DUMP_ROM` de hoje já deveria servir. **Trocam de banco de verdade** (a leitura linear dá dump errado):

| Mapper | Registrador (endereço de byte) | Banco |
|---|---|---|
| Realtec | `$400000`, `$402000`, `$404000` | 128 KiB (**já feito**, D179) |
| SSF2 | `$A130F3` a `$A130FF` | 512 KiB (**já feito** no OSCR) |
| Lion King 3 | escrita em `$700000` a `$7FFFFF`, valor `& 0xFF` | 32 KiB, janela de 1 MiB |
| Pokémon Stadium / Kaiju | escrita em `$700000` a `$7FFFFF`, valor `& 0x7F` | 32 KiB, mesma fórmula |
| Multicart pirata (A13) | escrita no bloco A13, deslocamento de byte `0x00` a `0x3E` | 64 KiB |
| Beggar Prince, Legend of Wukong, Star Odyssey | escrita no bloco A13 / `$E00` a `$F00`: modo de ROM e SRAM | variam |
| Super Mario World 64 | travas em `$600000` a `$67FFFF` | 64 KiB, lógica com vários registradores |

Detecção segura: por cabeçalho (produto e checksum, como o Genesis Plus GX faz), nunca escrevendo às cegas: um cartucho de flash repro aceita escritas nesses endereços.

### Lacunas (impedem implementar sem cartucho)

1. Pier Solar: base absoluta dos registradores, tamanho real da ROM e condição de desbloqueio. Sem o desbloqueio um dump linear sai espelhado em 32 KiB.
2. Piratas: a fórmula de janela do Lion King 3 / Pokémon Stadium (`(offset<<1) | (banco<<15)`) é a do MAME; não há como saber, sem cartucho, quantos valores de banco o cartucho aceita nem a ordem em que o dump deve ser montado.
3. Nada disto foi confirmado em cartucho real.

Próximo passo possível: dump de teste de um Pier Solar (ou de um dos piratas acima) para confirmar, com leitura linear, se a ROM sai espelhada e com quais escritas.

### Atualização: artigo de quem dumpou um Pier Solar real

Fonte: Brandon L. Wilson, "Pier Solar and the Great Reverser", PoC‖GTFO 15:02 (https://mcfp.felk.cvut.cz/publicDatasets/pocorgtfo/contents/articles/15-02.pdf; texto extraído com `pdftotext`). Único relato **confirmado em cartucho real** que achei. Reddit não pôde ser pesquisado (a ferramenta de busca recusa o domínio); a Krikzz forum deu 403 e a SpritesMind deu timeout.

Fatos do artigo:

- A leitura simples devolve os **primeiros 32 KiB espelhados** por todo o espaço (o mesmo resultado de um dump com o OSCR ou com qualquer leitor de barramento).
- "Os primeiros 32 KB ficam espelhados até que **acessos específicos a `0x18010`** ocorram. O espelhamento é **religado automaticamente pelo hardware se o sistema não estiver executando da ROM por mais de um tempo desconhecido**." O autor acha que o cartucho é uma FPGA e que distingue busca de instrução de leitura de dado: o dump só saiu fazendo o 68000 ficar num laço infinito *na ROM* (por Game Genie) enquanto o Z80 lia o cartucho.
- Depois do desbloqueio: **4 MB lineares** a partir de `$000000`, e os outros 4 MB (**8 MB no total**) por troca de banco "quase igual ao Super Street Fighter II" (registradores `$A130F3` a `$A130FF`, janelas de 512 KB; o autor leu o dump de 4 MB no IDA para descobrir). O checksum do cabeçalho conferiu com o dump completo.
- Save: EEPROM serial acessada por "um par de registradores" (o MAME diz SPI M95320, 4 KiB, em `$A13009` e `$A1300B` se a base for `$A13000`; a SpritesMind diz que `$A13000` a `$A1300F` é a área do Pier Solar).

Conclusão para este projeto:

- O OSCR (e este firmware) lê pelo barramento com o 68000 desligado. **Não há como reproduzir a "execução da ROM"** que o cartucho exige, nem se sabe qual sequência de acessos em `0x18010` desbloqueia. Implementar `Pier Solar` agora seria código sem como testar e provavelmente devolveria 32 KiB espelhados.
- O que **falta saber** para tentar: a sequência exata de leituras/escritas em `0x18010` (e o tempo antes de religar o espelhamento). Só se obtém com analisador lógico no barramento de um cartucho rodando no console, ou com os fontes do MAME/PicoDrive (`t5740.cpp` só tem um *hack* para `$018100` a `$0181FF`).
- Pier Solar fica **fora do alcance** do hardware atual até alguém medir essa sequência. Cartuchos de flash repro (Everdrive) só emulam o mapper do cartucho original.
