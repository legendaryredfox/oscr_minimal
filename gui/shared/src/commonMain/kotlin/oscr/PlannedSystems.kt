// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Outros cartuchos que o OSCR lê e que este projeto ainda não suporta (marcadores de lugar; sem id no protocolo, sem hardware, sem firmware).
 * A lista é a mesma de host/oscr_host/planned.py (um teste do host confere). Nomes próprios: não são traduzidos.
 */
class PlannedSystem(val key: String, val label: String)

val PLANNED_SYSTEMS: List<PlannedSystem> = listOf(
    PlannedSystem("a2600", "Atari 2600"), PlannedSystem("a5200", "Atari 5200"), PlannedSystem("a7800", "Atari 7800"), PlannedSystem("a8bit", "Atari 8-bit"),
    PlannedSystem("jaguar", "Atari Jaguar"), PlannedSystem("lynx", "Atari Lynx"), PlannedSystem("astrocade", "Bally Astrocade"),
    PlannedSystem("loopy", "Casio Loopy"), PlannedSystem("pv1000", "Casio PV-1000"), PlannedSystem("channelf", "Fairchild Channel F"),
    PlannedSystem("coleco", "ColecoVision"), PlannedSystem("c64", "Commodore 64"), PlannedSystem("vic20", "Commodore VIC-20"),
    PlannedSystem("cps3", "Capcom CPS3"), PlannedSystem("intellivision", "Intellivision"), PlannedSystem("leapster", "Leapster"),
    PlannedSystem("jammer", "Little Jammer"), PlannedSystem("jammerpro", "Little Jammer Pro"),
    PlannedSystem("vb", "Virtual Boy"), PlannedSystem("pokemini", "Pokémon Mini"), PlannedSystem("ngp", "Neo Geo Pocket"),
    PlannedSystem("odyssey2", "Odyssey 2"), PlannedSystem("pce", "PC Engine / TurboGrafx-16"), PlannedSystem("pcw", "Pocket Challenge W"),
    PlannedSystem("rca2", "RCA Studio II"), PlannedSystem("satellaview", "Satellaview (BS-X)"), PlannedSystem("sfm", "SF Memory"),
    PlannedSystem("supercan", "Super A'can"), PlannedSystem("supervision", "Watara Supervision"),
    PlannedSystem("ti99", "TI-99/4A"), PlannedSystem("pyuuta", "Tomy Pyuuta"), PlannedSystem("trs80", "TRS-80"), PlannedSystem("vectrex", "Vectrex"),
    PlannedSystem("vsmile", "V.Smile"), PlannedSystem("ws", "WonderSwan"), PlannedSystem("msx", "MSX"), PlannedSystem("arcadia", "Arcadia 2001"),
    PlannedSystem("gbsmart", "Game Boy Smart Card"), PlannedSystem("gbmem", "Game Boy Memory"),
)
