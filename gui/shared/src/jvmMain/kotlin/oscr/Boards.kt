// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.io.File
import java.security.MessageDigest

/**
 * Perfis das placas e a decisão "o firmware gravado serve a esta placa?" (D162). Espelha host/oscr_host/boards.py (mesmos nomes, mesmas regras, testado nos dois lados).
 *
 * O usuário escolhe a placa (`16_bits` ou `16_bits@v1.3`); [BoardPlanner.plan] compara o que ela precisa com o que o firmware diz no INFO e devolve o que fazer, sem tocar em nada:
 * `NONE`, `SET_PROFILE` (só gravar o perfil, barato), `FLASH` (grava a menor imagem que cobre a placa; quem chama pede confirmação) ou `UNSUPPORTED`.
 * Regra do usuário (2026-11-14): uma imagem só sempre que couber; hoje existe uma (`completa`).
 */
class BoardException(val kind: String, message: String, val params: Map<String, String>) : Exception(message)

data class BoardProfile(val board: String, val version: String, val slots: List<String>, val systems: Set<Int>, val voltageSelect: Boolean) {
    val label get() = "$board $version"
    val flags get() = if (voltageSelect) Board.VOLT_SELECT else 0
}

class BoardInfo(val board: String, val current: String, val slots: List<String>, val systems: Set<Int>, val versions: Map<String, Boolean>)

class FirmwareImage(val id: String, val hex: File, val firmware: Triple<Int, Int, Int>, val systems: Set<Int>, val sha256: String) {
    val firmwareStr get() = "${firmware.first}.${firmware.second}.${firmware.third}"
}

/** Um motivo sem texto: o código e os parâmetros; a CLI e a GUI traduzem. Códigos: no_response, missing_systems (`systems`), no_board, no_image, not_newer, set_profile. */
data class Reason(val code: String, val params: Map<String, String> = emptyMap())

enum class BoardAction { NONE, SET_PROFILE, FLASH, UNSUPPORTED }

class BoardPlan(val action: BoardAction, val reasons: List<Reason>, val image: FirmwareImage?, val profileFlags: Int)

object BoardPlanner {
    private fun resource(name: String): List<String> =
        BoardPlanner::class.java.classLoader.getResourceAsStream("oscr/$name")?.use { it.readBytes().toString(Charsets.UTF_8) }?.lines()?.filter { it.isNotBlank() && !it.startsWith("#") } ?: emptyList()

    /** Todas as placas, na ordem do arquivo (alfabética). Fonte: `perfis.tsv`, gerado por tools/gen_perfis.py. */
    val boards: List<BoardInfo> by lazy {
        val rows = resource("perfis.tsv").map { it.split('\t') }
        rows.groupBy { it[0] }.map { (name, rs) ->
            BoardInfo(name, rs.first { it[2] == "1" }[1], rs[0][3].split(',').filter { it.isNotEmpty() }, rs[0][4].split(',').filter { it.isNotEmpty() }.map { it.toInt() }.toSet(),
                rs.associate { it[1] to (it[5] == "1") })
        }
    }

    fun names(): List<String> = boards.map { it.board }

    /** `16_bits` (versão atual) ou `16_bits@v1.3` (o "v" é opcional). */
    fun resolve(spec: String): BoardProfile {
        val name = spec.substringBefore('@')
        val b = boards.firstOrNull { it.board == name }
            ?: throw BoardException("unknown_board", "unknown board: $name. Boards: ${names().joinToString(", ")}", mapOf("name" to name, "names" to names().joinToString(", ")))
        var ver = if ('@' in spec) spec.substringAfter('@') else b.current
        if (!ver.startsWith("v")) ver = "v$ver"
        val sel = b.versions[ver] ?: throw BoardException("unknown_version", "unknown version: $name $ver. Versions: ${b.versions.keys.joinToString(", ")}",
            mapOf("name" to name, "version" to ver, "versions" to b.versions.keys.joinToString(", ")))
        return BoardProfile(name, ver, b.slots, b.systems, sel)
    }

