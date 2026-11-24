// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Mappers do Atari 5200 e do Atari 7800 (F-20, D209): os ids dos `readROM` dos núcleos Atari5200.cpp e Atari7800.cpp do OSCR.
 * As mesmas regras estão em host/oscr_host/atari.py e firmware/oscr/include/dumper/AtariCore.h (host/tests/test_atari.py confere as três).
 * Os nomes são nomes próprios: iguais em todos os idiomas. `sized` = tamanhos (KB) que o campo `prg` aceita; vazio = tamanho fixo (o campo é ignorado).
 */
object Atari {
    data class Mapper(val id: Int, val name: String, val sized: List<Int> = emptyList())

    val A5200 = listOf(
        Mapper(0, "Standard 4K/8K/16K/32K", listOf(4, 8, 16, 32)), Mapper(1, "Two Chip 16K"), Mapper(2, "Bounty Bob Strikes Back 40K"),
    )
    val A7800 = listOf(
        Mapper(0, "Standard 16K/32K/48K", listOf(16, 32, 48)), Mapper(1, "SuperGame 128K"), Mapper(2, "SuperGame 144K [78S9]"),
        Mapper(3, "F-18 Hornet 64K [78AB]"), Mapper(4, "Double Dragon/Rampage 128K [78AC]"), Mapper(5, "Realsports Baseball etc. 64K [78S4]"),
        Mapper(6, "Karateka (PAL) 64K [78S4]"), Mapper(7, "Bankset 32K/48K/64K/128K", listOf(32, 48, 64, 128)), Mapper(8, "Crystal Quest/Bounty Bob 144K"),
    )

    fun mappers(system: CartSystem): List<Mapper> = if (system == CartSystem.A5200) A5200 else A7800

    /** KB que o `readROM` lê; 0 se mapper ou tamanho inválido. */
    fun a5200Kb(mapper: Int, kb: Int): Int = when (mapper) {
        0 -> if (kb in listOf(4, 8, 16, 32)) kb else 0
        1 -> 16
        2 -> 40
        else -> 0
    }

    private fun std(kb: Int) = if (kb > 32) 48 else if (kb > 16) 32 else 16

    /** KB que o `readROM` lê; 0 se mapper ou tamanho inválido. O bankset (7) lê duas vezes: acima de 64 KB o SuperGame de 128 KB, senão o padrão. */
    fun a7800Kb(mapper: Int, kb: Int): Int = when (mapper) {
        0 -> if (kb in listOf(16, 32, 48)) kb else 0
        7 -> if (kb in listOf(32, 48, 64, 128)) (if (kb > 64) 256 else 2 * std(kb)) else 0
        1 -> 128; 2 -> 144; 3 -> 64; 4 -> 128; 5, 6 -> 64; 8 -> 144
        else -> 0
    }

    fun kb(system: CartSystem, mapper: Int, kb: Int): Int = if (system == CartSystem.A5200) a5200Kb(mapper, kb) else a7800Kb(mapper, kb)
}
