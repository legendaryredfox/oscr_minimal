// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Relógio (RTC) do MBC3 do Game Boy (F-17, D192). O firmware manda e recebe 5 bytes, na ordem dos registradores 08h a 0Ch do MBC3: segundos, minutos, horas,
 * dias (byte baixo) e dias (byte alto: bit 0 = bit 8 dos dias, bit 6 = parado, bit 7 = estouro). Igual a host/oscr_host/gbrtc.py. O rodapé de 48 bytes é o
 * que BGB, VBA-M e mGBA põem depois do save (5 registradores ao vivo e 5 travados, 4 bytes cada, mais a hora do PC em segundos Unix, 8 bytes).
 */
object GbRtc {
    const val REGS = 5
    const val MAPPER = 7                                  // GbAcc::kRtc do firmware
    const val HALT = 0x40
    const val CARRY = 0x80
    const val FOOTER_BYTES = 48
    const val MAX_DAY = 511

    data class Value(val seconds: Int, val minutes: Int, val hours: Int, val days: Int, val halted: Boolean, val carry: Boolean) {
        /** Total em segundos, para comparar duas leituras. */
        val total: Long get() = ((days * 24L + hours) * 60 + minutes) * 60 + seconds
        fun text(): String = "%d %02d:%02d:%02d".format(days, hours, minutes, seconds)
    }

    fun decode(raw: ByteArray): Value {
        require(raw.size == REGS) { "o RTC tem $REGS bytes, vieram ${raw.size}" }
        val b = IntArray(REGS) { raw[it].toInt() and 0xFF }
        return Value(b[0] and 0x3F, b[1] and 0x3F, b[2] and 0x1F, ((b[4] and 1) shl 8) or b[3], (b[4] and HALT) != 0, (b[4] and CARRY) != 0)
    }

    fun encode(seconds: Int, minutes: Int, hours: Int, days: Int, halted: Boolean = false, carry: Boolean = false): ByteArray {
        require(seconds in 0..59 && minutes in 0..59 && hours in 0..23 && days in 0..MAX_DAY) { "hora ou dia fora da faixa" }
        return byteArrayOf(seconds.toByte(), minutes.toByte(), hours.toByte(), (days and 0xFF).toByte(),
            ((days shr 8) or (if (halted) HALT else 0) or (if (carry) CARRY else 0)).toByte())
    }

    /** `HH:MM` ou `HH:MM:SS`; null se inválida. */
    fun parseTime(text: String): Triple<Int, Int, Int>? {
        val n = text.trim().split(":").map { it.toIntOrNull() ?: return null }
        val t = when (n.size) { 2 -> listOf(n[0], n[1], 0); 3 -> n; else -> return null }
        return if (t[0] in 0..23 && t[1] in 0..59 && t[2] in 0..59) Triple(t[0], t[1], t[2]) else null
    }

    fun footer(raw: ByteArray, nowSeconds: Long): ByteArray {
        require(raw.size == REGS) { "o RTC tem $REGS bytes, vieram ${raw.size}" }
        val out = ByteArray(FOOTER_BYTES)
        for (copy in 0..1) for (i in 0 until REGS) out[copy * 20 + i * 4] = raw[i]
        for (i in 0..7) out[40 + i] = (nowSeconds shr (8 * i)).toByte()
        return out
    }

    /** Os 5 registradores ao vivo de um rodapé de 48 bytes (ou de um arquivo de 5 bytes). */
    fun fromFooter(data: ByteArray): ByteArray {
        if (data.size == REGS) return data.copyOf()
        require(data.size == FOOTER_BYTES) { "o rodapé do RTC tem $FOOTER_BYTES bytes, vieram ${data.size}" }
        return ByteArray(REGS) { data[it * 4] }
    }

    /** Os 5 registradores de um arquivo: 5 bytes, rodapé de 48 bytes ou .sav com o rodapé no fim (tamanho múltiplo de 1024 mais 48). */
    fun fromFile(data: ByteArray): ByteArray =
        fromFooter(if (data.size > FOOTER_BYTES && data.size % 1024 == FOOTER_BYTES) data.copyOfRange(data.size - FOOTER_BYTES, data.size) else data)

    /** Conferência depois de gravar: parado tem que ser igual; andando aceita até 2 s a mais (o relógio anda). */
    fun matches(want: Value, got: Value): Boolean =
        got.halted == want.halted && got.carry == want.carry && (if (want.halted) got.total == want.total else got.total - want.total in 0..2)
}
