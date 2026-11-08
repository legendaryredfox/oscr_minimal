# SPDX-License-Identifier: GPL-3.0-or-later
"""Mensagens da CLI em vários idiomas (pt-BR, en, ru, zh-CN), como a GUI (`I18n.kt`). Inglês é o reserva.

Idioma: `--lang` (antes ou depois do comando), senão a variável OSCR_LANG, senão a locale (LC_ALL, LC_MESSAGES, LANG); sem nada reconhecível, inglês.
O que **não** muda de idioma: as chaves do `--json` (`ok`, `error.kind`, nomes dos campos), os códigos de saída e os valores de `kind`.
Só os textos para pessoas (`message`, `hint` e as linhas de texto) mudam. Cobertura atual: erros do dispositivo e da CLI, recusas de gravação,
`power`, `firmware-flash` e `errors`; o resto dos comandos (saídas de `detect`, `dump` etc. e o `--help`) ainda é em português (D133).
Para acrescentar uma mensagem: uma chave em CATALOG com os quatro idiomas e `tr("chave", campo=valor)`; `tests/test_messages.py` confere que nenhuma tem idioma faltando."""
from __future__ import annotations

import os

TAGS = {"pt": "pt-BR", "pt-br": "pt-BR", "en": "en", "ru": "ru", "zh": "zh-CN", "zh-cn": "zh-CN"}
LANGS = ("pt-BR", "en", "ru", "zh-CN")
_lang = "en"


def normalize(tag: str | None) -> str | None:
    """'pt_BR.UTF-8' -> 'pt-BR'; 'en_US' -> 'en'; desconhecido -> None."""
    if not tag:
        return None
    t = tag.split(".")[0].split("@")[0].replace("_", "-").lower()
    return TAGS.get(t) or TAGS.get(t.split("-")[0])


def detect(argv: list[str] | None = None, env=None) -> str:
    env = os.environ if env is None else env
    argv = argv or []
    for i, a in enumerate(argv):
        if a == "--lang" and i + 1 < len(argv):
            return normalize(argv[i + 1]) or "en"
        if a.startswith("--lang="):
            return normalize(a.split("=", 1)[1]) or "en"
    for var in ("OSCR_LANG", "LC_ALL", "LC_MESSAGES", "LANG"):
        n = normalize(env.get(var))
        if n:
            return n
    return "en"


def set_lang(tag: str) -> None:
    global _lang
    _lang = normalize(tag) or "en"


def lang() -> str:
    return _lang


def tr(key: str, **kw) -> str:
    row = CATALOG[key]
    text = row.get(_lang) or row["en"]
    return text.format(**kw) if kw else text


def tr_in(tag: str, key: str, **kw) -> str:
    old = _lang
    try:
        set_lang(tag)
        return tr(key, **kw)
    finally:
        set_lang(old)


def _r(pt: str, en: str, ru: str, zh: str) -> dict:
    return {"pt-BR": pt, "en": en, "ru": ru, "zh-CN": zh}


