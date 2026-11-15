// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/**
 * Placa escolhida pelo usuário (`--board`): confere o firmware do Arduino, grava o perfil da placa e, se faltar suporte, grava o firmware certo (D162).
 * Mesmo contrato da CLI Python (host/oscr_host/cli/cmd_board.py). Regra do usuário (2026-11-14): uma imagem só sempre que couber; se o firmware gravado não serve,
 * grava a imagem que serve **depois de pedir confirmação** (apaga o firmware atual e reinicia o Mega; `--auto-flash` confirma de antemão, para scripts).
 */
private fun resolveBoard(a: Args): BoardProfile = try { BoardPlanner.resolve(a.opts["board"] ?: "") } catch (e: BoardException) {
    throw CliError("unknown_board", Msg.t("board.${e.kind}", *e.params.map { it.key to it.value }.toTypedArray()), EXIT_USAGE, Msg.t("board.unknown.hint"))
}

private fun reasonsText(rs: List<Reason>) = rs.joinToString("; ") { Msg.t("board.reason.${it.code}", *it.params.map { p -> p.key to p.value }.toTypedArray()) }

private fun selText(p: BoardProfile) = Msg.t(if (p.voltageSelect) "board.yes" else "board.no")

private fun confirmFlash(io: CliIo, a: Args, p: BoardProfile, what: String) {
    if ("auto-flash" in a.flags) return
    if (a.json || !io.interactive) throw CliError("refused", Msg.t("board.refused", "board" to p.label), EXIT_REFUSED, Msg.t("board.refused.hint"))
    io.err(Msg.t("board.ask", "what" to what.replaceFirstChar { it.uppercase() }))
    if (io.readLine()?.trim()?.lowercase() !in setOf("y", "yes", "s", "sim", "да", "д", "是", "是的")) throw CliError("refused", Msg.t("board.cancelled"), EXIT_REFUSED)
}

/** Garante que o Arduino serve à placa `--board`. `opened` é null se o Arduino não respondeu. Devolve a conexão pronta (nova, se gravou). */
internal fun ensureBoard(io: CliIo, a: Args, opened: Conn?): Conn {
    val profile = resolveBoard(a)
    val images = BoardPlanner.loadImages(a.opts["firmware-dir"])
    val state = if (opened != null && opened.info.boardProfile) try { opened.client.board() } catch (e: DeviceError) { null } else null
    var plan = BoardPlanner.plan(profile, opened?.info, state, images)
    var action = plan.action.name.lowercase()
    var conn = opened

    if (plan.action == BoardAction.UNSUPPORTED) {
        conn?.transport?.close()
        throw CliError("board_unsupported", Msg.t("board.unsupported", "board" to profile.label, "reasons" to reasonsText(plan.reasons)), EXIT_ERROR, Msg.t("board.unsupported.hint"))
    }
    if (plan.action == BoardAction.FLASH) {
        val img = plan.image!!
        val port = a.opts["port"] ?: if ("simulate" in a.flags) Msg.t("fw.simulator") else (io.listPorts().firstOrNull { p -> listOf("ttyUSB", "ttyACM", "cu.usb", "COM").any { it in p } }
            ?: throw CliError("no_port", Msg.t("err.no_port"), EXIT_NO_DEVICE, Msg.t("err.no_port.hint")))
        conn?.transport?.close()                                       // solta a porta para o avrdude
        io.err(Msg.t("board.need_flash", "board" to profile.label, "reasons" to reasonsText(plan.reasons)))
        confirmFlash(io, a, profile, Msg.t("board.flash_what", "fw" to img.firmwareStr, "image" to img.hex.name, "port" to port))
        io.err(Msg.t("board.flashing", "fw" to img.firmwareStr, "port" to port))
        if ("simulate" in a.flags) io.simFlashed = true
        else writeFirmware(io, a, img.hex, port) ?: throw CliError("flash_no_answer", Msg.t("board.flash_no_answer"), EXIT_NO_DEVICE, Msg.t("board.flash_no_answer.hint"))
        conn = open(io, a)
        val st = if (conn.info.boardProfile) conn.client.board() else null
        plan = BoardPlanner.plan(profile, conn.info, st, images)
        if (plan.action == BoardAction.FLASH || plan.action == BoardAction.UNSUPPORTED) {
            conn.transport.close()
            throw CliError("flash_still_missing", Msg.t("board.flash_still_missing", "board" to profile.label, "reasons" to reasonsText(plan.reasons)), EXIT_ERROR)
        }
        action = "flash"
    }
    var c = conn!!
    if (plan.action == BoardAction.SET_PROFILE) {
        c.client.board(Board.SET, plan.profileFlags)
        c = Conn(c.client, c.transport, c.client.info())
        io.err(Msg.t("board.profile_set", "board" to profile.label, "selector" to selText(profile)))
        if (action != "flash") action = "set_profile"
    }
    return Conn(c.client, c.transport, c.info, mapOf("board" to profile.board, "version" to profile.version, "action" to action, "firmware" to c.info.firmware))
}

internal fun cmdBoards(io: CliIo, a: Args): Int {
    val lines = mutableListOf(Msg.t("board.list_head"))
    val rows = BoardPlanner.boards.map { b ->
        lines += Msg.t("board.list_line", "board" to b.board, "current" to b.current, "slots" to b.slots.joinToString(", "), "selector" to Msg.t(if (b.versions[b.current] == true) "board.yes" else "board.no"))
        Json.obj("board" to b.board, "current" to b.current, "slots" to b.slots, "systems" to b.systems.sorted(), "versions" to Json.obj(*b.versions.map { it.key to it.value }.toTypedArray()))
    }
    emit(io, a, Json.obj("boards" to rows), lines)
    return EXIT_OK
}

internal fun cmdBoard(io: CliIo, a: Args): Int {
    if (a.opts["board"] == null) throw CliError("usage", Msg.t("board.need_arg"), EXIT_USAGE)
    val c = connect(io, a, needCart = false)
    try {
        val r = c.boardResult ?: emptyMap()
        val profile = resolveBoard(a)
        emit(io, a, Json.obj(*(r + mapOf("systems" to c.info.systemIds.sorted(), "voltage_select" to c.info.voltageSelect)).map { it.key to it.value }.toTypedArray()),
            listOf(Msg.t("board.ok", "board" to profile.label, "fw" to c.info.firmware)))
    } finally { c.transport.close() }
    return EXIT_OK
}
