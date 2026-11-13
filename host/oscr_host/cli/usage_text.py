# SPDX-License-Identifier: GPL-3.0-or-later
"""Texto de `--help` da CLI Kotlin nos quatro idiomas (D133). Vai para o TSV da Kotlin pela chave `usage.text`.
Comandos, opções, nomes de sistema e valores ficam como estão; só a descrição é traduzida."""

_EN = """usage: dumper [options] <command> [options]

commands:
  ports        list serial ports
  systems      list systems, extensions and per-system options (does not open the port)
  errors       list device error codes and CLI exit codes (does not open the port)
  info         firmware version and supported systems
  firmware-flash  flash the fork's firmware to the Arduino Mega over USB with avrdude (replaces the board's program) [--hex FILE --env NAME --avrdude PATH --yes --dry-run]
  detect       detect the cartridge            (-s SYSTEM)
  identify     identify saved ROMs by CRC32 in the database (--db), without opening the port
  search       search games by name in the database (--db), without opening the port
  dump         read the ROM                    (-s SYSTEM [-o FILE])
  save-read    read the save                   (-s SYSTEM [-o FILE])
  save-write   write the save                  (-s SYSTEM -i FILE --yes)
  flash-id     generic flash programmer: read the chip ID (--bus 8|plcc32|16|eprom --flash-kb N [--flash-type T])
  flash-read   generic flash programmer: read the whole chip to a file (-o FILE)
  flash-blank  generic flash programmer: check that the chip is blank (reads the chip and checks on the PC)
  flash-erase  generic flash programmer: ERASE the whole chip (--flash-type is required on 8-bit flash) --yes
  flash-write  generic flash programmer: erase and write a file to the chip (-i FILE), then read it back to verify
  rom-write    write the ROM to a flash cartridge, ERASES the chip (-i FILE [--chip nesmaker|a29040b] --yes)

options (accepted before or after the command):
  -p, --port PORT      serial port (default: first ttyUSB/ttyACM/COM)
  -b, --baud N         baud (default: 1000000, then 115200)
  --simulate           in-memory simulator (no hardware; only system 'mock' has a cartridge)
  --json               one JSON line on stdout, always with "ok"; errors: {"ok":false,"error":{kind,message,hint}}
  --progress MODE      auto | none | jsonl (one JSON line per 1% on stderr)
  --lang TAG           language of messages: en (default), pt-BR, ru, zh-CN (else OSCR_LANG, then the locale)
  -s, --system NAME    snes nes famicom md gba gb mock (default: mock)
  -o, --output FILE    output file (the right extension is added if missing; overwrites)
  -i, --input FILE     save file to write
  --block N            block size (default 512)
  --mapper N --prg KB --chr KB --ram KB     NES/Famicom/GBA options (see 'systems')
  --db PATH            extra game database: file or folder of .dat (No-Intro) or nes20db.xml; repeatable; also reads env OSCR_DB
                       (the project's own database, from the OSCR legacy, is always loaded first)
  --no-builtin-db      do not load the project's own game database
  --game NAME          dump, NES/Famicom: game name in the NES 2.0 XML database; fills --mapper/--prg/--chr left at 0
  --limit N            search: maximum results (default 20)
  --chip NAME          rom-write: nesmaker (SST 39SF040, mapper 30) or a29040b (mapper 0), default from the file's iNES mapper;
                       SNES: snes-lorom or snes-hirom (required, the wiring of the CFI flash)
                       Mega Drive: md-flash (the default; the firmware identifies the chip by ID: MX29F1610, S29GL064N, 32 and 64 Mbit M29W/MX29LV, MX29L3211, PA28F400, SST39VF)
  --bus NAME           flash-*: 8 (8-bit flash on the flash adapter), plcc32 (8-bit PLCC32 on the SNES adapter), 16 (16-bit flash) or eprom (27C322)
  --flash-kb N         flash-*: chip size in KB (1 to 8192; the EPROM is always 4096)
  --capacity KB        rom-write, SNES CFI, layout 1x: flash size, 2048 or 4096 (default: the smallest the ROM fits)
  --layout NAME        rom-write, SNES CFI: chips on the cartridge: 1x (one 2 or 4 MB chip, default), 2x2mb, 2x4mb, 4x2mb, 1x8mb (the last three: ROM of 6 to 8 MB, as in the OSCR)
  --block369 N         rom-write, GBA 369-in-1: 4 MB block (0 to 63) where writing starts ("Write Offset" of the OSCR); 0 = from the start
  --flash-type NAME    rom-write, SNES P0/P1 chips (snes-lorom-p0, snes-hirom-p0, snes-exlorom-p1, snes-exhirom-p1): 8-bit flash type (29f032, 29f1610, lh28f0xx, 29f1601, 29lv640, 29f800, 29gl, e28fxxxj3a)
  --flash-mb N         rom-write, SNES P0/P1: chip size in MB (1 to 8)
  --sector-kb N        rom-write, SNES P0/P1, types 29gl, lh28f0xx, e28fxxxj3a: sector size in KB (power of 2)
  --buffer N           rom-write, SNES P0/P1, same types: write buffer in bytes (power of 2, 2 to 128)
  --begin-timeout S    rom-write: seconds to wait for the erase before the data (default 90)
  --ignore-cart-limit  rom-write -s md: write even if the ROM is over 2 MiB on an S29GL cartridge (KY / FlashKit boards have only 2 MiB of flash; default: refuse, nothing erased)
  --raw                dump -s nes|famicom: write PRG and CHR as separate files (.prg and .chr), without the iNES header (the OSCR raw read)
  --twice              dump: read the ROM twice and compare; if they differ, write both reads (NAME.leitura1 and NAME.leitura2, as in the Python CLI) and exit with an error (kind mismatch)
  --flash-id           detect -s md: also identify the cartridge's flash chip (the probe writes ID commands to the cartridge; mask ROM ignores them)
  --color MODE         auto (default: only in a terminal, respects NO_COLOR), always or never: colours and ASCII art; --json never has them
  --sound              beep when done: one bell on success, three on failure (long operations)
  --hex FILE           firmware-flash: the firmware .hex (default: env OSCR_FIRMWARE_HEX or firmware/oscr/.pio/build/<env>/firmware.hex)
  --env NAME           firmware-flash: PlatformIO environment the .hex comes from (default SerialASCII; SerialASCII_Volt)
  --avrdude PATH       firmware-flash: avrdude to use (default: env AVRDUDE, PATH or PlatformIO's)
  --wait S             firmware-flash: seconds waiting for the device to answer INFO after flashing (default 12)
  --dry-run            firmware-flash: only show the avrdude command and the current firmware version
  --no-verify          firmware-flash, rom-write, save-write: do not read the ROM/save back to verify after writing (default: verify)
  --yes                do not ask before writing (required outside a terminal)
  --no-backup          save-write: do not read the current save first
  --backup-dir DIR     save-write: backup folder (default ~/oscr_backups)

exit codes: 0 ok | 1 error | 2 no cartridge | 3 no port/device | 4 refused (needs --yes) | 64 usage | 130 Ctrl+C
Full contract: docs/referencia/cli.md"""

