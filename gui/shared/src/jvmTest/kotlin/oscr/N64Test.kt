// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.test.*

/** Nintendo 64 (D158). Igual a host/tests/test_n64.py. */
class N64Test {
    @Test fun nomeDoDetect() {
        val h = N64.parseDetectName("3B941695 NSME SUPER_MARIO_64")
        assertEquals(0x3B941695L, h.crc1); assertEquals("NSME", h.gameId); assertEquals("SUPER MARIO 64", h.title)
        assertNull(N64.parseDetectName("sem formato").crc1); assertNull(N64.parseDetectName("").crc1)
    }

    @Test fun baseDoProjetoAchaPorCrc1() {
        assertTrue(N64Games.byCrc1.size > 900)
        val g = N64Games.byCrc1.getValue(0x033F4C13L).first()
        assertEquals(32, g.sizeMb); assertEquals(0, g.saveType); assertTrue("World Is Not Enough" in g.name)
        val s = N64Games.byCrc1.getValue(0x58FD3F25L).first()
        assertEquals(16, s.sizeMb); assertEquals(1, s.saveType); assertEquals(32768L, s.saveBytes)
        assertTrue(N64Games.byCrc1.values.flatten().all { it.saveType in N64.SAVE_BYTES })       // só tipos que o firmware conhece
    }

    @Test fun infoTrocaNomeETamanhos() {
        val r = DetectResult(11, 0, 0, 0, 0, "58FD3F25 NNSE 1080_SNOWBOARDING")
        val i = N64.info(r, N64Games.byCrc1)
        assertEquals("58FD3F25", i.crc1Hex); assertNotNull(i.game); assertEquals(16, i.game!!.sizeMb)
        val u = N64.info(DetectResult(11, 0, 0, 0, 0, "AAAAAAAA XXXX FOO_BAR"), N64Games.byCrc1)
        assertNull(u.game); assertEquals("FOO BAR", u.header.title)
    }

    @Test fun limites() {
        assertTrue(N64.sizeValid(1) && N64.sizeValid(64) && !N64.sizeValid(0) && !N64.sizeValid(65))
        assertEquals(mapOf(0 to 0L, 1 to 32768L, 2 to 98304L, 4 to 131072L, 5 to 512L, 6 to 2048L), N64.SAVE_BYTES)     // firmware: N64Core.h
        assertTrue(N64.saveTypeValid(5) && !N64.saveTypeValid(3))
        assertEquals(11, CartSystem.N64.id); assertEquals(".z64", CartSystem.N64.ext)
        assertTrue(PLANNED_SYSTEMS.none { it.key == "n64" })
    }
}
