// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull
import kotlin.test.assertNull
import kotlin.test.assertTrue

/** Responde a DUMP_ROM com um BEGIN de tipo e tamanho escolhidos pelo teste e conta os ABORT. */
private class BeginOnly(val kind: Int, val size: Int) : Transport {
    private val dec = FrameDecoder(); private var out = ByteArray(0); var aborts = 0
    override fun write(data: ByteArray) {
        for (f in dec.feed(data)) {
            if (f.type == Proto.T_DUMP_ROM) out += encodeFrame(Proto.T_BEGIN, f.seq, byteArrayOf(kind.toByte()) + le32(size) + le16(512))
            if (f.type == Proto.T_ABORT) aborts++
        }
    }
    override fun read(max: Int, timeoutMs: Long): ByteArray { val n = minOf(max, out.size); val r = out.copyOf(n); out = out.copyOfRange(n, out.size); return r }
}

class RevisaoTest {
    // ---- regras de validação (iguais às do firmware)
    @Test fun nesRegras() {
        assertNull(Rules.nes(0, 0, 0))                                         // automático
        assertNull(Rules.nes(4, 256, 128)); assertNull(Rules.nes(1, 128, 64)); assertNull(Rules.nes(206, 32, 32))
        assertEquals(S.V_UNSUPPORTED_MAPPER, Rules.nes(97, 32, 0)?.key)
        assertEquals(S.V_PRG_REQUIRED, Rules.nes(4, 0, 8)?.key)
        assertEquals(S.V_PRG_MULTIPLE16, Rules.nes(4, 20, 8)?.key)
        assertEquals(S.V_PRG_MULTIPLE32, Rules.nes(7, 48, 0)?.key); assertEquals(S.V_PRG_MULTIPLE32, Rules.nes(66, 48, 8)?.key)
        assertEquals(S.V_CHR_MULTIPLE8, Rules.nes(4, 128, 12)?.key)
        assertEquals(S.V_NO_CHR, Rules.nes(2, 128, 8)?.key)                    // UxROM usa CHR-RAM
        assertEquals(S.V_NEEDS_CHR, Rules.nes(79, 32, 0)?.key)                 // NINA tem CHR-ROM
        assertEquals(Problem(S.V_TOO_BIG_CHR, 128), Rules.nes(1, 128, 256))    // MMC1: CHR até 128 KB
        assertEquals(Problem(S.V_TOO_BIG_PRG, 128), Rules.nes(9, 256, 8))      // MMC2: PRG até 128 KB
        assertEquals(Problem(S.V_TOO_BIG_CHR, 256), Rules.nes(4, 128, 512))
        assertNull(Rules.nes(34, 128, 0)); assertNull(Rules.nes(34, 64, 64)); assertNull(Rules.nes(184, 32, 32)); assertNull(Rules.nes(180, 128, 0))   // lote de D64
        assertEquals(S.V_NO_CHR, Rules.nes(13, 32, 8)?.key); assertEquals(S.V_NEEDS_CHR, Rules.nes(68, 128, 0)?.key); assertEquals(S.V_PRG_MULTIPLE32, Rules.nes(86, 48, 8)?.key)
        assertEquals(Problem(S.V_TOO_BIG_PRG, 32), Rules.nes(184, 64, 8)); assertEquals(Problem(S.V_TOO_BIG_PRG, 512), Rules.nes(34, 1024, 0))
    }

    @Test fun ramESizeRegras() {
        assertNull(Rules.nesRam(4, 0)); assertNull(Rules.nesRam(1, 32)); assertNull(Rules.nesRam(5, 16)); assertNull(Rules.nesRam(4, 8))
        assertEquals(S.V_RAM_VALUES, Rules.nesRam(4, 32)?.key)                 // 16/32 KB só nos mappers 1 e 5
        assertEquals(S.V_RAM_VALUES, Rules.nesRam(1, 24)?.key)
        assertNull(Rules.romSize(CartSystem.SNES, 0)); assertNull(Rules.romSize(CartSystem.SNES, 6144)); assertNull(Rules.romSize(CartSystem.SNES, 8064))
        assertNotNull(Rules.romSize(CartSystem.SNES, 100)); assertNotNull(Rules.romSize(CartSystem.SNES, 8128))
        assertNull(Rules.romSize(CartSystem.MD, 512)); assertNotNull(Rules.romSize(CartSystem.MD, 16)); assertNotNull(Rules.romSize(CartSystem.MD, 9000))
        assertNull(Rules.romSize(CartSystem.GBA, 12345))
    }

    // ---- mensagens de erro traduzidas, sem texto fixo
    @Test fun todoErroTemTextoNosQuatroIdiomas() {
        val errors = Fail.entries.map { ProtocolError(it, "x") } + (1..10).map { DeviceError(it) } + DeviceError(99) + IllegalStateException("boom") + TimeoutError()
        for (lang in Lang.entries) for (e in errors) {
            val msg = describeError(lang, e)
            assertTrue(msg.startsWith(I18n.t(lang, S.ERR_PREFIX) + ":"), "$lang $e")
            assertTrue(msg.length > 12, "$lang $e")
            assertTrue("{0}" !in msg && "{1}" !in msg, "marcador sem trocar: $lang $e")
        }
        // o texto muda com o idioma (nada de português fixo para quem usa inglês)
        assertTrue(describeError(Lang.EN, TimeoutError()) != describeError(Lang.PT, TimeoutError()))
        assertTrue("0x0004" in describeError(Lang.EN, DeviceError(4)))
    }

    @Test fun marcadoresSaoTrocados() {
        assertEquals("Mapper 34 is not read by this firmware yet.", I18n.f(Lang.EN, S.V_UNSUPPORTED_MAPPER, 34))
        assertEquals("1.5 KB/s, 20 s left", I18n.f(Lang.EN, S.SPEED_ETA, "1.5", 20))
    }

    // ---- cliente: tipo e tamanho do BEGIN
    @Test fun clienteRecusaTipoErrado() {
        val t = BeginOnly(kind = 2, size = 100)                               // pediu ROM, o dispositivo anuncia save
        val e = assertFailsWith<ProtocolError> { OscrClient(t, 200, 500, retries = 0).dumpRom(CartSystem.MOCK) }
        assertEquals(Fail.BAD_KIND, e.fail); assertEquals(1, t.aborts)
    }

    @Test fun clienteRecusaTamanhoAbsurdo() {
        val t = BeginOnly(kind = 1, size = Proto.MAX_STREAM + 1)
        val e = assertFailsWith<ProtocolError> { OscrClient(t, 200, 500, retries = 0).dumpRom(CartSystem.MOCK) }
        assertEquals(Fail.BAD_SIZE, e.fail); assertEquals(1, t.aborts)
    }

    // ---- checksum do Game Boy
    @Test fun gameBoyChecksumDoCabecalho() {
        val d = ByteArray(0x8000)
        byteArrayOf(0xCE.toByte(), 0xED.toByte(), 0x66, 0x66).copyInto(d, 0x104)
        "TESTE".encodeToByteArray().copyInto(d, 0x134)
        var x = 0; for (i in 0x134 until 0x14D) x = (x - d.u8(i) - 1) and 0xFF
        d[0x14D] = x.toByte()
        assertEquals(CheckStatus.OK, verifyRom(CartSystem.GB, d).status)
        d[0x14D] = (d[0x14D].toInt() xor 1).toByte()
        assertEquals(CheckStatus.MISMATCH, verifyRom(CartSystem.GB, d).status)
        assertEquals(CheckStatus.NA, verifyRom(CartSystem.GB, ByteArray(0x200)).status)   // sem o logo da Nintendo
    }
}
