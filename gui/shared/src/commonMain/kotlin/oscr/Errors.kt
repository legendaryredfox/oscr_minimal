// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/** Texto de erro para o usuário, no idioma escolhido, com a causa provável e o que fazer. */
fun describeError(lang: Lang, e: Throwable): String {
    val body = when (e) {
        is DeviceError -> I18n.keyOrNull("ERR_DEV_${e.code}")?.let { I18n.t(lang, it) } ?: I18n.f(lang, S.ERR_DEV_OTHER, e.code.toString(16).uppercase().padStart(4, '0'))
        is TimeoutError -> failText(lang, e.fail, e.detail)
        is ProtocolError -> failText(lang, e.fail, e.detail)
        else -> I18n.f(lang, S.ERR_UNKNOWN, e.message ?: e::class.simpleName ?: "?")
    }
    return "${I18n.t(lang, S.ERR_PREFIX)}: $body"
}

private fun failText(lang: Lang, f: Fail, detail: String): String = when (f) {
    Fail.NO_RESPONSE -> I18n.t(lang, S.ERR_NO_RESPONSE)
    Fail.STALLED -> I18n.t(lang, S.ERR_STALLED)
    Fail.OPEN_PORT -> I18n.f(lang, S.ERR_OPEN_PORT, detail) + " " + I18n.t(lang, S.ERR_OPEN_PORT_LINUX)
    Fail.SHORT_REPLY -> I18n.f(lang, S.ERR_SHORT_REPLY, detail)
    Fail.BAD_END -> I18n.f(lang, S.ERR_BAD_END, detail)
    Fail.BAD_PAYLOAD -> I18n.f(lang, S.ERR_BAD_PAYLOAD, detail)
    Fail.BAD_KIND -> I18n.f(lang, S.ERR_BAD_KIND, detail)
    Fail.BAD_SIZE -> I18n.f(lang, S.ERR_BAD_SIZE, detail)
    Fail.PARTIAL_WRITE -> I18n.f(lang, S.ERR_PARTIAL_WRITE, detail)
    Fail.DISCONNECTED -> I18n.t(lang, S.ERR_DISCONNECTED)
}
