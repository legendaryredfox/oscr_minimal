# Repositórios de referência baixados e o que aprender deles (2026-11-13)

Pedido do usuário: achar mais repositórios e projetos open source de dumpers de cartucho, baixar os mais promissores para `references/`, analisar o firmware deles e dizer que melhorias ou recursos cabem aqui. **Nada foi adicionado ao projeto a partir desta análise: cada item da seção 3 espera a aprovação do usuário.**

## 1. O que foi baixado

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

## 2. O que cada um mostra

- **FlashGBX** é o mais rico. `FlashGBX/config/db_AGB.json` (2.948 jogos de GBA) e `db_DMG.json` (3.136 de GB) dão, para cada jogo, o **tipo de save (`st`) e o tamanho do save (`ss`)**, o tamanho da ROM e o CRC32; a chave é o **SHA-1 dos primeiros 0x180 bytes do cabeçalho** (`RomFileAGB.py`, linha 197 e seguintes). Hoje, no GBA, o nosso programa só adivinha o tipo de save procurando a cadeia da biblioteca de save na ROM (`FLASH1M_V`, `EEPROM_V`). Há também `fc_*.txt` (sequências de comando de dezenas de flash carts), "Dump Report" (relatório de preservação com hashes), decodificação de fotos do Game Boy Camera, leitor de e-Reader, backup de RTC e de saves "sem bateria", e uma lista de mappers de GB bem mais longa que a do OSCR (MBC1M, MMM01, M161, HuC-3, TAMA5, Sachen, Wisdom Tree, Datel...). O firmware L16 do GBxCart traz uma opção de **controle de fluxo** com janelas de 64 bytes por confirmação, para estabilidade.
- **famicom-dumper-client**: mappers descritos em **scripts C#** no PC (o firmware só faz leitura e escrita de barramento), então um mapper novo não exige regravar o firmware; leitura e gravação de **FDS**; saída em **NES 2.0** e **UNIF** (com `--battery`, tamanhos de PRG/CHR RAM e NVRAM); `--verify`, `--lock` (proteção de setores da flash depois de gravar), `--reset` (simula o reset do console) e `--sound` (aviso sonoro no fim); modo **servidor gRPC** para qualquer linguagem. O `INL-retro-progdump` faz o mesmo com Lua.
- **UMDv3**: cada adaptador de cartucho tem um **MCP23008** que **identifica o console** pelo I²C, e o firmware configura o barramento sozinho. O `SNES_Dumper` oferece `-read auto` ("modo automático"). Em ambos, o usuário não escolhe o sistema.
- **n64cartreader**: (1) **catálogo embutido** que identifica jogo, tamanho de ROM e tipo de save (o que fizemos agora na D158, pelo CRC1); (2) **interface Web Serial**: uma página HTML + JavaScript que fala com o dumper direto pelo Chrome ou Edge, sem instalar nada; (3) **matriz de validação** (`n64_validation_matrix.py`, `n64_cart_verify.py`): cada cartucho "dourado" tem hashes SHA-256 conhecidos, exporta-se, grava-se, relê-se e compara-se; (4) **procedimento de teste de fabricação** (`docs/MANUFACTURING_TEST.md`) para a placa recém-montada; (5) limitações conhecidas: **contenção do Joybus** quando cartucho e controle dividem o fio de dados, e reencaixar o cartucho antes de repetir a leitura da EEPROM depois de trocar o cartucho.
- **retrode3-oscr**: confirma o caminho que seguimos (OSCR com linha de comando no PC), mas sem protocolo de blocos com CRC nem GUI; as nossas camadas (CRC32 por bloco, ACK, JSON) vão além.

## 3. Propostas (todas aguardam aprovação do usuário)

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

## 4. Notas de licença

`FlashGBX`, `famicom-dumper-*` e `SNES_Dumper` (software) são GPL-3.0, a mesma licença do firmware daqui; copiar dados ou código exige manter o aviso de autoria e a licença. Os bancos `db_AGB.json` e `db_DMG.json` do FlashGBX derivam de listas da comunidade e de checagens do autor (Lesserkuma): antes do P2, ler o `Third Party Notices.md` do repositório e citar a origem em `database/` como já se faz com a base do OSCR.

## 5. O que foi feito depois da aprovação (D160)

O usuário aprovou P1, P2, P3, P4, P5, P6 e P9 (não P7, P8 nem P10). Feitos: **P1** (MD5 e SHA-1), **P2** (save do GBA pela base do FlashGBX; do GB não, porque `db_DMG.json` não traz save), **P3** (`tools/hwtest/hwtest.py` e `docs/referencia/teste-de-bancada.md`), **P4** (`--sound` e aviso na GUI), **P5** (`-s auto` e o botão da GUI), **P9** (`gbcamera` nas duas CLIs; **sem GUI**).

**P6 (`peek`) não foi feito, por decisão técnica a confirmar com o usuário:** (a) um `peek` de verdade (ler N bytes de um endereço qualquer) exige, para cada sistema, a preparação do barramento do núcleo do OSCR (`cartOn`, controles, direção dos pinos), diferente em cada um; sem placa para validar, um valor errado seria mostrado como se fosse bom, o pior resultado para um comando de diagnóstico; (b) a alternativa só no PC (um `dump` com poucos KB e `ABORT`) não serve: o firmware, depois do `ABORT`, deixa o núcleo do OSCR terminar a leitura inteira (o `StreamFile` só devolve erro; vários núcleos não param), o que leva minutos em ROMs grandes. Proposta: fazer o `peek` por sistema, começando pelo Mega Drive e pelo GBA, **junto da primeira placa montada**, comparando com um dump completo, e só então generalizar.

