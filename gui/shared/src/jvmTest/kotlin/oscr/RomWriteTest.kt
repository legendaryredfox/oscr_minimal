// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import oscr.cli.Cli
import oscr.cli.CliIo
import oscr.cli.SimDevice
import java.io.File
import kotlin.test.*

/** Igual a host/tests/test_rom_write.py. */
class RomWriteTest {
    private fun tmp() = kotlin.io.path.createTempDirectory("oscrrom").toFile().also { it.deleteOnExit() }

    private fun ines(prg: Int, chr: Int, mapper: Int, trainer: Boolean = false): ByteArray =
        byteArrayOf(0x4E, 0x45, 0x53, 0x1A, (prg / 16).toByte(), (chr / 8).toByte(), (((mapper and 0xF) shl 4) or (if (trainer) 4 else 0)).toByte(), (mapper and 0xF0).toByte()) +
            ByteArray(8) + ByteArray((prg + chr) * 1024) { ((it * 7) and 0xFF).toByte() }

    private fun run(vararg argv: String, interactive: Boolean = false): Triple<Int, String, String> {
        val out = StringBuilder(); val err = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { err.appendLine(it) }, interactive, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        return Triple(Cli.run(argv.toList(), io), out.toString().trim(), err.toString())
    }

    @Test fun splitEInferencia() {
        val img = RomImages.split(ines(32, 8, 0), FlashChip.A29040B)
        assertEquals(Triple(32, 8, 0), Triple(img.prgKb, img.chrKb, img.mapper)); assertEquals(40 * 1024, img.body.size)
        assertEquals(FlashChip.NESMAKER, RomImages.prepare(ines(512, 0, 30), null).first)
        assertEquals(FlashChip.A29040B, RomImages.prepare(ines(32, 8, 0), null).first)
        assertEquals(RomImageProblem.CHIP_UNKNOWN, assertFailsWith<RomImageException> { RomImages.prepare(ines(32, 8, 4), null) }.problem)
        assertEquals(32, RomImages.split(ByteArray(32768), FlashChip.NESMAKER).prgKb)
    }

    @Test fun errosDoArquivo() {
        assertEquals(RomImageProblem.TRAINER, assertFailsWith<RomImageException> { RomImages.split(ines(32, 0, 30, trainer = true), FlashChip.NESMAKER) }.problem)
        assertEquals(RomImageProblem.SIZE_MISMATCH, assertFailsWith<RomImageException> { RomImages.split(ines(32, 0, 30).copyOf(ines(32, 0, 30).size - 1), FlashChip.NESMAKER) }.problem)
        assertEquals(RomImageProblem.NEEDS_HEADER, assertFailsWith<RomImageException> { RomImages.split(ByteArray(16384), FlashChip.A29040B) }.problem)
        assertEquals(RomImageProblem.RAW_SIZE, assertFailsWith<RomImageException> { RomImages.split(ByteArray(1000), FlashChip.NESMAKER) }.problem)
    }

    @Test fun romWriteSimulado() {
        val d = tmp(); val f = File(d, "jogo.nes").also { it.writeBytes(ines(32, 8, 0)) }
        val r = run("--simulate", "--json", "rom-write", "-s", "mock", "-i", f.path, "--yes")
        assertEquals(0, r.first, r.second); assertTrue("\"chip\":\"a29040b\"" in r.second); assertTrue("\"bytes\":40960" in r.second)
    }

    @Test fun recusaSemYes() {
        val d = tmp(); val f = File(d, "jogo.nes").also { it.writeBytes(ines(32, 8, 0)) }
        val r = run("--simulate", "--json", "rom-write", "-s", "mock", "-i", f.path)
        assertEquals(4, r.first); assertTrue("\"kind\":\"refused\"" in r.second)
    }

