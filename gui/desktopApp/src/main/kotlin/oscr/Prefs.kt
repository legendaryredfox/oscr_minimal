// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.util.prefs.Preferences

/** Preferências do usuário entre execuções (idioma, porta, baud, sistema, pasta, tamanho da janela, primeira execução). */
object Prefs {
    private val p: Preferences = Preferences.userRoot().node("oscr_minimal")
    private fun <T> safe(default: T, block: () -> T): T = try { block() } catch (_: Exception) { default }   // sem preferências, o programa segue com os padrões

    var lang: String? get() = safe(null) { p.get("lang", null) }; set(v) = safe(Unit) { if (v == null) p.remove("lang") else p.put("lang", v) }
    var port: String get() = safe("") { p.get("port", "") }; set(v) = safe(Unit) { p.put("port", v) }
    var baud: Int get() = safe(1_000_000) { p.getInt("baud", 1_000_000) }; set(v) = safe(Unit) { p.putInt("baud", v) }
    var system: String get() = safe("SNES") { p.get("system", "SNES") }; set(v) = safe(Unit) { p.put("system", v) }
    var lastDir: String get() = safe("") { p.get("lastDir", "") }; set(v) = safe(Unit) { p.put("lastDir", v) }
    var firstRunDone: Boolean get() = safe(false) { p.getBoolean("firstRunDone", false) }; set(v) = safe(Unit) { p.putBoolean("firstRunDone", v) }
    var saveReport: Boolean get() = safe(true) { p.getBoolean("saveReport", true) }; set(v) = safe(Unit) { p.putBoolean("saveReport", v) }
    /** Bases de dados de jogos (arquivos ou pastas), uma por linha. */
    var dbPaths: List<String> get() = safe(emptyList()) { p.get("dbPaths", "").split("\n").filter { it.isNotEmpty() } }; set(v) = safe(Unit) { p.put("dbPaths", v.joinToString("\n")) }
    var winW: Int get() = safe(1000) { p.getInt("winW", 1000) }; set(v) = safe(Unit) { p.putInt("winW", v) }
    var winH: Int get() = safe(820) { p.getInt("winH", 820) }; set(v) = safe(Unit) { p.putInt("winH", v) }
}
