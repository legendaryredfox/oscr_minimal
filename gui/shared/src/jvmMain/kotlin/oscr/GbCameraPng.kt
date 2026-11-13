// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.io.ByteArrayOutputStream
import java.io.DataOutputStream
import java.util.zip.CRC32
import java.util.zip.Deflater

/** PNG indexado (4 cores) com ampliação inteira. Igual a gbcamera.png de host/oscr_host/gbcamera.py. */
object GbCameraPng {
    fun encode(pixels: ByteArray, width: Int, height: Int, palette: String = "gray", scale: Int = 1): ByteArray {
        val pal = GbCamera.PALETTES.getValue(palette)
        val rows = ByteArrayOutputStream()
        for (y in 0 until height) {
            val row = ByteArray(1 + width * scale)
            for (x in 0 until width) for (k in 0 until scale) row[1 + x * scale + k] = pixels[y * width + x]
            repeat(scale) { rows.write(row) }
        }
        val out = ByteArrayOutputStream()
        out.write(byteArrayOf(0x89.toByte(), 'P'.code.toByte(), 'N'.code.toByte(), 'G'.code.toByte(), 13, 10, 26, 10))
        fun chunk(tag: String, body: ByteArray) {
            val d = DataOutputStream(out); d.writeInt(body.size)
            val t = tag.toByteArray(Charsets.ISO_8859_1); d.write(t); d.write(body)
            d.writeInt(CRC32().also { it.update(t); it.update(body) }.value.toInt())
        }
        val ihdr = ByteArrayOutputStream().also { DataOutputStream(it).apply { writeInt(width * scale); writeInt(height * scale); write(byteArrayOf(8, 3, 0, 0, 0)) } }
        chunk("IHDR", ihdr.toByteArray())
        chunk("PLTE", ByteArray(12) { ((pal[it / 3] shr (16 - 8 * (it % 3))) and 0xFF).toByte() })
        val def = Deflater(9); def.setInput(rows.toByteArray()); def.finish()
        val z = ByteArrayOutputStream(); val buf = ByteArray(8192)
        while (!def.finished()) z.write(buf, 0, def.deflate(buf))
        chunk("IDAT", z.toByteArray()); chunk("IEND", ByteArray(0))
        return out.toByteArray()
    }
}
