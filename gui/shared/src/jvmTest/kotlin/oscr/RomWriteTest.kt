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
        assertEquals(listOf(FlashChip.SNES_LOROM, FlashChip.SNES_HIROM, FlashChip.SNES_LOROM_P0, FlashChip.SNES_HIROM_P0, FlashChip.SNES_EXLOROM_P1, FlashChip.SNES_EXHIROM_P1), FlashChip.forSystem(CartSystem.SNES))
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

    // ---------------------------------------------------------------- Mega Drive (MX29F1610 / S29GL064N)
    private fun mdRom(n: Int) = ByteArray(n) { ((it * 11 + 5) and 0xFF).toByte() }

    @Test fun mdDivideEErros() {
        val a = RomImages.splitMd(mdRom(524288))
        assertEquals(Triple(512, 0, 0), Triple(a.prgKb, a.chrKb, a.flashKb))
        assertEquals(1, RomImages.splitMd(mdRom(1000)).prgKb)
        assertEquals(RomImageProblem.MD_SIZE, assertFailsWith<RomImageException> { RomImages.splitMd(mdRom(1001)) }.problem)
        assertEquals(RomImageProblem.MD_SIZE, assertFailsWith<RomImageException> { RomImages.splitMd(ByteArray(0)) }.problem)
        assertEquals(RomImageProblem.MD_TOO_BIG, assertFailsWith<RomImageException> { RomImages.splitMd(mdRom(8 * 1024 * 1024 + 2)) }.problem)
        val smd = mdRom(512 + 2048).also { "SEGA".encodeToByteArray().copyInto(it, 512 + 0x100) }
        assertEquals(RomImageProblem.MD_SMD, assertFailsWith<RomImageException> { RomImages.splitMd(smd) }.problem)
        assertEquals(listOf(FlashChip.MD_FLASH), FlashChip.forSystem(CartSystem.MD))
    }

    @Test fun romWriteMdSimulado() {
        val d = tmp(); val f = File(d, "jogo.md").also { it.writeBytes(mdRom(524288)) }
        val r = run("--simulate", "--json", "rom-write", "-s", "mock", "-i", f.path, "--chip", "md-flash", "--yes")
        assertEquals(0, r.first, r.second); assertTrue("\"chip\":\"md-flash\"" in r.second); assertTrue("\"bytes\":524288" in r.second)
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "md", "-i", f.path, "--chip", "nesmaker", "--yes").first)
    }

    // ---------------------------------------------------------------- SNES: 2 e 4 chips, 8 MB, P0/P1
    @Test fun snesPlanoVetores() {
        val m = SnesLayouts.MB
        fun p(l: Int, size: Int, cap: Int = 0) = SnesLayouts.plan(l, size, cap).map { listOf(it.chip, it.addr, it.len, it.src) }
        assertEquals(listOf(listOf(1, 0, m, 0)), p(0, 1 * m, 2 * m))
        assertTrue(p(0, 3 * m, 2 * m).isEmpty() && p(0, m, 3 * m).isEmpty() && p(0, 1000, 2 * m).isEmpty())
        assertEquals(listOf(listOf(1, 0, m, 0), listOf(2, 0, 0, 2 * m)), p(1, 1 * m))
        assertEquals(listOf(listOf(1, 0, 2 * m, 0), listOf(2, 0, m, 2 * m)), p(1, 3 * m))
        assertTrue(p(1, 5 * m).isEmpty())
        assertEquals(listOf(listOf(1, 0, 4 * m, 4 * m), listOf(2, 0, 4 * m, 0)), p(2, 8 * m))
        assertEquals(listOf(listOf(1, 0, 2 * m, 4 * m), listOf(2, 0, 4 * m, 0)), p(2, 6 * m))
        assertTrue(p(2, 4 * m).isEmpty())
        assertEquals(listOf(listOf(1, 0, 2 * m, 4 * m), listOf(2, 0, 2 * m, 6 * m), listOf(3, 0, 2 * m, 0), listOf(4, 0, 2 * m, 2 * m)), p(3, 8 * m))
        assertEquals(listOf(listOf(1, 0, 2 * m, 4 * m), listOf(2, 0, 0, 6 * m), listOf(3, 0, 2 * m, 0), listOf(4, 0, 2 * m, 2 * m)), p(3, 6 * m))
        assertTrue(p(3, 2 * m).isEmpty())
        assertEquals(listOf(listOf(1, 0, 4 * m, 4 * m), listOf(1, 4 * m, 4 * m, 0)), p(4, 8 * m))
        assertEquals(listOf(listOf(1, 0, 2 * m, 4 * m), listOf(1, 4 * m, 4 * m, 0)), p(4, 6 * m))
        assertTrue(p(4, 7 * m).isEmpty() && p(9, m).isEmpty())
    }

    @Test fun snesReordenaComoOOscr() {
        val m = SnesLayouts.MB
        val rom = ByteArray(8 * m) { ((it / 4096) and 0xFF).toByte() }
        fun r(from: Int, to: Int) = rom.copyOfRange(from, to)
        val a = RomImages.splitSnes(rom, null, "1x8mb")
        assertEquals(Triple(4, 8192, 8192), Triple(a.layout, a.flashKb, a.prgKb)); assertTrue(a.rom!!.contentEquals(rom))
        assertTrue(a.body.contentEquals(r(4 * m, 8 * m) + r(0, 4 * m)))
        assertTrue(RomImages.splitSnes(rom, null, "4x2mb").body.contentEquals(r(4 * m, 6 * m) + r(6 * m, 8 * m) + r(0, 2 * m) + r(2 * m, 4 * m)))
        assertTrue(RomImages.splitSnes(rom.copyOf(6 * m), null, "4x2mb").body.contentEquals(r(4 * m, 6 * m) + r(0, 2 * m) + r(2 * m, 4 * m)))
        val b = RomImages.splitSnes(rom.copyOf(3 * m), null, "2x2mb")
        assertTrue(b.body.contentEquals(r(0, 3 * m))); assertEquals(4096, b.flashKb)
        assertTrue(RomImages.splitSnes(rom, null, "2x4mb").body.contentEquals(r(4 * m, 8 * m) + r(0, 4 * m)))
        assertEquals(RomImageProblem.SNES_BAD_LAYOUT, assertFailsWith<RomImageException> { RomImages.splitSnes(snesRom(512), null, "4x2mb") }.problem)
        assertEquals(RomImageProblem.SNES_CAPACITY_FIXED, assertFailsWith<RomImageException> { RomImages.splitSnes(rom, 2048, "1x8mb") }.problem)
        assertEquals(RomImageProblem.SNES_LAYOUT, assertFailsWith<RomImageException> { RomImages.splitSnes(rom, null, "3x") }.problem)
    }

    @Test fun snesCodigoDoChipEGenerico() {
        val one = RomImages.splitSnes(snesRom(512))
        assertEquals(0x0001, RomImages.chipCode(FlashChip.SNES_LOROM, one)); assertEquals(0x0002, RomImages.chipCode(FlashChip.SNES_HIROM, one))
        assertEquals(0x0402, RomImages.chipCode(FlashChip.SNES_HIROM, RomImages.splitSnes(snesRom(6144), null, "1x8mb")))
        val g = RomImages.splitSnesGeneric(snesRom(1024), 4, "29f032")
        assertEquals(0x1004, RomImages.chipCode(FlashChip.SNES_EXHIROM_P1, g)); assertEquals(Triple(4096, 1, SnesLayouts.GENERIC), Triple(g.flashKb, g.wireChr, g.layout))
        assertEquals(1, RomImages.chipCode(FlashChip.NESMAKER, one))
        val gl = RomImages.splitSnesGeneric(snesRom(1000), 4, "29gl", 128, 32)
        assertEquals(0, gl.body.size % (128 * 1024)); assertEquals(7 or (17 shl 4) or (5 shl 9), gl.wireChr)
        assertTrue(gl.rom!!.contentEquals(snesRom(1000))); assertTrue(gl.body.drop(1000 * 1024).all { it == 0xFF.toByte() })
        assertEquals(8 or (17 shl 4) or (5 shl 9), RomImages.splitSnesGeneric(snesRom(512), 1, "e28fxxxj3a").wireChr)
        assertEquals(RomImageProblem.GEN_NEEDS_SECTOR, assertFailsWith<RomImageException> { RomImages.splitSnesGeneric(snesRom(512), 4, "29gl") }.problem)
        assertEquals(RomImageProblem.GEN_SECTOR, assertFailsWith<RomImageException> { RomImages.splitSnesGeneric(snesRom(512), 4, "29gl", 100, 32) }.problem)
        assertEquals(RomImageProblem.GEN_BUFFER, assertFailsWith<RomImageException> { RomImages.splitSnesGeneric(snesRom(512), 4, "29gl", 128, 256) }.problem)
        assertEquals(RomImageProblem.GEN_TYPE, assertFailsWith<RomImageException> { RomImages.splitSnesGeneric(snesRom(512), 4, "xx") }.problem)
        assertEquals(RomImageProblem.GEN_MB, assertFailsWith<RomImageException> { RomImages.splitSnesGeneric(snesRom(512), 9, "29f032") }.problem)
        assertEquals(RomImageProblem.GEN_NO_FIT, assertFailsWith<RomImageException> { RomImages.splitSnesGeneric(snesRom(5120), 4, "29f032") }.problem)
    }

    @Test fun romWriteSnesGenericoSimulado() {
        val d = tmp(); val f = File(d, "jogo.sfc").also { it.writeBytes(snesRom(512)) }
        val r = run("--simulate", "--json", "rom-write", "-s", "mock", "-i", f.path, "--chip", "snes-exlorom-p1", "--flash-type", "29f032", "--flash-mb", "2", "--yes")
        assertEquals(0, r.first, r.second); assertTrue("\"flash_kb\":2048" in r.second); assertTrue("\"bytes\":524288" in r.second)
        val e = run("--simulate", "--json", "rom-write", "-s", "mock", "-i", f.path, "--chip", "snes-exlorom-p1", "--yes")
        assertEquals(64, e.first); assertTrue("--flash-type" in e.second)
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "mock", "-i", f.path, "--chip", "snes-lorom", "--layout", "4x2mb", "--yes").first)
    }

    // ---------------------------------------------------------------- GBA
    private fun gbaRom(kb: Int) = ByteArray(kb * 1024) { ((it * 13 + 7) and 0xFF).toByte() }

    @Test fun gbaDivideECodigo() {
        val a = RomImages.splitGba(gbaRom(4096))
        assertEquals(Triple(4096, 0, 4 * 1024 * 1024), Triple(a.prgKb, a.block, a.body.size))
        assertEquals(0x0001, RomImages.chipCode(FlashChip.GBA_FLASH, a))
        assertEquals(0x0501, RomImages.chipCode(FlashChip.GBA_FLASH, RomImages.splitGba(gbaRom(1024), 5)))
        assertEquals(RomImageProblem.GBA_BLOCK, assertFailsWith<RomImageException> { RomImages.splitGba(gbaRom(1), 64) }.problem)
        assertEquals(RomImageProblem.GBA_SIZE, assertFailsWith<RomImageException> { RomImages.splitGba(ByteArray(1000)) }.problem)
        assertEquals(RomImageProblem.GBA_TOO_BIG, assertFailsWith<RomImageException> { RomImages.splitGba(gbaRom(8192), 63) }.problem)
        assertEquals(listOf(FlashChip.GBA_FLASH), FlashChip.forSystem(CartSystem.GBA))
    }

    @Test fun romWriteGbaSimulado() {
        val d = tmp(); val f = File(d, "jogo.gba").also { it.writeBytes(gbaRom(1024)) }
        val r = run("--simulate", "--json", "rom-write", "-s", "mock", "-i", f.path, "--chip", "gba-flash", "--yes")
        assertEquals(0, r.first, r.second); assertTrue("\"chip\":\"gba-flash\"" in r.second); assertTrue("\"bytes\":1048576" in r.second)
        assertEquals(0, run("--simulate", "--json", "rom-write", "-s", "mock", "-i", f.path, "--chip", "gba-flash", "--block369", "3", "--yes").first)
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "gba", "-i", f.path, "--chip", "nesmaker", "--yes").first)
    }

    // ---------------------------------------------------------------- Game Boy
    private fun gbRom(kb: Int) = ByteArray(kb * 1024) { ((it * 17 + 9) and 0xFF).toByte() }

    @Test fun gbDivideECodigos() {
        val a = RomImages.splitGb(gbRom(512), FlashChip.GB_CFI)
        assertEquals(Pair(512, 512 * 1024), Pair(a.prgKb, a.body.size))
        assertEquals((1..8).toList(), FlashChip.forSystem(CartSystem.GB).map { RomImages.chipCode(it, a) })
        assertEquals(32, RomImages.splitGb(gbRom(32), FlashChip.GB_ORANGE_FM).prgKb)
        for ((d, c) in listOf(ByteArray(0) to FlashChip.GB_CFI, ByteArray(16384) to FlashChip.GB_CFI, ByteArray(32768 + 100) to FlashChip.GB_CFI)) {
            assertEquals(RomImageProblem.GB_SIZE, assertFailsWith<RomImageException> { RomImages.splitGb(d, c) }.problem)
        }
        assertEquals(RomImageProblem.GB_TOO_BIG, assertFailsWith<RomImageException> { RomImages.splitGb(gbRom(8192), FlashChip.GB_CFI) }.problem)
        assertEquals(RomImageProblem.GB_ORANGE, assertFailsWith<RomImageException> { RomImages.splitGb(gbRom(64), FlashChip.GB_ORANGE_FM) }.problem)
    }

    @Test fun romWriteGbSimulado() {
        val d = tmp(); val f = File(d, "jogo.gb").also { it.writeBytes(gbRom(256)) }
        val r = run("--simulate", "--json", "rom-write", "-s", "mock", "-i", f.path, "--chip", "gb-diy-mbc5", "--yes")
        assertEquals(0, r.first, r.second); assertTrue("\"chip\":\"gb-diy-mbc5\"" in r.second); assertTrue("\"bytes\":262144" in r.second)
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "gb", "-i", f.path, "--yes").first)
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "gb", "-i", f.path, "--chip", "md-flash", "--yes").first)
    }

    // ---------------------------------------------------------------- programador de flash genérico
    @Test fun flashProgParametrosEDivisao() {
        val a = FlashProg.params("16", 4096)
        assertEquals(Triple(3, 4096, 0), Triple(a.chip, a.prgKb, a.chrWord))
        assertEquals(Pair(4, 4096), FlashProg.params("eprom", null).let { it.chip to it.prgKb })
        val b = FlashProg.params("8", 512, "29f032")
        assertEquals(Triple(1, 512, 1), Triple(b.chip, b.prgKb, b.chrWord))
        assertEquals(7 or (17 shl 4) or (5 shl 9), FlashProg.params("plcc32", 512, "29gl", 128, 32).chrWord)
        assertEquals(0, FlashProg.params("8", 512).chrWord)
        assertEquals(RomImageProblem.FP_NEEDS_TYPE, assertFailsWith<RomImageException> { FlashProg.params("8", 512, needType = true) }.problem)
        assertEquals(RomImageProblem.FP_KB, assertFailsWith<RomImageException> { FlashProg.params("8", null) }.problem)
        assertEquals(RomImageProblem.FP_KB, assertFailsWith<RomImageException> { FlashProg.params("8", 9000) }.problem)
        assertEquals(RomImageProblem.FP_BUS, assertFailsWith<RomImageException> { FlashProg.params("usb", 1) }.problem)
        assertEquals(RomImageProblem.GEN_NEEDS_SECTOR, assertFailsWith<RomImageException> { FlashProg.params("8", 512, "29gl") }.problem)
        val j = FlashProg.split(ByteArray(1024), "16", 1024)
        assertEquals(Triple(3, 1024, 1024), Triple(j.chip, j.prgKb, j.body.size))
        val g = FlashProg.split(ByteArray(1536), "8", 1024, "29gl", 128, 32)
        assertEquals(128 * 1024, g.body.size); assertEquals(1536, g.rom.size); assertTrue(g.body.drop(1536).all { it == 0xFF.toByte() })
        assertEquals(RomImageProblem.FP_SIZE, assertFailsWith<RomImageException> { FlashProg.split(ByteArray(100), "16", 1024) }.problem)
        assertEquals(RomImageProblem.FP_NO_FIT, assertFailsWith<RomImageException> { FlashProg.split(ByteArray(2048), "16", 1) }.problem)
        assertEquals(4096, FlashProg.split(ByteArray(4096 * 1024), "eprom", null).prgKb)
    }

    @Test fun flashComandosSimulados() {
        val d = tmp(); val f = File(d, "chip.bin").also { it.writeBytes(ByteArray(1024)) }
        val w = run("--simulate", "--json", "flash-write", "-s", "mock", "--bus", "16", "--flash-kb", "1024", "-i", f.path, "--yes")
        assertEquals(0, w.first, w.second); assertTrue("\"bus\":\"16\"" in w.second); assertTrue("\"verify\":\"skipped\"" in w.second)
        assertEquals(0, run("--simulate", "--json", "flash-erase", "-s", "mock", "--bus", "8", "--flash-kb", "512", "--flash-type", "29f032", "--yes").first)
        val e = run("--simulate", "--json", "flash-erase", "-s", "mock", "--bus", "8", "--flash-kb", "512", "--yes")
        assertEquals(64, e.first); assertTrue("--flash-type" in e.second)
        assertEquals(64, run("--simulate", "--json", "flash-erase", "-s", "mock", "--bus", "eprom", "--yes").first)
        val b = run("--simulate", "--json", "flash-blank", "-s", "mock", "--bus", "16", "--flash-kb", "32")
        assertEquals(1, b.first); assertTrue("\"blank\":false" in b.second)
        val o = File(d, "lido.bin")
        assertEquals(0, run("--simulate", "--json", "flash-read", "-s", "mock", "--bus", "16", "--flash-kb", "32", "-o", o.path).first)
        assertEquals(32768, o.length().toInt())
        val dev = SimDevice(); val c = OscrClient(dev, 500, 5000)
        assertTrue(c.info().flashProg)
        c.erase(CartSystem.MOCK, 3, 1024, 0); assertEquals(Triple(3, 1024, 0), dev.lastErase)
        assertEquals(11, assertFailsWith<DeviceError> { c.erase(CartSystem.MOCK, 9, 1024, 0) }.code)
    }
}
