// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.io.File
import kotlin.test.*

/** Igual a host/tests/test_gbrtc.py (a parte sem dispositivo). */
class GbRtcTest {
    @Test fun codigoDoFirmwareBate() {
        val root = generateSequence(File("").absoluteFile) { it.parentFile }.first { File(it, "firmware/oscr/include/dumper/GbAcc.h").exists() }
        val acc = File(root, "firmware/oscr/include/dumper/GbAcc.h").readText()
        assertEquals(GbRtc.MAPPER, Regex("kRtc = (\\d+)").find(acc)!!.groupValues[1].toInt())
        assertEquals(GbRtc.REGS, Regex("kRegs = (\\d+)").find(File(root, "firmware/oscr/include/dumper/GbRtc.h").readText())!!.groupValues[1].toInt())
    }

    @Test fun codificaEDecodifica() {
        val raw = GbRtc.encode(5, 4, 3, 300, halted = true, carry = true)
        assertContentEquals(byteArrayOf(5, 4, 3, (300 and 0xFF).toByte(), (0x01 or 0x40 or 0x80).toByte()), raw)
        assertEquals(GbRtc.Value(5, 4, 3, 300, halted = true, carry = true), GbRtc.decode(raw))
        assertEquals(255, GbRtc.decode(byteArrayOf(-1, -1, -1, -1, 0xFE.toByte())).days)          // bits que o MBC3 não usa são ignorados
        for (bad in listOf(listOf(60, 0, 0, 0), listOf(0, 60, 0, 0), listOf(0, 0, 24, 0), listOf(0, 0, 0, 512)))
            assertFailsWith<IllegalArgumentException> { GbRtc.encode(bad[0], bad[1], bad[2], bad[3]) }
        assertFailsWith<IllegalArgumentException> { GbRtc.decode(ByteArray(4)) }
    }

    @Test fun horaERodape() {
        assertEquals(Triple(7, 5, 0), GbRtc.parseTime("07:05"))
        assertEquals(Triple(23, 59, 58), GbRtc.parseTime("23:59:58"))
        for (bad in listOf("24:00", "12:60", "12", "ab:cd", "1:2:3:4")) assertNull(GbRtc.parseTime(bad), bad)
        val raw = GbRtc.encode(1, 2, 3, 4)
        val f = GbRtc.footer(raw, 1_700_000_000L)
        assertEquals(48, f.size)
        assertContentEquals(f.copyOfRange(0, 20), f.copyOfRange(20, 40))
        assertEquals(1, f[0].toInt()); assertEquals(0, f[1].toInt())
        var ts = 0L; for (i in 7 downTo 0) ts = (ts shl 8) or (f[40 + i].toLong() and 0xFF)
        assertEquals(1_700_000_000L, ts)
        assertContentEquals(raw, GbRtc.fromFooter(f)); assertContentEquals(raw, GbRtc.fromFooter(raw))
        assertFailsWith<IllegalArgumentException> { GbRtc.fromFooter(ByteArray(7)) }
    }

    @Test fun conferencia() {
        val want = GbRtc.decode(GbRtc.encode(10, 0, 0, 1))
        assertTrue(GbRtc.matches(want, GbRtc.decode(GbRtc.encode(12, 0, 0, 1))))
        assertFalse(GbRtc.matches(want, GbRtc.decode(GbRtc.encode(19, 0, 0, 1))))
        assertFalse(GbRtc.matches(want, GbRtc.decode(GbRtc.encode(9, 0, 0, 1))))
        val halted = GbRtc.decode(GbRtc.encode(10, 0, 0, 1, halted = true))
        assertTrue(GbRtc.matches(halted, halted)); assertFalse(GbRtc.matches(halted, GbRtc.decode(GbRtc.encode(11, 0, 0, 1, halted = true))))
    }
}
