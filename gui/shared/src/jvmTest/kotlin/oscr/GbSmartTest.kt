// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull
import kotlin.test.assertTrue
import kotlin.test.assertFalse

/** GB Smart Card 32M (F-20, D249): sistema 33 e a lista de jogos por DETECT (espelha host/tests/test_gbsmart.py). */
class GbSmartTest {
    private fun fake(games: List<Triple<String, Long, Int>>, cart: Boolean = true): Pair<(Int) -> DetectResult, MutableList<Int>> {
        val calls = mutableListOf<Int>()
        val f: (Int) -> DetectResult = { n ->
            calls += n
            when {
                !cart -> DetectResult(33, 1, 0, 0, 0, "")
                n < games.size -> DetectResult(33, games[n].third, games[n].second, 8192, 1, games[n].first)
                else -> DetectResult(33, GbSmart.ST_PAST_END, 0, 0, 0, "")
            }
        }
        return f to calls
    }

    @Test fun idEExtensao() {
        assertEquals(33, CartSystem.GBSMART.id)
        assertEquals(".gb", CartSystem.GBSMART.ext)
        assertTrue(PLANNED_SYSTEMS.none { it.key == "gbsmart" })
    }

    @Test fun listaParaNoFim() {
        val (f, calls) = fake(listOf(Triple("TETRIS", 32768L, 0), Triple("ZELDA", 524288L, 4)))
        val g = GbSmart.listGames(f)!!
        assertEquals(listOf("TETRIS", "ZELDA"), g.map { it.title })
        assertTrue(g[0].headerOk); assertFalse(g[1].headerOk)
        assertEquals(listOf(0, 1, 2), calls)
    }

    @Test fun semCartuchoEVazia() {
        assertNull(GbSmart.listGames(fake(emptyList(), cart = false).first))
        assertEquals(0, GbSmart.listGames(fake(emptyList()).first)!!.size)
    }

    @Test fun limite() {
        val (f, calls) = fake(List(200) { Triple("X", 32768L, 0) })
        assertEquals(GbSmart.MAX_GAMES, GbSmart.listGames(f)!!.size)
        assertEquals(127, calls.size)
        assertEquals(0xFF, GbSmart.WHOLE)
    }
}
