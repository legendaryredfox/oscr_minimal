# Fork do firmware do OSCR: plano e estado

Decisão do usuário em 2026-11-03 (D65): em vez do firmware próprio (`firmware/oscr_serial`, D38), usar o **firmware novo do OSCR** e remover o que não usamos (cartão SD, N64 e outros consoles). O programa do computador (`host/` e `gui/`) continua no escopo e mantém o protocolo serial.

## 1. Estado (2026-11-03)

| Item | Estado |
|---|---|
| Cópia do upstream em `firmware/oscr/` | feita (commit `d9cb26a` do upstream) |
| Núcleos desligados (`user.ini`) | nenhum dos que a placa tem slot (o autoteste foi ligado na D152, o SMS na D137 e o N64 na D158) |
| Compila para o Mega (`pio run -e SerialASCII`) | sim: 118.572 B de flash (46,7%), 3.147 B de RAM (38,4%) |
| UI de texto silenciada | feita (`ClockedSerial.mute`, `rawWrite` só para o protocolo) |
| `OSCR::Storage` sem SD | **feito**: `StreamFile` (arquivo virtual) e `StreamSd` (sem sistema de arquivos); o SD sai do build |
| Modo fluxo no protocolo (`Session`) | **feito e testado no PC**: `stream_read`/`stream_write`, `BEGIN` com tamanho `0xFFFFFFFF`, cliente Python e GUI aceitam |
| Laço de comandos (`src/dumper/Dumper.cpp`) ligado aos núcleos | **SNES**, **NES/Famicom**, **Mega Drive**, **GBA** e **GB/GBC**: `DETECT`, `DUMP_ROM`, `READ_SAVE`, `WRITE_SAVE`. **Compila; nunca rodou** |
| NES/Famicom | **ligado (D75)**: `nesProbe` em `Dumper.cpp` monta o registro do núcleo (sem CRDB) a partir de mapper/PRG/CHR/RAM do PC; compila (121.722 B de flash, 47,9%; RAM 41,0%); nunca rodou |
| Erros fatais e esperas por botão | `fatalError` volta ao laço por `longjmp`; `waitButton` não espera |
| Identificação por banco de dados no PC | **feita (D76)**: `host/oscr_host/database.py` e `gui/shared/.../Database.kt` (No-Intro `.dat` e NES 2.0 XML), `identify`/`search`/`--db`/`--game` nas duas CLIs e painel Configurações na GUI |
| Firmware próprio `oscr_serial` | **arquivado (D76)** em `firmware/arquivo/`; o protocolo do fork tem testes próprios em `firmware/oscr/pc-tests/` |
| Validação em hardware | nenhuma |

## 1.1 O que foi feito nesta rodada
- `firmware/oscr_serial/oscr_session.*`: modo fluxo (`Backend::streams()`, `stream_read`, `stream_write`). Os núcleos do OSCR empurram os bytes durante a leitura, em vez de o protocolo puxar por `offset`; os blocos `DATA` são montados num buffer de `block` bytes e cada um espera o `ACK`. No `WRITE_SAVE`, o `ACK` de cada bloco só sai depois que o núcleo consumiu o bloco, para o PC não encher a UART (64 B) enquanto o cartucho grava.
- Testes no PC com um backend de fluxo (`sim_stdio stream`) e o cliente Python: ROM de 5.000 B e save de 2.000 B em pedaços de 300 B contra blocos de 64 a 1.020 B; gravação de 1 a 4.096 B lida em pedaços de 77 B; dado errado devolve `ERRO 0x0007`. 71 testes do host.
- Fork: `include/dumper/StreamFile.h`, `src/dumper/StreamFile.cpp`, `src/dumper/Dumper.cpp` e as cópias do protocolo em `src/dumper/` (um teste confere que são idênticas às de `firmware/oscr_serial`).
- Patches no upstream (todos pequenos, marcados com `OSCR_DUMPER` ou comentários "fork"): `include/flags.h` (flag), `include/api/Storage.h` (tipo do arquivo e do `sd`), `src/arch/avr/generic/Storage.cpp` (sem SD), `ClockedSerial` (mudo e `rawWrite`), `src/ui/interfaces/serial/ascii.cpp` (`_error`, `_fatalError`, `waitButton`), `src/main.cpp` (laço), `include/cores/MegaDrive.h` (`eepSize`).

