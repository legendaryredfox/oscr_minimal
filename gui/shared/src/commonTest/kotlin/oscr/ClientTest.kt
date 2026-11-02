// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.test.Test
import kotlin.test.assertContentEquals
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

/** Dispositivo simulado e síncrono: responde dentro de `write` (sem threads). */
private class FakeDevice(val rom: ByteArray = mockData(), var corruptFirstData: Boolean = false) : Transport {
    private val dec = FrameDecoder()
    private var out = ByteArray(0)
    private var seq = 0
    private var block = 512
    private var corrupted = false

    private fun push(type: Int, payload: ByteArray, corrupt: Boolean = false) {
        val f = encodeFrame(type, seq, payload)
        if (corrupt) f[8] = (f[8].toInt() xor 0xFF).toByte()
        out += f
    }
    private fun data(off: Int) {
        val n = minOf(block, rom.size - off)
        val bad = corruptFirstData && !corrupted && off == 0
        if (bad) corrupted = true
        push(Proto.T_DATA, le32(off) + rom.copyOfRange(off, off + n), bad)
    }

    override fun write(data: ByteArray) {
        for (f in dec.feed(data)) {
            seq = f.seq
            when (f.type) {
                Proto.T_INFO -> push(Proto.T_INFO_RESP, byteArrayOf(1, 0, 1, 0, 1, 0, 0) + le16(1024))
                Proto.T_DUMP_ROM -> {
                    block = f.payload.u16(1).takeIf { it > 0 } ?: 512
                    push(Proto.T_BEGIN, byteArrayOf(1) + le32(rom.size) + le16(block))
                }
                Proto.T_ACK, Proto.T_NAK -> {
                    val off = f.payload.u32(0)
                    if (f.type == Proto.T_NAK) data(off)
                    else if (off == 0 && f.payload.u32(0) == 0 && !began) { began = true; data(0) }
                    else if (off + block < rom.size) data(off + block)
                    else if (off + block >= rom.size && off < rom.size) push(Proto.T_END, le32(rom.size) + le32(crc32(rom)))
                }
            }
        }
    }
    private var began = false
    override fun read(max: Int, timeoutMs: Long): ByteArray {
        if (out.isEmpty()) return ByteArray(0)
        val n = minOf(max, out.size); val r = out.copyOfRange(0, n); out = out.copyOfRange(n, out.size); return r
    }
}

class ClientTest {
    @Test fun opcoesDeMapperViajamNoPayload() {
        var visto = ByteArray(0)
        val espiao = object : Transport {
            override fun write(data: ByteArray) { FrameDecoder().feed(data).forEach { if (it.type == Proto.T_DUMP_ROM) visto = it.payload } }
            override fun read(max: Int, timeoutMs: Long) = ByteArray(0)
        }
        runCatching { OscrClient(espiao, 5, 10, retries = 0).dumpRom(CartSystem.NES, 512, 4, 128, 64) }
        assertEquals(9, visto.size); assertEquals(4, visto.u16(3)); assertEquals(128, visto.u16(5)); assertEquals(64, visto.u16(7))
    }

    @Test fun ramDoSaveViajaNoReadSave() {
        var visto = ByteArray(0)
        val espiao = object : Transport {
            override fun write(data: ByteArray) { FrameDecoder().feed(data).forEach { if (it.type == Proto.T_READ_SAVE) visto = it.payload } }
            override fun read(max: Int, timeoutMs: Long) = ByteArray(0)
        }
        runCatching { OscrClient(espiao, 5, 10, retries = 0).readSave(CartSystem.NES, 512, 1, 32) }
        assertEquals(9, visto.size); assertEquals(1, visto.u16(3)); assertEquals(32, visto.u16(5)); assertEquals(0, visto.u16(7))
    }

    @Test fun info() {
        val i = OscrClient(FakeDevice(), 50, 500).info()
        assertEquals(1, i.proto); assertEquals(true, i.mock); assertEquals(1024, i.maxPayload)
    }

    @Test fun dumpReconstroiArquivoECrc() {
        val seen = ArrayList<Long>()
        val r = OscrClient(FakeDevice(), 50, 500).dumpRom(CartSystem.MOCK) { d, _ -> seen += d }
        assertContentEquals(mockData(), r.data)
        assertEquals(crc32(mockData()), r.crc32)
        assertEquals(32768L, seen.last())
        assertEquals("D1DF4327", r.crcHex)
    }

    @Test fun blocoCorrompidoEReenviado() {
        val r = OscrClient(FakeDevice(corruptFirstData = true), 20, 500).dumpRom(CartSystem.MOCK, 256)
        assertContentEquals(mockData(), r.data)
    }

    @Test fun semDispositivoEstouraOTempo() {
        val silent = object : Transport {
            override fun write(data: ByteArray) {}
            override fun read(max: Int, timeoutMs: Long) = ByteArray(0)
        }
        assertFailsWith<TimeoutError> { OscrClient(silent, 10, 20, retries = 1).info() }
    }
}
