// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import oscr.cli.OPTIONS
import oscr.cli.parseArgs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Pokémon Mini (F-20, D227): sistema 29, sem opções (512 KB fixos), com adaptador, fora dos planejados, aviso nos 4 idiomas. Espelha host/tests/test_pokemini.py e pc-tests/test_pkm.cpp. */
class PokemonMiniTest {
    @Test fun idEExtensao() {
        assertEquals(29, CartSystem.POKEMINI.id); assertEquals(".min", CartSystem.POKEMINI.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)
    }

    @Test fun saiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "pokemini" })
    }

    @Test fun semOpcoesEComAdaptador() {
        assertEquals(emptyList(), OPTIONS["pokemini"])
        assertEquals("pokemini", parseArgs(listOf("dump", "-s", "pokemini")).opts["system"])
        assertTrue(CartSystem.POKEMINI.needsAdapter)
    }

    @Test fun avisoDe3v3NosQuatroIdiomas() {
        for (l in Lang.entries) {
            val txt = I18n.t(l, S.POKEMINI_HINT)
            assertTrue(txt.contains("3.3") || txt.contains("3,3"), "$l")
            assertTrue(txt.contains("PokemonMini.cpp"), "$l")
        }
    }
}
