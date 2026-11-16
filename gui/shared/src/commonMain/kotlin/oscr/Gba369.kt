// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Leitura do GBA 369-in-1 (F-18, D174): as mesmas regras de firmware/oscr/include/dumper/Gba369.h e de host/oscr_host/gba369.py.
 * `mapper` do DUMP_ROM = 0x8000 | (bloco << 8); `prg_kb` = tamanho em MB (0 só no bloco 0: lê os 256 MB, "Read 256MB" do OSCR).
 */
object Gba369 {
    const val FLAG = 0x8000
    const val BANK_MB = 32
    const val TOTAL_MB = 256
    const val MAX_BLOCK = 63

    fun code(block: Int): Int = FLAG or (block shl 8)

    /** Chave da mensagem (cli-messages.tsv) do problema, ou null se o pedido vale. */
    fun errorKey(block: Int, mb: Int): String? = when {
        block !in 0..MAX_BLOCK -> "gba369.block"
        mb == 0 -> if (block == 0) null else "gba369.size0"
        mb !in 1..BANK_MB || (mb >= 4 && mb % 4 != 0) -> "gba369.size"
        (block * 4) % BANK_MB + mb > BANK_MB -> "gba369.bank"
        else -> null
    }

    fun bytes(mb: Int): Long = (if (mb == 0) TOTAL_MB else mb).toLong() shl 20
}