_PT = """uso: dumper [opções] <comando> [opções]

comandos:
  ports        lista as portas seriais
  systems      lista sistemas, extensões e opções de cada sistema (não abre a porta)
  errors       lista os códigos de erro do dispositivo e os códigos de saída da CLI (não abre a porta)
  info         versão do firmware e sistemas suportados
  firmware-flash  grava o firmware do fork no Arduino Mega pela USB com o avrdude (substitui o programa da placa) [--hex ARQ --env NOME --avrdude CAMINHO --yes --dry-run]
  detect       detecta o cartucho              (-s SISTEMA)
  identify     identifica ROMs salvas pelo CRC32 na base de dados (--db), sem abrir a porta
  search       busca jogos pelo nome na base de dados (--db), sem abrir a porta
  dump         lê a ROM                        (-s SISTEMA [-o ARQ])
  save-read    lê o save                       (-s SISTEMA [-o ARQ])
  save-write   grava o save                    (-s SISTEMA -i ARQ --yes)
  flash-id     programador de flash genérico: lê o ID do chip (--bus 8|plcc32|16|eprom --flash-kb N [--flash-type T])
  flash-read   programador de flash genérico: lê o chip inteiro para um arquivo (-o ARQ)
  flash-blank  programador de flash genérico: confere se o chip está em branco (lê o chip e confere no PC)
  flash-erase  programador de flash genérico: APAGA o chip inteiro (--flash-type é obrigatório na flash de 8 bits) --yes
  flash-write  programador de flash genérico: apaga e grava um arquivo no chip (-i ARQ), depois lê de volta para conferir
  rom-write    grava a ROM em um cartucho flash, APAGA o chip (-i ARQ [--chip nesmaker|a29040b] --yes)

opções (aceitas antes ou depois do comando):
  -p, --port PORTA     porta serial (padrão: a primeira ttyUSB/ttyACM/COM)
  -b, --baud N         baud (padrão: 1000000, depois 115200)
  --simulate           simulador em memória (sem hardware; só o sistema 'mock' tem cartucho)
  --json               uma linha JSON na saída padrão, sempre com "ok"; erros: {"ok":false,"error":{kind,message,hint}}
  --progress MODO      auto | none | jsonl (uma linha JSON por 1% no stderr)
  --lang TAG           idioma das mensagens: en (padrão), pt-BR, ru, zh-CN (senão OSCR_LANG, depois a locale)
  -s, --system NOME    snes nes famicom md gba gb mock (padrão: mock)
  -o, --output ARQ     arquivo de saída (a extensão certa é acrescentada se faltar; sobrescreve)
  -i, --input ARQ      arquivo de save a gravar
  --block N            tamanho do bloco (padrão 512)
  --mapper N --prg KB --chr KB --ram KB     opções de NES/Famicom/GBA (veja 'systems')
  --db CAMINHO         base de jogos extra: arquivo ou pasta de .dat (No-Intro) ou nes20db.xml; repetível; lê também a variável OSCR_DB
                       (a base do próprio projeto, herdada do OSCR, é sempre carregada primeiro)
  --no-builtin-db      não carrega a base de jogos do próprio projeto
  --game NOME          dump, NES/Famicom: nome do jogo na base XML NES 2.0; preenche --mapper/--prg/--chr deixados em 0
  --limit N            search: máximo de resultados (padrão 20)
  --chip NOME          rom-write: nesmaker (SST 39SF040, mapper 30) ou a29040b (mapper 0), padrão pelo mapper iNES do arquivo;
                       SNES: snes-lorom ou snes-hirom (obrigatório, a ligação da flash CFI)
                       Mega Drive: md-flash (o padrão; o firmware identifica o chip pelo ID: MX29F1610, S29GL064N, M29W/MX29LV de 32 e 64 Mbit, MX29L3211, PA28F400, SST39VF)
  --bus NOME           flash-*: 8 (flash de 8 bits no adaptador de flash), plcc32 (PLCC32 de 8 bits no adaptador SNES), 16 (flash de 16 bits) ou eprom (27C322)
  --flash-kb N         flash-*: tamanho do chip em KB (1 a 8192; a EPROM é sempre 4096)
  --capacity KB        rom-write, SNES CFI, layout 1x: tamanho da flash, 2048 ou 4096 (padrão: o menor em que a ROM cabe)
  --layout NOME        rom-write, SNES CFI: chips no cartucho: 1x (um chip de 2 ou 4 MB, padrão), 2x2mb, 2x4mb, 4x2mb, 1x8mb (os três últimos: ROM de 6 a 8 MB, como no OSCR)
  --block369 N         rom-write, GBA 369-in-1: bloco de 4 MB (0 a 63) onde a gravação começa ("Write Offset" do OSCR); 0 = do início
  --flash-type NOME    rom-write, chips SNES P0/P1 (snes-lorom-p0, snes-hirom-p0, snes-exlorom-p1, snes-exhirom-p1): tipo de flash de 8 bits (29f032, 29f1610, lh28f0xx, 29f1601, 29lv640, 29f800, 29gl, e28fxxxj3a)
  --flash-mb N         rom-write, SNES P0/P1: tamanho do chip em MB (1 a 8)
  --sector-kb N        rom-write, SNES P0/P1, tipos 29gl, lh28f0xx, e28fxxxj3a: tamanho do setor em KB (potência de 2)
  --buffer N           rom-write, SNES P0/P1, mesmos tipos: buffer de gravação em bytes (potência de 2, de 2 a 128)
  --begin-timeout S    rom-write: segundos de espera pelo apagamento antes dos dados (padrão 90)
  --ignore-cart-limit  rom-write -s md: grava mesmo que a ROM passe de 2 MiB num cartucho S29GL (placas KY / FlashKit só têm 2 MiB de flash; padrão: recusa, nada apagado)
  --raw                dump -s nes|famicom: grava PRG e CHR em arquivos separados (.prg e .chr), sem o cabeçalho iNES (a leitura raw do OSCR)
  --twice              dump: lê a ROM duas vezes e compara; se diferirem, grava as duas leituras (NOME.leitura1 e NOME.leitura2, como na CLI Python) e sai com erro (kind mismatch)
  --flash-id           detect -s md: identifica também o chip de flash do cartucho (a sonda grava comandos de ID no cartucho; ROM de máscara ignora)
  --color MODO         auto (padrão: só em terminal, respeita NO_COLOR), always ou never: cores e arte ASCII; --json nunca tem
  --sound              avisa ao terminar: um sinal sonoro se deu certo e três se falhou (operações longas)
  --hex ARQ            firmware-flash: o .hex do firmware (padrão: variável OSCR_FIRMWARE_HEX ou firmware/oscr/.pio/build/<env>/firmware.hex)
  --env NOME           firmware-flash: ambiente do PlatformIO de onde vem o .hex (padrão SerialASCII; SerialASCII_Volt)
  --avrdude CAMINHO    firmware-flash: avrdude a usar (padrão: variável AVRDUDE, PATH ou o do PlatformIO)
  --wait S             firmware-flash: segundos esperando o dispositivo responder ao INFO depois da gravação (padrão 12)
  --dry-run            firmware-flash: só mostra o comando do avrdude e a versão atual do firmware
  --no-verify          firmware-flash, rom-write, save-write: não lê a ROM/save de volta para conferir depois de gravar (padrão: conferir)
  --yes                não pergunta antes de gravar (obrigatório fora de terminal)
  --no-backup          save-write: não lê o save atual antes
  --backup-dir DIR     save-write: pasta do backup (padrão ~/oscr_backups)

códigos de saída: 0 ok | 1 erro | 2 sem cartucho | 3 sem porta/dispositivo | 4 recusado (precisa de --yes) | 64 uso | 130 Ctrl+C
Contrato completo: docs/referencia/cli.md"""

