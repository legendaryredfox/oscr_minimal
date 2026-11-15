// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Conversão mecânica da ordem de bytes de um save, para abrir em emulador (H-1, D163). Espelho de host/oscr_host/saveconv.py.
 * Não diz qual emulador espera qual ordem: isso não foi conferido com emulador nenhum.
 */
object SaveConv {
    val OPS = listOf("swap16", "swap32", "md-expand-odd", "md-expand-even", "md-compact-odd", "md-compact-even")

    /** Inverte os bytes de cada palavra de [width] (2 ou 4) bytes; o tamanho precisa ser múltiplo de [width]. */
    fun swap(data: ByteArray, width: Int): ByteArray {
        require(width == 2 || width == 4) { "width" }
        require(data.size % width == 0) { "size" }
        val out = ByteArray(data.size)
        for (i in data.indices) { val w = i - i % width; out[i] = data[w + width - 1 - i % width] }
        return out
    }

    /** Cada byte vira uma palavra de 16 bits: o byte útil no endereço ímpar ([odd]) ou par, [fill] no outro. */
    fun mdExpand(data: ByteArray, odd: Boolean, fill: Int = 0xFF): ByteArray {
        require(fill in 0..255) { "fill" }
        val out = ByteArray(data.size * 2) { fill.toByte() }
        for (i in data.indices) out[2 * i + (if (odd) 1 else 0)] = data[i]
        return out
    }

    /** Fica só com os bytes dos endereços ímpares ([odd]) ou pares; o tamanho precisa ser par. */
    fun mdCompact(data: ByteArray, odd: Boolean): ByteArray {
        require(data.size % 2 == 0) { "size" }
        return ByteArray(data.size / 2) { data[2 * it + (if (odd) 1 else 0)] }
    }

    fun convert(data: ByteArray, op: String, fill: Int = 0xFF): ByteArray = when (op) {
        "swap16" -> swap(data, 2)
        "swap32" -> swap(data, 4)
        "md-expand-odd", "md-expand-even" -> mdExpand(data, op.endsWith("odd"), fill)
        "md-compact-odd", "md-compact-even" -> mdCompact(data, op.endsWith("odd"))
        else -> throw IllegalArgumentException("op")
    }
}
