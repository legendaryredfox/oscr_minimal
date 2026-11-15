// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import kotlin.test.*

/** clock-cal (F-3, P-03), igual a host/tests/test_clock.py: quadro CLOCK, fator a partir da medida, comando da CLI com o simulador, firmware antigo e módulo ausente. */
class ClockTest {
    private class Run(val code: Int, val out: String)

    private fun run(vararg argv: String, oldFw: Boolean = false): Run {
        val out = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".", simOldFw = oldFw)
        return Run(Cli.run(argv.toList(), io), out.toString().trim())
    }

    @Test fun quadros() {
        assertContentEquals(byteArrayOf(0), buildClock(Clock.STATUS))
        assertContentEquals(byteArrayOf(1) + le32(-1234), buildClock(Clock.SET, -1234))
        assertFailsWith<IllegalArgumentException> { buildClock(Clock.SET, Clock.MAX_PPB + 1) }
        assertEquals(ClockState(true, true, -5, true), parseClock(byteArrayOf(1, 1) + le32(-5) + byteArrayOf(1)))
        assertFailsWith<ProtocolError> { parseClock(ByteArray(6)) }
    }

    @Test fun fatorAPartirDaMedida() {
        assertEquals(100_000L, clockFactorFromMeasure(4_000_400.0, 4_000_000.0))
        assertEquals(-100_000L, clockFactorFromMeasure(3_999_600.0, 4_000_000.0))
        assertEquals(0L, clockFactorFromMeasure(4_000_000.0, 4_000_000.0))
        assertEquals(100_000L, clockFactorFromMeasure(1_000_100.0, 1_000_000.0))
        assertEquals(Math.round((1.0001 * 1.0001 - 1) * 1e9), clockFactorFromMeasure(4_000_400.0, 4_000_000.0, 100_000))
        assertFailsWith<IllegalArgumentException> { clockFactorFromMeasure(0.0, 4_000_000.0) }
    }

    @Test fun clienteESimulador() {
        val dev = SimDevice()
        val c = OscrClient(dev, 500, 5000)
        assertEquals(ClockState(true, false, 0, false), c.clock())
        assertEquals(-250, c.clock(Clock.SET, -250).ppb)
        assertTrue(c.clock(Clock.TEST_ON).test)
        assertFalse(c.clock(Clock.TEST_OFF).test)
        assertTrue(c.clock().stored)
        assertEquals(listOf(0 to 0, 1 to -250, 2 to 0, 3 to 0, 0 to 0), dev.clockCalls)
    }

    @Test fun moduloAusente() {
        val c = OscrClient(SimDevice(clockPresent = false), 500, 5000)
        assertFalse(c.clock().present)
        assertEquals(7, assertFailsWith<DeviceError> { c.clock(Clock.SET, 10) }.code)
    }

    @Test fun cliConsultaNaoMudaNada() {
        val r = run("--simulate", "--json", "clock-cal")
        assertEquals(0, r.code)
        assertTrue("\"present\":true" in r.out && "\"stored\":false" in r.out && "\"factor_ppb\":0" in r.out && "\"applied\":false" in r.out, r.out)
        assertTrue("4000000" in r.out && "3072000" in r.out && "1000000" in r.out)
    }

    @Test fun cliAplicaAMedida() {
        var r = run("--simulate", "--json", "clock-cal", "--measured", "4000400")
        assertTrue("\"applied\":true" in r.out && "\"factor_ppb\":100000" in r.out, r.out)
        r = run("--simulate", "--json", "clock-cal", "--measured", "1000100", "--target", "1000000")
        assertTrue("\"factor_ppb\":100000" in r.out, r.out)
        r = run("--simulate", "--json", "clock-cal", "--factor", "-42", "--test", "on")
        assertTrue("\"factor_ppb\":-42" in r.out && "\"test\":true" in r.out, r.out)
    }

    @Test fun cliArgumentosInvalidos() {
        for (argv in listOf(listOf("--factor", "1", "--measured", "4000000"), listOf("--factor", "2000000"), listOf("--measured", "0"), listOf("--measured", "5000000"), listOf("--test", "x")))
            assertEquals(64, run("--simulate", "--json", "clock-cal", *argv.toTypedArray()).code, argv.toString())
    }

    @Test fun cliFirmwareAntigo() {
        val r = run("--simulate", "--json", "clock-cal", oldFw = true)
        assertEquals(1, r.code); assertTrue("\"kind\":\"no_clock\"" in r.out, r.out)
    }
}