## 1.2 Como cada coisa se comporta, e as dúvidas
- Cada arquivo aberto para escrita pelo núcleo grava no **mesmo** fluxo. Se um núcleo criar dois arquivos num comando, os bytes se concatenam. No Mega Drive isso não acontece em `readROM`/`readSram`; os outros consoles ainda não foram conferidos.
- Depois do dump, os núcleos releem o arquivo para somar o checksum e comparar com a base de dados: no fluxo serial a releitura devolve 0 bytes (o CRC32 do arquivo inteiro vai no `END`). O que o núcleo imprime sobre isso fica mudo.
- A verificação do `writeSram` (que relê o arquivo) não funciona no fluxo: o PC precisa **reler o save depois de gravar** e comparar. O `WRITE_SAVE` do firmware próprio já conferia byte a byte; aqui não.
- O baud é 1.000.000, **definido pelo `monitor_speed` da placa `mega-embed` no `user.ini`** (vira `OSCR_BAUD`). O upstream usa 250.000. **Correção (D196):** o texto antigo dizia que o `setup()` do fork reabre a serial no baud do protocolo com `ClockedSerial.begin(OSCR_DUMPER_BAUD)`, mas com `ENABLE_STATIC_BAUD=1` o `begin(baud)` ignora o argumento e usa `OSCR_BAUD`; sem o `monitor_speed` o firmware falava a 250.000 e nenhum comando respondia. O `OSCR_DUMPER_BAUD` do `Dumper.cpp` não tem efeito.
- Não conferi o que `OSCR::Power::setVoltage`/`changeVoltagePrompt` fazem sem VSELECT neste shield. Sem `ENABLE_ONBOARD_ATMEGA`, `enableCartridge` não faz nada.
- Um `longjmp` por cima do código dos núcleos pula destrutores e deixa o hardware como estava: o laço sempre chama `Power::disableCartridge()` depois.

## 2. O acoplamento com o SD

Todos os núcleos gravam por `OSCR::Storage::Shared` (`include/api/Storage.h`, implementação AVR em `src/arch/avr/generic/Storage.cpp`): `createFile`/`createFolder`, `open`, `sharedFile.write/read/seek/close`, `buffer` compartilhado. Usos por núcleo: SNES 92, NES 72, MD 83, GBA 93, GB 146 (linhas citando `Storage::`). Como o acesso é por essa API, a troca é em um ponto.

Pontos que o plano precisa resolver:
1. **Gravar (ler ROM/save do cartucho):** `File::write` vira quadros `DATA` do protocolo, e `createFile`/`close` viram `BEGIN` (com o nome e a extensão que o núcleo escolheu) e `END` com o CRC32. O CRC32 do arquivo já é calculado pelo `File` (`crcState`).
2. **Ler (gravar save no cartucho):** `File::read` vira um pedido de bloco ao PC. O PC precisa mandar o arquivo sob demanda.
3. **`seek`/`size`/`available`:** usados por conferência e por barras de progresso; em fluxo serial só existe sequencial, então os pontos que dependem de `seek` precisam ser achados (um por um) e adaptados.
4. **Menus:** os núcleos são dirigidos por menus (`OSCR::UI`). Com `io:serial` o menu aparece como texto e as escolhas vêm de comandos digitados. Para o nosso protocolo é preciso chamar as funções dos núcleos (por exemplo ler ROM do SNES) **sem o menu**, ou deixar o PC dirigir o menu serial.
5. **Base de dados (CRDB):** usa o SD também. Sem SD, a identificação do cartucho por base de dados some (o mapper/tamanho do NES voltam a ser informados pelo usuário, como hoje).
6. **Configurações, logs e atualizador:** também usam o SD; desligar.

## 3. O que falta (levantado em 2026-11-03; os itens 3.1.1 a 3.1.6 estão feitos só para o Mega Drive)

