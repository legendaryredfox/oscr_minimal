// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.security.MessageDigest
import kotlin.test.*

/** `--board` na CLI Kotlin: confere o firmware e grava o certo depois de pedir confirmação (D162). Espelha host/tests/test_board_cli.py. */
class BoardCliTest {
    private class Run(val code: Int, val out: String, val err: String, val io: CliIo)

    private fun images(): File {
        val d = kotlin.io.path.createTempDirectory("imgcli").toFile().also { it.deleteOnExit() }
        val hex = File(d, "oscr-0.2.0-completa.hex").also { it.writeText(":00000001FF\n") }
        val sha = MessageDigest.getInstance("SHA-256").digest(hex.readBytes()).joinToString("") { "%02x".format(it) }
        File(d, "manifest.tsv").writeText("completa\t${hex.name}\t0.2.0\t1,2,3,4,5,6,7,8,9,10,11\t$sha\n")
        return d
    }

    private fun run(old: Boolean, interactive: Boolean = false, answer: String? = null, vararg args: String): Run {
        val out = StringBuilder(); val err = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { err.appendLine(it) }, interactive, false, { answer }, { listOf("/dev/ttyACM0") }, { _, _ -> error("sem porta real") }, ".", simOldFw = old)
        val code = Cli.run(args.toList(), io)
        return Run(code, out.toString(), err.toString(), io)
    }

    @Test fun boardsListaAsPlacasSemUsarOArduino() {
        val r = run(false, args = arrayOf("--json", "boards"))
        assertEquals(0, r.code); assertTrue("\"16_bits\"" in r.out && "\"completa\"" in r.out, r.out)
    }

    @Test fun placaDesconhecidaEErroDeUso() {
        val r = run(false, args = arrayOf("--simulate", "--json", "--board", "zx_spectrum", "board"))
        assertEquals(64, r.code); assertTrue("unknown_board" in r.out, r.out)
    }

    @Test fun firmwareQueServeSoGravaOPerfil() {
        val d = images()
        val r = run(false, args = arrayOf("--simulate", "--json", "--firmware-dir", d.path, "--board", "16_bits", "board"))
        assertEquals(0, r.code, r.out + r.err); assertTrue("\"action\":\"set_profile\"" in r.out.replace(" ", ""), r.out); assertTrue("\"voltage_select\":true" in r.out.replace(" ", ""), r.out)
    }

    @Test fun firmwareAntigoSemConfirmacaoERecusadoENaoGrava() {
        val r = run(true, args = arrayOf("--simulate", "--json", "--firmware-dir", images().path, "--board", "16_bits", "board"))
        assertEquals(4, r.code, r.out); assertTrue("refused" in r.out); assertFalse(r.io.simFlashed)
    }

    @Test fun firmwareAntigoComAutoFlashGravaEDepoisAjustaOPerfil() {
        val r = run(true, args = arrayOf("--simulate", "--json", "--auto-flash", "--firmware-dir", images().path, "--board", "16_bits", "board"))
        assertEquals(0, r.code, r.out + r.err); assertTrue(r.io.simFlashed); assertTrue("\"action\":\"flash\"" in r.out.replace(" ", ""), r.out); assertTrue("0.2.0" in r.err)
    }

    @Test fun perguntaNoTerminalNaoCancelaESimGrava() {
        val d = images().path
        val no = run(true, interactive = true, answer = "n", args = arrayOf("--simulate", "--firmware-dir", d, "--board", "16_bits", "board"))
        assertEquals(4, no.code); assertFalse(no.io.simFlashed)
        val yes = run(true, interactive = true, answer = "y", args = arrayOf("--simulate", "--firmware-dir", d, "--board", "16_bits", "board"))
        assertEquals(0, yes.code, yes.out + yes.err); assertTrue(yes.io.simFlashed); assertTrue("replaced" in yes.err)
    }

    @Test fun semImagemConhecidaNaoGravaEExplica() {
        val empty = kotlin.io.path.createTempDirectory("vazio").toFile().also { it.deleteOnExit() }
        val r = run(true, args = arrayOf("--simulate", "--json", "--auto-flash", "--firmware-dir", empty.path, "--board", "16_bits", "board"))
        assertEquals(1, r.code, r.out); assertTrue("board_unsupported" in r.out); assertFalse(r.io.simFlashed)
    }

    @Test fun boardValeParaQualquerComandoDeCartucho() {
        val r = run(false, args = arrayOf("--simulate", "--json", "--firmware-dir", images().path, "--board", "snes", "detect", "-s", "mock"))
        assertEquals(0, r.code, r.out + r.err); assertTrue("\"ok\":true" in r.out.replace(" ", ""), r.out)
    }
}
