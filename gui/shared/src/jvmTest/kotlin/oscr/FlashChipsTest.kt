// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class FlashChipsTest {
    @Test fun tabelaCarrega() { assertTrue(FlashChips.count() >= 30) }

    @Test fun achaPeloId() {
        assertEquals(listOf("A" to "01AD"), FlashChips.idsFromText("I=FFFF A=01AD B=0000 S=FFFF"))
        assertEquals(listOf("" to "C2F1"), FlashChips.idsFromText("ID C2F1"))
        val c = FlashChips.candidates("I=FFFF A=01AD B=0000 S=FFFF", "8")
        assertEquals(listOf("AM29F016B"), c.map { it.name }); assertEquals("29f032", c[0].flashType); assertEquals(2L shl 20, c[0].size)
        assertEquals("--flash-type 29f032 --flash-kb 2048", FlashChips.commandHint(c[0], "8"))
    }

    @Test fun mesmoIdDoisChips() {
        val g = FlashChips.candidates("I=FFFF A=FFFF B=017E S=FFFF", "8")
        assertEquals(listOf("S29GL032M", "S29GL064M"), g.map { it.name }.sorted())
        assertTrue("--sector-kb 64 --buffer 32" in FlashChips.commandHint(g[0], "8"))
    }

    @Test fun barramentoEGba() {
        val c = FlashChips.candidates("ID C2F1", "16")
        assertEquals("MX29F1610", c[0].name); assertEquals("--flash-kb 2048", FlashChips.commandHint(c[0], "16"))
        assertTrue(FlashChips.candidates("ID C2F1", "8").isEmpty())
        assertTrue(FlashChips.candidates("ID 227E", "16").isEmpty())
    }
}
