// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.io.File
import kotlin.test.*

/** Acessórios do SNES (F-10, D178): Sufami Turbo, GPC e ram-test. Mesmos casos de host/tests/test_snes_acc.py e de firmware/oscr/pc-tests/test_snesacc.cpp. */
class SnesAccTest {
    private fun run(vararg argv: String): Int {
        val io = oscr.cli.CliIo({ }, { }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        return oscr.cli.Cli.run(argv.toList(), io)
    }

    @Test fun codigosBatemComOFirmware() {
        val h = generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "firmware/oscr/include/dumper/SnesAcc.h") }.firstOrNull { it.exists() }?.readText() ?: return
        fun code(name: String) = Regex("$name = 0x([0-9A-Fa-f]+)").find(h)!!.groupValues[1].toInt(16)
        assertEquals(code("kSufamiA"), Proto.SNES_ACCESSORIES["sufami-a"]); assertEquals(code("kSufamiB"), Proto.SNES_ACCESSORIES["sufami-b"])
        assertEquals(code("kGpc"), Proto.SNES_ACCESSORIES["gpc"]); assertEquals(code("kGpcBytes"), Proto.GPC_BYTES)
        assertTrue(Proto.SNES_ACCESSORIES.values.all { it >= 0x8000 } && Proto.SNES_ACCESSORIES.values.none { it in SnesType.CODES.values })
    }

    @Test fun recusasAntesDeFalarComOCartucho() {
        val bad = File.createTempFile("gpcx", ".bin").also { it.deleteOnExit(); it.writeBytes(ByteArray(1000)) }
        for (argv in listOf(
            listOf("dump", "-s", "snes", "--accessory", "gpc"), listOf("detect", "-s", "snes", "--accessory", "gpc"), listOf("save-read", "-s", "snes", "--accessory", "sufami-a"),
            listOf("dump", "-s", "md", "--accessory", "sufami-a"), listOf("dump", "-s", "snes", "--accessory", "sufami-a", "--type", "lorom"),
            listOf("save-write", "-s", "snes", "--accessory", "gpc", "-i", bad.path, "--yes"), listOf("ram-test", "-s", "md", "--yes")))
            assertEquals(64, run("--simulate", "--json", *argv.toTypedArray()), argv.toString())
        assertEquals(oscr.cli.EXIT_REFUSED, run("--simulate", "--json", "ram-test"))              // sem --yes e sem terminal
    }
}
