// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.test.*

/** Tipo de ROM do SNES forçado pelo PC (F-2, D164). Mesmos códigos de host/tests/test_snes_type.py e firmware/oscr/pc-tests/test_snes_type.cpp. */
class SnesTypeTest {
    private fun run(vararg argv: String): Int {
        val io = oscr.cli.CliIo({ }, { }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        return oscr.cli.Cli.run(argv.toList(), io)
    }

    @Test fun codigos() { assertEquals(mapOf("lorom" to 1, "hirom" to 2, "sa1" to 3, "exhirom" to 4), SnesType.CODES) }

    @Test fun soNoSnesEValorConhecido() {
        assertEquals(64, run("--simulate", "--json", "detect", "-s", "md", "--type", "lorom"))
        assertEquals(64, run("--simulate", "--json", "detect", "-s", "snes", "--type", "xyz"))
    }

    @Test fun snesAceitaOTipo() {
        for (t in SnesType.CODES.keys) assertEquals(2, run("--simulate", "--json", "detect", "-s", "snes", "--type", t))     // o simulador só tem cartucho MOCK: sem cartucho
    }
}
