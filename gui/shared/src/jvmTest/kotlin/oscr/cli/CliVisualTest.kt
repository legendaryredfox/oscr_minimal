package oscr.cli

import kotlin.test.*

/** Camada visual da CLI (Ui): igual a host/tests/test_cli_visual.py. */
class CliVisualTest {
    private val ansi = Regex("\u001b\\[[0-9;]*[A-Za-z]")

    private fun run(vararg argv: String, tty: Boolean = false): Triple<Int, String, String> {
        val out = StringBuilder(); val err = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { err.appendLine(it) }, false, tty, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".", stdoutTty = tty)
        return Triple(Cli.run(argv.toList(), io), out.toString(), err.toString())
    }

    @Test fun saidaRedirecionadaNaoTemEnfeite() {
        val (code, out, _) = run("--simulate", "detect", "-s", "mock")
        assertEquals(0, code); assertFalse(ansi.containsMatchIn(out)); assertTrue("cartridge detected" in out)
    }

    @Test fun terminalDesenhaOCartucho() {
        val (code, out, _) = run("--simulate", "detect", "-s", "mock", tty = true)
        val plain = ansi.replace(out, "")
        assertEquals(0, code); assertTrue(ansi.containsMatchIn(out)); assertTrue("S N E S" in plain && "cartridge detected" in plain && "32768 bytes" in plain)
    }

    @Test fun jsonNuncaTemEnfeite() {
        val (code, out, _) = run("--color", "always", "--simulate", "--json", "detect", "-s", "mock", tty = true)
        assertEquals(0, code); assertFalse(ansi.containsMatchIn(out)); assertTrue(out.trim().startsWith("{"))
    }

    @Test fun colorNeverEAlways() {
        assertFalse(ansi.containsMatchIn(run("--color", "never", "--simulate", "detect", "-s", "mock", tty = true).second))
        assertTrue(ansi.containsMatchIn(run("--color", "always", "--simulate", "detect", "-s", "mock").second))
        assertEquals(64, run("--color", "roxo", "--simulate", "detect", "-s", "mock").first)
    }

    @Test fun arteAlinhadaELogo() {
        for (k in 1..6) { val rows = Ui.cartridge(false, k); assertEquals(1, rows.map { it.length }.toSet().size, "arte $k"); assertTrue(rows.size >= 6) }
        assertEquals(5, Ui.logo().size); assertEquals(1, Ui.logo().map { it.length }.toSet().size)
    }

    @Test fun barraEDecorate() {
        assertEquals(12, Ui.bar(false, 0.5, 10).length)
        assertEquals(Ui.bar(false, 1.0, 4), Ui.bar(false, 2.0, 4))
        val line = "ROM written: NES Maker  CRC32 DEADBEEF  OK"
        assertTrue(ansi.replace(Ui.decorate(true, line), "").endsWith(line)); assertEquals(line, Ui.decorate(false, line))
    }

    @Test fun erroColoridoEmStderr() {
        val (code, _, err) = run("--color", "always", "--simulate", "save-write", "-s", "mock", "-i", "/nao/existe", "--yes")
        assertEquals(1, code); assertTrue("error:" in ansi.replace(err, ""))
    }
}
