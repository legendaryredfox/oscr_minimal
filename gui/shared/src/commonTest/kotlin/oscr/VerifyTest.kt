// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.test.Test
import kotlin.test.assertEquals

private fun rom(n: Int, seed: Int = 1): ByteArray { var x = seed; return ByteArray(n) { x = (x * 1103515245 + 12345) and 0x7FFFFFFF; (x shr 16).toByte() } }

class VerifyTest {
    @Test fun megaDriveOkEMismatch() {
        val d = rom(0x40000); "SEGA".encodeToByteArray().copyInto(d, 0x100)
        var t = 0; var i = 0x200
        while (i < d.size) { t += (d.u8(i) shl 8) or d.u8(i + 1); i += 2 }
        t = t and 0xFFFF; d[0x18E] = (t shr 8).toByte(); d[0x18F] = t.toByte()
        assertEquals(CheckStatus.OK, verifyRom(CartSystem.MD, d).status)
        d[0x300] = (d[0x300].toInt() xor 1).toByte()
        assertEquals(CheckStatus.MISMATCH, verifyRom(CartSystem.MD, d).status)
    }

    @Test fun gbaComplemento() {
        val d = rom(0x1000, 2); byteArrayOf(0x24, 0xFF.toByte(), 0xAE.toByte(), 0x51).copyInto(d, 4)
        var s = 0x19; for (i in 0xA0 until 0xBD) s += d.u8(i)
        d[0xBD] = (-s).toByte()
        assertEquals(CheckStatus.OK, verifyRom(CartSystem.GBA, d).status)
        d[0xA2] = (d[0xA2].toInt() xor 0xFF).toByte()
        assertEquals(CheckStatus.MISMATCH, verifyRom(CartSystem.GBA, d).status)
    }

    @Test fun snesPotenciaDe2() {
        val d = rom(0x80000, 3); val pos = 0x7FC0
        byteArrayOf(-1, -1, 0, 0).copyInto(d, pos + 0x1C)
        var s = 0L; for (b in d) s += b.toLong() and 0xFF
        val t = (s and 0xFFFF).toInt()
        d[pos + 0x1E] = t.toByte(); d[pos + 0x1F] = (t shr 8).toByte()
        d[pos + 0x1C] = (t xor 0xFFFF).toByte(); d[pos + 0x1D] = ((t xor 0xFFFF) shr 8).toByte()
        assertEquals(CheckStatus.OK, verifyRom(CartSystem.SNES, d).status)
        d[0x1000] = (d[0x1000].toInt() xor 1).toByte()
        assertEquals(CheckStatus.MISMATCH, verifyRom(CartSystem.SNES, d).status)
    }

    @Test fun semCabecalhoOuSemChecksum() {
        assertEquals(CheckStatus.NA, verifyRom(CartSystem.SNES, rom(0x80000, 5)).status)
        assertEquals(CheckStatus.NA, verifyRom(CartSystem.NES, rom(0x8000, 6)).status)
        assertEquals(CheckStatus.NA, verifyRom(CartSystem.MD, ByteArray(100)).status)
    }
}
