// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import kotlin.test.*

/** Baud do fallback (H-3, P-14), igual a host/tests/test_baud.py: 1.000.000, 500.000 e 115.200, nessa ordem; --baud fixa um só. */
class BaudTest {
    private class Mudo : Transport {
        override fun write(data: ByteArray) {}
        override fun read(max: Int, timeoutMs: Long): ByteArray { Thread.sleep(minOf(timeoutMs, 10)); return ByteArray(0) }
    }

    private fun run(vararg argv: String): Pair<List<Int>, String> {
        val abertas = mutableListOf<Int>(); val out = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { }, false, false, { null }, { emptyList() }, { _, b -> abertas += b; Mudo() }, ".")
        Cli.run(argv.toList(), io)
        return abertas to out.toString()
    }

    @Test fun ordemDosBauds() = assertEquals(listOf(1_000_000, 500_000, 115_200), Proto.BAUDS)

    @Test fun tentaOsTresELista() {
        val (abertas, out) = run("--port", "/dev/falsa", "--json", "info")
        assertEquals(listOf(1_000_000, 500_000, 115_200), abertas)
        assertTrue("1000000, 500000, 115200" in out, out)
    }

    @Test fun baudFixoTentaSoUm() = assertEquals(listOf(500_000), run("--port", "/dev/falsa", "--baud", "500000", "--json", "info").first)
}
