// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Identificação do jogo no PC por CRC32. Igual a host/oscr_host/database.py (a leitura dos arquivos fica em jvmMain/DatabaseLoader.kt).
 * Formatos: No-Intro/Redump (Logiqx XML) e NES 2.0 XML (traz mapper, submapper e tamanhos de PRG, CHR e RAM).
 */
data class DbEntry(
    val name: String,
    val crc: Int,                      // CRC32 do que a base descreve
    val size: Long = 0,
    val source: String = "",
    val kind: String = "logiqx",       // "logiqx" ou "nes20"
    val prgCrc: Int? = null,
    val chrCrc: Int? = null,
    val mapper: Int? = null,
    val submapper: Int? = null,
    val prgKb: Int? = null,
    val chrKb: Int? = null,
    val ramKb: Int? = null,
    val battery: Boolean = false,
) {
    /** Opções do NES/Famicom (mapper, PRG, CHR, RAM em KB), ou null se a base não traz mapper e tamanhos. */
    fun nesOptions(): NesOptions? =
        if (mapper == null || (prgKb ?: 0) == 0) null else NesOptions(mapper, prgKb!!, chrKb ?: 0, ramKb ?: 0)
}

data class NesOptions(val mapper: Int, val prgKb: Int, val chrKb: Int, val ramKb: Int)

data class DbMatch(val entry: DbEntry, val how: How, val others: Int = 0) {
    enum class How { CRC32, CRC32_NO_HEADER, CRC32_PRG_CHR }
}

class Database {
    val entries = ArrayList<DbEntry>()
    private val byCrc = HashMap<Int, MutableList<DbEntry>>()
    private val byPrg = HashMap<Int, MutableList<DbEntry>>()
    val files = ArrayList<String>()
    val size get() = entries.size

    /** Já há entrada com esse CRC32? (a base JSON do OSCR só acrescenta o que falta, D127) */
    fun has(crc: Int) = byCrc.containsKey(crc)

    fun add(e: DbEntry) {
        entries += e
        byCrc.getOrPut(e.crc) { ArrayList() } += e
        e.prgCrc?.let { byPrg.getOrPut(it) { ArrayList() } += e }
    }

    /** Acha o jogo pelo CRC32 do arquivo. No NES/Famicom tenta também sem o cabeçalho iNES e pelos CRC32 da PRG e da CHR. */
    fun identify(system: CartSystem, data: ByteArray): DbMatch? {
        byCrc[crc32(data)]?.let { return DbMatch(it[0], DbMatch.How.CRC32, it.size - 1) }
        if ((system == CartSystem.NES || system == CartSystem.FAMICOM) && data.size > 16 &&
            data[0] == 'N'.code.toByte() && data[1] == 'E'.code.toByte() && data[2] == 'S'.code.toByte() && data[3] == 0x1A.toByte()) {
            byCrc[crc32(data, 16, data.size - 16)]?.let { return DbMatch(it[0], DbMatch.How.CRC32_NO_HEADER, it.size - 1) }
            val prgLen = data.u8(4) * 16384; val chrLen = data.u8(5) * 8192
            if (prgLen > 0 && 16 + prgLen + chrLen <= data.size) {
                val chrCrc = if (chrLen > 0) crc32(data, 16 + prgLen, chrLen) else null
                val c = byPrg[crc32(data, 16, prgLen)]?.filter { it.chrCrc == chrCrc }.orEmpty()
                if (c.isNotEmpty()) return DbMatch(c[0], DbMatch.How.CRC32_PRG_CHR, c.size - 1)
            }
        }
        return null
    }

    /** Entradas cujo nome contém todas as palavras de [text] (sem diferenciar maiúsculas). */
    fun search(text: String, limit: Int = 20): List<DbEntry> {
        val words = text.lowercase().split(Regex("\\s+")).filter { it.isNotEmpty() }
        val out = ArrayList<DbEntry>()
        for (e in entries) {
            val n = e.name.lowercase()
            if (words.all { it in n }) { out += e; if (out.size >= limit) break }
        }
        return out
    }

    /** Só os jogos da base NES 2.0 (com mapper e tamanhos), para o seletor de jogo do NES/Famicom. */
    fun searchNes(text: String, limit: Int = 20): List<DbEntry> {
        val words = text.lowercase().split(Regex("\\s+")).filter { it.isNotEmpty() }
        val out = ArrayList<DbEntry>()
        for (e in entries) {
            if (e.nesOptions() == null) continue
            val n = e.name.lowercase()
            if (words.all { it in n }) { out += e; if (out.size >= limit) break }
        }
        return out
    }
}
