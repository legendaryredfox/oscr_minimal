// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * GB Smart Card 32M (F-20, D249): a lista de jogos do "Game Menu" do OSCR, um DETECT por índice. Espelha host/oscr_host/gbsmart.py.
 * O firmware acha o jogo N com o `getGames` do OSCR; `status` 5 = o cartucho tem menos jogos (firmware/oscr/include/dumper/GbSmartCore.h).
 */
object GbSmart {
    const val WHOLE = 0xFF          // mapper 255: a flash inteira (4 MB)
    const val MAX_GAMES = 127       // 4 MB em blocos de 32 KB, menos o menu
    const val ST_PAST_END = 5

    data class Game(val index: Int, val title: String, val romSize: Long, val saveSize: Long, val headerOk: Boolean)

    /** `detect(índice)`: o DETECT_RESP do sistema 33. null = nenhum cartucho; senão a lista (pode ser vazia). */
    fun listGames(detect: (Int) -> DetectResult): List<Game>? {
        val out = mutableListOf<Game>()
        for (n in 0 until MAX_GAMES) {
            val r = detect(n)
            if (r.status == 0 || r.status == 4) { out += Game(n, r.name, r.romSize, r.saveSize, r.status == 0); continue }
            if (r.status == 1 && n == 0) return null
            break
        }
        return out
    }
}
