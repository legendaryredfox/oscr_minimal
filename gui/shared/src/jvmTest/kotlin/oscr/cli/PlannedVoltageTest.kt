// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import kotlin.test.*

/** H-4 (P-16), igual a host/tests/test_planned.py: o `systems` marca os adaptadores de 3,3 V da comunidade. */
class PlannedVoltageTest {
    @Test fun marcaOsDe3v3() {
        assertEquals(setOf("leapster", "jammerpro"), PLANNED_SYSTEMS.filter { it.needs3v3 }.map { it.key }.toSet())
        val out = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        assertEquals(0, Cli.run(listOf("--json", "systems"), io))
        assertTrue("\"name\":\"leapster\"" in out && "\"voltage\":\"3v3\"" in out, out.toString())
        val txt = StringBuilder()
        val io2 = CliIo({ txt.appendLine(it) }, { }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".", env = { if (it == "OSCR_LANG") "pt-BR" else null })
        assertEquals(0, Cli.run(listOf("systems"), io2))
        assertTrue("[3,3 V]" in txt && "não pode ir num slot de 5 V" in txt, txt.toString())
    }
}
