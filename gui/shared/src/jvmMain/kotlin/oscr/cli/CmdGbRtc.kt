// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.time.LocalTime

/**
 * Comando gb-rtc: relógio (RTC) do MBC3 do Game Boy (F-17, D192). Sem opção só lê. Com --now, --set, --day, --halt, --run ou --clear-carry grava os 5 registradores
 * (o que não foi pedido fica como estava) e confere lendo de volta. `-o` guarda o rodapé de 48 bytes de save; `-i` grava no cartucho o relógio de um rodapé (ou de um .sav com o rodapé no fim). Igual a host/oscr_host/cli/cmd_gbrtc.py.
 */
internal fun cmdGbRtc(io: CliIo, a: Args): Int {
    if ("now" in a.flags && a.opts["set"] != null) throw CliError("usage", Msg.t("gbrtc.both"), EXIT_USAGE)
    var newTime: Triple<Int, Int, Int>? = null
    a.opts["set"]?.let { s -> newTime = GbRtc.parseTime(s) ?: throw CliError("usage", Msg.t("gbrtc.bad_time", "value" to s), EXIT_USAGE) }
    if ("now" in a.flags) LocalTime.now().let { newTime = Triple(it.hour, it.minute, it.second) }
    val day = a.opts["day"]?.let { d -> d.toIntOrNull()?.takeIf { it in 0..GbRtc.MAX_DAY } ?: throw CliError("usage", Msg.t("gbrtc.bad_day", "max" to GbRtc.MAX_DAY), EXIT_USAGE) }
    if ("halt" in a.flags && "run" in a.flags) throw CliError("usage", Msg.t("gbrtc.halt_run"), EXIT_USAGE)
    val edits = newTime != null || day != null || "halt" in a.flags || "run" in a.flags || "clear-carry" in a.flags
    var fileRaw: ByteArray? = null
    a.opts["input"]?.let { path ->
        if (edits) throw CliError("usage", Msg.t("gbrtc.input_alone"), EXIT_USAGE)
        fileRaw = try { GbRtc.fromFile(File(path).readBytes()).let { r -> GbRtc.decode(r).let { d -> GbRtc.encode(d.seconds, d.minutes, d.hours, d.days, d.halted, d.carry) } } }
        catch (e: Exception) { if (e is IllegalArgumentException || e is java.io.IOException) throw CliError("usage", Msg.t("gbrtc.bad_input", "path" to path), EXIT_USAGE) else throw e }
    }
    val write = edits || fileRaw != null
    val c = connect(io, a.withOpt("system", "gb"))
    val gb = CartSystem.GB
    fun read(): ByteArray = try { c.client.dumpRom(gb, 0, GbRtc.MAPPER, 0, 0).data } catch (e: DeviceError) {
        if (e.code == 10) throw CliError("no_rtc", Msg.t("gbrtc.no_rtc"), EXIT_ERROR) else throw e      // E_SEM_SAVE: não é MBC3 com TIMER
    }
    val before: ByteArray
    var raw: ByteArray
    var verified: Boolean? = null
    try {
        before = read(); raw = before
        if (write) {
            val old = GbRtc.decode(before)
            val t = newTime ?: Triple(old.hours, old.minutes, old.seconds)
            val halted = if ("halt" in a.flags) true else if ("run" in a.flags) false else old.halted
            raw = fileRaw ?: GbRtc.encode(t.third, t.second, t.first, day ?: old.days, halted, old.carry && "clear-carry" !in a.flags)
            c.client.writeSave(gb, raw, 512, GbRtc.MAPPER, 0, null)
            verified = GbRtc.matches(GbRtc.decode(raw), GbRtc.decode(read()))
        }
    } finally { c.transport.close() }
    val old = GbRtc.decode(before)
    fun state(h: Boolean) = Msg.t(if (h) "gbrtc.halted" else "gbrtc.running")
    val lines = mutableListOf(Msg.t("gbrtc.state", "value" to old.text(), "state" to state(old.halted), "carry" to Msg.t(if (old.carry) "gbrtc.carry_yes" else "gbrtc.carry_no")))
    if (write) {
        val nv = GbRtc.decode(raw)
        lines += Msg.t("gbrtc.written", "value" to nv.text(), "state" to state(nv.halted))
        lines += Msg.t(if (verified == true) "gbrtc.verified" else "gbrtc.not_verified")
    }
    var saved: String? = null
    a.opts["output"]?.let { o -> File(o).writeBytes(GbRtc.footer(if (write) raw else before, System.currentTimeMillis() / 1000)); saved = o; lines += Msg.t("gbrtc.saved", "path" to o) }
    fun obj(v: GbRtc.Value, r: ByteArray) = Json.obj("seconds" to v.seconds, "minutes" to v.minutes, "hours" to v.hours, "days" to v.days, "halted" to v.halted, "carry" to v.carry,
        "raw" to r.joinToString("") { "%02x".format(it) })
    emit(io, a, Json.obj("before" to obj(old, before), "written" to if (write) obj(GbRtc.decode(raw), raw) else null, "verified" to verified, "footer" to saved), lines)
    return if (verified == false) EXIT_ERROR else EXIT_OK
}
