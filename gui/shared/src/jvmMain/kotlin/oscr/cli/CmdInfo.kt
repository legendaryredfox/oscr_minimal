// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Comandos ports, systems, errors e info. */
internal fun cmdPorts(io: CliIo, a: Args): Int {
    val p = io.listPorts()
    emit(io, a, Json.obj("ports" to p), p)
    return EXIT_OK
}

internal fun cmdSystems(io: CliIo, a: Args): Int {
    val rows = CartSystem.entries.map { Json.obj("name" to it.name.lowercase(), "id" to it.id, "extension" to it.ext,
        "options" to OPTIONS.getValue(it.name.lowercase()), "needs_cartridge" to (it != CartSystem.MOCK)) }
    val planned = PLANNED_SYSTEMS.map { Json.obj("name" to it.key, "label" to it.label, "supported" to false) }
    emit(io, a, Json.obj("systems" to rows, "planned" to planned),
        rows.map { "${(it["name"] as String).padEnd(8)} id ${it["id"]}  ${it["extension"]}  ${Msg.t("systems.options")}: ${(it["options"] as List<*>).joinToString(", ").ifEmpty { "-" }}" } +
            listOf("", Msg.t("systems.planned")) + PLANNED_SYSTEMS.map { "  ${it.key.padEnd(13)} ${it.label}" })
    return EXIT_OK
}

internal fun cmdErrors(io: CliIo, a: Args, lang: Lang): Int {
    val dev = (1..11).map { Json.obj("code" to it, "text" to I18n.t(lang, S.valueOf("ERR_DEV_$it"))) }
    val exits = EXIT_CODES.map { c -> Json.obj("exit_code" to c, "meaning" to exitMeaning(c)) }
    emit(io, a, Json.obj("device_errors" to dev, "exit_codes" to exits),
        EXIT_CODES.map { c -> Msg.t("errors.exit_line", "code" to c, "text" to exitMeaning(c)) } + dev.map { Msg.t("errors.dev_line", "code" to it["code"], "text" to it["text"]) })
    return EXIT_OK
}

internal fun cmdInfo(io: CliIo, a: Args): Int {
    val c = connect(io, a, needCart = false); val i = c.info
    val names = CartSystem.entries.filter { it.id < 16 && i.systemsMask and (1 shl it.id) != 0 }.map { it.name.lowercase() }
    c.transport.close()
    if (!a.json && colorOn(io, a)) io.out(Ui.banner(true, VERSION) + "\n")
    emit(io, a, Json.obj("proto" to i.proto, "firmware" to i.firmware, "flags" to i.flags, "max_payload" to i.maxPayload, "mock" to i.mock,
        "si5351" to i.si5351, "pic" to (i.flags and 4 != 0), "systems" to names),
        listOf(Msg.t("info.line", "proto" to i.proto, "fw" to i.firmware, "mock" to Msg.t(if (i.mock) "yes" else "no"), "si" to Msg.t(if (i.si5351) "yes" else "no"),
            "systems" to names.joinToString(", ").ifEmpty { "-" }, "maxp" to i.maxPayload)))
    return EXIT_OK
}
