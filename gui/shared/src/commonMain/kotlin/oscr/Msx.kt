// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Mappers do MSX (F-20, D230): os ids do `readROM` do núcleo MSX.cpp do OSCR e a faixa de tamanhos de cada um (`msxmapsize[]` do OSCR legado).
 * As mesmas regras estão em firmware/oscr/include/dumper/MsxCore.h (pc-tests/test_msx.cpp); MsxTest.kt confere as duas.
 * Os nomes são nomes próprios: iguais em todos os idiomas. `rom` = KB de ROM aceitos; `ram` = KB de SRAM aceitos (vazio = sem save).
 */
object Msx {
    data class Mapper(val id: Int, val name: String, val rom: List<Int>, val ram: List<Int> = emptyList())

    val MAPPERS = listOf(
        Mapper(0, "No mapper", listOf(8, 16, 32, 64)),
        Mapper(1, "ASCII8", listOf(64, 128, 256, 512), listOf(2, 8)),
        Mapper(2, "ASCII16", listOf(64, 128, 256, 512, 1024), listOf(2, 8)),
        Mapper(3, "Cross Blaim", listOf(64)),
        Mapper(4, "Game Master 2", listOf(128), listOf(8)),
        Mapper(5, "HAL Note", listOf(1024), listOf(16)),
        Mapper(6, "Harry Fox", listOf(64)),
        Mapper(7, "Koei", listOf(256, 512, 1024), listOf(8, 32)),
        Mapper(8, "Konami (no SCC)", listOf(64, 128, 256, 512, 1024)),
        Mapper(9, "Konami SCC", listOf(128, 256, 512, 1024)),
        Mapper(10, "MSX-DOS2", listOf(64)),
        Mapper(11, "PAC / FM-PAC", listOf(64), listOf(8)),
        Mapper(12, "R-Type", listOf(384)),
        Mapper(13, "Super Lode Runner", listOf(128)),
        Mapper(14, "Hudson Soft Bee Pack", listOf(16, 32)),
    )

    fun mapper(id: Int): Mapper? = MAPPERS.firstOrNull { it.id == id }

    /** Texto do item da lista: id, nome e tamanhos (só números e siglas, iguais em todos os idiomas). */
    fun label(m: Mapper): String = "${m.id} ${m.name} · ROM ${m.rom.joinToString("/")} KB" + (if (m.ram.isNotEmpty()) " · SRAM ${m.ram.joinToString("/")} KB" else "")
}