    /** Onde procurar o manifest.tsv: a pasta dada vale sozinha; senão OSCR_FIRMWARE_DIR; senão a `firmware/` do instalador; senão `firmware/images` procurada da pasta atual para cima. */
    fun imageDir(explicit: String?): File? {
        (explicit ?: System.getenv("OSCR_FIRMWARE_DIR"))?.let { return File(it.replaceFirst("~", System.getProperty("user.home") ?: "~")) }
        AppResources.firmwareDir()?.let { return it }               // programa instalado: as imagens vêm no instalador (H-7)
        var d: File? = File(".").absoluteFile.normalize()
        while (d != null) { File(d, "firmware/images").takeIf { it.isDirectory }?.let { return it }; d = d.parentFile }
        return null
    }

    /** Imagem sem o `.hex` ao lado, ou com SHA-256 que não bate, é ignorada. */
    fun loadImages(explicit: String? = null): List<FirmwareImage> {
        val dir = imageDir(explicit) ?: return emptyList()
        val mf = File(dir, "manifest.tsv").takeIf { it.isFile } ?: return emptyList()
        return mf.readLines().filter { it.isNotBlank() && !it.startsWith("#") }.mapNotNull { ln ->
            val c = ln.split('\t')
            val hex = File(dir, c[1]).takeIf { it.isFile } ?: return@mapNotNull null
            val sha = MessageDigest.getInstance("SHA-256").digest(hex.readBytes()).joinToString("") { "%02x".format(it) }
            if (sha != c[4]) return@mapNotNull null
            val fw = c[2].split('.').map { it.toInt() }
            FirmwareImage(c[0], hex, Triple(fw[0], fw[1], fw[2]), c[3].split(',').filter { it.isNotEmpty() }.map { it.toInt() }.toSet(), sha)
        }
    }

    private fun cmp(a: Triple<Int, Int, Int>, b: Triple<Int, Int, Int>) = compareValuesBy(a, b, { it.first }, { it.second }, { it.third })

    /** A menor imagem que cobre o que a placa precisa (menos sistemas), a mais nova no empate. */
    fun bestImage(images: List<FirmwareImage>, needed: Set<Int>): FirmwareImage? =
        images.filter { it.systems.containsAll(needed) }.sortedWith { a, b -> if (a.systems.size != b.systems.size) a.systems.size - b.systems.size else cmp(b.firmware, a.firmware) }.firstOrNull()

    private fun fwOf(info: DeviceInfo): Triple<Int, Int, Int> = info.firmware.split('.').let { Triple(it.getOrNull(0)?.toIntOrNull() ?: 0, it.getOrNull(1)?.toIntOrNull() ?: 0, it.getOrNull(2)?.toIntOrNull() ?: 0) }

    private fun systemName(id: Int) = CartSystem.entries.firstOrNull { it.id == id }?.name?.lowercase() ?: id.toString()

    /** Decide o que fazer. `info` é o INFO do firmware gravado (null = não respondeu); `state` é o BOARD_RESP (null se o firmware não tem BOARD). */
    fun plan(profile: BoardProfile, info: DeviceInfo?, state: BoardState?, images: List<FirmwareImage>): BoardPlan {
        val flags = profile.flags
        if (info == null) {
            val img = bestImage(images, profile.systems)
            return if (img == null) BoardPlan(BoardAction.UNSUPPORTED, listOf(Reason("no_response"), Reason("no_image")), null, flags)
            else BoardPlan(BoardAction.FLASH, listOf(Reason("no_response")), img, flags)
        }
        val reasons = mutableListOf<Reason>()
        val missing = (profile.systems - info.systemIds).sorted()
        if (missing.isNotEmpty()) reasons += Reason("missing_systems", mapOf("systems" to missing.joinToString(", ") { systemName(it) }))
        val selectorOk = info.voltageSelect == profile.voltageSelect
        if (!info.boardProfile && !selectorOk) reasons += Reason("no_board")
        if (reasons.isNotEmpty()) {
            val img = bestImage(images, profile.systems) ?: return BoardPlan(BoardAction.UNSUPPORTED, reasons + Reason("no_image"), null, flags)
            if (cmp(img.firmware, fwOf(info)) <= 0 && missing.isEmpty() && info.boardProfile) return BoardPlan(BoardAction.UNSUPPORTED, reasons + Reason("not_newer"), null, flags)
            return BoardPlan(BoardAction.FLASH, reasons, img, flags)
        }
        val stored = state?.stored == true
        if (info.boardProfile && (!stored || !selectorOk)) return BoardPlan(BoardAction.SET_PROFILE, listOf(Reason("set_profile")), null, flags)
        return BoardPlan(BoardAction.NONE, emptyList(), null, flags)
    }
}
