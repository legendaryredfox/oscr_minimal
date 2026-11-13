// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.security.MessageDigest

/**
 * Tipo e tamanho do save de um jogo de GBA pelo cabeçalho da ROM (D160, P2). Igual a host/oscr_host/gba_db.py: base `flashgbx/gba.tsv` (do FlashGBX, GPL-3.0), chave = SHA-1 dos
 * primeiros 0x180 bytes do cabeçalho; numeração do OSCR (0 nenhum, 1 EEPROM 512 B, 2 EEPROM 8 KB, 3 SRAM 32 KB, 4 Flash 64 KB, 5 Flash 128 KB, 6 Flash 1 MB). Só sugere.
 */
object GbaSaveDb {
    data class Game(val name: String, val crc32: Long, val romSize: Long, val saveType: Int, val saveSize: Long) {
        val label: String get() = SAVE_LABEL[saveType] ?: "?"
    }

    val SAVE_LABEL = mapOf(0 to "none", 1 to "EEPROM 512 B", 2 to "EEPROM 8 KB", 3 to "SRAM 32 KB", 4 to "Flash 64 KB", 5 to "Flash 128 KB", 6 to "Flash 1 MB")

    val games: Map<String, Game> by lazy {
        val text = GbaSaveDb::class.java.classLoader.getResourceAsStream("flashgbx/gba.tsv")?.use { it.readBytes().toString(Charsets.UTF_8) } ?: return@lazy emptyMap()
        parse(text)
    }

    fun parse(text: String): Map<String, Game> {
        val out = HashMap<String, Game>()
        for (line in text.lineSequence()) {
            if (line.isEmpty() || line.startsWith("#")) continue
            val f = line.split('\t')
            if (f.size < 6) continue
            val crc = f[1].toLongOrNull(16) ?: continue
            out[f[0].uppercase()] = Game(f[5], crc, f[2].toLongOrNull() ?: continue, f[3].toIntOrNull() ?: continue, f[4].toLongOrNull() ?: continue)
        }
        return out
    }

    /** SHA-1 do cabeçalho como o FlashGBX calcula: 0x0A a 0x180 se o título é "YJencrypted"; 0x00 a 0x100 se o código do jogo começa com "M"; senão 0x00 a 0x180. */
    fun headerSha1(rom: ByteArray): String? {
        if (rom.size < 0x180) return null
        val title = rom.copyOfRange(0xA0, 0xAC).let { t -> var n = t.size; while (n > 0 && (t[n - 1].toInt() == 0 || t[n - 1].toInt() == 0x20)) n--; String(t, 0, n, Charsets.ISO_8859_1) }
        val (from, to) = if (title == "YJencrypted") 0x0A to 0x180 else if (rom[0xAC].toInt() == 'M'.code) 0 to 0x100 else 0 to 0x180
        return MessageDigest.getInstance("SHA-1").digest(rom.copyOfRange(from, to)).joinToString("") { "%02X".format(it) }
    }

    fun lookup(rom: ByteArray, db: Map<String, Game> = games): Game? = headerSha1(rom)?.let { db[it] }
}
