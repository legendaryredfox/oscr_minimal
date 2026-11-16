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
        assertEquals(listOf(FlashChip.N64_FLASH), FlashChip.forSystem(CartSystem.N64))
        assertFalse(FlashChip.N64_FLASH in FlashChip.forSystem(CartSystem.GBA))
    }

    @Test fun cliRecusaAntesDeFalarComOCartucho() {
        val f = File.createTempFile("n64", ".z64").also { it.deleteOnExit(); it.writeBytes(z64(1024)) }
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "n64", "-i", f.path, "--chip", "gba-flash", "--yes"))
        val bad = File.createTempFile("n64", ".bin").also { it.deleteOnExit(); it.writeBytes(ByteArray(8192)) }
        assertEquals(64, run("--simulate", "--json", "rom-write", "-s", "n64", "-i", bad.path, "--yes"))
    }
}
