package oscr

import kotlin.test.Test
import kotlin.test.assertEquals

/** D208: o INFO leva os ids 16 a 31 num u16 no fim; firmware antigo (9 bytes) continua valendo. */
class InfoMaskTest {
    @Test fun idsAltosViramParteDaMascara() {
        val i = DeviceInfo(1, "0.2.0", 0, (1 shl 15) or (1 shl 16) or (1 shl 31), 520)
        assertEquals(setOf(15, 16, 31), i.systemIds)
    }
}
