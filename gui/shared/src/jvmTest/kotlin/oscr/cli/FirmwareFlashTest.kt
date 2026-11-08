// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import java.io.File
import kotlin.test.*

/** firmware-flash (D131), igual a host/tests/test_firmware_flash.py: o avrdude é um script falso que registra os argumentos (só em Unix). */
class FirmwareFlashTest {
    private class Run(val code: Int, val out: String, val err: String)

    private fun run(vararg argv: String): Run {
        val out = StringBuilder(); val err = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { err.appendLine(it) }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        return Run(Cli.run(argv.toList(), io), out.toString().trim(), err.toString())
    }

    private val unix = !System.getProperty("os.name").startsWith("Windows")
    private fun fake(exit: Int = 0): Triple<File, File, File> {
        val d = kotlin.io.path.createTempDirectory("fwflash").toFile().also { it.deleteOnExit() }
        val log = File(d, "args.txt"); val hex = File(d, "firmware.hex").apply { writeText(":00000001FF\n") }
        val exe = File(d, "avrdude").apply {
            writeText("#!/bin/sh\nprintf '%s\\n' \"\$@\" > '${log.path}'\nprintf 'Writing | ##### | 50%% 0.5s\\rWriting | ########## | 100%% 1s\\r\\n' >&2\n" +
                if (exit != 0) "echo 'avrdude: erro de teste' >&2\nexit $exit\n" else "echo 'avrdude done.' >&2\n")
            setExecutable(true)
        }
        return Triple(exe, hex, log)
    }

    @Test fun dryRunMostraOComando() {
        val (exe, hex, log) = fake()
        val r = run("--json", "-p", "/dev/ttyOSCRteste", "firmware-flash", "--hex", hex.path, "--avrdude", exe.path, "--dry-run")
        assertEquals(0, r.code, r.out); assertTrue(r.out.startsWith("{\"ok\":true,\"dry_run\":true"), r.out)
        assertTrue(r.out.contains("\"-p\",\"atmega2560\",\"-c\",\"wiring\",\"-P\",\"/dev/ttyOSCRteste\",\"-b\",\"115200\",\"-D\",\"-U\",\"flash:w:${hex.path}:i\""), r.out)
        assertFalse(log.exists())
    }

    @Test fun gravaComYesETraduzOProgresso() {
        if (!unix) return
        val (exe, hex, log) = fake()
        val r = run("--json", "--progress", "jsonl", "-p", "/dev/ttyOSCRteste", "firmware-flash", "--hex", hex.path, "--avrdude", exe.path, "--yes", "--wait", "0")
        assertEquals(0, r.code, r.out); assertTrue(r.out.contains("\"verified\":true") && r.out.contains("\"responds\":false"), r.out)
        val args = log.readLines(); assertEquals(listOf("-U", "flash:w:${hex.path}:i"), args.takeLast(2)); assertFalse("-V" in args)
        assertTrue(r.err.contains("\"label\":\"writing\"") && r.err.contains("\"percent\":100"), r.err)
    }

    @Test fun noVerifyPassaOV() {
        if (!unix) return
        val (exe, hex, log) = fake()
        val r = run("--json", "-p", "/dev/x", "firmware-flash", "--hex", hex.path, "--avrdude", exe.path, "--yes", "--wait", "0", "--no-verify")
        assertEquals(0, r.code); assertTrue("-V" in log.readLines()); assertTrue(r.out.contains("\"verified\":false"))
    }

    @Test fun avrdudeQueFalha() {
        if (!unix) return
        val (exe, hex, _) = fake(exit = 1)
        val r = run("--json", "-p", "/dev/x", "firmware-flash", "--hex", hex.path, "--avrdude", exe.path, "--yes", "--wait", "0")
        assertEquals(3, r.code); assertTrue(r.out.contains("\"kind\":\"avrdude\"") && r.out.contains("erro de teste") && r.out.contains("dialout"), r.out)
    }

    @Test fun recusaSemYes() {
        val (exe, hex, log) = fake()
        val r = run("--json", "-p", "/dev/x", "firmware-flash", "--hex", hex.path, "--avrdude", exe.path)
        assertEquals(4, r.code); assertTrue(r.out.contains("\"kind\":\"refused\"")); assertFalse(log.exists())
    }

    @Test fun semHexESemAvrdude() {
        val r = run("--json", "-p", "/dev/x", "firmware-flash", "--hex", "/nao/existe.hex", "--yes")
        assertEquals(64, r.code); assertTrue(r.out.contains("\"kind\":\"no_hex\"") && r.out.contains("pio run"), r.out)
        val (_, hex, _) = fake()
        val r2 = run("--json", "-p", "/dev/x", "firmware-flash", "--hex", hex.path, "--avrdude", "/nao/existe/avrdude", "--yes")
        assertEquals(64, r2.code); assertTrue(r2.out.contains("\"kind\":\"no_avrdude\""), r2.out)
    }

    @Test fun simuladorNaoChamaOAvrdude() {
        val (_, hex, log) = fake()
        val r = run("--json", "--simulate", "firmware-flash", "--hex", hex.path, "--yes")
        assertEquals(0, r.code, r.out); assertTrue(r.out.contains("\"simulated\":true")); assertFalse(log.exists())
    }
}
