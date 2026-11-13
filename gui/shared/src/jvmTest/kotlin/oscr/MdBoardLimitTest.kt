// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertNull

/** Limite de 2 MiB dos cartuchos KY / FlashKit (S29GL) e códigos do autoselect (bancada do md_rewriter, 2026-11-13). */
class MdBoardLimitTest {
    @Test
    fun s29glTemLimiteDe2MiB() {
        val c = MdFlashChip(true, "S29GL064N 017E1000", "S29GL064N", 8L shl 20)
        assertEquals(2L shl 20, c.boardLimitBytes)
        assertEquals("017E1000", c.codes)
        assertEquals(2L shl 20, MdFlashChip(true, "S29GL-7E 017E1A00", "S29GL-7E", 4L shl 20).boardLimitBytes)
    }

    @Test
    fun outrosChipsEChipDesconhecidoNaoTemLimite() {
        assertNull(MdFlashChip(true, "MX29F1610 C2F1", "MX29F1610", 2L shl 20).boardLimitBytes)
        assertNull(MdFlashChip(false, "? FFFFFFFF", null, 0L).boardLimitBytes)
        assertEquals("", MdFlashChip(false, "", null, 0L).codes)
    }
}
