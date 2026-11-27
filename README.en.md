# oscr_minimal — SNES / NES / Famicom / Mega Drive / GBA cartridge dumper

An **Arduino Mega 2560 (R3) shield** that reads ROMs and saves from game cartridges over USB, straight to the PC. No LCD, no SD card, one cartridge at a time. Derived from the [Open Source Cartridge Reader](https://github.com/sanni/cartreader) (OSCR) by sanni and community; hardware CC BY 4.0, software GPL v3.

> **Status: experimental.** Twelve boards (KiCad projects and gerbers in `boards/`), a firmware fork of the OSCR with a serial protocol, a Python CLI, and a Kotlin CLI/GUI (pt-BR, en, ru, zh). **No board has been assembled and nothing has been tested with a real cartridge yet.** Only the PC-side tests and the hardware checks (ERC, DRC, netlist against the OSCR pin map) have run. CI has never run. Most documents are in Brazilian Portuguese; `README.md` is the main one.

## Differences from the original OSCR

The firmware is the OSCR's and the boards keep its pinout; what changes is **where the interface lives** (on the computer, not on the device) and **the size of the hardware**.

- **Computer required.** No LCD, buttons, SD card or RTC. Control and files go over USB through a binary serial protocol (CRC32 frames, per-block ACK, 1,000,000 baud with fallback to 500,000 and 115,200). The firmware never stores a file; ROMs and saves stream straight to the PC.
- **Hardware.** A 100 % through-hole shield on a plain **Arduino Mega 2560 R3**, hand-solderable, instead of the SMD HW5 board with its embedded Mega Pro module; several variants by system combination (`boards/README.md`).
- **Same pinout as HW5.** Every slot signal goes to the same Mega pin, which is why the OSCR read cores run unchanged (`boards/<board>/docs/pinmap.md`).
- **Voltage.** 5 V fixed on the SNES, NES, Famicom, Mega Drive and Master System slots; 3.3 V on the GBA and N64 slots (own regulator). Some recent board versions have an optional 3.3 V / 5 V selector with a jumper lock. 5 V is never switched off by software. The original has a 3V/5V switch and VSELECT.
- **Firmware.** The new OSCR firmware copied to `firmware/oscr/`, cores selected in `user.ini` (SNES with its accessories, NES/Famicom, Mega Drive, Master System, N64, GB/GBC/GBA, the flash programmer, self-test), plus 19 other systems through an adapter on the SNES slot (Atari 2600/5200/7800/8-bit/Lynx/Jaguar, ColecoVision, Neo Geo Pocket, Vectrex and others; adapters not designed yet, `docs/planos/adaptadores.md`). The remaining upstream consoles (for example Commodore 64 and PC Engine) are not enabled. Own code lives in `firmware/oscr/src/dumper/` (protocol, `StreamFile` in place of the SD, command loop instead of menus, board profile, voltage and clock commands); patches to upstream are few and marked. Baud is 1,000,000 against upstream's 250,000.
- **PC side.** Game identification (No-Intro, NES 2.0) happens on the PC instead of the CRDB on the SD; save backup before writing and read-back after; a Python CLI, a Kotlin CLI (same JSON contract for scripts) and a Kotlin GUI for Linux, macOS and Windows (pt-BR, en, ru, zh); firmware flashing from the program.
- **Not a replacement.** The original has years of field use. This fork has almost no hardware validation: its first run (2026-11-21, a bare Mega with no shield or cartridge) found and fixed several problems, from a wrong baud rate to a firmware flash that hung, and **no real cartridge has been read yet**. For a standalone reader that needs no computer, use the original OSCR.

Details: [`docs/referencia/fork-oscr.md`](docs/referencia/fork-oscr.md) and [`docs/referencia/funcoes-oscr.md`](docs/referencia/funcoes-oscr.md) (Portuguese).

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

## Adapters and reference repositories

The cartridge-reading code comes from the OSCR; what changes per system is the adapter. Sources consulted and adapters the firmware recognizes (D136, D137):

| Reference | What for |
|---|---|
| <https://github.com/sanni/cartreader> (`hardware/` folder: `mastersystem_adapter`, `six_slot_adapter`, `*_adapter`) | KiCad of the OSCR adapters; the `megadrive_sms` Master System slot and the slot footprints come from here (CC BY 4.0). Archived since 2026-06 |
| <https://github.com/oscartreader/oscr-firmware> | current OSCR firmware (GPL v3), base of the fork in `firmware/oscr/` |
| <https://github.com/oscartreader/oscr-databases> | game databases and the flash chip table (`database/oscr/`, D127 and D135; no declared license) |
| <https://github.com/oscartreader/oscr-hardware> | hardware repository of the new upstream (empty on 2026-11-08) |
| <https://github.com/sanni/cartreader/discussions/874> | Game Gear adapter discussion (slot with the RetroSix connector) |
| <https://www.raphnet.net/electronique/sms_cartridge_programmer/index_en.php> | **Raphnet** Master System / SG-1000 adapter (`SMSRaphnet` and `SG1000Raphnet` modes of `SMS.cpp`) |
| <https://forum.retrode.com> | **Retrode** adapters (`SMSRetrode`, `GGRetrode` of `SMS.cpp`) |
| <https://www.retrosix.wiki> | Game Gear and other Sega cartridge pinouts |
| <https://www.smspower.org/maxim/Documents/Pinouts> | cartridge connector pinout of the Master System, Mark III and SG-1000 |

**Game Gear and SG-1000** have no slot of their own on this project's boards: they use an adapter in the Mega Drive slot (Retron 3in1, Retrode, Raphnet). The adapters I found are commercial; **I found no open (KiCad) files** for them. If an open-source adapter shows up, add its link here.

## Safety and legal

Use at your own risk. One cartridge at a time, USB unplugged when swapping. Writing a ROM erases the chip. The tool is meant for backing up cartridges you own; the repository ships no ROMs, BIOS or keys (`database/oscr/` holds only game names and CRC32s from the OSCR). Console and company names are trademarks of their owners, used only to state compatibility.

## Contributing

Hardware test reports are the most useful contribution: see `CONTRIBUTING.md` and the "Teste em hardware" issue template.

## License

Hardware: CC BY 4.0. Software: GPL v3 or later. See `LICENSE.md`.
