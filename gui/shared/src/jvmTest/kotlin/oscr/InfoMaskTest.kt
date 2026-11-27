package oscr

import kotlin.test.Test
import kotlin.test.assertEquals

/** D208: o INFO leva os ids 16 a 31 num u16 no fim; firmware antigo (9 bytes) continua valendo. */
class InfoMaskTest {
    @Test fun idsAltosViramParteDaMascara() {
        val i = DeviceInfo(1, "0.2.0", 0, (1L shl 15) or (1L shl 16) or (1L shl 31), 520)
        assertEquals(setOf(15, 16, 31), i.systemIds)
    }

    /** D232: os ids 32 a 63 vão num u32 no fim (INFO de 15 bytes), e o simulador da CLI os manda. */
    @Test fun ids32a63ViajamNoInfoDe15Bytes() {
        val i = DeviceInfo(1, "0.2.0", 0, (1L shl 31) or (1L shl 32) or (1L shl 63), 520)
        assertEquals(setOf(31, 32, 63), i.systemIds)
        val mask = (1L shl 2) or (1L shl 31) or (1L shl 32) or (1L shl 50)
        val c = OscrClient(oscr.cli.SimDevice(systemsMask = mask))
        assertEquals(setOf(2, 31, 32, 50), c.info().systemIds)
    }
}