CATALOG: dict[str, dict[str, str]] = {
    # ---- prefixos da linha de erro
    "err.prefix": _r("erro", "error", "ошибка", "错误"),
    "err.hint_prefix": _r("Dica", "Hint", "Подсказка", "提示"),
    # ---- erros do dispositivo (códigos 1 a 12; texto e dica)
    "dev.unknown": _r("desconhecido", "unknown", "неизвестно", "未知"),
    "dev.1.msg": _r("comando desconhecido ou não suportado", "unknown or unsupported command", "неизвестная или неподдерживаемая команда", "未知或不支持的命令"),
    "dev.1.hint": _r("atualize o firmware e o programa para a mesma versão", "update the firmware and the program to the same version", "обновите прошивку и программу до одной версии", "请将固件和程序更新到同一版本"),
    "dev.2.msg": _r("sistema desconhecido ou não suportado", "unknown or unsupported system", "неизвестная или неподдерживаемая система", "未知或不支持的主机"),
    "dev.2.hint": _r("o chip, o mapper ou o sistema deste cartucho ainda não é lido (veja docs/referencia/uso.md)", "the chip, mapper or system of this cartridge is not read yet (see docs/referencia/uso.md)", "чип, маппер или система этого картриджа пока не читаются (см. docs/referencia/uso.md)", "此卡带的芯片、mapper 或主机尚不支持读取（见 docs/referencia/uso.md）"),
    "dev.3.msg": _r("nenhum cartucho detectado", "no cartridge detected", "картридж не обнаружен", "未检测到卡带"),
    "dev.3.hint": _r("encaixe o cartucho até o fim, limpe os contatos e confira o sistema escolhido", "seat the cartridge fully, clean the contacts and check the chosen system", "вставьте картридж до упора, очистите контакты и проверьте выбранную систему", "请把卡带插到底，清洁触点并确认所选主机"),
    "dev.4.msg": _r("argumento inválido", "invalid argument", "неверный аргумент", "参数无效"),
    "dev.4.hint": _r("confira mapper, PRG, CHR, RAM e o tamanho do arquivo (docs/referencia/protocolo.md)", "check mapper, PRG, CHR, RAM and the file size (docs/referencia/protocolo.md)", "проверьте маппер, PRG, CHR, RAM и размер файла (docs/referencia/protocolo.md)", "请检查 mapper、PRG、CHR、RAM 和文件大小（docs/referencia/protocolo.md）"),
    "dev.5.msg": _r("reenvios excedidos", "retries exceeded", "превышено число повторов", "重试次数过多"),
    "dev.5.hint": _r("troque o cabo, evite hubs USB ou use --baud 115200", "change the cable, avoid USB hubs or use --baud 115200", "смените кабель, избегайте USB-хабов или используйте --baud 115200", "请更换线缆，避免 USB 集线器，或使用 --baud 115200"),
    "dev.6.msg": _r("CRC32 do arquivo não confere", "file CRC32 does not match", "CRC32 файла не совпадает", "文件 CRC32 不符"),
    "dev.6.hint": _r("refaça a leitura; se repetir, limpe os contatos e troque o cabo", "read again; if it repeats, clean the contacts and change the cable", "повторите чтение; если повторится — очистите контакты и смените кабель", "请重新读取；若重复出现，请清洁触点并更换线缆"),
    "dev.7.msg": _r("erro de leitura/gravação no cartucho", "cartridge read/write error", "ошибка чтения/записи картриджа", "卡带读写错误"),
    "dev.7.hint": _r("confira a bateria e os contatos; numa gravação o save pode ter ficado incompleto: tente de novo e use o backup", "check the battery and the contacts; after a write the save may be incomplete: try again and use the backup", "проверьте батарею и контакты; после записи сохранение может быть неполным: повторите и используйте резервную копию", "请检查电池和触点；写入后存档可能不完整：请重试并使用备份"),
    "dev.8.msg": _r("dispositivo ocupado", "device busy", "устройство занято", "设备忙"),
    "dev.8.hint": _r("espere o fim da operação anterior", "wait for the previous operation to finish", "дождитесь окончания предыдущей операции", "请等待上一个操作结束"),
    "dev.9.msg": _r("abortado", "aborted", "прервано", "已中止"),
    "dev.9.hint": _r("operação cancelada", "operation cancelled", "операция отменена", "操作已取消"),
    "dev.10.msg": _r("cartucho não tem save", "cartridge has no save", "у картриджа нет сохранения", "卡带没有存档"),
    "dev.10.hint": _r("este cartucho não tem save, ou o mapper/tipo informado não tem save", "this cartridge has no save, or the given mapper/type has none", "у этого картриджа нет сохранения, или у указанного маппера/типа его нет", "此卡带没有存档，或所给 mapper/类型没有存档"),
    "dev.11.msg": _r("chip de flash não reconhecido", "flash chip not recognized", "флеш-чип не распознан", "未识别闪存芯片"),
    "dev.11.hint": _r("o cartucho não é uma flash do tipo escolhido (ou está sujo/mal encaixado): confira o chip, os contatos e o encaixe; nada foi gravado", "the cartridge is not a flash of the chosen type (or is dirty/badly seated): check the chip, the contacts and the fit; nothing was written", "картридж не является флеш-памятью выбранного типа (или грязный/плохо вставлен): проверьте чип, контакты и посадку; ничего не записано", "卡带不是所选类型的闪存（或有污垢/未插好）：请检查芯片、触点和插入情况；未写入任何内容"),
    "dev.12.msg": _r("cartucho desligado (5V dos slots cortado)", "cartridge powered off (slots' 5V cut)", "картридж обесточен (5V слотов отключено)", "卡带已断电（插槽 5V 已切断）"),
    "dev.12.hint": _r("ligue o 5V dos slots: `dumper power on` (a CLI e a GUI ligam sozinhas, a menos que use --power keep)", "turn the slots' 5V on: `dumper power on` (the CLI and the GUI do it by themselves unless you use --power keep)", "включите 5V слотов: `dumper power on` (CLI и GUI делают это сами, если не указан --power keep)", "请打开插槽 5V：`dumper power on`（CLI 和 GUI 会自动打开，除非使用 --power keep）"),
    # ---- erros da CLI
    "err.timeout": _r("o dispositivo parou de responder; confira o cabo e repita", "the device stopped responding; check the cable and retry", "устройство перестало отвечать; проверьте кабель и повторите", "设备停止响应；请检查数据线后重试"),
    "err.interrupted": _r("interrompido", "interrupted", "прервано", "已中断"),
    "err.no_port": _r("nenhuma porta serial encontrada", "no serial port found", "последовательный порт не найден", "未找到串口"),
    "err.no_port.hint": _r("conecte o dispositivo, use --port, ou --simulate sem hardware (no Linux: grupo dialout)", "connect the device, use --port, or --simulate without hardware (Linux: dialout group)", "подключите устройство, укажите --port или используйте --simulate без оборудования (Linux: группа dialout)", "请连接设备，使用 --port，或在没有硬件时使用 --simulate（Linux：dialout 组）"),
    "err.open_port": _r("não foi possível abrir {port}: {error}", "could not open {port}: {error}", "не удалось открыть {port}: {error}", "无法打开 {port}：{error}"),
    "err.open_port.hint": _r("feche outros programas que usam a porta; no Linux o usuário precisa estar no grupo dialout", "close other programs using the port; on Linux the user must be in the dialout group", "закройте другие программы, использующие порт; в Linux пользователь должен быть в группе dialout", "请关闭其他占用该端口的程序；在 Linux 中用户需要在 dialout 组"),
    "err.no_response": _r("sem resposta do dispositivo em {port} ({bauds} baud): {error}", "no response from the device on {port} ({bauds} baud): {error}", "нет ответа от устройства на {port} ({bauds} бод): {error}", "设备在 {port} 无响应（{bauds} 波特）：{error}"),
    "err.no_response.hint": _r("confira se o firmware está gravado, a porta e o baud (--baud 115200)", "check that the firmware is flashed, the port and the baud (--baud 115200)", "проверьте, что прошивка записана, порт и скорость (--baud 115200)", "请确认固件已烧录，检查端口和波特率（--baud 115200）"),
    # ---- recusas e cancelamento
    "cancelled": _r("cancelado", "cancelled", "отменено", "已取消"),
    "refused.repeat": _r("repita o comando com --yes", "repeat the command with --yes", "повторите команду с --yes", "请加上 --yes 重新运行命令"),
    "refused.rom": _r("recusado: gravar a ROM APAGA o chip de flash do cartucho. Em modo não interativo confirme com --yes.", "refused: writing the ROM ERASES the cartridge's flash chip. Outside a terminal confirm with --yes.", "отказано: запись ПЗУ СТИРАЕТ флеш-чип картриджа. Вне терминала подтвердите с --yes.", "已拒绝：写入 ROM 会擦除卡带的闪存芯片。在非交互模式下请用 --yes 确认。"),
    "refused.erase": _r("recusado: apagar o chip PERDE tudo o que ele tem. Em modo não interativo confirme com --yes.", "refused: erasing the chip LOSES everything on it. Outside a terminal confirm with --yes.", "отказано: стирание чипа УНИЧТОЖИТ всё, что на нём. Вне терминала подтвердите с --yes.", "已拒绝：擦除芯片会丢失其中所有内容。在非交互模式下请用 --yes 确认。"),
    "refused.write": _r("recusado: gravar APAGA o chip. Em modo não interativo confirme com --yes.", "refused: writing ERASES the chip. Outside a terminal confirm with --yes.", "отказано: запись СТИРАЕТ чип. Вне терминала подтвердите с --yes.", "已拒绝：写入会擦除芯片。在非交互模式下请用 --yes 确认。"),
    "refused.save": _r("recusado: gravar o save sobrescreve a memória do cartucho. Em modo não interativo confirme com --yes.", "refused: writing the save overwrites the cartridge's memory. Outside a terminal confirm with --yes.", "отказано: запись сохранения перезаписывает память картриджа. Вне терминала подтвердите с --yes.", "已拒绝：写入存档会覆盖卡带的存储。在非交互模式下请用 --yes 确认。"),
    "refused.save.hint": _r("repita o comando com --yes (o save atual é salvo em --backup-dir antes, a menos que use --no-backup)", "repeat the command with --yes (the current save is backed up to --backup-dir first, unless you use --no-backup)", "повторите команду с --yes (текущее сохранение сначала копируется в --backup-dir, если не указан --no-backup)", "请加上 --yes 重新运行命令（除非使用 --no-backup，否则会先把当前存档备份到 --backup-dir）"),
    "refused.firmware": _r("recusado: gravar o firmware troca o programa do Arduino. Em modo não interativo confirme com --yes.", "refused: flashing the firmware replaces the Arduino's program. Outside a terminal confirm with --yes.", "отказано: запись прошивки заменяет программу Arduino. Вне терминала подтвердите с --yes.", "已拒绝：烧录固件会替换 Arduino 的程序。在非交互模式下请用 --yes 确认。"),
    # ---- códigos de saída (comando `errors`)
    "exit.0": _r("sucesso", "success", "успех", "成功"),
    "exit.1": _r("erro do dispositivo, do protocolo, de timeout ou de arquivo", "device, protocol, timeout or file error", "ошибка устройства, протокола, тайм-аут или ошибка файла", "设备、协议、超时或文件错误"),
    "exit.2": _r("nenhum cartucho (detect) ou o dispositivo respondeu 'nenhum cartucho'", "no cartridge (detect) or the device answered 'no cartridge'", "нет картриджа (detect) или устройство ответило «нет картриджа»", "没有卡带（detect），或设备回答“没有卡带”"),
    "exit.3": _r("porta serial não encontrada ou dispositivo sem resposta", "serial port not found or device not responding", "последовательный порт не найден или устройство не отвечает", "未找到串口或设备无响应"),
    "exit.4": _r("operação recusada: falta --yes fora de um terminal", "operation refused: --yes is missing outside a terminal", "операция отклонена: вне терминала не указан --yes", "操作被拒绝：在终端之外缺少 --yes"),
    "exit.64": _r("argumentos inválidos", "invalid arguments", "неверные аргументы", "参数无效"),
    "exit.130": _r("interrompido (Ctrl+C)", "interrupted (Ctrl+C)", "прервано (Ctrl+C)", "已中断（Ctrl+C）"),
    "errors.exit_line": _r("saída {code}: {text}", "exit {code}: {text}", "выход {code}: {text}", "退出码 {code}：{text}"),
    "errors.dev_line": _r("erro 0x{code:04X}: {text}", "error 0x{code:04X}: {text}", "ошибка 0x{code:04X}: {text}", "错误 0x{code:04X}：{text}"),
    # ---- detect
    "detect.status.0": _r("cartucho detectado", "cartridge detected", "картридж обнаружен", "已检测到卡带"),
    "detect.status.1": _r("nenhum cartucho", "no cartridge", "нет картриджа", "没有卡带"),
    "detect.status.2": _r("não suportado", "not supported", "не поддерживается", "不支持"),
    "detect.status.3": _r("erro de hardware", "hardware error", "ошибка оборудования", "硬件错误"),
    "detect.status.4": _r("cabeçalho inválido ou ilegível (há dados, mas o checksum do cabeçalho não confere; ou, no Mega Drive com a placa v. 1.2, o pino /CART indica cartucho mas o cabeçalho não leu: limpe os contatos e encaixe de novo)", "invalid or unreadable header (there is data, but the header checksum does not match; or, on the Mega Drive with the v. 1.2 board, the /CART pin says there is a cartridge but the header could not be read: clean the contacts and reseat it)", "недопустимый или нечитаемый заголовок (данные есть, но контрольная сумма заголовка не сходится; или на Mega Drive с платой v. 1.2 контакт /CART указывает на картридж, но заголовок не прочитан: очистите контакты и вставьте заново)", "头部无效或无法读取（有数据，但头部校验和不符；或在 Mega Drive 的 v. 1.2 开发板上，/CART 引脚显示有卡带但未能读取头部：请清洁触点并重新插入）"),
    # ---- power
    "power.state_on": _r("5V dos slots: ligado", "slots' 5V: on", "5V слотов: включено", "插槽 5V：已开"),
    "power.state_off": _r("5V dos slots: desligado", "slots' 5V: off", "5V слотов: выключено", "插槽 5V：已关"),
    "power.no_switch": _r("esta placa/firmware não tem a chave de 5V: o 5V fica sempre ligado", "this board/firmware has no 5V switch: the 5V is always on", "в этой плате/прошивке нет ключа 5V: 5V всегда включено", "此开发板/固件没有 5V 开关：5V 始终开启"),
    "power.rail_low": _r("sensor do rail: baixo (seguro trocar o cartucho)", "rail sensor: low (safe to swap the cartridge)", "датчик шины: низкий (картридж можно менять)", "电源轨传感器：低（可以更换卡带）"),
    "power.rail_high": _r("sensor do rail: alto (ainda há tensão: não troque o cartucho)", "rail sensor: high (voltage still present: do not swap the cartridge)", "датчик шины: высокий (напряжение ещё есть: не меняйте картридж)", "电源轨传感器：高（仍有电压：请勿更换卡带）"),
    "power.can_swap": _r("pode trocar o cartucho", "you can swap the cartridge", "можно менять картридж", "可以更换卡带"),
    "power.no_sensor": _r(" (sem sensor de tensão: o firmware já esperou a descarga; confira com o multímetro)", " (no voltage sensor: the firmware already waited for the discharge; check with a multimeter)", " (нет датчика напряжения: прошивка уже дождалась разряда; проверьте мультиметром)", "（没有电压传感器：固件已等待放电；请用万用表确认）"),
    "power.then_on": _r("; depois rode `dumper power on`", "; then run `dumper power on`", "; затем выполните `dumper power on`", "；之后运行 `dumper power on`"),
    # ---- firmware-flash
    "fw.no_hex": _r("arquivo de firmware não encontrado: {path}", "firmware file not found: {path}", "файл прошивки не найден: {path}", "未找到固件文件：{path}"),
    "fw.no_hex.hint": _r("use --hex ARQUIVO.hex, ou compile antes: `cd firmware/oscr && pio run -e {env}`", "use --hex FILE.hex, or build first: `cd firmware/oscr && pio run -e {env}`", "укажите --hex ФАЙЛ.hex или сначала соберите: `cd firmware/oscr && pio run -e {env}`", "请使用 --hex 文件.hex，或先编译：`cd firmware/oscr && pio run -e {env}`"),
    "fw.no_avrdude_given": _r("avrdude não encontrado: {path}", "avrdude not found: {path}", "avrdude не найден: {path}", "未找到 avrdude：{path}"),
    "fw.no_avrdude_given.hint": _r("confira o caminho de --avrdude", "check the path given in --avrdude", "проверьте путь в --avrdude", "请检查 --avrdude 的路径"),
    "fw.no_avrdude": _r("avrdude não encontrado", "avrdude not found", "avrdude не найден", "未找到 avrdude"),
    "fw.no_avrdude.hint": _r("instale o avrdude (Linux: `sudo apt install avrdude`; macOS: `brew install avrdude`; Windows: winget ou o pacote do Arduino) ou use --avrdude CAMINHO", "install avrdude (Linux: `sudo apt install avrdude`; macOS: `brew install avrdude`; Windows: winget or the Arduino package) or use --avrdude PATH", "установите avrdude (Linux: `sudo apt install avrdude`; macOS: `brew install avrdude`; Windows: winget или пакет Arduino) или укажите --avrdude ПУТЬ", "请安装 avrdude（Linux：`sudo apt install avrdude`；macOS：`brew install avrdude`；Windows：winget 或 Arduino 软件包），或使用 --avrdude 路径"),
    "fw.simulated_exe": _r("avrdude (simulado)", "avrdude (simulated)", "avrdude (имитация)", "avrdude（模拟）"),
    "fw.simulator": _r("simulador", "simulator", "симулятор", "模拟器"),
    "fw.dry_run": _r("não gravou nada (--dry-run). Comando: {cmd}", "nothing was written (--dry-run). Command: {cmd}", "ничего не записано (--dry-run). Команда: {cmd}", "未写入任何内容（--dry-run）。命令：{cmd}"),
    "fw.what": _r("gravar {hex} ({size} bytes de HEX) em {port} com o avrdude", "write {hex} ({size} bytes of HEX) to {port} with avrdude", "записать {hex} ({size} байт HEX) в {port} с помощью avrdude", "用 avrdude 把 {hex}（{size} 字节 HEX）写入 {port}"),
    "fw.ask": _r("{what}. O firmware atual será substituído. Continuar? [s/N] ", "{what}. The current firmware will be replaced. Continue? [y/N] ", "{what}. Текущая прошивка будет заменена. Продолжить? [y/N] ", "{what}。当前固件将被替换。继续？[y/N] "),
    "fw.simulated": _r("simulado: {what}", "simulated: {what}", "имитация: {what}", "模拟：{what}"),
    "fw.failed": _r("o avrdude falhou (código {code}): {detail}", "avrdude failed (code {code}): {detail}", "avrdude завершился с ошибкой (код {code}): {detail}", "avrdude 失败（代码 {code}）：{detail}"),
    "fw.failed.no_message": _r("sem mensagem", "no message", "нет сообщения", "无消息"),
    "fw.failed.hint": _r("confira a porta e o cabo, feche outros programas que usam a porta (monitor serial, GUI) e repita; no Linux, grupo dialout", "check the port and the cable, close other programs using the port (serial monitor, GUI) and retry; on Linux, dialout group", "проверьте порт и кабель, закройте другие программы, использующие порт (монитор порта, GUI), и повторите; в Linux — группа dialout", "请检查端口和数据线，关闭其他占用该端口的程序（串口监视器、GUI）后重试；在 Linux 中检查 dialout 组"),
    "fw.done": _r("firmware gravado em {port}", "firmware written to {port}", "прошивка записана через {port}", "固件已写入 {port}"),
    "fw.done_verified": _r(" e conferido pelo avrdude", " and verified by avrdude", " и проверена avrdude", "并已由 avrdude 校验"),
    "fw.answered": _r("o dispositivo respondeu ao INFO: firmware {fw}, protocolo {proto}", "the device answered INFO: firmware {fw}, protocol {proto}", "устройство ответило на INFO: прошивка {fw}, протокол {proto}", "设备已响应 INFO：固件 {fw}，协议 {proto}"),
    "fw.before": _r(" (antes: {fw})", " (before: {fw})", " (раньше: {fw})", "（之前：{fw}）"),
    "fw.no_answer": _r("o dispositivo ainda não respondeu ao INFO (a porta pode ter mudado de nome): rode `dumper info` em alguns segundos", "the device has not answered INFO yet (the port may have changed name): run `dumper info` in a few seconds", "устройство пока не ответило на INFO (порт мог сменить имя): выполните `dumper info` через несколько секунд", "设备尚未响应 INFO（端口名称可能已改变）：请几秒后运行 `dumper info`"),
    # ---- dump, save, rom-write, flash-*, detect, info, db (D133, segunda fatia)
    "dump.game_only_nes": _r("--game vale só para NES e Famicom", "--game only applies to NES and Famicom", "--game применим только к NES и Famicom", "--game 仅适用于 NES 和 Famicom"),
    "dump.raw_only_nes": _r("--raw vale só para NES e Famicom", "--raw only applies to NES and Famicom", "--raw применим только к NES и Famicom", "--raw 仅适用于 NES 和 Famicom"),
    "dump.raw_no_header": _r("--raw: o firmware não devolveu um cabeçalho iNES para separar PRG e CHR", "--raw: the firmware did not return an iNES header to split PRG and CHR", "--raw: прошивка не вернула заголовок iNES для разделения PRG и CHR", "--raw：固件没有返回用于拆分 PRG 和 CHR 的 iNES 头"),
    "dump.raw_header_big": _r("--raw: cabeçalho iNES maior que os dados lidos", "--raw: iNES header larger than the data read", "--raw: заголовок iNES больше прочитанных данных", "--raw：iNES 头大于所读数据"),
    "dump.no_chr": _r("sem CHR-ROM (o cartucho usa CHR-RAM)", "no CHR-ROM (the cartridge uses CHR-RAM)", "нет CHR-ROM (картридж использует CHR-RAM)", "没有 CHR-ROM（卡带使用 CHR-RAM）"),
    "dump.ines_full": _r("iNES completo (PRG + CHR com cabeçalho): CRC32 {crc}", "full iNES (PRG + CHR with header): CRC32 {crc}", "полный iNES (PRG + CHR с заголовком): CRC32 {crc}", "完整 iNES（PRG + CHR 含头）：CRC32 {crc}"),
    "dump.twice_ok": _r("leitura dupla: as duas leituras são idênticas (CRC32 {crc})", "double read: both reads are identical (CRC32 {crc})", "двойное чтение: оба чтения идентичны (CRC32 {crc})", "两次读取：两次结果相同（CRC32 {crc}）"),
    "dump.warning": _r("aviso: ", "warning: ", "предупреждение: ", "警告："),
    "dump.game": _r("jogo: {name} ({source}, {how})", "game: {name} ({source}, {how})", "игра: {name} ({source}, {how})", "游戏：{name}（{source}，{how}）"),
    "dump.game_more": _r("jogo: {name} ({source}, {how}, mais {others} idêntica(s))", "game: {name} ({source}, {how}, {others} more identical)", "игра: {name} ({source}, {how}, ещё идентичных: {others})", "游戏：{name}（{source}，{how}，另有 {others} 个相同）"),
    "dump.game_missing": _r("jogo: não encontrado na base ({n} entradas): dump novo, variante, ou erro de leitura se o CRC32 devia estar lá", "game: not found in the database ({n} entries): a new dump, a variant, or a read error if the CRC32 should be there", "игра: не найдена в базе ({n} записей): новый дамп, вариант или ошибка чтения, если CRC32 должен там быть", "游戏：数据库中未找到（{n} 条）：可能是新的转储、变体，或在 CRC32 本应存在时为读取错误"),
    "dump.mismatch": _r("as duas leituras diferem ({diff} byte(s); primeira diferença no byte {first}; CRC32 {crc1} e {crc2})", "the two reads differ ({diff} byte(s); first difference at byte {first}; CRC32 {crc1} and {crc2})", "два чтения различаются ({diff} байт; первое отличие в байте {first}; CRC32 {crc1} и {crc2})", "两次读取不同（{diff} 字节；首个差异在字节 {first}；CRC32 {crc1} 和 {crc2}）"),
    "dump.mismatch.hint": _r("limpe os contatos do cartucho e do slot e leia de novo; compare os dois arquivos gravados", "clean the cartridge and slot contacts and read again; compare the two saved files", "очистите контакты картриджа и слота и прочитайте снова; сравните два сохранённых файла", "请清洁卡带和插槽的触点后重新读取；比较保存的两个文件"),
    "save.eeprom_warn": _r("aviso: o conteúdo se repete a cada 512 bytes: é uma EEPROM de 512 bytes. Refaça com --mapper 1.", "warning: the content repeats every 512 bytes: it is a 512-byte EEPROM. Redo with --mapper 1.", "предупреждение: содержимое повторяется каждые 512 байт: это EEPROM на 512 байт. Повторите с --mapper 1.", "警告：内容每 512 字节重复一次：这是 512 字节的 EEPROM。请用 --mapper 1 重做。"),
    "save.ask": _r("Gravar {n} bytes no save de {system}? Isso sobrescreve o save do cartucho. Continuar? [s/N] ", "Write {n} bytes to the {system} save? This overwrites the cartridge's save. Continue? [y/N] ", "Записать {n} байт в сохранение {system}? Это перезапишет сохранение картриджа. Продолжить? [y/N] ", "把 {n} 字节写入 {system} 的存档？这会覆盖卡带的存档。继续？[y/N] "),
    "save.written": _r("save gravado: {n} bytes  CRC32 {crc}", "save written: {n} bytes  CRC32 {crc}", "сохранение записано: {n} байт  CRC32 {crc}", "存档已写入：{n} 字节  CRC32 {crc}"),
    "save.verify_failed": _r("o save lido de volta NÃO confere com o gravado (primeiro byte diferente no offset {first}; lido {read}, esperado {exp}, {n} bytes lidos de {total})", "the save read back does NOT match what was written (first differing byte at offset {first}; read {read}, expected {exp}, {n} bytes read of {total})", "считанное обратно сохранение НЕ совпадает с записанным (первый отличающийся байт по смещению {first}; прочитано {read}, ожидалось {exp}, прочитано {n} байт из {total})", "回读的存档与写入内容不符（首个不同字节在偏移 {first}；读到 {read}，期望 {exp}，已读 {n}/{total} 字节）"),
    "save.verify_failed.hint": _r("limpe os contatos, confira o tipo de save (--mapper/--ram) e grave de novo; o backup do save anterior está em --backup-dir", "clean the contacts, check the save type (--mapper/--ram) and write again; the previous save's backup is in --backup-dir", "очистите контакты, проверьте тип сохранения (--mapper/--ram) и запишите снова; резервная копия прежнего сохранения в --backup-dir", "请清洁触点，检查存档类型（--mapper/--ram）后重新写入；之前存档的备份在 --backup-dir"),
    "verify.skipped_flag": _r("conferência depois de gravar: pulada (--no-verify)", "post-write verification: skipped (--no-verify)", "проверка после записи: пропущена (--no-verify)", "写入后校验：已跳过（--no-verify）"),
    "verify.skipped": _r("conferência depois de gravar: pulada", "post-write verification: skipped", "проверка после записи: пропущена", "写入后校验：已跳过"),
    "verify.ok": _r("conferência depois de gravar: OK (leu {n} bytes, CRC32 {crc})", "post-write verification: OK (read {n} bytes, CRC32 {crc})", "проверка после записи: OK (прочитано {n} байт, CRC32 {crc})", "写入后校验：通过（读取 {n} 字节，CRC32 {crc}）"),
    "verify.ok_chip": _r("conferência depois de gravar: OK (leu {n} bytes do chip)", "post-write verification: OK (read {n} bytes from the chip)", "проверка после записи: OK (прочитано {n} байт из чипа)", "写入后校验：通过（从芯片读取 {n} 字节）"),
    "rom.mapper_warn": _r("aviso: o arquivo é do mapper {file}, mas o chip {chip} é de cartucho de mapper {chipmapper}", "warning: the file is mapper {file}, but chip {chip} belongs to mapper {chipmapper} cartridges", "предупреждение: файл для маппера {file}, но чип {chip} относится к картриджам маппера {chipmapper}", "警告：文件属于 mapper {file}，但芯片 {chip} 属于 mapper {chipmapper} 的卡带"),
    "rom.what_flash": _r("{label}: ROM {prg} KB em flash de {flash} KB, {layout} ({n} bytes enviados)", "{label}: ROM {prg} KB in a {flash} KB flash, {layout} ({n} bytes sent)", "{label}: ROM {prg} КБ во флеш {flash} КБ, {layout} (отправлено {n} байт)", "{label}：ROM {prg} KB，写入 {flash} KB 闪存，{layout}（发送 {n} 字节）"),
    "rom.what_block": _r("{label}: ROM {n} bytes, bloco {block}", "{label}: ROM {n} bytes, block {block}", "{label}: ROM {n} байт, блок {block}", "{label}：ROM {n} 字节，块 {block}"),
    "rom.what_plain": _r("{label}: ROM {n} bytes", "{label}: ROM {n} bytes", "{label}: ROM {n} байт", "{label}：ROM {n} 字节"),
    "rom.what_prgchr": _r("{label}: PRG {prg} KB, CHR {chr} KB ({n} bytes)", "{label}: PRG {prg} KB, CHR {chr} KB ({n} bytes)", "{label}: PRG {prg} КБ, CHR {chr} КБ ({n} байт)", "{label}：PRG {prg} KB，CHR {chr} KB（{n} 字节）"),
    "rom.ask": _r("Gravar {what}? Isso APAGA a ROM atual do cartucho. Continuar? [s/N] ", "Write {what}? This ERASES the cartridge's current ROM. Continue? [y/N] ", "Записать {what}? Это СТЁРЕТ текущую ПЗУ картриджа. Продолжить? [y/N] ", "写入 {what}？这会擦除卡带当前的 ROM。继续？[y/N] "),
    "rom.written": _r("ROM gravada: {what}  CRC32 {crc}", "ROM written: {what}  CRC32 {crc}", "ПЗУ записано: {what}  CRC32 {crc}", "ROM 已写入：{what}  CRC32 {crc}"),
    "rom.skip_gbcam": _r("(o 2º jogo do GB Camera não é visto pela leitura comum)", "(the 2nd GB Camera game is not seen by the normal read)", "(второй игры GB Camera не видно при обычном чтении)", "（常规读取看不到 GB Camera 的第 2 个游戏）"),
    "rom.skip_gba": _r("(a leitura do GBA não alcança o bloco N do 369-in-1, nem mais de 64 MB)", "(the GBA read does not reach block N of the 369-in-1, nor more than 64 MB)", "(чтение GBA не достигает блока N в 369-in-1 и объёма свыше 64 МБ)", "（GBA 的读取无法到达 369-in-1 的第 N 块，也无法读取超过 64 MB）"),
    "rom.verify_failed": _r("a ROM lida de volta NÃO confere com a gravada (primeiro byte diferente no offset {first}; lido {read}, esperado {exp})", "the ROM read back does NOT match what was written (first differing byte at offset {first}; read {read}, expected {exp})", "считанная обратно ПЗУ НЕ совпадает с записанной (первый отличающийся байт по смещению {first}; прочитано {read}, ожидалось {exp})", "回读的 ROM 与写入内容不符（首个不同字节在偏移 {first}；读到 {read}，期望 {exp}）"),
    "rom.verify_failed.hint": _r("limpe os contatos, confira se o chip é o escolhido e grave de novo; o chip pode estar apagado ou pela metade", "clean the contacts, check that the chip is the chosen one and write again; the chip may be erased or half-written", "очистите контакты, проверьте, что чип выбран верно, и запишите снова; чип может быть стёрт или записан наполовину", "请清洁触点，确认芯片与所选一致后重新写入；芯片可能已被擦除或只写了一半"),
    "fw.unsupported_write_rom": _r("este firmware não aceita WRITE_ROM", "this firmware does not support WRITE_ROM", "эта прошивка не поддерживает WRITE_ROM", "此固件不支持 WRITE_ROM"),
    "fw.unsupported.hint": _r("atualize o firmware (docs/referencia/funcoes-oscr.md)", "update the firmware (docs/referencia/funcoes-oscr.md)", "обновите прошивку (docs/referencia/funcoes-oscr.md)", "请更新固件（docs/referencia/funcoes-oscr.md）"),
    "flash.no_prog": _r("este firmware não tem o programador de flash genérico", "this firmware has no generic flash programmer", "в этой прошивке нет универсального программатора флеш-памяти", "此固件没有通用闪存编程器"),
    "flash.blank_yes": _r("em branco", "blank", "чип пуст", "空白"),
    "flash.blank_no": _r("NÃO está em branco (primeiro byte diferente de FF no offset {first})", "NOT blank (first byte other than FF at offset {first})", "НЕ пуст (первый байт, отличный от FF, по смещению {first})", "不是空白（首个非 FF 字节在偏移 {first}）"),
    "flash.eprom_no_erase": _r("EPROM não se apaga (a 27C322 só apaga com luz ultravioleta); use flash-blank para conferir se está em branco", "an EPROM cannot be erased (the 27C322 only erases with ultraviolet light); use flash-blank to check that it is blank", "EPROM не стирается (27C322 стирается только ультрафиолетом); используйте flash-blank, чтобы проверить, пуста ли она", "EPROM 无法擦除（27C322 只能用紫外线擦除）；请用 flash-blank 检查是否空白"),
    "flash.erase_ask": _r("Apagar {chip} de {kb} KB? Isso PERDE o conteúdo. Continuar? [s/N] ", "Erase {chip} of {kb} KB? This LOSES its contents. Continue? [y/N] ", "Стереть {chip} на {kb} КБ? Содержимое будет ПОТЕРЯНО. Продолжить? [y/N] ", "擦除 {kb} KB 的 {chip}？其内容将丢失。继续？[y/N] "),
    "flash.write_what": _r("{chip}: {n} bytes em um chip de {kb} KB", "{chip}: {n} bytes in a {kb} KB chip", "{chip}: {n} байт в чипе {kb} КБ", "{chip}：{n} 字节，芯片 {kb} KB"),
    "flash.write_ask": _r("Gravar {what}? Isso APAGA o conteúdo atual do chip. Continuar? [s/N] ", "Write {what}? This ERASES the chip's current contents. Continue? [y/N] ", "Записать {what}? Это СТЁРЕТ текущее содержимое чипа. Продолжить? [y/N] ", "写入 {what}？这会擦除芯片当前内容。继续？[y/N] "),
    "flash.written": _r("gravado: {what}  CRC32 {crc}", "written: {what}  CRC32 {crc}", "записано: {what}  CRC32 {crc}", "已写入：{what}  CRC32 {crc}"),
    "flash.verify_failed": _r("o chip lido de volta NÃO confere com o arquivo (primeiro byte diferente no offset {first})", "the chip read back does NOT match the file (first differing byte at offset {first})", "считанный обратно чип НЕ совпадает с файлом (первый отличающийся байт по смещению {first})", "回读的芯片与文件不符（首个不同字节在偏移 {first}）"),
    "flash.verify_failed.hint": _r("confira o tipo do flash, limpe os contatos e grave de novo; o chip pode estar apagado ou pela metade", "check the flash type, clean the contacts and write again; the chip may be erased or half-written", "проверьте тип флеш-памяти, очистите контакты и запишите снова; чип может быть стёрт или записан наполовину", "请检查闪存类型，清洁触点后重新写入；芯片可能已被擦除或只写了一半"),
    "detect.flash_id_md_only": _r("--flash-id vale só para o Mega Drive (-s md)", "--flash-id only applies to the Mega Drive (-s md)", "--flash-id применим только к Mega Drive (-s md)", "--flash-id 仅适用于 Mega Drive（-s md）"),
    "detect.title_line": _r("  título: {name}  ROM: {rom} bytes  save: {save} bytes", "  title: {name}  ROM: {rom} bytes  save: {save} bytes", "  название: {name}  ПЗУ: {rom} байт  сохранение: {save} байт", "  标题：{name}  ROM：{rom} 字节  存档：{save} 字节"),
    "detect.unknown_title": _r("(desconhecido)", "(unknown)", "(неизвестно)", "（未知）"),
    "detect.attempts": _r("  {n} tentativas de leitura do cabeçalho (ciclo de energia do SA-1)", "  {n} attempts to read the header (SA-1 power cycle)", "  попыток чтения заголовка: {n} (цикл питания SA-1)", "  读取头部尝试了 {n} 次（SA-1 电源循环）"),
    "detect.field_title": _r("título", "title", "название", "标题"),
    "detect.field_save": _r("save", "save", "сохранение", "存档"),
    "detect.field_tries": _r("tentativas", "attempts", "попытки", "尝试"),
    "detect.field_tries_val": _r("{n} (ciclo de energia do SA-1)", "{n} (SA-1 power cycle)", "{n} (цикл питания SA-1)", "{n}（SA-1 电源循环）"),
    "detect.field_chip": _r("chip", "chip", "чип", "芯片"),
    "chip.no_id": _r("chip de flash: este firmware não identifica o chip", "flash chip: this firmware does not identify the chip", "флеш-чип: эта прошивка не определяет чип", "闪存芯片：此固件无法识别芯片"),
    "chip.known": _r("chip de flash: {chip}  ({kb} KB)", "flash chip: {chip}  ({kb} KB)", "флеш-чип: {chip}  ({kb} КБ)", "闪存芯片：{chip}（{kb} KB）"),
    "chip.unknown": _r("chip de flash: fora da tabela ou sem resposta ({ids})", "flash chip: not in the table or no response ({ids})", "флеш-чип: нет в таблице или не отвечает ({ids})", "闪存芯片：不在表中或无响应（{ids}）"),
    "chip.cfi_size": _r("; a consulta CFI diz {kb} KB", "; the CFI query says {kb} KB", "; запрос CFI сообщает {kb} КБ", "；CFI 查询显示 {kb} KB"),
    "info.line": _r("protocolo {proto}  firmware {fw}  MOCK={mock}  Si5351={si}  sistemas: {systems}  payload máx. {maxp}", "protocol {proto}  firmware {fw}  MOCK={mock}  Si5351={si}  systems: {systems}  max payload {maxp}", "протокол {proto}  прошивка {fw}  MOCK={mock}  Si5351={si}  системы: {systems}  макс. полезная нагрузка {maxp}", "协议 {proto}  固件 {fw}  MOCK={mock}  Si5351={si}  系统：{systems}  最大载荷 {maxp}"),
    "yes": _r("sim", "yes", "да", "是"),
    "no": _r("não", "no", "нет", "否"),
    "systems.options": _r("opções", "options", "опции", "选项"),
    "systems.planned": _r("em breve (outros cartuchos do OSCR, ainda sem hardware, firmware nem id no protocolo):", "coming soon (other OSCR cartridges, no hardware, firmware or protocol id yet):", "скоро (другие картриджи OSCR; пока нет оборудования, прошивки и id в протоколе):", "即将支持（OSCR 的其他卡带；暂无硬件、固件和协议 id）："),
    "db.not_found": _r("não encontrado na base", "not found in the database", "не найдено в базе", "数据库中未找到"),
}
