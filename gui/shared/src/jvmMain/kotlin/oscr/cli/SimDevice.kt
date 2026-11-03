// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/**
 * Dispositivo simulado e síncrono (modo MOCK, sistemas 0 e 255) para `--simulate` e testes: responde dentro de `write`, sem threads.
 * Igual em comportamento a host/oscr_host/sim.py (sem injeção de falhas). O comportamento por sistema real é testado no firmware C++.
 */
class SimDevice(val rom: ByteArray = mockData(), var save: ByteArray = ByteArray(8192) { ((it * 3 + 1) and 0xFF).toByte() }) : Transport {
    private val dec = FrameDecoder()
    private var out = ByteArray(0)
    private var seq = 0
    private var block = Proto.DEFAULT_BLOCK
    private var data = ByteArray(0)
    private var phase = 0                       // 0 = parado, 1 = BEGIN enviado, 2 = DATA, 3 = END enviado
    private var wSize = 0
    private var wBuf = ByteArray(0)
    private var wExpected = 0
    private var writing = false
    private var writingRom = false
    var writtenRom: ByteArray? = null
    var lastRomOptions: Triple<Int, Int, Int>? = null

    private fun push(type: Int, payload: ByteArray = ByteArray(0)) { out += encodeFrame(type, seq, payload) }
    private fun error(code: Int, text: String = "") = push(Proto.T_ERRO, le16(code) + byteArrayOf(text.length.toByte()) + text.encodeToByteArray())
    private fun sendData(off: Int) { val n = minOf(block, data.size - off); push(Proto.T_DATA, le32(off) + data.copyOfRange(off, off + n)) }

    override fun write(data: ByteArray) {
        for (f in dec.feed(data)) { seq = f.seq; handle(f) }
    }

    private fun handle(f: Frame) {
        when (f.type) {
            Proto.T_INFO -> push(Proto.T_INFO_RESP, byteArrayOf(1, 0, 1, 0, 9) + le16(0) + le16(Proto.MAX_PAYLOAD))
            Proto.T_DETECT -> {
                val sys = f.payload.getOrNull(0)?.toInt()?.and(0xFF) ?: 0
                if (sys == 0 || sys == 255) push(Proto.T_DETECT_RESP, byteArrayOf(255.toByte(), 0) + le32(rom.size) + le32(save.size) + byteArrayOf(1, 4) + "MOCK".encodeToByteArray())
                else push(Proto.T_DETECT_RESP, byteArrayOf(sys.toByte(), 1) + ByteArray(8) + byteArrayOf(0, 0))
            }
            Proto.T_DUMP_ROM, Proto.T_READ_SAVE -> {
                val sys = f.payload.getOrNull(0)?.toInt()?.and(0xFF) ?: 0
                if (sys != 0 && sys != 255) return error(3, "sem cartucho")
                block = (if (f.payload.size >= 3) f.payload.u16(1) else 0).takeIf { it > 0 } ?: Proto.DEFAULT_BLOCK
                if (block > Proto.MAX_PAYLOAD - 4) return error(4, "bloco grande")
                val rom = f.type == Proto.T_DUMP_ROM
                data = if (rom) this.rom else save
                phase = 1
                push(Proto.T_BEGIN, byteArrayOf((if (rom) Proto.KIND_ROM else Proto.KIND_SAVE).toByte()) + le32(data.size) + le16(block))
            }
            Proto.T_ACK, Proto.T_NAK -> {
                val off = f.payload.u32(0)
                if (f.type == Proto.T_NAK) { if (phase >= 2) sendData(off); return }
                when (phase) {
                    1 -> { phase = 2; if (data.isEmpty()) { phase = 3; push(Proto.T_END, le32(0) + le32(crc32(data))) } else sendData(0) }
                    2 -> { val next = off + block; if (next < data.size) sendData(next) else { phase = 3; push(Proto.T_END, le32(data.size) + le32(crc32(data))) } }
                    3 -> phase = 0
                }
            }
            Proto.T_WRITE_SAVE -> {
                val sys = f.payload.getOrNull(0)?.toInt()?.and(0xFF) ?: 0
                if (f.payload.size < 7) return error(4, "args")
                wSize = f.payload.u32(1)
                if (sys != 0 && sys != 255) return error(2)
                if (wSize < 0 || wSize > (1 shl 20)) return error(4)
                wBuf = ByteArray(wSize); wExpected = 0; writing = true
                push(Proto.T_D_ACK, le32(0))
            }
            Proto.T_WRITE_ROM -> {                  // chip, PRG e CHR em KB; no simulador o chip 9 "não é reconhecido"
                val sys = f.payload.getOrNull(0)?.toInt()?.and(0xFF) ?: 0
                if (f.payload.size < 13) return error(4, "args")
                wSize = f.payload.u32(1)
                val chip = f.payload.u16(7); val prg = f.payload.u16(9); val chr = f.payload.u16(11)
                lastRomOptions = Triple(chip, prg, chr)
                if (sys != 0 && sys != 255) return error(2)
                if (chip == 9) return error(11, "id")
                if (wSize < 0 || wSize != (prg + chr) * 1024) return error(4, "tamanho")
                wBuf = ByteArray(wSize); wExpected = 0; writing = true; writingRom = true
                push(Proto.T_D_ACK, le32(0))
            }
            Proto.T_H_DATA -> if (writing) {
                val off = f.payload.u32(0); val n = f.payload.size - 4
                if (off == wExpected && off + n <= wSize) { f.payload.copyInto(wBuf, off, 4, 4 + n); wExpected += n; push(Proto.T_D_ACK, le32(off)) }
                else if (off < wExpected) push(Proto.T_D_ACK, le32(off))
            }
            Proto.T_H_END -> if (writing) {
                val total = f.payload.u32(0); val crc = f.payload.u32(4)
                if (total != wSize || wExpected != wSize || crc32(wBuf) != crc) return error(6, "crc")
                if (writingRom) writtenRom = wBuf else save = wBuf
                writing = false; writingRom = false
                push(Proto.T_D_ACK, le32(total))
            }
            Proto.T_ABORT -> { phase = 0; writing = false; push(Proto.T_D_ACK, le32(0)) }
            else -> error(1, "comando")
        }
    }

    override fun read(max: Int, timeoutMs: Long): ByteArray {
        if (out.isEmpty()) return ByteArray(0)
        val n = minOf(max, out.size); val r = out.copyOfRange(0, n); out = out.copyOfRange(n, out.size); return r
    }
}
