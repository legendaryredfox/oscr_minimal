// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Nintendo 64 (D158): o que o PC faz no lugar do cartão SD do OSCR. Igual a host/oscr_host/n64.py e a firmware/oscr/include/dumper/N64Core.h.
 * O `DETECT` devolve "CCCCCCCC IIII TÍTULO" (CRC1 do cabeçalho, código do jogo e nome); o tamanho da ROM (MB) e o tipo de save vêm da base do projeto
 * (database/oscr/json/n64.json, pelo CRC1) ou do que o usuário informar. A leitura do arquivo da base fica em jvmMain/N64Games.kt.
 */
object N64 {
    const val MIN_MB = 1
    const val MAX_MB = 64
    val COMMON_MB = listOf(4, 8, 12, 16, 24, 32, 40, 48, 64)

    /** Tipos de save do OSCR (campo `mapper` do protocolo) e os bytes do arquivo de save de cada um. */
    val SAVE_BYTES = mapOf(0 to 0L, 1 to 32768L, 2 to 98304L, 4 to 131072L, 5 to 512L, 6 to 2048L)
    val SAVE_LABEL = mapOf(0 to "none", 1 to "SRAM 32 KB", 2 to "SRAM 96 KB", 4 to "FlashRAM 128 KB", 5 to "EEPROM 4 Kbit", 6 to "EEPROM 16 Kbit")

    data class Header(val crc1: Long?, val gameId: String, val title: String)
    data class Game(val name: String, val crc1: Long, val crc32: Long, val sizeMb: Int, val saveType: Int) {
        val saveBytes: Long get() = SAVE_BYTES[saveType] ?: 0L
    }

    /** O que a base diz de um cartucho detectado. `game` é a primeira entrada com o CRC1; `others` as demais; `ambiguous` se pedem tamanho ou save diferentes. */
    data class Info(val header: Header, val game: Game?, val others: Int, val ambiguous: Boolean) {
        val crc1Hex: String? get() = header.crc1?.let { hex8(it) }
    }

    private val HEADER = Regex("""^([0-9A-Fa-f]{8}) (.{4}) ?(.*)$""")

    fun parseDetectName(name: String): Header {
        val m = HEADER.find(name) ?: return Header(null, "", name.trim())
        return Header(m.groupValues[1].toLong(16), m.groupValues[2], m.groupValues[3].trim().replace('_', ' '))
    }

    fun info(detect: DetectResult, games: Map<Long, List<Game>>): Info {
        val h = parseDetectName(detect.name)
        val list = h.crc1?.let { games[it] }.orEmpty()
        return Info(h, list.firstOrNull(), maxOf(0, list.size - 1), list.map { it.sizeMb to it.saveType }.toSet().size > 1)
    }

    fun sizeValid(mb: Int) = mb in MIN_MB..MAX_MB
    fun saveTypeValid(t: Int) = t in SAVE_BYTES
    private fun hex8(v: Long) = v.toString(16).uppercase().padStart(8, '0')
}
