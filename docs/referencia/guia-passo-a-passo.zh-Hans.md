# 分步指南：从组装好的板子到第一次转储

参考 `md_rewriter` 的指南（`md_rewriter/docs/guide/`）。本指南只是按正确顺序把其他文档里已有的内容串起来，细节请看那些文档。其他语言版本：[pt-BR](guia-passo-a-passo.md)、[en](guia-passo-a-passo.en.md)、[ru](guia-passo-a-passo.ru.md)。译文尚未经母语者审校。

## 0. 选择板子和要买的东西

1. 在 [`boards/README.md`](../../boards/README.md) 中按系统选板子（每块板的当前版本见 `boards/versoes.json`）。**v1.0** 是带保险丝的最简版本；**v1.1**（有的话）增加 3.3 V/5 V 电压选择器。
2. 元件：`boards/<板子>/docs/bom.md` 和 `componentes-opcionais.md`。没有符号的元件（排针、垫柱、USB 线）列在 BOM 末尾。
3. 下单：`boards/<板子>/fab/PEDIDO.md`（版本 zip、预览核对、SHA-256）。**付款前请在 KiCad 中检查布线**（由自动布线器完成）。

## 1. 焊接与组装

按 `boards/<板子>/docs/montagem.md` 操作：先焊低的元件（电阻、电容、PIC 插座、LED、电解电容、Si5351 排母、卡槽，最后在 shield 插在 Mega 上的状态下焊接连接 Mega 的排针）。然后目视检查，**通电前**检查 5 V–GND 导通（不允许短路），之后才在**不插卡带、不装 PIC、不装 Si5351**的情况下通电，测量每个卡槽 VCC 上的 5 V。

## 2. 电脑与固件

1. Linux：把用户加入 `dialout` 组（`sudo usermod -aG dialout $USER`，然后注销再登录）。macOS 和 Windows 通常自带 Mega 驱动。
2. 通过 USB-C 给 Mega 刷入 fork 固件：`python3 host/dumper.py firmware-flash`（或 GUI 的“Arduino 固件”卡片；需要 `avrdude`）。使用 PlatformIO：`cd firmware/oscr && pio run -e SerialASCII -t upload`（带电压选择器的板子：`-e SerialASCII_Volt`）。
3. `python3 host/dumper.py info` 必须显示协议、固件版本和系统列表。

## 3. 按顺序做第一批测试

详细内容见 [`uso.md`](uso.md) 第 7 节（葡萄牙语）。

1. **不插卡带：**`python3 host/dumper.py selftest`（约 45 秒）。它会报告引脚间短路、D7 上拉和 Si5351 的问题。若有发现，请**停下**并检查焊接。
2. **MOCK 模式（测试固件）：**`dump -s mock` 得到 CRC32 `D1DF4327`。
3. **安装模块：**Si5351 和烧录了 `snescic-lock-resync.hex` 的 PIC12F629（只有带 SA-1 的 SNES 需要 PIC）。
4. **Mega Drive，只读：**`python3 tools/boards/megadrive/hwtest_md.py nocart`，然后在卡槽里插入卡带运行 `... cart`。这套测试绝不会向卡带写入任何内容。
5. **第一次真实转储**：用简单的卡带（SNES LoROM 或 NES mapper 0）：`detect -s snes` 和 `dump -s snes -o youxi`；把 CRC32 与 No-Intro 对比。

## 4. 写入闪存复刻卡带

只在读取并核对之后进行。风险顺序：先备份存档，再 EEPROM，GBA 闪存，最后是 `rom-write`（会擦除芯片）。**切勿向原版掩膜 ROM 卡带写入。**先在没有价值的复刻卡带上试。

- Mega Drive：`rom-write -s md -i youxi.md --yes`。**带 S29GL 的 KY / FlashKit 卡带只有 2 MiB 闪存**：超过时 CLI 会在擦除前拒绝（如果你的板子接了全部 8 MiB，可用 `--ignore-cart-limit` 强制）。固件在擦除后检查 `FFFFh`，程序会把 ROM 读回来比对。
- 更换卡带时**请拔掉 USB**（卡槽的 5 V 不由软件切断）。

## 5. 常见问题

见 [`uso.md`](uso.md) 第 4 节的表格。最常见的三个：串口不出现（`dialout` 组）、卡带未检测到（清洁触点，对照丝印检查标签方向）、CRC 不一致（用 `dump --twice` 读两次）。
