// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Tipo de ROM do SNES forçado pelo PC (F-2, D164). Vai no terceiro campo opcional (`chr_kb`), que o SNES não usa; 0 = pelo cabeçalho.
 * Espelho de host/oscr_host/protocol.py (SNES_TYPES) e de firmware/oscr/include/dumper/SnesType.h.
 */
object SnesType {
    val CODES = linkedMapOf("lorom" to 1, "hirom" to 2, "sa1" to 3, "exhirom" to 4)
}