    @Test fun errosDeUso() {
        val d = tmp()
        val m4 = File(d, "m4.nes").also { it.writeBytes(ines(32, 8, 4)) }
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "mock", "-i", m4.path, "--yes").first)
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "snes", "-i", m4.path, "--yes").first)
        val bad = File(d, "ruim.nes").also { it.writeBytes(ines(32, 0, 30).copyOf(ines(32, 0, 30).size - 5)) }
        val r = run("--simulate", "--json", "rom-write", "-s", "mock", "-i", bad.path, "--yes")
        assertEquals(64, r.first); assertTrue("\"kind\":\"bad_rom\"" in r.second)
    }

    @Test fun chipNaoReconhecidoEInfo() {
        val dev = SimDevice(); val c = OscrClient(dev, 500, 5000)
        assertTrue(c.info().writeRom)
        val e = assertFailsWith<DeviceError> { c.writeRom(CartSystem.MOCK, ByteArray(16384), 9, 16, 0) }
        assertEquals(11, e.code)
        val crc = c.writeRom(CartSystem.MOCK, ByteArray(16384) { 3 }, 1, 16, 0)
        assertEquals(crc32(ByteArray(16384) { 3 }), crc); assertEquals(Triple(1, 16, 0), dev.lastRomOptions)
    }

    @Test fun conferenciaDepoisDeGravar() {
        val c = OscrClient(SimDevice(), 500, 5000)
        val ok = verifyWritten(c, CartSystem.MOCK, FlashChip.A29040B, RomImage(mockData(), 32, 0, 0))
        assertTrue(ok.ok); assertNull(ok.firstDiff)
        val bad = mockData().also { it[1234] = (it[1234].toInt() xor 0xFF).toByte() }
        val v = verifyWritten(c, CartSystem.MOCK, FlashChip.A29040B, RomImage(bad, 32, 0, 0))
        assertFalse(v.ok); assertEquals(1234, v.firstDiff)
        val short = verifyWritten(c, CartSystem.MOCK, FlashChip.A29040B, RomImage(mockData().copyOf(mockData().size + 10), 32, 0, 0))
        assertFalse(short.ok); assertEquals(mockData().size, short.firstDiff)
    }

    @Test fun simuladorPulaAConferencia() {
        val d = tmp(); val f = File(d, "jogo.nes").also { it.writeBytes(ines(32, 8, 0)) }
        val r = run("--simulate", "--json", "rom-write", "-s", "mock", "-i", f.path, "--yes")
        assertTrue("\"verify\":\"skipped\"" in r.second, r.second)
    }

    // ---------------------------------------------------------------- SNES (flash CFI)
    private fun snesRom(kb: Int, copier: Boolean = false): ByteArray = (if (copier) ByteArray(512) else ByteArray(0)) + ByteArray(kb * 1024) { ((it * 5 + 3) and 0xFF).toByte() }

    @Test fun snesDividePorCapacidadeETiraCabecalhoDeCopiadora() {
        val a = RomImages.splitSnes(snesRom(1024))
        assertEquals(Triple(1024, 2048, 0), Triple(a.prgKb, a.flashKb, a.chrKb)); assertEquals(1024 * 1024, a.body.size)
        assertEquals(4096, RomImages.splitSnes(snesRom(3072)).flashKb)
        assertEquals(4096, RomImages.splitSnes(snesRom(1024), 4096).flashKb)
        assertTrue(RomImages.splitSnes(snesRom(512, copier = true)).body.contentEquals(snesRom(512)))
    }

    @Test fun snesErros() {
        assertEquals(RomImageProblem.SNES_SIZE, assertFailsWith<RomImageException> { RomImages.splitSnes(ByteArray(1000)) }.problem)
        assertEquals(RomImageProblem.SNES_SIZE, assertFailsWith<RomImageException> { RomImages.splitSnes(ByteArray(0)) }.problem)
        assertEquals(RomImageProblem.SNES_TOO_BIG, assertFailsWith<RomImageException> { RomImages.splitSnes(snesRom(6144)) }.problem)
        assertEquals(RomImageProblem.SNES_NO_FIT, assertFailsWith<RomImageException> { RomImages.splitSnes(snesRom(3072), 2048) }.problem)
        assertEquals(RomImageProblem.SNES_CAPACITY, assertFailsWith<RomImageException> { RomImages.splitSnes(snesRom(1024), 1024) }.problem)
    }

    @Test fun chipsPorSistema() {
        assertEquals(listOf(FlashChip.SNES_LOROM, FlashChip.SNES_HIROM), FlashChip.forSystem(CartSystem.SNES))
        assertEquals(listOf(FlashChip.NESMAKER, FlashChip.A29040B), FlashChip.forSystem(CartSystem.NES))
        assertEquals(FlashChip.entries.toList(), FlashChip.forSystem(CartSystem.MOCK))
    }

    @Test fun romWriteSnesSimulado() {
        val d = tmp(); val f = File(d, "jogo.sfc").also { it.writeBytes(snesRom(1024, copier = true)) }
        val r = run("--simulate", "--json", "rom-write", "-s", "mock", "-i", f.path, "--chip", "snes-lorom", "--yes")
        assertEquals(0, r.first, r.second)
        assertTrue("\"chip\":\"snes-lorom\"" in r.second); assertTrue("\"flash_kb\":2048" in r.second); assertTrue("\"bytes\":1048576" in r.second)
    }

    @Test fun romWriteSnesExigeChipDoSnes() {
        val d = tmp(); val f = File(d, "jogo.sfc").also { it.writeBytes(snesRom(512)) }
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "snes", "-i", f.path, "--yes").first)
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "snes", "-i", f.path, "--chip", "nesmaker", "--yes").first)
    }
}
