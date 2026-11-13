// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import kotlin.test.*

/** Recusa do `rom-write -s md` acima de 2 MiB num S29GL (KY / FlashKit), com `--ignore-cart-limit`. Igual a host/tests/test_rom_write.py. */
class MdBoardLimitCliTest {
    private class Run(val code: Int, val out: String, val dev: SimDevice)

    private fun run(chipName: String, bytes: Int, vararg extra: String): Run {
        val d = kotlin.io.path.createTempDirectory("oscrlimit").toFile().also { it.deleteOnExit() }
        val f = File(d, "jogo.md").also { it.writeBytes(ByteArray(bytes) { i -> ((i * 11 + 5) and 0xFF).toByte() }) }
        val dev = SimDevice(mdFlashName = chipName)
        val out = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { out.appendLine(it) }, false, false, { null }, { listOf("/dev/ttyACM0") }, { _, _ -> dev }, ".")
        val code = Cli.run(listOf("--json", "rom-write", "-s", "md", "-i", f.path, "--chip", "md-flash", "--yes", "--no-verify", "--port", "/dev/ttyACM0") + extra, io)
        return Run(code, out.toString(), dev)
    }

    @Test fun acimaDe2MiBNoS29glRecusaAntesDeApagar() {
        val r = run("S29GL064N 017E1000", 4 shl 20)
        assertEquals(4, r.code); assertNull(r.dev.writtenRom)
        assertTrue("2 MiB" in r.out && "--ignore-cart-limit" in r.out, r.out)
    }

    @Test fun ignoreCartLimitForca() {
        val r = run("S29GL064N 017E1000", 4 shl 20, "--ignore-cart-limit")
        assertEquals(0, r.code, r.out); assertNotNull(r.dev.writtenRom)
    }

    @Test fun exatamente2MiBPassaEOutroChipNaoTemLimite() {
        assertEquals(0, run("S29GL064N 017E1001", 2 shl 20).code)
        assertEquals(0, run("M29W320EB 0020", 4 shl 20).code)
    }
}
