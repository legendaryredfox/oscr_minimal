// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Texto de cada achado do autoteste, no idioma escolhido. */
internal fun selftestLines(r: SelfTestResult): List<String> {
    val lines = r.findings.map { f ->
        val key = when (f.kind) { "gnd" -> "selftest.gnd"; "pair" -> "selftest.pair"; "pullup" -> "selftest.pullup"; "clockgen" -> "selftest.clockgen"; else -> "selftest.unknown" }
        Msg.t(key, "pin" to (f.pins.getOrNull(0) ?: ""), "a" to (f.pins.getOrNull(0) ?: ""), "b" to (f.pins.getOrNull(1) ?: ""), "kind" to f.kind)
    }
    return if (r.truncated) lines + Msg.t("selftest.truncated") else lines
}

/** Comando selftest: autoteste da placa sem cartucho (curtos entre os pinos, pull-up do D7, Si5351; P-12). Sai com 1 se achar problema. */
internal fun cmdSelftest(io: CliIo, a: Args): Int {
    val c = connect(io, a, needCart = false)                  // não mexe na tensão: o teste roda sem cartucho
    val r = try {
        if (!c.info.selftest) throw CliError("no_selftest", Msg.t("selftest.unsupported"), EXIT_ERROR)
        if (!a.json) io.err(Msg.t("selftest.start"))
        c.client.selftest()
    } finally { c.transport.close() }
    val lines = selftestLines(r) + Msg.t(if (r.ok) "selftest.ok" else "selftest.found", "n" to r.findings.size)
    emit(io, a, Json.obj("ok" to r.ok, "truncated" to r.truncated, "findings" to r.findings.map { Json.obj("kind" to it.kind, "pins" to it.pins) }), lines)
    return if (r.ok) EXIT_OK else EXIT_ERROR
}
