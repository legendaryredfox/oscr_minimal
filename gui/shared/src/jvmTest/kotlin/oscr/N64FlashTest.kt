// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.io.File
import kotlin.test.*

/** Gravação de ROM em flash repro de N64 (F-19, D176). Mesmos casos de host/tests/test_rom_write.py e do firmware (N64Core.h: flashBytesValid). */
class N64FlashTest {
    private fun run(vararg argv: String): Int {
        val io = oscr.cli.CliIo({ }, { }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        return oscr.cli.Cli.run(argv.toList(), io)
    }

    private fun z64(kb: Int): ByteArray = ByteArray(kb * 1024) { ((it * 11 + 3) and 0xFF).toByte() }.also { it[0] = 0x80.toByte(); it[1] = 0x37; it[2] = 0x12; it[3] = 0x40 }
    private fun v64(z: ByteArray) = ByteArray(z.size) { z[it xor 1] }
    private fun n64(z: ByteArray) = ByteArray(z.size) { z[it xor 3] }

    @Test fun converteAOrdemECompletaOSetor() {
        val z = z64(1024)
        assertContentEquals(z, RomImages.splitN64(z).body)
        assertContentEquals(z, RomImages.splitN64(v64(z)).body)
        assertContentEquals(z, RomImages.splitN64(n64(z)).body)
        val img = RomImages.splitN64(z.copyOf(z.size - 100))
        assertEquals(1024 * 1024, img.body.size); assertEquals(1024, img.prgKb); assertNull(img.mapper)
        assertTrue((img.body.size - 100 until img.body.size).all { img.body[it] == 0xFF.toByte() })
        assertEquals(1, RomImages.chipCode(FlashChip.N64_FLASH, img))
    }

    @Test fun recusas() {
        for (d in listOf(ByteArray(0), ByteArray(100), ByteArray(8192), byteArrayOf(0, 1, 2, 3) + ByteArray(8192), z64(65 * 1024)))
            assertFailsWith<RomImageException> { RomImages.splitN64(d) }
        assertEquals(64 * 1024 * 1024, RomImages.splitN64(z64(64 * 1024)).body.size)
    }

    @Test fun chipsDoSistema() {
        assertEquals(listOf(FlashChip.N64_FLASH, FlashChip.GAMESHARK, FlashChip.XPLORER64), FlashChip.forSystem(CartSystem.N64).sortedBy { it.code })
        assertFalse(FlashChip.N64_FLASH in FlashChip.forSystem(CartSystem.GBA))
    }

    @Test fun cliRecusaAntesDeFalarComOCartucho() {
        val f = File.createTempFile("n64", ".z64").also { it.deleteOnExit(); it.writeBytes(z64(1024)) }
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "n64", "-i", f.path, "--chip", "gba-flash", "--yes"))
        val bad = File.createTempFile("n64", ".bin").also { it.deleteOnExit(); it.writeBytes(ByteArray(8192)) }
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "n64", "-i", bad.path, "--yes"))
    }

    @Test fun xplorerEmbaralhaComoOHost() {
        // valores calculados por host/oscr_host/romimage.py (xplorer_unscramble, que um teste do host confere contra a fórmula do N64.cpp do OSCR)
        val want = mapOf(0 to 1988, 1 to 1732, 127 to 3085, 128 to 2020, 4095 to 2107, 4096 to 6084, 70000 to 72653, 131071 to 129083)
        for ((a, w) in want) assertEquals(w, RomImages.xplorerUnscramble(a), "a=$a")
        for (block in listOf(0, 1, 31)) assertEquals((0 until 4096).map { block * 4096 + it }.toSet(), (0 until 4096).map { RomImages.xplorerUnscramble(block * 4096 + it) }.toSet())
        val img = ByteArray(256 * 1024) { ((it * 7 + 1) and 0xFF).toByte() }
        val out = RomImages.splitXplorer(img)
        assertContentEquals(img, out.rom); assertEquals(256 * 1024, out.body.size)
        val crc = java.util.zip.CRC32().also { it.update(out.body) }.value
        assertEquals(0xbbf15911L, crc)                                      // o mesmo corpo que o host Python gera
        assertFailsWith<RomImageException> { RomImages.splitXplorer(ByteArray(128 * 1024)) }
    }

    @Test fun gamesharkEAcessorios() {
        val gs = ByteArray(256 * 1024) { it.toByte() }
        assertContentEquals(gs, RomImages.splitGameshark(gs).body)
        for (n in listOf(0, 8 * 1024, 16 * 1024 + 256, 1024 * 1024 + 16 * 1024)) assertFailsWith<RomImageException> { RomImages.splitGameshark(ByteArray(n)) }
        assertEquals(0x8002, FlashChip.GAMESHARK.backupCode); assertEquals(0x8003, FlashChip.XPLORER64.backupCode)
        assertTrue(FlashChip.GAMESHARK.accessory && FlashChip.XPLORER64.accessory && !FlashChip.N64_FLASH.accessory)
        val f = File.createTempFile("gsx", ".bin").also { it.deleteOnExit(); it.writeBytes(ByteArray(1000)) }
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "n64", "--chip", "xplorer64", "-i", f.path, "--yes"))
    }
}
