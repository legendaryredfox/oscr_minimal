package oscr

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNotNull
import kotlin.test.assertNull

/** F-20, D209: Atari 5200 e 7800, as mesmas regras de tamanho do firmware (AtariCore.h) e do Python (atari.py). */
class AtariTest {
    @Test fun ids() {
        assertEquals(16, CartSystem.A5200.id); assertEquals(".a52", CartSystem.A5200.ext)
        assertEquals(17, CartSystem.A7800.id); assertEquals(".a78", CartSystem.A7800.ext)
    }

    @Test fun tamanhos5200() {
        assertEquals(listOf(4, 8, 16, 32), listOf(4, 8, 16, 32).map { Atari.a5200Kb(0, it) })
        assertEquals(0, Atari.a5200Kb(0, 12)); assertEquals(16, Atari.a5200Kb(1, 0)); assertEquals(40, Atari.a5200Kb(2, 0)); assertEquals(0, Atari.a5200Kb(3, 16))
    }

    @Test fun tamanhos7800() {
        assertEquals(listOf(16, 32, 48), listOf(16, 32, 48).map { Atari.a7800Kb(0, it) }); assertEquals(0, Atari.a7800Kb(0, 64))
        assertEquals(listOf(128, 144, 64, 128, 64, 64, 144), listOf(1, 2, 3, 4, 5, 6, 8).map { Atari.a7800Kb(it, 0) }); assertEquals(0, Atari.a7800Kb(9, 16))
        assertEquals(listOf(64, 96, 96, 256), listOf(32, 48, 64, 128).map { Atari.a7800Kb(7, it) }); assertEquals(0, Atari.a7800Kb(7, 16))
    }

    @Test fun regrasDaGui() {
        assertNull(Rules.atari(CartSystem.A5200, 0, 16)); assertNotNull(Rules.atari(CartSystem.A5200, 0, 12)); assertNotNull(Rules.atari(CartSystem.A5200, 3, 0))
        assertNull(Rules.atari(CartSystem.A5200, 2, 0))        // tamanho fixo: o campo é ignorado
        assertNull(Rules.atari(CartSystem.A7800, 7, 128)); assertNotNull(Rules.atari(CartSystem.A7800, 7, 16)); assertNotNull(Rules.atari(CartSystem.A7800, 9, 0))
    }
}
