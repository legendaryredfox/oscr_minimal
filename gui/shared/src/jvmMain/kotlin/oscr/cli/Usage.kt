// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Texto de ajuda e rótulos fixos. */
internal val STATUS = mapOf(0 to "cartridge detected", 1 to "no cartridge", 2 to "not supported", 3 to "hardware error",
    4 to "invalid header (data present but the header checksum fails: clean the contacts and reseat)")

internal val HELP = """
usage: dumper [options] <command> [options]

commands:
  ports        list serial ports
  systems      list systems, extensions and per-system options (does not open the port)
  errors       list device error codes and CLI exit codes (does not open the port)
  info         firmware version and supported systems
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
  --lang TAG           language of device error texts: en (default), pt-BR, ru, zh-CN
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
  --raw                dump -s nes|famicom: write PRG and CHR as separate files (.prg and .chr), without the iNES header (the OSCR raw read)
  --twice              dump: read the ROM twice and compare; if they differ, write both reads (NAME.leitura1 and NAME.leitura2, as in the Python CLI) and exit with an error (kind mismatch)
  --flash-id           detect -s md: also identify the cartridge's flash chip (the probe writes ID commands to the cartridge; mask ROM ignores them)
  --color MODE         auto (default: only in a terminal, respects NO_COLOR), always or never: colours and ASCII art; --json never has them
  --power MODE         power-switch boards: auto (default: turn the slots' 5V on before the command and keep it on) or keep (do not touch the 5V)
  --no-verify          rom-write, save-write: do not read the ROM/save back to verify after writing (default: verify)
  --yes                do not ask before writing (required outside a terminal)
  --no-backup          save-write: do not read the current save first
  --backup-dir DIR     save-write: backup folder (default ~/oscr_backups)

exit codes: 0 ok | 1 error | 2 no cartridge | 3 no port/device | 4 refused (needs --yes) | 64 usage | 130 Ctrl+C
Full contract: docs/referencia/cli.md
""".trim()
