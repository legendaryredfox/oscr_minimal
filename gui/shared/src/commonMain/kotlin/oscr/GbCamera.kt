// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Fotos do Game Boy Camera a partir de um save de 128 KB (D160, P9; formato de FlashGBX/PocketCamera.py). Igual a host/oscr_host/gbcamera.py:
 * 30 fotos de 128 x 112 pixels em 2 bits (16 x 14 tiles), a foto n em 0x2000 + n * 0x1000; "cara do jogo" em 0x11FC; última imagem (128 x 123) em 0x0000;
 * ordem do álbum em 0x11D7 (30 bytes; 0xFF ou repetido = apagada). O PNG é escrito em jvmMain/GbCameraPng.kt.
 */
object GbCamera {
    const val SAVE_BYTES = 128 * 1024
    const val W = 128
    const val H = 112
    const val H_LAST = 123

    /** Paletas RGB, índice 0 = mais claro. */
    val PALETTES = mapOf(
        "gray" to listOf(0xFFFFFF, 0xAAAAAA, 0x555555, 0x000000),
        "green" to listOf(0x9BBC0F, 0x8BAC0F, 0x306230, 0x0F380F),
        "gbc" to listOf(0xF0F0F0, 0xDAC46A, 0x705834, 0x1E1E1E),
    )

    class Photo(val name: String, val pixels: ByteArray, val width: Int, val height: Int, val deleted: Boolean = false, val empty: Boolean = false)

    /** (blocos na ordem do álbum, blocos apagados): apagados vão para o fim, como no FlashGBX. */
    fun albumOrder(data: ByteArray): Pair<List<Int>, Set<Int>> {
        val order = arrayOfNulls<Int>(30)
        val deleted = ArrayList<Int>(); val seen = ArrayList<Int>()
        for (i in 0 until 30) {
            val v = data[0x11D7 + i].toInt() and 0xFF
            if (v == 0xFF || v in seen || v >= 30) deleted += i else order[v] = i
            seen += v
        }
        return (order.filterNotNull() + deleted) to deleted.toSet()
    }

    fun decode(buf: ByteArray, from: Int, tilesHigh: Int = 14): ByteArray {
        val out = ByteArray(W * tilesHigh * 8)
        for (th in 0 until tilesHigh) for (tw in 0 until 16) {
            val pos = from + 16 * (th * 16 + tw)
            if (pos + 16 > buf.size) continue
            for (i in 0 until 8) {
                val lo = buf[pos + i * 2].toInt(); val hi = buf[pos + i * 2 + 1].toInt()
                for (j in 0 until 8) out[(th * 8 + i) * W + tw * 8 + j] = ((((hi shr (7 - j)) and 1) shl 1) or ((lo shr (7 - j)) and 1)).toByte()
            }
        }
        return out
    }

    fun extract(data: ByteArray): List<Photo> {
        require(data.size == SAVE_BYTES) { "the Game Boy Camera save is $SAVE_BYTES bytes, this one is ${data.size}" }
        val (order, deleted) = albumOrder(data)
        val out = ArrayList<Photo>()
        for (pos in 0 until 30) {
            val block = order[pos]; val off = 0x2000 + block * 0x1000
            val empty = (off until off + 0x1000).all { data[it] == data[off] }
            out += Photo("photo_%02d".format(pos + 1), decode(data, off), W, H, block in deleted, empty)
        }
        out += Photo("game_face", decode(data, 0x11FC), W, H)
        out += Photo("last_seen", decode(data, 0, 16).copyOf(W * H_LAST), W, H_LAST)
        return out
    }
}
