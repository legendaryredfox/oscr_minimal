// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import kotlin.test.*

/** P5 (D160): descobrir o sistema do cartucho só com leituras. Igual ao bloco "detecção automática" de host/tests/test_melhorias_referencia.py. */
class AutoDetectTest {
    private fun run(vararg argv: String, simVolt: Boolean = false, simCart5v: Boolean = false): Triple<Int, String, String> {
        val out = StringBuilder(); val err = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { err.appendLine(it) }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".", simVolt = simVolt, simCart5v = simCart5v)
        return Triple(Cli.run(argv.toList(), io), out.toString().trim(), err.toString())
    }


    @Test fun ordemEPrimeiroAchado() {
        assertEquals(listOf(CartSystem.N64, CartSystem.GBA, CartSystem.GB, CartSystem.MD, CartSystem.SNES, CartSystem.SMS, CartSystem.NES), AUTO_ORDER)
        assertEquals(CartSystem.NES, AUTO_ORDER.last())                          // o NES por último: o DETECT dele aceita quase qualquer dado
    }

    @Test fun semCartuchoSaiCom2() {
        val (code, out, _) = run("detect", "-s", "auto", "--simulate", "--json")
        assertEquals(2, code); assertTrue("no_cartridge" in out, out)
    }

    @Test fun comCartuchoAchaOPrimeiroDaOrdem() {                                // o simulador com cartucho de 5 V "responde" em qualquer sistema: o primeiro é o N64
        val (code, out, err) = run("detect", "-s", "auto", "--simulate", "--voltage", "5v", simVolt = true, simCart5v = true)
        assertEquals(0, code, out + err)
    }

    @Test fun gravarExigeSistemaExplicito() {
        for (argv in listOf(listOf("save-write", "-s", "auto", "-i", "x", "--yes"), listOf("rom-write", "-s", "auto", "-i", "x", "--yes"))) {
            val (code, out, _) = run(*argv.toTypedArray(), "--simulate", "--json")
            assertEquals(64, code, out); assertTrue("auto" in out, out)
        }
    }
}