_RU = """использование: dumper [опции] <команда> [опции]

команды:
  ports        список последовательных портов
  systems      список систем, расширений и опций каждой системы (порт не открывается)
  errors       список кодов ошибок устройства и кодов возврата CLI (порт не открывается)
  info         версия прошивки и поддерживаемые системы
  firmware-flash  записать прошивку форка в Arduino Mega по USB через avrdude (заменяет программу платы) [--hex ФАЙЛ --env ИМЯ --avrdude ПУТЬ --yes --dry-run]
  detect       определить картридж             (-s СИСТЕМА)
  identify     опознать сохранённые ROM по CRC32 в базе (--db), порт не открывается
  search       искать игры по названию в базе (--db), порт не открывается
  dump         прочитать ROM                   (-s СИСТЕМА [-o ФАЙЛ])
  save-read    прочитать сохранение            (-s СИСТЕМА [-o ФАЙЛ])
  save-write   записать сохранение             (-s СИСТЕМА -i ФАЙЛ --yes)
  flash-id     универсальный программатор flash: прочитать ID микросхемы (--bus 8|plcc32|16|eprom --flash-kb N [--flash-type T])
  flash-read   универсальный программатор flash: прочитать всю микросхему в файл (-o ФАЙЛ)
  flash-blank  универсальный программатор flash: проверить, что микросхема пуста (читает микросхему и проверяет на ПК)
  flash-erase  универсальный программатор flash: СТЕРЕТЬ всю микросхему (для 8-битной flash обязателен --flash-type) --yes
  flash-write  универсальный программатор flash: стереть и записать файл в микросхему (-i ФАЙЛ), затем прочитать обратно для проверки
  rom-write    записать ROM в flash-картридж, СТИРАЕТ микросхему (-i ФАЙЛ [--chip nesmaker|a29040b] --yes)

опции (принимаются до или после команды):
  -p, --port ПОРТ      последовательный порт (по умолчанию: первый ttyUSB/ttyACM/COM)
  -b, --baud N         скорость (по умолчанию: 1000000, затем 115200)
  --simulate           симулятор в памяти (без оборудования; картридж есть только у системы 'mock')
  --json               одна строка JSON в stdout, всегда с "ok"; ошибки: {"ok":false,"error":{kind,message,hint}}
  --progress РЕЖИМ     auto | none | jsonl (одна строка JSON на каждый 1% в stderr)
  --lang TAG           язык сообщений: en (по умолчанию), pt-BR, ru, zh-CN (иначе OSCR_LANG, затем локаль)
  -s, --system ИМЯ     snes nes famicom md gba gb mock (по умолчанию: mock)
  -o, --output ФАЙЛ    выходной файл (нужное расширение добавляется, если его нет; перезаписывает)
  -i, --input ФАЙЛ     файл сохранения для записи
  --block N            размер блока (по умолчанию 512)
  --mapper N --prg KB --chr KB --ram KB     опции NES/Famicom/GBA (см. 'systems')
  --db ПУТЬ            дополнительная база игр: файл или папка с .dat (No-Intro) или nes20db.xml; можно повторять; читает также переменную OSCR_DB
                       (собственная база проекта, унаследованная от OSCR, всегда загружается первой)
  --no-builtin-db      не загружать собственную базу игр проекта
  --game ИМЯ           dump, NES/Famicom: название игры в XML-базе NES 2.0; заполняет --mapper/--prg/--chr, оставленные равными 0
  --limit N            search: максимум результатов (по умолчанию 20)
  --chip ИМЯ           rom-write: nesmaker (SST 39SF040, mapper 30) или a29040b (mapper 0), по умолчанию по iNES-мапперу файла;
                       SNES: snes-lorom или snes-hirom (обязательно, разводка flash CFI)
                       Mega Drive: md-flash (по умолчанию; прошивка определяет микросхему по ID: MX29F1610, S29GL064N, M29W/MX29LV на 32 и 64 Мбит, MX29L3211, PA28F400, SST39VF)
  --bus ИМЯ            flash-*: 8 (8-битная flash на адаптере flash), plcc32 (8-битная PLCC32 на адаптере SNES), 16 (16-битная flash) или eprom (27C322)
  --flash-kb N         flash-*: размер микросхемы в КБ (от 1 до 8192; EPROM всегда 4096)
  --capacity KB        rom-write, SNES CFI, раскладка 1x: размер flash, 2048 или 4096 (по умолчанию: наименьший, в который помещается ROM)
  --layout ИМЯ         rom-write, SNES CFI: микросхемы на картридже: 1x (одна на 2 или 4 МБ, по умолчанию), 2x2mb, 2x4mb, 4x2mb, 1x8mb (последние три: ROM от 6 до 8 МБ, как в OSCR)
  --block369 N         rom-write, GBA 369-in-1: блок 4 МБ (от 0 до 63), с которого начинается запись ("Write Offset" в OSCR); 0 = с начала
  --flash-type ИМЯ     rom-write, микросхемы SNES P0/P1 (snes-lorom-p0, snes-hirom-p0, snes-exlorom-p1, snes-exhirom-p1): тип 8-битной flash (29f032, 29f1610, lh28f0xx, 29f1601, 29lv640, 29f800, 29gl, e28fxxxj3a)
  --flash-mb N         rom-write, SNES P0/P1: размер микросхемы в МБ (от 1 до 8)
  --sector-kb N        rom-write, SNES P0/P1, типы 29gl, lh28f0xx, e28fxxxj3a: размер сектора в КБ (степень двойки)
  --buffer N           rom-write, SNES P0/P1, те же типы: буфер записи в байтах (степень двойки, от 2 до 128)
  --begin-timeout S    rom-write: сколько секунд ждать стирания перед данными (по умолчанию 90)
  --ignore-cart-limit  rom-write -s md: записать, даже если ROM больше 2 МиБ на картридже S29GL (платы KY / FlashKit имеют только 2 МиБ флеша; по умолчанию: отказ, ничего не стёрто)
  --raw                dump -s nes|famicom: записать PRG и CHR отдельными файлами (.prg и .chr), без заголовка iNES (raw-чтение OSCR)
  --twice              dump: прочитать ROM дважды и сравнить; если различаются, записать оба чтения (ИМЯ.leitura1 и ИМЯ.leitura2, как в CLI на Python) и выйти с ошибкой (kind mismatch)
  --flash-id           detect -s md: также определить flash-микросхему картриджа (зонд записывает в картридж команды ID; масочное ROM их игнорирует)
  --color РЕЖИМ        auto (по умолчанию: только в терминале, учитывает NO_COLOR), always или never: цвета и ASCII-графика; в --json их нет никогда
  --sound              звуковой сигнал по окончании: один при успехе и три при ошибке (долгие операции)
  --hex ФАЙЛ           firmware-flash: .hex прошивки (по умолчанию: переменная OSCR_FIRMWARE_HEX или firmware/oscr/.pio/build/<env>/firmware.hex)
  --env ИМЯ            firmware-flash: окружение PlatformIO, откуда берётся .hex (по умолчанию SerialASCII; SerialASCII_Volt)
  --avrdude ПУТЬ       firmware-flash: какой avrdude использовать (по умолчанию: переменная AVRDUDE, PATH или из PlatformIO)
  --wait S             firmware-flash: сколько секунд ждать ответа устройства на INFO после записи (по умолчанию 12)
  --dry-run            firmware-flash: только показать команду avrdude и текущую версию прошивки
  --no-verify          firmware-flash, rom-write, save-write: не читать ROM/сохранение обратно для проверки после записи (по умолчанию: проверять)
  --yes                не спрашивать перед записью (обязательно вне терминала)
  --no-backup          save-write: не читать текущее сохранение заранее
  --backup-dir DIR     save-write: папка резервной копии (по умолчанию ~/oscr_backups)

коды возврата: 0 ок | 1 ошибка | 2 нет картриджа | 3 нет порта/устройства | 4 отказано (нужен --yes) | 64 использование | 130 Ctrl+C
Полный контракт: docs/referencia/cli.md"""

