// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import oscr.cli.OPTIONS
import oscr.cli.parseArgs
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

/** Família Sega de 8 bits (D137): Master System, Game Gear e SG-1000 no protocolo, na CLI e na lista de sistemas. Espelha host/tests/test_sega.py. */
class SegaTest {
    @Test fun idsEExtensoes() {
        assertEquals(8, CartSystem.SMS.id); assertEquals(".sms", CartSystem.SMS.ext)
        assertEquals(9, CartSystem.GG.id); assertEquals(".gg", CartSystem.GG.ext)
        assertEquals(10, CartSystem.SG1000.id); assertEquals(".sg", CartSystem.SG1000.ext)
        val ids = CartSystem.entries.map { it.id }
        assertEquals(ids.size, ids.toSet().size)                  // nenhum id repetido
    }

    @Test fun smsSaiuDosPlanejados() {
        assertFalse(PLANNED_SYSTEMS.any { it.key == "sms" || it.label == "Master System" })
    }

    @Test fun opcoesPorSistema() {
        assertEquals(listOf("mapper", "prg"), OPTIONS["sms"]); assertEquals(listOf("mapper", "prg"), OPTIONS["gg"]); assertEquals(listOf("prg"), OPTIONS["sg1000"])
    }

    @Test fun cliAceitaAdaptadorETamanho() {
        for (s in listOf("sms", "gg", "sg1000")) {
            val a = parseArgs(listOf("detect", "-s", s, "--mapper", "2"))
            assertEquals(s, a.opts["system"]); assertEquals("2", a.opts["mapper"])
            val d = parseArgs(listOf("dump", "-s", s, "--mapper", "1", "--prg", "128"))
            assertEquals("1", d.opts["mapper"]); assertEquals("128", d.opts["prg"])
        }
    }

    @Test fun textosDaGuiNosQuatroIdiomas() {
        for (l in Lang.entries) for (k in listOf(S.SEGA_HINT, S.SEGA_ADAPTER, S.SEGA_ADAPTER_HINT)) assertTrue(I18n.t(l, k).isNotBlank(), "$l $k")
    }
}
