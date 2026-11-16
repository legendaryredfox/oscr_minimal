// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.io.File
import kotlin.test.*

/** Leitura do GBA 369-in-1 (F-18, D174). Mesmos casos de host/tests/test_gba369.py e firmware/oscr/pc-tests/test_gba369.cpp. */
class Gba369Test {
    private fun run(vararg argv: String): Int {
        val io = oscr.cli.CliIo({ }, { }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        return oscr.cli.Cli.run(argv.toList(), io)
    }

    @Test fun codigoERegras() {
        assertEquals(0x8000, Gba369.code(0)); assertEquals(0xBF00, Gba369.code(63))
        for ((b, m) in listOf(0 to 0, 0 to 32, 8 to 32, 7 to 4, 63 to 4, 2 to 1, 2 to 3, 0 to 8)) assertNull(Gba369.errorKey(b, m), "$b/$m")
        for ((b, m) in listOf(1 to 0, 1 to 32, 7 to 8, 63 to 8, 2 to 5, 2 to 6, 0 to 33, 64 to 4, -1 to 4)) assertNotNull(Gba369.errorKey(b, m), "$b/$m")
        assertEquals(256L shl 20, Gba369.bytes(0)); assertEquals(32L shl 20, Gba369.bytes(32))
        assertTrue(Proto.MAX_STREAM >= 256 shl 20)
    }

    @Test fun constantesBatemComOFirmware() {
        val h = generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "firmware/oscr/include/dumper/Gba369.h") }.firstOrNull { it.exists() }?.readText()
            ?: return                                              // fora da árvore do repositório (pacote instalado): nada a conferir
        assertEquals(Gba369.FLAG, Regex("kFlag = 0x([0-9A-Fa-f]+)").find(h)!!.groupValues[1].toInt(16))
        assertEquals(Gba369.BANK_MB, Regex("kBankMb = (\\d+)").find(h)!!.groupValues[1].toInt())
        assertEquals(Gba369.TOTAL_MB, Regex("kTotalMb = (\\d+)").find(h)!!.groupValues[1].toInt())
    }

    @Test fun guiAvisaComAsMesmasRegras() {
        assertNull(Rules.gba369(0, 0)); assertEquals(S.V_G369_SIZE0, Rules.gba369(1, 0)?.key); assertEquals(S.V_G369_BANK, Rules.gba369(7, 8)?.key)
        assertEquals(S.V_G369_SIZE, Rules.gba369(2, 6)?.key); assertEquals(S.V_G369_BLOCK, Rules.gba369(64, 4)?.key)
    }

    @Test fun cliRecusaPedidoInvalidoAntesDeFalarComOCartucho() {
        assertEquals(64, run("--simulate", "--json", "dump", "-s", "gba", "--block369", "1"))
        assertEquals(64, run("--simulate", "--json", "dump", "-s", "gba", "--block369", "7", "--prg", "8"))
        assertEquals(64, run("--simulate", "--json", "dump", "-s", "snes", "--block369", "0"))
        assertEquals(64, run("--simulate", "--json", "dump", "-s", "gba", "--block369", "x"))
    }
}