_ZH = """用法：dumper [选项] <命令> [选项]

命令：
  ports        列出串口
  systems      列出系统、扩展名和各系统的选项（不打开串口）
  errors       列出设备错误码和 CLI 退出码（不打开串口）
  info         固件版本和支持的系统
  firmware-flash  用 avrdude 通过 USB 把分支固件写入 Arduino Mega（替换板子上的程序）[--hex 文件 --env 名称 --avrdude 路径 --yes --dry-run]
  detect       检测卡带                        (-s 系统)
  identify     按 CRC32 在数据库（--db）中识别已保存的 ROM，不打开串口
  search       按名称在数据库（--db）中搜索游戏，不打开串口
  dump         读取 ROM                        (-s 系统 [-o 文件])
  save-read    读取存档                        (-s 系统 [-o 文件])
  save-write   写入存档                        (-s 系统 -i 文件 --yes)
  flash-id     通用 flash 编程器：读取芯片 ID（--bus 8|plcc32|16|eprom --flash-kb N [--flash-type T]）
  flash-read   通用 flash 编程器：把整片芯片读入文件（-o 文件）
  flash-blank  通用 flash 编程器：检查芯片是否为空白（读取芯片并在电脑上检查）
  flash-erase  通用 flash 编程器：擦除整片芯片（8 位 flash 必须给出 --flash-type）--yes
  flash-write  通用 flash 编程器：擦除并把文件写入芯片（-i 文件），然后读回校验
  rom-write    把 ROM 写入 flash 卡带，会擦除芯片（-i 文件 [--chip nesmaker|a29040b] --yes）

选项（可放在命令之前或之后）：
  -p, --port 端口      串口（默认：第一个 ttyUSB/ttyACM/COM）
  -b, --baud N         波特率（默认：1000000，然后 115200）
  --simulate           内存模拟器（无需硬件；只有系统 'mock' 有卡带）
  --json               标准输出一行 JSON，始终带 "ok"；错误：{"ok":false,"error":{kind,message,hint}}
  --progress 模式      auto | none | jsonl（stderr 上每 1% 输出一行 JSON）
  --lang TAG           消息语言：en（默认）、pt-BR、ru、zh-CN（否则取 OSCR_LANG，再取系统区域设置）
  -s, --system 名称    snes nes famicom md gba gb mock（默认：mock）
  -o, --output 文件    输出文件（缺少时自动补上正确扩展名；会覆盖）
  -i, --input 文件     要写入的存档文件
  --block N            块大小（默认 512）
  --mapper N --prg KB --chr KB --ram KB     NES/Famicom/GBA 选项（见 'systems'）
  --db 路径            额外的游戏数据库：.dat（No-Intro）文件或文件夹，或 nes20db.xml；可重复；同时读取环境变量 OSCR_DB
                       （项目自带的、继承自 OSCR 的数据库总是最先加载）
  --no-builtin-db      不加载项目自带的游戏数据库
  --game 名称          dump，NES/Famicom：NES 2.0 XML 数据库中的游戏名；填入留为 0 的 --mapper/--prg/--chr
  --limit N            search：最多结果数（默认 20）
  --chip 名称          rom-write：nesmaker（SST 39SF040，mapper 30）或 a29040b（mapper 0），默认按文件的 iNES mapper；
                       SNES：snes-lorom 或 snes-hirom（必填，CFI flash 的接线）
                       Mega Drive：md-flash（默认；固件按 ID 识别芯片：MX29F1610、S29GL064N、32 和 64 Mbit 的 M29W/MX29LV、MX29L3211、PA28F400、SST39VF）
  --bus 名称           flash-*：8（flash 适配器上的 8 位 flash）、plcc32（SNES 适配器上的 8 位 PLCC32）、16（16 位 flash）或 eprom（27C322）
  --flash-kb N         flash-*：芯片大小，单位 KB（1 到 8192；EPROM 固定为 4096）
  --capacity KB        rom-write，SNES CFI，布局 1x：flash 大小，2048 或 4096（默认：能容纳 ROM 的最小值）
  --layout 名称        rom-write，SNES CFI：卡带上的芯片：1x（一片 2 或 4 MB，默认）、2x2mb、2x4mb、4x2mb、1x8mb（后三种：6 到 8 MB 的 ROM，与 OSCR 相同）
  --block369 N         rom-write，GBA 369-in-1：开始写入的 4 MB 块（0 到 63）（OSCR 的 "Write Offset"）；0 = 从头开始
  --flash-type 名称    rom-write，SNES P0/P1 芯片（snes-lorom-p0、snes-hirom-p0、snes-exlorom-p1、snes-exhirom-p1）：8 位 flash 类型（29f032、29f1610、lh28f0xx、29f1601、29lv640、29f800、29gl、e28fxxxj3a）
  --flash-mb N         rom-write，SNES P0/P1：芯片大小，单位 MB（1 到 8）
  --sector-kb N        rom-write，SNES P0/P1，类型 29gl、lh28f0xx、e28fxxxj3a：扇区大小，单位 KB（2 的幂）
  --buffer N           rom-write，SNES P0/P1，同样的类型：写入缓冲区字节数（2 的幂，2 到 128）
  --begin-timeout S    rom-write：写入数据前等待擦除的秒数（默认 90）
  --ignore-cart-limit  rom-write -s md：即使 ROM 超过 S29GL 卡带的 2 MiB 也写入（KY / FlashKit 板只有 2 MiB 闪存；默认：拒绝，不擦除）
  --raw                dump -s nes|famicom：把 PRG 和 CHR 写成两个文件（.prg 和 .chr），不带 iNES 头（OSCR 的 raw 读取）
  --twice              dump：读取 ROM 两次并比较；若不同，则写出两次读取的结果（名称.leitura1 和 名称.leitura2，与 Python CLI 相同）并以错误退出（kind mismatch）
  --flash-id           detect -s md：同时识别卡带的 flash 芯片（探测会向卡带写入 ID 命令；掩膜 ROM 会忽略）
  --color 模式         auto（默认：仅在终端中，遵循 NO_COLOR）、always 或 never：颜色和 ASCII 图案；--json 永远没有
  --sound              完成时发出提示音：成功响一声，失败响三声（耗时较长的操作）
  --hex 文件           firmware-flash：固件 .hex（默认：环境变量 OSCR_FIRMWARE_HEX 或 firmware/oscr/.pio/build/<env>/firmware.hex）
  --env 名称           firmware-flash：.hex 所来自的 PlatformIO 环境（默认 SerialASCII；SerialASCII_Volt）
  --avrdude 路径       firmware-flash：使用的 avrdude（默认：环境变量 AVRDUDE、PATH 或 PlatformIO 自带的）
  --wait S             firmware-flash：写入后等待设备回应 INFO 的秒数（默认 12）
  --dry-run            firmware-flash：只显示 avrdude 命令和当前固件版本
  --no-verify          firmware-flash、rom-write、save-write：写入后不回读 ROM/存档校验（默认：校验）
  --yes                写入前不询问（在终端之外必须给出）
  --no-backup          save-write：事先不读取当前存档
  --backup-dir DIR     save-write：备份文件夹（默认 ~/oscr_backups）

退出码：0 成功 | 1 错误 | 2 无卡带 | 3 无串口/设备 | 4 被拒绝（需要 --yes）| 64 用法 | 130 Ctrl+C
完整约定：docs/referencia/cli.md"""

USAGE = {"pt-BR": _PT, "en": _EN, "ru": _RU, "zh-CN": _ZH}
