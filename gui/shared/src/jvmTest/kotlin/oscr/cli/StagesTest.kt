// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import kotlin.test.*

/** PROGRESSO com etapa (F-1), igual a host/tests/test_stages.py: o firmware avisa apagando, gravando, lendo e autoteste; firmware antigo não emite. */
class StagesTest {
    private fun client(dev: SimDevice): Pair<OscrClient, MutableList<Triple<Int, Long, Long>>> {
        val c = OscrClient(dev, 500, 5000)
        val seen = mutableListOf<Triple<Int, Long, Long>>()
        c.onStage = { s, d, t -> seen += Triple(s, d, t) }
        return c to seen
    }

    @Test fun clienteRecebeAsEtapas() {
        val (c, seen) = client(SimDevice())
        c.selftest()
        c.erase(CartSystem.MOCK, 3, 0, 0)
        val res = c.dumpRom(CartSystem.MOCK)
        c.writeSave(CartSystem.MOCK, res.data.copyOf(1024))
        assertEquals(listOf(Proto.STAGE_SELFTEST, Proto.STAGE_ERASE, Proto.STAGE_READ, Proto.STAGE_WRITE), seen.map { it.first })
        assertEquals(res.data.size.toLong(), seen[2].third)                      // a leitura anuncia o total
    }

    @Test fun firmwareAntigoNaoEmite() {
        val (c, seen) = client(SimDevice(stages = false))
        c.erase(CartSystem.MOCK, 3, 0, 0)
        c.dumpRom(CartSystem.MOCK)
        assertTrue(seen.isEmpty())
    }

    private fun jsonl(vararg argv: String, env: (CliIo) -> Unit = {}): String {
        val err = StringBuilder()
        val io = CliIo({ }, { err.appendLine(it) }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        env(io)
        Cli.run(argv.toList(), io)
        return err.toString()
    }

    @Test fun cliJsonlMostraAEtapa() {
        val err = jsonl("--simulate", "--json", "--progress", "jsonl", "selftest")
        assertTrue("\"event\":\"stage\"" in err && "\"stage\":\"selftest\"" in err, err)
        assertFalse("\"event\":\"stage\"" in jsonl("--simulate", "--json", "--progress", "none", "selftest"))
    }
}
