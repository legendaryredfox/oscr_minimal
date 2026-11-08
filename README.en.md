# oscr_minimal — SNES / NES / Famicom / Mega Drive / GBA cartridge dumper

An **Arduino Mega 2560 (R3) shield** that reads ROMs and saves from game cartridges over USB, straight to the PC. No LCD, no SD card, one cartridge at a time. Derived from the [Open Source Cartridge Reader](https://github.com/sanni/cartreader) (OSCR) by sanni and community; hardware CC BY 4.0, software GPL v3.

> **Status: experimental.** Eight boards (KiCad projects and gerbers in `boards/`), a firmware fork of the OSCR with a serial protocol, a Python CLI, and a Kotlin CLI/GUI (pt-BR, en, ru, zh). **No board has been assembled and nothing has been tested with a real cartridge yet.** Only the PC-side tests and the hardware checks (ERC, DRC, netlist against the OSCR pin map) have run. CI has never run. Most documents are in Brazilian Portuguese; `README.md` is the main one.

## Boards

| Folder | Slots |
|---|---|
| `boards/16_and_8_bits/` | SNES, NES, Famicom, Mega Drive, GBA |
| `boards/16_bits/` | SNES, Mega Drive |
| `boards/megadrive/`, `snes/`, `nes/`, `famicom/`, `famicom_nes/`, `gb_gba/` | one system each (`famicom_nes`: both Famicom and NES; `gb_gba`: GBA, and GB/GBC through an adapter) |

All slots are wired to the same Arduino pins as the OSCR HW5, so the OSCR cartridge code runs unchanged. 5 V on every slot except GBA (3.3 V). Fully through-hole except the GBA slot. Only the `16_bits` v1.0 has been ordered, by the maintainer.

## SNES CIC

The SNES boards use a **PIC12F629** (8-pin DIP, socketed). We are studying alternatives to the 8-pin CIC, e.g. an RP2040-Zero running the same program in an interpreter (`docs/planos/placa-v1.3-rp2040.md`); none of it is validated in hardware.

## Build and test

```
cd host && python3 -m pytest -q                       # Python host
make -C firmware/oscr/pc-tests test                   # firmware logic on the PC
cd firmware/oscr && pio run -e SerialASCII            # firmware for the Mega 2560
cd gui && ./gradlew :shared:jvmTest :desktopApp:compileKotlin :cliApp:compileKotlin
python3 tools/check_netlist.py --board <board>        # schematic vs boards/<board>/docs/pinmap.md
```

## Safety and legal

Use at your own risk. One cartridge at a time, USB unplugged when swapping. Writing a ROM erases the chip. The tool is meant for backing up cartridges you own; the repository ships no ROMs, BIOS or keys (`database/oscr/` holds only game names and CRC32s from the OSCR). Console and company names are trademarks of their owners, used only to state compatibility.

## Contributing

Hardware test reports are the most useful contribution: see `CONTRIBUTING.md` and the "Teste em hardware" issue template.

## License

Hardware: CC BY 4.0. Software: GPL v3 or later. See `LICENSE.md`.
