// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import oscr.cli.OPTIONS
import oscr.cli.parseArgs
import java.io.File
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** MSX (F-20, D230): sistema 31, mapper e tamanhos de ROM e SRAM, com adaptador, fora dos planejados, textos nos 4 idiomas. Espelha host/tests/test_msx.py e pc-tests/test_msx.cpp. */
class MsxTest {
    @Test fun idEExtensao() {
        assertEquals(31, CartSystem.MSX.id); assertEquals(".rom", CartSystem.MSX.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "msx" })
    }

    @Test fun opcoesEComAdaptador() {
        assertEquals(listOf("mapper", "prg", "ram"), OPTIONS["msx"])
        val a = parseArgs(listOf("save-read", "-s", "msx", "--mapper", "1", "--ram", "8"))
        assertEquals("1", a.opts["mapper"]); assertEquals("8", a.opts["ram"])
        assertTrue(CartSystem.MSX.needsAdapter)
    }

    @Test fun regras() {
        assertNull(Rules.msx(0, 32)); assertNull(Rules.msx(2, 1024)); assertNull(Rules.msx(12, 384)); assertNull(Rules.msx(11, 64))
        assertNotNull(Rules.msx(0, 128)); assertNotNull(Rules.msx(12, 512)); assertNotNull(Rules.msx(11, 32)); assertNotNull(Rules.msx(15, 64))
        assertNull(Rules.msxRam(1, 2)); assertNull(Rules.msxRam(7, 32)); assertNull(Rules.msxRam(5, 16))
        assertNotNull(Rules.msxRam(7, 16)); assertNotNull(Rules.msxRam(0, 8)); assertNotNull(Rules.msxRam(1, 0))
    }

    /** Os KB de cada mapper saem das mesmas faixas de índices de MsxCore.h (tabelas `romSizes` e `ramSizes` do núcleo). */
    @Test fun igualAoFirmware() {
        val h = generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "firmware/oscr/include/dumper/MsxCore.h") }.firstOrNull { it.exists() }?.readText()
        assertNotNull(h)
        val rom = listOf(0, 8, 16, 32, 64, 128, 256, 512, 1024); val ram = listOf(0, 2, 8, 16, 32)
        val rows = Regex("""\{\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*\},\s*//\s*(\d+)""").findAll(h).map { it.groupValues.drop(1).map(String::toInt) }.toList()
        assertEquals(15, rows.size)
        for ((lo, hi, rlo, rhi, id) in rows) {
            val m = Msx.mapper(id)!!
            val romKb = when (id) { 12 -> listOf(384); 11 -> listOf(64); else -> (lo..hi).filter { it > 0 }.map { rom[it] } }
            val ramKb = (rlo..rhi).filter { it > 0 }.map { ram[it] }.filterNot { id == 7 && it == 16 }
            assertEquals(romKb, m.rom, "mapper $id"); assertEquals(ramKb, m.ram, "mapper $id")
        }
    }

    @Test fun textosNosQuatroIdiomas() {
        for (l in Lang.entries) {
            assertTrue(I18n.t(l, S.MSX_HINT).contains("MSX.cpp"), "$l")
            assertTrue(I18n.t(l, S.V_MSX_RAM).contains("PAC"), "$l")
            assertTrue(I18n.t(l, S.V_MSX_SIZE).isNotBlank() && I18n.t(l, S.MSX_MAPPER).contains("MSX"), "$l")
        }
    }
}
