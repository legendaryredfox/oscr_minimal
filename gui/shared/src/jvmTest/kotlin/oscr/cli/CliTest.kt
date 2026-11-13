// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import kotlin.test.*

/** Contrato da CLI para agentes (docs/referencia/cli.md), igual a host/tests/test_cli_agentes.py. */
class CliTest {
    private class Run(val code: Int, val out: String, val err: String) {
        fun json(): Map<String, String> = Regex("\"(\\w+)\":(\"(?:[^\"\\\\]|\\\\.)*\"|[^,}\\]{]+)").findAll(out).associate { it.groupValues[1] to it.groupValues[2].trim('"') }
    }

    private fun run(vararg argv: String, interactive: Boolean = false, ports: List<String> = emptyList(), home: String = "."): Run {
        val out = StringBuilder(); val err = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { err.appendLine(it) }, interactive, false, { null }, { ports }, { _, _ -> error("sem porta") }, home)
        return Run(Cli.run(argv.toList(), io), out.toString().trim(), err.toString())
    }

    private fun tmp() = kotlin.io.path.createTempDirectory("oscrcli").toFile().also { it.deleteOnExit() }

    @Test fun soundTocaBelNoFim() {                                  // P4 (D160): um BEL se deu certo, três se falhou
        assertEquals(1, run("detect", "-s", "mock", "--simulate", "--json", "--sound").err.count { it == '\u0007' })
        assertEquals(3, run("detect", "-s", "snes", "--simulate", "--json", "--sound").err.count { it == '\u0007' })
        assertEquals(0, run("detect", "-s", "mock", "--simulate", "--json").err.count { it == '\u0007' })
    }

    @Test fun jsonDepoisDoSubcomando() {
        val r = run("detect", "-s", "mock", "--simulate", "--json")
        assertEquals(0, r.code); assertEquals("true", r.json()["ok"]); assertEquals("0", r.json()["status"])
    }

    @Test fun todoJsonTemOk() {
        val d = tmp()
        for (argv in listOf(listOf("info"), listOf("systems"), listOf("errors"), listOf("dump", "-s", "mock", "-o", "$d/a"))) {
            val r = run("--simulate", "--json", *argv.toTypedArray())
            assertEquals(0, r.code, argv.toString()); assertTrue(r.out.startsWith("{\"ok\":true"), r.out)
        }
    }

    @Test fun dumpTwiceComLeiturasIguais() {
        val d = tmp()
        val r = run("--simulate", "--json", "dump", "-s", "mock", "--twice", "-o", "$d/x")
        assertEquals(0, r.code); assertEquals("true", r.json()["twice"])
        assertContentEquals(mockData(), File("$d/x.bin").readBytes()); assertFalse(File("$d/x.leitura1.bin").exists())
    }

    @Test fun diffSummaryContaDiferencas() {
        assertEquals(0 to -1, oscr.diffSummary(byteArrayOf(1, 2, 3), byteArrayOf(1, 2, 3)))
        assertEquals(1 to 3, diffSummary(byteArrayOf(1, 2, 3, 4), byteArrayOf(1, 2, 3)))
        assertEquals(1 to 2, diffSummary(byteArrayOf(1, 2, 9, 4), byteArrayOf(1, 2, 3, 4)))
    }

    @Test fun dumpCrcEArquivoBatemComOMock() {
        val d = tmp()
        val r = run("--simulate", "--json", "dump", "-s", "mock", "-o", "$d/x")
        assertContentEquals(mockData(), File("$d/x.bin").readBytes())
        assertEquals(crc32(mockData()).toLong().and(0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0'), r.json()["crc32"])
        assertEquals("na", r.json()["checksum"])
    }

    @Test fun saveGravaELeDeVolta() {
        val d = tmp(); val src = File("$d/in.sav").also { it.writeBytes(ByteArray(200) { i -> i.toByte() }) }
        val w = run("--simulate", "--json", "save-write", "-s", "mock", "-i", src.path, "--yes", "--backup-dir", "$d/bk")
        assertEquals(0, w.code, w.out); assertEquals(1, File("$d/bk").listFiles()!!.size)
        assertEquals(0, run("--simulate", "save-read", "-s", "mock", "-o", "$d/s").code)
        assertEquals(8192, File("$d/s.sav").length().toInt())
    }

    @Test fun semPortaDaSaida3() {
        val r = run("--json", "detect")
        assertEquals(3, r.code); assertEquals("false", r.json()["ok"]); assertEquals("no_port", r.json()["kind"])
    }

    @Test fun usoInvalidoDaSaida64() {
        val r = run("--json", "detect", "-s", "naoexiste", "--simulate")
        assertEquals(64, r.code); assertEquals("usage", r.json()["kind"])
        assertEquals(64, run("--json", "detect", "--naoexiste").code)
        assertEquals(64, run("--json", "voar").code)
    }

    @Test fun recusaSemYesForaDeTerminal() {
        val d = tmp(); val src = File("$d/in.sav").also { it.writeBytes(ByteArray(16)) }
        val r = run("--simulate", "--json", "save-write", "-s", "mock", "-i", src.path, "--backup-dir", "$d/bk")
        assertEquals(4, r.code); assertEquals("refused", r.json()["kind"]); assertFalse(File("$d/bk").exists())
    }

    @Test fun arquivoInexistenteViraIo() {
        val r = run("--simulate", "--json", "save-write", "-s", "mock", "-i", "/nao/existe.sav", "--yes")
        assertEquals(1, r.code); assertEquals("io", r.json()["kind"])
    }

    @Test fun detectSemCartuchoDaSaida2() {
        val r = run("--simulate", "--json", "detect", "-s", "snes")
        assertEquals(2, r.code); assertEquals("false", r.json()["ok"]); assertEquals("1", r.json()["status"])
        val e = run("--simulate", "--json", "dump", "-s", "snes", "-o", "${tmp()}/z")
        assertEquals(2, e.code); assertEquals("no_cartridge", e.json()["kind"]); assertEquals("3", e.json()["device_code"])
    }

    @Test fun progressoJsonlEmStderr() {
        val r = run("--simulate", "--json", "--progress", "jsonl", "dump", "-s", "mock", "-o", "${tmp()}/p")
        val last = r.err.lines().filter { it.startsWith("{") }.last()
        assertTrue("\"percent\":100" in last && "\"label\":\"rom\"" in last, last)
    }

    @Test fun systemsEErrorsNaoAbremAPorta() {
        val s = run("systems", "--json").out
        for (n in CartSystem.entries) assertTrue("\"name\":\"${n.name.lowercase()}\"" in s, n.name)
        assertTrue("\"exit_code\":64" in run("errors", "--json").out)
    }

    @Test fun jsonEscapaTexto() {
        assertEquals("{\"a\":\"x\\\"y\\n\",\"b\":[1,true,null]}", Json.encode(Json.obj("a" to "x\"y\n", "b" to listOf(1, true, null))))
    }
}
