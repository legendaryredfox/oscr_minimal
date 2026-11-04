// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import oscr.cli.Cli
import oscr.cli.CliIo
import java.io.File
import kotlin.test.*

/** Igual a host/tests/test_database.py. */
class DatabaseTest {
    private fun tmp() = kotlin.io.path.createTempDirectory("oscrdb").toFile().also { it.deleteOnExit() }
    private fun hex(b: ByteArray) = (crc32(b).toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')

    private fun logiqx(f: File, vararg e: Triple<String, Int, String>): File {
        val rows = e.joinToString("") { (n, s, c) -> """<game name="$n"><description>$n</description><rom name="$n.bin" size="$s" crc="$c" sha1="00"/></game>""" }
        f.writeText("""<?xml version="1.0"?><datafile><header><name>teste</name></header>$rows</datafile>""")
        return f
    }

    private fun nes(prg: ByteArray, chr: ByteArray, mapper: Int = 0) =
        byteArrayOf(0x4E, 0x45, 0x53, 0x1A, (prg.size / 16384).toByte(), (chr.size / 8192).toByte(), ((mapper and 0xF) shl 4).toByte(), (mapper and 0xF0).toByte()) + ByteArray(8) + prg + chr

    private fun run(vararg argv: String): Triple<Int, String, String> {
        val out = StringBuilder(); val err = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { err.appendLine(it) }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        return Triple(Cli.run(argv.toList(), io), out.toString().trim(), err.toString())
    }

    @Test fun logiqxPorCrc() {
        val d = tmp(); val rom = ByteArray(2048) { it.toByte() }
        val db = Database(); DatabaseLoader.load(db, logiqx(File(d, "a.dat"), Triple("Jogo A", rom.size, hex(rom)), Triple("Jogo B", 3, "00000001")).path)
        assertEquals(2, db.size)
        val m = db.identify(CartSystem.SNES, rom)
        assertNotNull(m); assertEquals("Jogo A", m.entry.name); assertEquals(DbMatch.How.CRC32, m.how); assertEquals("a.dat", m.entry.source)
        assertNull(db.identify(CartSystem.SNES, rom + 1))
    }

    @Test fun nesSemCabecalho() {
        val d = tmp(); val n = nes(ByteArray(16384) { 1 }, ByteArray(8192) { 2 })
        val db = Database(); DatabaseLoader.load(db, logiqx(File(d, "n.dat"), Triple("Mario", n.size - 16, hex(n.copyOfRange(16, n.size)))).path)
        assertEquals(DbMatch.How.CRC32_NO_HEADER, db.identify(CartSystem.NES, n)?.how)
        assertNull(db.identify(CartSystem.SNES, n))
    }

    private val nes20 = """<?xml version="1.0"?><nes20db>
<game><rom name="Zelda.nes" size="1" crc32="DEADBEEF"/><prgrom size="32768" crc32="%s"/><chrrom size="16384" crc32="%s"/>
<prgnvram size="8192"/><pcb mapper="1" submapper="0" mirroring="H" battery="1"/></game>
<game><rom name="Outro.nes" size="1" crc32="00000002"/><prgrom size="32768" crc32="00000003"/><pcb mapper="0" submapper="0"/></game></nes20db>"""

    @Test fun nes20PorPrgEChrEOpcoes() {
        val d = tmp(); val prg = ByteArray(32768) { 7 }; val chr = ByteArray(16384) { 9 }
        val f = File(d, "nes20db.xml").also { it.writeText(nes20.format(hex(prg), hex(chr))) }
        val db = Database(); DatabaseLoader.load(db, f.path)
        val m = db.identify(CartSystem.NES, nes(prg, chr, 1))
        assertNotNull(m); assertEquals("Zelda.nes", m.entry.name); assertEquals(DbMatch.How.CRC32_PRG_CHR, m.how)
        assertEquals(NesOptions(1, 32, 16, 8), m.entry.nesOptions()); assertTrue(m.entry.battery)
        assertEquals("Zelda.nes", db.search("zelda")[0].name); assertTrue(db.search("zelda nada").isEmpty())
    }

    @Test fun pastaEXmlInvalido() {
        val d = tmp(); logiqx(File(d, "x.dat"), Triple("A", 1, "00000010")); File(d, "leiame.txt").writeText("ignorado")
        assertEquals(1, DatabaseLoader.load(Database(), d.path))
        File(d, "ruim.dat").writeText("<datafile><game")
        assertFailsWith<DatabaseError> { DatabaseLoader.load(Database(), File(d, "ruim.dat").path) }
        assertFailsWith<DatabaseError> { DatabaseLoader.load(Database(), File(d, "naoexiste").path) }
    }

    @Test fun cliIdentifyESearch() {
        val d = tmp(); val rom = "abc".repeat(100).toByteArray()
        File(d, "j.sfc").writeBytes(rom)
        val dat = logiqx(File(d, "d.dat"), Triple("Super Teste (USA)", rom.size, hex(rom)))
        val r = run("--json", "--no-builtin-db", "identify", "$d/j.sfc", "--db", dat.path)
        assertEquals(0, r.first, r.second); assertTrue("Super Teste (USA)" in r.second)
        File(d, "k.sfc").writeBytes("zzz".toByteArray())
        val r2 = run("--json", "--no-builtin-db", "identify", "$d/k.sfc", "--db", dat.path)
        assertEquals(1, r2.first); assertTrue("\"game\":null" in r2.second)
        val r3 = run("--json", "--no-builtin-db", "search", "teste", "--db", dat.path)
        assertEquals(0, r3.first); assertTrue(hex(rom) in r3.second)
    }

    @Test fun cliSemBaseDaErroEstruturado() {
        val r = run("--json", "--no-builtin-db", "search", "x")
        assertEquals(64, r.first); assertTrue("\"kind\":\"no_database\"" in r.second)
    }

    @Test fun dumpSimuladoMostraOJogo() {
        val d = tmp()
        run("--simulate", "--json", "dump", "-s", "mock", "-o", "$d/m")
        val data = File("$d/m.bin").readBytes()
        val dat = logiqx(File(d, "d.dat"), Triple("Padrão MOCK", data.size, hex(data)))
        val r = run("--simulate", "--json", "--no-builtin-db", "dump", "-s", "mock", "-o", "$d/m", "--db", dat.path)
        assertEquals(0, r.first); assertTrue("\"name\":\"Padrão MOCK\"" in r.second, r.second)
        val e = logiqx(File(d, "e.dat"), Triple("Outro", 1, "00000001"))
        assertTrue("\"game\":null" in run("--simulate", "--json", "--no-builtin-db", "dump", "-s", "mock", "-o", "$d/m", "--db", e.path).second)
    }

    @Test fun dumpGamePreencheOMapper() {
        val d = tmp(); val f = File(d, "nes20db.xml").also { it.writeText(nes20.format("00000005", "00000006")) }
        assertNotEquals(64, run("--simulate", "--json", "--no-builtin-db", "dump", "-s", "nes", "--game", "zelda", "--db", f.path, "-o", "$d/z").first)
        val r = run("--simulate", "--json", "--no-builtin-db", "dump", "-s", "nes", "--game", "naoexiste", "--db", f.path)
        assertEquals(64, r.first); assertTrue("game_not_found" in r.second)
        assertEquals(64, run("--simulate", "--json", "--no-builtin-db", "dump", "-s", "snes", "--game", "zelda", "--db", f.path).first)
    }

    @Test fun systemsListaOsPlanejados() {
        val r = run("--json", "systems")
        assertEquals(0, r.first); assertTrue("\"planned\":[" in r.second); assertTrue("\"key\"" !in r.second)
        for (p in PLANNED_SYSTEMS) assertTrue("\"name\":\"${p.key}\"" in r.second, p.key)
        assertEquals(PLANNED_SYSTEMS.size, PLANNED_SYSTEMS.map { it.key }.toSet().size)
        assertTrue(PLANNED_SYSTEMS.none { p -> CartSystem.entries.any { it.name.lowercase() == p.key } })
    }

    // ---- base que vem no projeto (database/oscr/, do OSCR legado; empacotada como recurso)

    private val osrcNes = "Jogo Um (USA).nes\r\nA2C2C172,D1628A60,4E45531A10001008000007070000000\r\n\r\n" +
        "Zelda Teste (USA).nes\r\n%s,00000000,4E45531A020112080000070700000000\r\n\r\n" +
        "Sem Dados\r\n\r\n" +
        "Outro (Japan).nes\r\n00000007,00000000,4E45531A010001080000000700000001\r\n"

    @Test fun leitorOscrTxt() {
        val n = nes(ByteArray(32768) { 5 }, ByteArray(8192) { 6 }, mapper = 4)
        val es = DatabaseLoader.parseOscr(osrcNes.format(hex(n.copyOfRange(16, n.size))), "nes.txt")
        assertEquals(listOf("Jogo Um (USA)", "Zelda Teste (USA)", "Outro (Japan)"), es.map { it.name })
        assertNull(es[0].mapper)
        val z = es[1]
        assertEquals(listOf("oscr", "nes.txt"), listOf(z.kind, z.source))
        assertEquals(NesOptions(1, 32, 8, 8), z.nesOptions()); assertEquals(40960L, z.size); assertTrue(z.battery)
        val db = Database(); es.forEach { db.add(it) }
        val m = db.identify(CartSystem.NES, n)
        assertEquals("Zelda Teste (USA)", m?.entry?.name); assertEquals(DbMatch.How.CRC32_NO_HEADER, m?.how)
    }

    @Test fun inesCabecalhos() {
        val h = "4E45531A100010080000070700000001".chunked(2).map { it.toInt(16).toByte() }.toByteArray()
        val i = DatabaseLoader.ines(h)!!
        assertEquals(listOf(1, 0, 256, 0, 8, false), listOf(i.mapper, i.submapper, i.prgKb, i.chrKb, i.ramKb, i.battery))
        val h1 = byteArrayOf(0x4E, 0x45, 0x53, 0x1A, 2, 1, 0x12, 0x00, 0, 0, 0, 0, 0, 0, 0, 0)
        val j = DatabaseLoader.ines(h1)!!
        assertEquals(listOf(1, 32, 8, 8, true), listOf(j.mapper, j.prgKb, j.chrKb, j.ramKb, j.battery))
        val big = byteArrayOf(0x4E, 0x45, 0x53, 0x1A, 0, 0, 0xF0.toByte(), 0x08, 0x31, 0x11, 0, 0, 0, 0, 0, 0)
        assertEquals(listOf(0x10F, 3), DatabaseLoader.ines(big)!!.let { listOf(it.mapper, it.submapper) })
        assertNull(DatabaseLoader.ines(big.copyOf(15))); assertNull(DatabaseLoader.ines(ByteArray(16)))
        assertNull(DatabaseLoader.ines(byteArrayOf(0x4E, 0x45, 0x53, 0x1A, 0, 0, 0, 0x08, 0, 0x0F, 0, 0, 0, 0, 0, 0)))
    }

    @Test fun baseDoProjetoCarregaSozinha() {
        val db = DatabaseLoader.loadAll(emptyList())
        assertTrue(db.size > 23000, "${db.size}")
        val by = db.entries.groupingBy { it.source }.eachCount()
        assertTrue((by["md.txt"] ?: 0) > 2500 && (by["nes.txt"] ?: 0) > 7000 && (by["snes.txt"] ?: 0) > 3800, by.toString())
        assertEquals(0, DatabaseLoader.loadAll(emptyList(), builtin = false).size)
        assertTrue(db.search("sonic", 5).isNotEmpty())
        val nesE = db.entries.filter { it.source == "nes.txt" }
        assertTrue(nesE.count { it.nesOptions() != null } > nesE.size * 0.99)
        assertTrue(nesE.none { it.name.endsWith(".nes", true) })
    }

    @Test fun baseDoProjetoESomaComADoUsuario() {
        val d = tmp(); val rom = ByteArray(800) { (it % 2).toByte() }
        val db = DatabaseLoader.loadAll(listOf(logiqx(File(d, "u.dat"), Triple("Meu Jogo", rom.size, hex(rom))).path))
        assertEquals("Meu Jogo", db.identify(CartSystem.SNES, rom)?.entry?.name)
        assertTrue(db.size > 23000)
    }

    @Test fun cliSearchUsaABaseDoProjeto() {
        val r = run("--json", "search", "sonic", "--limit", "3")
        assertEquals(0, r.first, r.second); assertTrue("\"entries_in_database\":2" in r.second || "\"entries_in_database\":3" in r.second, r.second)
        assertEquals(1, run("--json", "search", "zzzznaoexiste").first)
    }

    @Test fun dumpSimuladoComABaseDoProjetoNaoAchaOPadraoMock() {
        val d = tmp()
        val r = run("--simulate", "--json", "dump", "-s", "mock", "-o", "$d/m")
        assertEquals(0, r.first, r.second); assertTrue("\"game\":null" in r.second, r.second)
    }

    @Test fun flashIdMdSoIdentifica() {
        val r1 = run("--simulate", "--json", "flash-read", "--bus", "md")
        assertEquals(64, r1.first); assertTrue("rom-write" in r1.second, r1.second)
        assertEquals(64, run("--simulate", "--json", "flash-erase", "--bus", "md", "--yes").first)
        val r2 = run("--simulate", "--json", "flash-id", "--bus", "md", "--flash-kb", "4096")
        assertEquals(64, r2.first); assertTrue("--flash-kb" in r2.second, r2.second)
    }
}