### 3.1 Firmware (`firmware/oscr/`)
1. **Silenciar a UI de texto.** Hoje a UI do OSCR imprime texto na mesma UART em que vai o protocolo binário; um `print` no meio de um quadro o corrompe. Plano: uma marca de "mudo" em `ClockedSerial` (a UI passa a descartar) e uma escrita crua separada para o protocolo.
2. **Trocar o `OSCR::Storage` (SdFat) por uma saída serial.** `File::write/writeRaw` viram quadros `DATA` (com espera de `ACK`), `createFile` vira o `BEGIN`, `close` vira o `END` com o CRC32 que o `File` já calcula. `File::read` (usado ao gravar save) vira pedido de bloco ao PC. `rewind`, `seekSet/seekCur`, `getSize` e `Storage::sd.exists` precisam de um comportamento definido: em fluxo serial só há sequencial, então o que os núcleos fazem depois do dump (reler o arquivo para somar o checksum, 13 `rewind` no GB, 1 `seekSet(16)` e 1 `seekSet(16+PRG)` no NES) deixa de existir ou é refeito no PC.
3. **Tirar o SD do build:** `setup()` chama `Storage::setup`, `Logger`, `Time` e `Configuration`; os dois últimos usam arquivo. Desligar por configuração ou por `#if`.
4. **Laço de comandos do protocolo no lugar do menu.** `loop()` do upstream abre o menu dos consoles. O novo laço lê quadros, atende `INFO`, `DETECT`, `DUMP_ROM`, `READ_SAVE`, `WRITE_SAVE` e chama a função do núcleo certo (por exemplo `MegaDrive::getCartInfo()` e `readROM()`). Isso exige declarar no cabeçalho de cada núcleo funções que hoje são internas ao `.cpp`.
5. **Tamanho desconhecido no `BEGIN`.** Os núcleos só conhecem o tamanho dentro de `readROM()`. O `BEGIN` passa a aceitar `0xFFFFFFFF` (desconhecido); o `END` leva o tamanho e o CRC32 reais. O host e a GUI precisam aceitar isso (barra de progresso pelo tamanho do `DETECT`).
6. **Erros fatais e esperas por botão.** `OSCR::UI::fatalError`, `error` e `waitButton` travam esperando o usuário. No modo protocolo, devem responder `ERRO` e voltar ao laço (candidato: `setjmp/longjmp`).
7. **Opções do usuário (NES: mapper, PRG, CHR; GBA: tipo de save).** Os núcleos as leem de variáveis internas preenchidas por menu; o laço de comandos precisa preenchê-las a partir dos campos do protocolo.
8. **Um núcleo por vez**, cada um com leitura e teste de compilação: Mega Drive (primeiro), GBA, GB/GBC, SNES, NES/Famicom.
9. **Hardware do shield versus HW5 do upstream:** o upstream assume `ENABLE_ONBOARD_ATMEGA`/VSELECT em partes; o shield não tem VSELECT nem chave 3V/5V. Conferir as flags do ambiente `SerialASCII` e o que `Power::setVoltage` faz sem VSELECT.

### 3.2 Banco de dados: identificação no computador (decisão do usuário, 2026-11-03)
O firmware novo identifica o jogo por uma base (CRDB) lida do cartão SD. Sem SD, **a identificação passa para o computador**, pela serial:
- O firmware **não** carrega a CRDB. Ele devolve ao PC o que o PC precisa para identificar: no `DETECT`, o nome do cabeçalho, os tamanhos e o checksum do cabeçalho; depois do dump, o `END` com o CRC32.
- O PC (host/GUI) consulta uma base do usuário (No-Intro, NES 2.0 XML ou a CRDB do OSCR, em arquivo local) pelo CRC32 e mostra o nome do jogo, a versão e se o dump confere.
- Para o **NES**, onde o cartucho não diz o mapper, o PC escolhe mapper, PRG, CHR e RAM na base (por nome do jogo escolhido pelo usuário) e os manda como opções do `DUMP_ROM`, que o protocolo já aceita. A tabela mapper → faixas válidas de tamanho (`crdbNESMapperRecord`) também fica no PC.
- Ficam fora do firmware: `CRDB`, o navegador de base, os arquivos `.crdb`. Isso economiza flash e remove a dependência do SD.
- Os arquivos da base **não vêm no clone** do OSCR (`databases/` está vazio). O usuário traz a base; o formato do No-Intro (`.dat` XML) e o da CRDB têm leitor simples no host.

### 3.3 Host (`host/`) e GUI (`gui/`)
1. Aceitar `BEGIN` com tamanho desconhecido.
2. Leitor de base de dados local (CRC32 → nome, mapper, tamanhos) e o campo "base de dados" na GUI e na CLI.
3. Mostrar o nome do jogo identificado ao lado do CRC32.
4. Os testes do host que usam o firmware simulado em C++ (`test_firmware_cpp`) continuam valendo para o protocolo, mas não para os núcleos do OSCR.

## 4. Ordem de trabalho
1. Silenciar a UI de texto e escrever o `Storage` serial (itens 3.1.1 a 3.1.3).
2. Laço de comandos com um núcleo de ponta a ponta: **Mega Drive, `DETECT` e `DUMP_ROM`** (itens 3.1.4 a 3.1.6), compilando para o Mega.
3. `READ_SAVE` e `WRITE_SAVE` do Mega Drive; depois GBA, GB/GBC, SNES e NES (3.1.7 e 3.1.8).
4. Host e GUI (3.3) e a base de dados no PC (3.2).
5. ~~Arquivar `firmware/oscr_serial`~~ feito (D76).

## 5. Riscos

- Nenhum teste existente no PC cobre o código do OSCR: ele não roda fora do AVR. Os testes com cartucho simulado (990 verificações) são do nosso código e deixam de valer para o fork.
- O tamanho do firmware com tudo ligado era de cerca de 125 KB dos 253 KB (valor de 2026-11-03); hoje, com N64, SMS, flash e autoteste, são 194 KB. Medição atual na seção 6.
- O firmware do OSCR é grande (SNES 2.921 linhas, NES 5.305, MD 3.065, GBA 3.137, GB 3.619). Cada console precisa de leitura antes de ser ligado ao protocolo.

