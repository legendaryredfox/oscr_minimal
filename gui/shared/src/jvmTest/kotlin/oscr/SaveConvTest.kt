// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.test.*

/** save-convert (H-1, D163). Mesmos vetores de host/tests/test_saveconv.py. */
class SaveConvTest {
    private fun b(vararg v: Int) = ByteArray(v.size) { v[it].toByte() }

    @Test fun swapVetores() {
        assertContentEquals(b(2, 1, 4, 3, 6, 5), SaveConv.convert(b(1, 2, 3, 4, 5, 6), "swap16"))
        assertContentEquals(b(3, 2, 1, 0, 7, 6, 5, 4), SaveConv.convert(b(0, 1, 2, 3, 4, 5, 6, 7), "swap32"))
        val d = ByteArray(256) { it.toByte() }
        for (op in listOf("swap16", "swap32")) assertContentEquals(d, SaveConv.convert(SaveConv.convert(d, op), op))
        assertFailsWith<IllegalArgumentException> { SaveConv.convert(b(1, 2, 3), "swap16") }
        assertFailsWith<IllegalArgumentException> { SaveConv.convert(b(1, 2, 3, 4, 5, 6), "swap32") }
    }

    @Test fun mdExpandECompact() {
        assertContentEquals(b(0xFF, 0x11, 0xFF, 0x22), SaveConv.convert(b(0x11, 0x22), "md-expand-odd"))
        assertContentEquals(b(0x11, 0xFF, 0x22, 0xFF), SaveConv.convert(b(0x11, 0x22), "md-expand-even"))
        assertContentEquals(b(0, 0x11), SaveConv.convert(b(0x11), "md-expand-odd", 0))
        val d = ByteArray(64) { (it + 1).toByte() }
        assertContentEquals(d, SaveConv.convert(SaveConv.convert(d, "md-expand-odd"), "md-compact-odd"))
        assertContentEquals(d, SaveConv.convert(SaveConv.convert(d, "md-expand-even"), "md-compact-even"))
        assertContentEquals(b(2, 4), SaveConv.convert(b(1, 2, 3, 4), "md-compact-odd"))
        assertContentEquals(b(1, 3), SaveConv.convert(b(1, 2, 3, 4), "md-compact-even"))
        assertFailsWith<IllegalArgumentException> { SaveConv.convert(b(1, 2, 3), "md-compact-odd") }
        assertFailsWith<IllegalArgumentException> { SaveConv.convert(b(1), "xyz") }
    }

    private fun cli(vararg argv: String): Pair<Int, String> {
        val out = StringBuilder()
        val io = oscr.cli.CliIo({ out.appendLine(it) }, { }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        return oscr.cli.Cli.run(argv.toList(), io) to out.toString()
    }

    @Test fun comandoDaCli() {
        val dir = java.nio.file.Files.createTempDirectory("saveconv").toFile()
        val src = java.io.File(dir, "jogo.sav").also { it.writeBytes(b(1, 2, 3, 4)) }
        val (code, out) = cli("--json", "save-convert", "-i", src.path, "--op", "swap16")
        assertEquals(0, code); assertTrue("jogo_swap16.sav" in out)
        assertContentEquals(b(2, 1, 4, 3), java.io.File(dir, "jogo_swap16.sav").readBytes())
        val dst = java.io.File(dir, "x.srm")
        assertEquals(0, cli("--json", "save-convert", "-i", src.path, "-o", dst.path, "--op", "md-expand-odd", "--fill", "0x00").first)
        assertContentEquals(b(0, 1, 0, 2, 0, 3, 0, 4), dst.readBytes())
        src.writeBytes(b(1, 2, 3))
        assertEquals(1, cli("--json", "save-convert", "-i", src.path, "--op", "swap16").first)
        assertEquals(64, cli("--json", "save-convert", "-i", src.path, "--op", "md-expand-odd", "--fill", "300").first)
        assertEquals(64, cli("--json", "save-convert", "-i", src.path, "--op", "xyz").first)
        dir.deleteRecursively()
    }
}
