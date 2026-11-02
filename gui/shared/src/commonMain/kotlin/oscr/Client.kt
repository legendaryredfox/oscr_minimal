// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.time.TimeSource

/** Transporte síncrono (porta serial, simulador...). `read` devolve de 1 a `max` bytes ou vazio no tempo esgotado. */
interface Transport {
    fun write(data: ByteArray)
    fun read(max: Int, timeoutMs: Long): ByteArray
    fun close() {}
}

typealias Progress = (done: Long, total: Long) -> Unit

class OscrClient(
    private val t: Transport,
    private val timeoutMs: Long = 1000,
    private val longTimeoutMs: Long = 10_000,
    private val retries: Int = 3,
) {
    private val dec = FrameDecoder()
    private val queue = ArrayDeque<Frame>()
    private var seqCounter = 0

    private fun nextSeq(): Int { seqCounter = (seqCounter + 1) and 0xFF; return seqCounter }
    private fun send(type: Int, payload: ByteArray, seq: Int) = t.write(encodeFrame(type, seq, payload))

    private fun recv(timeout: Long, seq: Int?): Frame? {
        val start = TimeSource.Monotonic.markNow()
        while (true) {
            val i = queue.indexOfFirst { seq == null || it.seq == seq }
            if (i >= 0) return queue.removeAt(i)
            val left = timeout - start.elapsedNow().inWholeMilliseconds
            if (left <= 0) return null
            val d = t.read(1100, minOf(left, 200))
            if (d.isNotEmpty()) queue += dec.feed(d)
        }
    }

    private fun request(type: Int, payload: ByteArray, seq: Int, expect: Set<Int>, timeout: Long, accept: (Frame) -> Boolean = { true }): Frame {
        repeat(retries + 1) {
            send(type, payload, seq)
            val start = TimeSource.Monotonic.markNow()
            while (true) {
                val f = recv(maxOf(0, timeout - start.elapsedNow().inWholeMilliseconds), seq) ?: break
                if (f.type == Proto.T_ERRO) throw parseError(f.payload)
                if (f.type in expect && accept(f)) return f
            }
        }
        throw TimeoutError("sem resposta ao comando 0x${type.toString(16)}")
    }

    private fun parseError(p: ByteArray): DeviceError {
        if (p.size < 3) return DeviceError(0)
        return DeviceError(p.u16(0), p.copyOfRange(3, minOf(p.size, 3 + p.u8(2))).decodeToString())
    }

    fun info(): DeviceInfo {
        val p = request(Proto.T_INFO, ByteArray(0), nextSeq(), setOf(Proto.T_INFO_RESP), timeoutMs).payload
        if (p.size < 7) throw ProtocolError("INFO_RESP curto")
        return DeviceInfo(p.u8(0), "${p.u8(1)}.${p.u8(2)}.${p.u8(3)}", p.u8(4), p.u16(5), if (p.size >= 9) p.u16(7) else Proto.MAX_PAYLOAD)
    }

    fun detect(system: CartSystem): DetectResult {
        val p = request(Proto.T_DETECT, byteArrayOf(system.id.toByte()), nextSeq(), setOf(Proto.T_DETECT_RESP), longTimeoutMs).payload
        if (p.size < 12) throw ProtocolError("DETECT_RESP curto")
        return DetectResult(p.u8(0), p.u8(1), p.u32(2).toLong() and 0xFFFFFFFFL, p.u32(6).toLong() and 0xFFFFFFFFL,
            p.u8(10), p.copyOfRange(12, minOf(p.size, 12 + p.u8(11))).decodeToString())
    }

    fun abort() = send(Proto.T_ABORT, ByteArray(0), nextSeq())

    private fun streamIn(cmd: Int, payload: ByteArray, progress: Progress?): DumpResult {
        val seq = nextSeq()
        val begin = request(cmd, payload, seq, setOf(Proto.T_BEGIN), longTimeoutMs).payload
        val kind = begin.u8(0); val size = begin.u32(1)
        send(Proto.T_ACK, le32(0), seq)
        val buf = ByteArray(size)
        var expected = 0; var idle = 0
        while (true) {
            val f = recv(if (expected == 0) longTimeoutMs else timeoutMs * 3, seq)
            if (f == null) {
                if (++idle > retries) throw TimeoutError("o dispositivo parou de enviar dados")
                send(Proto.T_NAK, le32(expected), seq); continue
            }
            idle = 0
            when (f.type) {
                Proto.T_DATA -> {
                    val off = f.payload.u32(0); val n = f.payload.size - 4
                    when {
                        off == expected && off + n <= size -> {
                            f.payload.copyInto(buf, off, 4, 4 + n); expected += n
                            send(Proto.T_ACK, le32(off), seq); progress?.invoke(expected.toLong(), size.toLong())
                        }
                        off < expected -> send(Proto.T_ACK, le32(off), seq)
                        else -> send(Proto.T_NAK, le32(expected), seq)
                    }
                }
                Proto.T_END -> {
                    val total = f.payload.u32(0); val crc = f.payload.u32(4)
                    if (total != size || expected != size) { abort(); throw ProtocolError("END com total $total, recebido $expected, esperado $size") }
                    val mine = crc32(buf)
                    if (mine != crc) { abort(); throw DeviceError(6, "CRC32 não confere") }
                    send(Proto.T_ACK, le32(total), seq)
                    return DumpResult(buf, mine, kind)
                }
                Proto.T_ERRO -> throw parseError(f.payload)
                Proto.T_BEGIN -> send(Proto.T_ACK, le32(0), seq)
            }
        }
    }

    /** NES/Famicom: `mapper`, `prgKb` e `chrKb` são opcionais (0 = automático/NROM); ver docs/protocolo.md. */
    fun dumpRom(system: CartSystem, block: Int = 0, mapper: Int = 0, prgKb: Int = 0, chrKb: Int = 0, progress: Progress? = null): DumpResult {
        var p = byteArrayOf(system.id.toByte()) + le16(block)
        if (mapper != 0 || prgKb != 0 || chrKb != 0) p += le16(mapper) + le16(prgKb) + le16(chrKb)
        return streamIn(Proto.T_DUMP_ROM, p, progress)
    }

    /** NES/Famicom: `mapper` 1 ou 4 (PRG-RAM com bateria, 8 KB); `ramKb` 16 ou 32 só no mapper 1 (0 = 8 KB). */
    fun readSave(system: CartSystem, block: Int = 0, mapper: Int = 0, ramKb: Int = 0, progress: Progress? = null): DumpResult {
        var p = byteArrayOf(system.id.toByte()) + le16(block)
        if (mapper != 0 || ramKb != 0) p += le16(mapper) + le16(ramKb) + le16(0)
        return streamIn(Proto.T_READ_SAVE, p, progress)
    }

    fun writeSave(system: CartSystem, data: ByteArray, block: Int = Proto.DEFAULT_BLOCK, mapper: Int = 0, ramKb: Int = 0, progress: Progress? = null): Int {
        val seq = nextSeq()
        request(Proto.T_WRITE_SAVE, byteArrayOf(system.id.toByte()) + le32(data.size) + le16(block) + (if (mapper != 0 || ramKb != 0) le16(mapper) + le16(ramKb) + le16(0) else ByteArray(0)), seq, setOf(Proto.T_D_ACK), longTimeoutMs) { it.payload.u32(0) == 0 }
        var off = 0
        while (off < data.size) {
            val n = minOf(block, data.size - off); val o = off
            request(Proto.T_H_DATA, le32(o) + data.copyOfRange(o, o + n), seq, setOf(Proto.T_D_ACK), longTimeoutMs) { it.payload.u32(0) == o }
            off += n; progress?.invoke(off.toLong(), data.size.toLong())
        }
        val crc = crc32(data)
        request(Proto.T_H_END, le32(data.size) + le32(crc), seq, setOf(Proto.T_D_ACK), longTimeoutMs) { it.payload.u32(0) == data.size }
        return crc
    }
}
