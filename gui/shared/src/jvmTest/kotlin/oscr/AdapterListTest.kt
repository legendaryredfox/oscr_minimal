// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** A lista de sistemas da GUI separa os que precisam de adaptador (D218, pedido do usuário). */
class AdapterListTest {
    @Test fun slotDireto() {
        for (s in listOf(CartSystem.SNES, CartSystem.NES, CartSystem.FAMICOM, CartSystem.MD, CartSystem.GBA, CartSystem.SMS, CartSystem.N64, CartSystem.FLASH))
            assertFalse(s.needsAdapter, s.name)
    }

    @Test fun comAdaptador() {
        for (s in listOf(CartSystem.GB, CartSystem.GG, CartSystem.SG1000, CartSystem.COLECO, CartSystem.NGP, CartSystem.VECTREX, CartSystem.A2600, CartSystem.A5200,
            CartSystem.A7800, CartSystem.A8BIT, CartSystem.LYNX, CartSystem.JAGUAR, CartSystem.ARCADIA, CartSystem.RCA2, CartSystem.PYUUTA, CartSystem.SUPERVISION))
            assertTrue(s.needsAdapter, s.name)
    }

    @Test fun nenhumSistemaFicaSemClassificacaoNoLugarErrado() {
        // todo sistema novo cai em "com adaptador" por padrão: quem acrescentar um de slot direto precisa mexer na lista e neste teste
        val direct = CartSystem.entries.filter { !it.needsAdapter }.map { it.name }.toSet()
        assertEquals(setOf("SNES", "NES", "FAMICOM", "MD", "GBA", "SMS", "N64", "FLASH", "MOCK"), direct)
    }

    @Test fun tituloNosQuatroIdiomas() {
        for (l in Lang.entries) assertTrue(I18n.t(l, S.ADAPTER_TITLE).isNotBlank(), "$l")
    }
}
