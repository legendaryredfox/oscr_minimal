// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertTrue

private fun ByteArray.hex() = joinToString(" ") { (it.toInt() and 0xFF).toString(16).uppercase().padStart(2, '0') }
private fun u(v: Int) = v.toLong() and 0xFFFFFFFFL

class ProtocolTest {
    @Test fun crc32Vetores() {
        assertEquals(0xCBF43926L, u(crc32("123456789".encodeToByteArray())))
        assertEquals(0L, u(crc32(ByteArray(0))))
        assertEquals(0xD2F82B80L, u(crc32("OSCR".encodeToByteArray())))
    }

    @Test fun quadroInfoBytesExatos() {
        assertEquals("A5 5A 01 01 00 00 4E D2 3A 98", encodeFrame(Proto.T_INFO, 1).hex())
    }

    @Test fun decodificadorRessincronizaEDescartaCrcRuim() {
        val bad = encodeFrame(Proto.T_DETECT, 6, byteArrayOf(1)).also { it[6] = (it[6].toInt() xor 1).toByte() }
        val good = encodeFrame(Proto.T_INFO, 5)
        val d = FrameDecoder()
        val out = d.feed(byteArrayOf(0, 0xA5.toByte(), 0xFF.toByte()) + bad + good)
        assertEquals(listOf(5), out.map { it.seq })
        assertTrue(d.badFrames >= 1)
    }

    @Test fun decodificadorEmPedacosDeUmByte() {
        val raw = encodeFrame(Proto.T_DETECT, 9, byteArrayOf(1)) + encodeFrame(Proto.T_INFO, 10)
        val d = FrameDecoder()
        val out = raw.flatMap { d.feed(byteArrayOf(it)) }
        assertEquals(listOf(9, 10), out.map { it.seq })
    }

    @Test fun payloadMaximo() {
        val pl = ByteArray(1024) { it.toByte() }
        val f = FrameDecoder().feed(encodeFrame(Proto.T_DATA, 3, pl)).single()
        assertContentEquals(pl, f.payload)
    }

    @Test fun padraoMock() {
        val d = mockData()
        assertEquals(32768, d.size); assertEquals(0, d[0].toInt()); assertEquals(7, d[1].toInt())
    }
}
