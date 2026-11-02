// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

enum class CheckStatus { OK, MISMATCH, NA }

/** Resultado da verificação do checksum do cabeçalho (Mega Drive, SNES, GBA). Igual a host/oscr_host/verify.py. */
data class Check(val status: CheckStatus, val name: String = "", val expected: Int = 0, val computed: Int = 0) {
    fun hex(v: Int) = (v and 0xFFFF).toString(16).uppercase().padStart(4, '0')
}

private fun ByteArray.sumRange(from: Int, to: Int): Long { var s = 0L; for (i in from until to) s += this[i].toLong() and 0xFF; return s }

private fun md(d: ByteArray): Check {
    if (d.size < 0x200 || !(d[0x100] == 'S'.code.toByte() && d[0x101] == 'E'.code.toByte() && d[0x102] == 'G'.code.toByte() && d[0x103] == 'A'.code.toByte())) return Check(CheckStatus.NA)
    val exp = (d.u8(0x18E) shl 8) or d.u8(0x18F)
    var total = 0
    var i = 0x200
    while (i < d.size) { total += (d.u8(i) shl 8) or (if (i + 1 < d.size) d.u8(i + 1) else 0); i += 2 }
    total = total and 0xFFFF
    return Check(if (total == exp) CheckStatus.OK else CheckStatus.MISMATCH, "Mega Drive", exp, total)
}

private fun gba(d: ByteArray): Check {
    if (d.size < 0xC0 || d.u8(4) != 0x24 || d.u8(5) != 0xFF || d.u8(6) != 0xAE || d.u8(7) != 0x51) return Check(CheckStatus.NA)
    val comp = (-(d.sumRange(0xA0, 0xBD).toInt() + 0x19)) and 0xFF
    return Check(if (comp == d.u8(0xBD)) CheckStatus.OK else CheckStatus.MISMATCH, "GBA", d.u8(0xBD), comp)
}

private fun snes(d: ByteArray): Check {
    for (pos in intArrayOf(0x7FC0, 0xFFC0)) {
        if (d.size < pos + 0x20) continue
        val comp = d.u16(pos + 0x1C); val chk = d.u16(pos + 0x1E)
        if (comp xor chk != 0xFFFF || (comp == 0 && chk == 0)) continue
        val n = d.size
        val p = Integer.highestOneBit(n)
        val total: Long = if (p == n) d.sumRange(0, n) else {
            val rest = n - p
            if (p % rest != 0) return Check(CheckStatus.NA)
            d.sumRange(0, p) + d.sumRange(p, n) * (p / rest)
        }
        val t = (total and 0xFFFF).toInt()
        return Check(if (t == chk) CheckStatus.OK else CheckStatus.MISMATCH, "SNES", chk, t)
    }
    return Check(CheckStatus.NA)
}

fun verifyRom(system: CartSystem, data: ByteArray): Check = when (system) {
    CartSystem.MD -> md(data)
    CartSystem.GBA -> gba(data)
    CartSystem.SNES -> snes(data)
    else -> Check(CheckStatus.NA)
}

/** Tipo de save do GBA achado na ROM (mesma numeração do OSCR e do campo "tipo de save"). Igual a gba_save_hint em verify.py. */
data class GbaSaveHint(val type: Int, val label: String, val tag: String)

private val gbaSaveIds = listOf(
    Triple("FLASH1M_V", 5, "Flash 128 KB"),
    Triple("FLASH512_V", 4, "Flash 64 KB"),
    Triple("FLASH_V", 4, "Flash 64 KB"),
    Triple("EEPROM_V", 2, "EEPROM 512 B / 8 KB"),
    Triple("SRAM_F_V", 3, "FRAM 32 KB"),
    Triple("SRAM_V", 3, "SRAM 32 KB"),
)

private fun ByteArray.indexOfAscii(s: String): Int {
    val n = s.length
    outer@ for (i in 0..size - n) {
        for (j in 0 until n) if (this[i + j] != s[j].code.toByte()) continue@outer
        return i
    }
    return -1
}

fun gbaSaveHint(rom: ByteArray): GbaSaveHint? {
    for ((needle, code, label) in gbaSaveIds) {
        val i = rom.indexOfAscii(needle)
        if (i >= 0) {
            var end = i + needle.length
            while (end < rom.size && end - i < 20 && rom[end] in 0x30..0x39) end++
            return GbaSaveHint(code, label, String(CharArray(end - i) { (rom[i + it].toInt() and 0xFF).toChar() }))
        }
    }
    return null
}
