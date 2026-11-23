// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Mappers do Atari 2600 (F-20, D206): os ids do `readROM` do núcleo Atari2600.cpp do OSCR e o tamanho que cada um lê (KB; 0 = E7, 8, 12 ou 16).
 * A mesma tabela está em host/oscr_host/a2600.py e firmware/oscr/include/dumper/AtariCore.h (host/tests/test_a2600.py confere as três).
 * Os nomes são nomes próprios: iguais em todos os idiomas.
 */
object A2600 {
    data class Mapper(val id: Int, val name: String, val kb: Int)

    val MAPPERS = listOf(
        Mapper(0x20, "2K standard", 2), Mapper(0xC0, "CV 2K", 2), Mapper(0x40, "4K standard", 4), Mapper(0x3F, "3F (Tigervision) 8K", 8),
        Mapper(0xE0, "E0 8K", 8), Mapper(0xF8, "F8 8K", 8), Mapper(0x08, "F8SC 8K (RAM)", 8), Mapper(0xF9, "F9 (Time Pilot) 8K", 8),
        Mapper(0xFE, "FE 8K", 8), Mapper(0x0A, "UA 8K", 8), Mapper(0xD0, "DPC 10K", 10), Mapper(0xFA, "FA 12K", 12),
        Mapper(0xE7, "E7 8/12/16K", 0), Mapper(0xF6, "F6 16K", 16), Mapper(0x06, "F6SC 16K (RAM)", 16), Mapper(0x3E, "3E 32K (RAM 32K)", 32),
        Mapper(0xF4, "F4 32K", 32), Mapper(0x04, "F4SC 32K (RAM)", 32), Mapper(0xF0, "F0 64K", 64), Mapper(0x07, "X07 64K", 64),
        Mapper(0xDF, "DFSC 128K", 128), Mapper(0xBA, "SUPERbank 128K", 128), Mapper(0xBB, "SUPERbank 256K", 256),
    )

    fun byId(id: Int): Mapper? = MAPPERS.firstOrNull { it.id == id }
}