## 6. Orçamento de flash e RAM (medido em 2026-11-14, D162)

`python3 tools/flash_budget.py measure` compila `SerialASCII` e soma o tamanho dos símbolos do `firmware.elf` por namespace (`avr-nm -S -C`). Código que o compilador embutiu (LTO) conta no chamador, então o valor de cada núcleo é um **piso**. A soma dos símbolos (190.734 B) fica 3,6 KB abaixo do total do `pio` (tabela de vetores, preenchimento e `.data` copiado).

| Origem (namespace do símbolo) | Flash (B) | % do flash do Mega | RAM (B) |
|---|---|---|---|
| libc, Arduino e outros | 38077 | 15.0 % | 1031 |
| núcleo NES | 31156 | 12.3 % | 72 |
| núcleo N64 | 16747 | 6.6 % | 26 |
| núcleo MegaDrive | 15444 | 6.1 % | 28 |
| OSCR::Dumper | 13189 | 5.2 % | 1275 |
| núcleo SNES | 12600 | 5.0 % | 6 |
| núcleo GameBoyAdvance | 12527 | 4.9 % | 2 |
| núcleo GameBoy | 8683 | 3.4 % | 7 |
| núcleo GameBoyX | 7820 | 3.1 % | 0 |
| núcleo Flash | 7673 | 3.0 % | 24 |
| OSCR::UI | 4697 | 1.8 % | 12 |
| camada dumper (src/dumper) | 4532 | 1.8 % | 89 |
| núcleo GameBoySmart | 2543 | 1.0 % | 56 |
| núcleo SMS | 2402 | 0.9 % | 1 |
| OSCR::Storage | 2204 | 0.9 % | 745 |
| OSCR::Strings | 1842 | 0.7 % | 0 |
| OSCR::CRDB | 1452 | 0.6 % | 0 |
| OSCR::Databases | 1334 | 0.5 % | 16 |
| OSCR::CRC32 | 1082 | 0.4 % | 4 |
| núcleo SelfTest | 973 | 0.4 % | 0 |
| núcleo GameBoyMem | 689 | 0.3 % | 0 |
| OSCR::Updater | 677 | 0.3 % | 0 |
| OSCR::Lang | 647 | 0.3 % | 0 |
| OSCR::Cores | 469 | 0.2 % | 92 |
| OSCR::Apps | 420 | 0.2 % | 0 |
| OSCR::Power | 344 | 0.1 % | 0 |
| OSCR::Util | 188 | 0.1 % | 0 |
| OSCR::Settings | 144 | 0.1 % | 0 |
| OSCR::Time | 105 | 0.0 % | 9 |
| OSCR::Menus | 40 | 0.0 % | 40 |
| OSCR::Logger | 34 | 0.0 % | 25 |
| OSCR::Serial | 0 | 0.0 % | 33 |
| soma dos símbolos | 190734 | | 3593 |
| **medido pelo `pio` (SerialASCII)** | **194372** | **76.5 %** | **4128** |
| total do Mega (flash sem bootloader; RAM) | 253952 | | 8192 |

Leitura:

- **Sobram 59.580 B de flash (23,5 %) e 4.064 B de RAM.** A imagem única continua cabendo, então **nenhuma variante foi criada** (regra do usuário, D161). O teste `python3 tools/flash_budget.py check` falha acima de 95 % do flash ou 80 % da RAM (a pilha precisa de folga) e roda para `SerialASCII` e `SerialASCII_Volt`.
- Os maiores núcleos são NES (31 KB, por causa dos mappers), N64 (17 KB), Mega Drive (15 KB), SNES (13 KB) e GBA (13 KB).  O núcleo `Flash` sozinho tem 7,7 KB; o custo total de `HAS_FLASH` (antes estimado em ~27 KB) inclui as funções de gravação espalhadas nos outros núcleos e nas costuras `*Flash.cpp`, e **não** foi medido aqui.
- **Folga que dá para recuperar sem tirar função** (nada disso foi feito): `OSCR::UI` (4,7 KB, a interface de texto está muda), `OSCR::Updater`, `OSCR::Lang`, `OSCR::Apps` e `OSCR::Storage` (2,2 KB e 745 B de RAM, o SD que não existe aqui). São cerca de 9 KB de flash e 0,8 KB de RAM.
- **Não dá para medir "sem o núcleo X" desligando-o no `user.ini`:** a camada `src/dumper/` chama todos os núcleos sem `#if`; as seis compilações tentadas falharam. Se um dia uma variante for necessária, é preciso primeiro condicionar essas chamadas a `#if` (por exemplo `OSCR_HAS_N64`).
