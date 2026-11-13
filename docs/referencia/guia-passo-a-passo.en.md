# Step-by-step guide: from the assembled board to the first dump

Modelled on the `md_rewriter` guide (`md_rewriter/docs/guide/`). This guide only strings together, in the right order, what the other documents already say; details live there. Portuguese version: [`guia-passo-a-passo.md`](guia-passo-a-passo.md). Also in [Russian](guia-passo-a-passo.ru.md) and [Chinese](guia-passo-a-passo.zh-Hans.md) (not reviewed by native speakers).

## 0. Pick the board and what to buy

1. Pick the board in [`boards/README.md`](../../boards/README.md) (by systems; the current version of each is in `boards/versoes.json`). **v1.0** is the minimal one with a fuse; **v1.1** (where it exists) adds the 3.3 V/5 V voltage selector.
2. Parts: `boards/<board>/docs/bom.md` and `componentes-opcionais.md`. Parts without a symbol (pins, spacers, USB cable) are at the end of the BOM.
3. Ordering the board: `boards/<board>/fab/PEDIDO.md` (version zip, preview check, SHA-256). **Review the layout in KiCad before paying** (it was routed by an autorouter).

## 1. Soldering and assembly

Follow `boards/<board>/docs/montagem.md`: lowest part first (resistors, capacitors, PIC socket, LED, electrolytic, Si5351 headers, slots, pins to the Mega last with the shield plugged in). Then inspect visually, check 5 V–GND continuity **before powering** (no short allowed), and only then power it **with no cartridge, no PIC and no Si5351**, measuring 5 V at each slot's VCC.

## 2. Computer and firmware

1. Linux: add your user to the `dialout` group (`sudo usermod -aG dialout $USER`, log out and in). macOS and Windows usually ship the Mega driver.
2. Flash the fork firmware to the Mega over USB-C: `python3 host/dumper.py firmware-flash` (or the GUI's "Arduino firmware" card; needs `avrdude`). With PlatformIO instead: `cd firmware/oscr && pio run -e SerialASCII -t upload` (boards with the voltage selector: `-e SerialASCII_Volt`).
3. `python3 host/dumper.py info` must show the protocol, the firmware version and the systems.

## 3. First tests, in order

Full detail in [`uso.md`](uso.md), section 7 (Portuguese).

1. **No cartridge:** `python3 host/dumper.py selftest` (about 45 s). It reports shorts between pins, the D7 pull-up and the Si5351. If it finds anything, **stop** and check the soldering.
2. **MOCK mode (test firmware):** `dump -s mock` gives CRC32 `D1DF4327`.
3. **Install the modules:** Si5351 and the PIC12F629 programmed with `snescic-lock-resync.hex` (only SNES with SA-1 needs the PIC).
4. **Mega Drive, read only:** `python3 tools/boards/megadrive/hwtest_md.py nocart`, then `... cart` with a cartridge in the slot. That suite never writes to the cartridge.
5. **First real dump** with a simple cartridge (SNES LoROM or NES mapper 0): `detect -s snes` and `dump -s snes -o game`; compare the CRC32 with No-Intro.

## 4. Writing a flash repro cartridge

Only after reading and checking. Risk order: save with backup, EEPROM, GBA flash and last `rom-write` (erases the chip). **Never write to an original mask-ROM cartridge.** Try a worthless repro first.

- Mega Drive: `rom-write -s md -i game.md --yes`. **KY / FlashKit cartridges with an S29GL have only 2 MiB of flash**: above that the CLI refuses before erasing (`--ignore-cart-limit` forces it, if your board wires all 8 MiB). The firmware checks for `FFFFh` after the erase and the program reads the ROM back and compares.
- Swap cartridges **with USB unplugged** (the slots' 5 V is not switched by software).

## 5. Common problems

Table in [`uso.md`](uso.md), section 4. The three most frequent: serial port missing (`dialout` group), cartridge not detected (clean the contacts, check the label side on the silkscreen) and CRC mismatch (read twice with `dump --twice`).
