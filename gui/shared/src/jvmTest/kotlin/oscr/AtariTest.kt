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

/** F-20, D210: Atari 8 bits e Lynx. */
class Atari8Test {
    @Test fun ids() {
        assertEquals(18, CartSystem.A8BIT.id); assertEquals(".rom", CartSystem.A8BIT.ext)
        assertEquals(19, CartSystem.LYNX.id); assertEquals(".lnx", CartSystem.LYNX.ext)
    }

    @Test fun tamanhos() {
        assertEquals(listOf(8, 16, 32, 40, 64, 128), Atari.A8_SIZES.map { Atari.a8Kb(0, it) })
        assertEquals(0, Atari.a8Kb(0, 24)); assertEquals(8, Atari.a8Kb(1, 0)); assertEquals(8, Atari.a8Kb(1, 99)); assertEquals(0, Atari.a8Kb(2, 8))
        assertNull(Rules.atari8(0, 40)); assertNotNull(Rules.atari8(0, 24)); assertNull(Rules.atari8(1, 0)); assertNotNull(Rules.atari8(2, 8))
    }
}

/** F-20, D211: Atari Jaguar. */
class JaguarTest {
    @Test fun idEExtensao() { assertEquals(20, CartSystem.JAGUAR.id); assertEquals(".jag", CartSystem.JAGUAR.ext) }

    @Test fun saves() {
        assertEquals(listOf(128, 256, 512, 1024, 2048, 131072, 0), (0..6).map { Atari.jaguarSaveBytes(it) }); assertEquals(6, Atari.JAGUAR_SAVES.size)
    }

    @Test fun tamanhos() {
        listOf(1024, 2048, 4096).forEach { assertNull(Rules.romSize(CartSystem.JAGUAR, it)) }
        listOf(0, 512, 3072, 6144).forEach { assertNotNull(Rules.romSize(CartSystem.JAGUAR, it)) }
    }
}
