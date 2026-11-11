package oscr.cli

import oscr.*
import kotlin.test.*

/** Autoteste da placa sem cartucho (P-12). Igual a host/tests/test_selftest.py. */
class SelftestTest {
    private fun run(vararg argv: String, simSelftest: Boolean = false): Triple<Int, String, String> {
        val out = StringBuilder(); val err = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { err.appendLine(it) }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".",
            simSelftest = simSelftest)
        return Triple(Cli.run(argv.toList(), io), out.toString().trim(), err.toString())
    }

    @Test fun nomeDosPinos() {
        assertEquals("D22", pinName(22)); assertEquals("D53", pinName(53)); assertEquals("A0", pinName(54)); assertEquals("A15", pinName(69))
    }

    @Test fun parseDaResposta() {
        assertEquals(SelfTestResult(true, false, emptyList()), parseSelfTest(byteArrayOf(0, 0)))
        val r = parseSelfTest(byteArrayOf(0, 3, 1, 30, 0, 2, 22, 57, 3, 7, 0))
        assertFalse(r.ok)
        assertEquals(listOf(SelfTestFinding("gnd", listOf("D30")), SelfTestFinding("pair", listOf("D22", "A3")), SelfTestFinding("pullup", listOf("D7"))), r.findings)
        val t = parseSelfTest(byteArrayOf(1, 1, 4, 0, 0))
        assertTrue(t.truncated); assertEquals(listOf(SelfTestFinding("clockgen", emptyList())), t.findings)
        assertEquals("unknown99", parseSelfTest(byteArrayOf(0, 1, 99, 5, 6)).findings[0].kind)
        assertFailsWith<ProtocolError> { parseSelfTest(byteArrayOf(0, 2, 1, 2)) }
        assertFailsWith<ProtocolError> { parseSelfTest(ByteArray(0)) }
    }

    @Test fun infoAnunciaOAutoteste() {
        val dev = SimDevice(); val c = OscrClient(dev, 500, 5000)
        assertTrue(c.info().selftest)
        assertEquals(SelfTestResult(true, false, emptyList()), c.selftest()); assertEquals(1, dev.selftestCalls)
    }

    @Test fun simuladorCortaEm24Achados() {
        val dev = SimDevice(selftestReport = List(30) { Triple(1, 22 + it % 10, 0) })
        val r = OscrClient(dev, 500, 5000).selftest()
        assertTrue(r.truncated); assertEquals(24, r.findings.size); assertFalse(r.ok)
    }

    @Test fun cliSemProblema() {
        val (code, out, _) = run("--simulate", "--json", "selftest")
        assertEquals(0, code); assertTrue("\"ok\":true" in out); assertTrue("\"findings\":[]" in out)
    }

    @Test fun cliComProblemasSaiCom1() {
        val (code, out, err) = run("--simulate", "--json", "selftest", simSelftest = true)
        assertEquals(1, code); assertTrue("\"ok\":false" in out); assertTrue("\"D30\"" in out); assertTrue("\"A3\"" in out)
        val (c2, o2, e2) = run("--simulate", "--lang", "pt-BR", "selftest", simSelftest = true)
        assertEquals(1, c2); assertTrue("pino D30 em curto com GND" in o2); assertTrue("pinos D22 e A3 em curto entre si" in o2); assertTrue("2 problema(s)" in o2)
        assertTrue("45 s" in e2)                                                           // o aviso de espera vai para o stderr
        val (_, o3, _) = run("--simulate", "--lang", "en", "selftest", simSelftest = true)
        assertTrue("pin D30 is shorted to GND" in o3); assertTrue("pins D22 and A3 are shorted together" in o3)
    }
}
