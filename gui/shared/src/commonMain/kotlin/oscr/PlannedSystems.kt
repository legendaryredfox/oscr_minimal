// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Outros cartuchos que o OSCR lê e que este projeto ainda não suporta (marcadores de lugar; sem id no protocolo, sem hardware, sem firmware).
 * `needs3v3`: adaptador de 3,3 V da comunidade (P-16, H-4). A lista é a mesma de host/oscr_host/planned.py (um teste do host confere). Nomes próprios: não são traduzidos.
 */
class PlannedSystem(val key: String, val label: String, val needs3v3: Boolean = false)

val PLANNED_SYSTEMS: List<PlannedSystem> = listOf(
    PlannedSystem("loopy", "Casio Loopy"), 
    PlannedSystem("c64", "Commodore 64"), PlannedSystem("vic20", "Commodore VIC-20"),
    PlannedSystem("cps3", "Capcom CPS3"), PlannedSystem("intellivision", "Intellivision"), PlannedSystem("leapster", "Leapster", true),
    PlannedSystem("jammer", "Little Jammer"), PlannedSystem("jammerpro", "Little Jammer Pro", true),
    PlannedSystem("vb", "Virtual Boy"), PlannedSystem("pokemini", "Pokémon Mini", true),
    PlannedSystem("pce", "PC Engine / TurboGrafx-16"), PlannedSystem("pcw", "Pocket Challenge W"),
    PlannedSystem("satellaview", "Satellaview (BS-X)"), PlannedSystem("sfm", "SF Memory"),
    PlannedSystem("supercan", "Super A'can"),
    PlannedSystem("ti99", "TI-99/4A"), PlannedSystem("trs80", "TRS-80"),
    PlannedSystem("vsmile", "V.Smile", true), PlannedSystem("ws", "WonderSwan"), PlannedSystem("msx", "MSX"),
    PlannedSystem("gbsmart", "Game Boy Smart Card"), PlannedSystem("gbmem", "Game Boy Memory"),
)
