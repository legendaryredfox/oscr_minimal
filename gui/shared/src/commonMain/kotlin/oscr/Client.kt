// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import kotlin.time.TimeSource

/** Transporte síncrono (porta serial, simulador...). `read` devolve de 1 a `max` bytes ou vazio no tempo esgotado. */
interface Transport {
    fun write(data: ByteArray)
    fun read(max: Int, timeoutMs: Long): ByteArray
    fun close() {}
    /** false depois de a porta ser fechada ou perdida (cabo desligado). */
    val isOpen: Boolean get() = true
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

    private fun request(type: Int, payload: ByteArray, seq: Int, expect: Set<Int>, timeout: Long, resend: Int = retries, accept: (Frame) -> Boolean = { true }): Frame {
        repeat(resend + 1) {
            send(type, payload, seq)
            val start = TimeSource.Monotonic.markNow()
            while (true) {
                val f = recv(maxOf(0, timeout - start.elapsedNow().inWholeMilliseconds), seq) ?: break
                if (f.type == Proto.T_ERRO) throw parseError(f.payload)
                if (f.type in expect && accept(f)) return f
            }
        }
        throw TimeoutError(Fail.NO_RESPONSE, "0x${type.toString(16)}")
    }

    private fun parseError(p: ByteArray): DeviceError {
        if (p.size < 3) return DeviceError(0)
        return DeviceError(p.u16(0), p.copyOfRange(3, minOf(p.size, 3 + p.u8(2))).decodeToString())
    }

    fun info(): DeviceInfo {
        val p = request(Proto.T_INFO, ByteArray(0), nextSeq(), setOf(Proto.T_INFO_RESP), timeoutMs).payload
        if (p.size < 7) throw ProtocolError(Fail.SHORT_REPLY, "INFO_RESP")
        return DeviceInfo(p.u8(0), "${p.u8(1)}.${p.u8(2)}.${p.u8(3)}", p.u8(4), p.u16(5), if (p.size >= 9) p.u16(7) else Proto.MAX_PAYLOAD)
    }

    /** SELFTEST: autoteste da placa sem cartucho (curtos entre pinos, pull-up do D7, Si5351; P-12). Demora cerca de 45 s no firmware. */
    fun selftest(): SelfTestResult =
        parseSelfTest(request(Proto.T_SELFTEST, ByteArray(0), nextSeq(), setOf(Proto.T_SELFTEST_RESP), maxOf(longTimeoutMs, 90_000L)).payload)

    /** VOLT: consulta ou escolhe a tensão dos slots ([Volt]); seletor 3,3 V/5 V (D138). O firmware espera o rail assentar (~0,2 s). */
    fun voltage(action: Int = Volt.STATUS): VoltState {
        val p = request(Proto.T_VOLT, byteArrayOf(action.toByte()), nextSeq(), setOf(Proto.T_VOLT_RESP), longTimeoutMs).payload
        if (p.size < 3) throw ProtocolError(Fail.SHORT_REPLY, "VOLT_RESP")
        return VoltState(p.u8(0) != 0, when (p.u8(1)) { 1 -> "3v3"; 2 -> "5v"; else -> "5v-fixed" }, p.u8(2) != 0)
    }

    fun detect(system: CartSystem, chip: Int = 0, prgKb: Int = 0, chrKb: Int = 0): DetectResult {
        val opts = if (chip != 0 || prgKb != 0 || chrKb != 0) le16(chip) + le16(prgKb) + le16(chrKb) else ByteArray(0)    // programador de flash genérico: as opções vão no DETECT
        val p = request(Proto.T_DETECT, byteArrayOf(system.id.toByte()) + opts, nextSeq(), setOf(Proto.T_DETECT_RESP), longTimeoutMs).payload
        if (p.size < 12) throw ProtocolError(Fail.SHORT_REPLY, "DETECT_RESP")
        return DetectResult(p.u8(0), p.u8(1), p.u32(2).toLong() and 0xFFFFFFFFL, p.u32(6).toLong() and 0xFFFFFFFFL,
            p.u8(10), p.copyOfRange(12, minOf(p.size, 12 + p.u8(11))).decodeToString())
    }

    /** Pode ser chamado de outra thread (botão Cancelar): o `write` do transporte é sincronizado. */
    fun abort() = send(Proto.T_ABORT, ByteArray(0), nextSeq())

    private fun streamIn(cmd: Int, payload: ByteArray, progress: Progress?, expectKind: Int): DumpResult {
        val seq = nextSeq()
        val begin = request(cmd, payload, seq, setOf(Proto.T_BEGIN), longTimeoutMs).payload
        val kind = begin.u8(0); val size = begin.u32(1)
        if (kind != expectKind) { abort(); throw ProtocolError(Fail.BAD_KIND, "$kind") }
        val unknown = size == -1                                   // núcleos do OSCR: 0xFFFFFFFF = tamanho só no END
        if (!unknown && (size < 0 || size > Proto.MAX_STREAM)) { abort(); throw ProtocolError(Fail.BAD_SIZE, "$size") }
        send(Proto.T_ACK, le32(0), seq)
        var buf = ByteArray(if (unknown) 65536 else size)
        var expected = 0; var idle = 0
        while (true) {
            val f = recv(if (expected == 0) longTimeoutMs else timeoutMs * 3, seq)
            if (f == null) {
                if (++idle > retries) throw TimeoutError(Fail.STALLED)
                send(Proto.T_NAK, le32(expected), seq); continue
            }
            idle = 0
            when (f.type) {
                Proto.T_DATA -> {
                    val off = f.payload.u32(0); val n = f.payload.size - 4
                    when {
                        off == expected && (unknown || off + n <= size) -> {
                            if (unknown) {
                                if (expected.toLong() + n > Proto.MAX_STREAM) { abort(); throw ProtocolError(Fail.BAD_SIZE, "${expected + n}") }
                                if (expected + n > buf.size) buf = buf.copyOf(maxOf(buf.size * 2, expected + n))
                            }
                            f.payload.copyInto(buf, off, 4, 4 + n); expected += n
                            send(Proto.T_ACK, le32(off), seq); progress?.invoke(expected.toLong(), if (unknown) 0L else size.toLong())
                        }
                        off < expected -> send(Proto.T_ACK, le32(off), seq)
                        else -> send(Proto.T_NAK, le32(expected), seq)
                    }
                }
                Proto.T_END -> {
                    val total = f.payload.u32(0); val crc = f.payload.u32(4)
                    if ((!unknown && total != size) || expected != total) { abort(); throw ProtocolError(Fail.BAD_END, "$total/$expected/$size") }
                    if (unknown) buf = buf.copyOf(total)
                    val mine = crc32(buf)
                    if (mine != crc) { abort(); throw DeviceError(6) }
                    send(Proto.T_ACK, le32(total), seq)
                    return DumpResult(buf, mine, kind)
                }
                Proto.T_ERRO -> throw parseError(f.payload)
                Proto.T_BEGIN -> send(Proto.T_ACK, le32(0), seq)
            }
        }
    }

    /** NES/Famicom: `mapper`, `prgKb` e `chrKb` são opcionais (0 = automático/NROM); ver docs/referencia/protocolo.md. */
    fun dumpRom(system: CartSystem, block: Int = 0, mapper: Int = 0, prgKb: Int = 0, chrKb: Int = 0, progress: Progress? = null): DumpResult {
        var p = byteArrayOf(system.id.toByte()) + le16(block)
        if (mapper != 0 || prgKb != 0 || chrKb != 0) p += le16(mapper) + le16(prgKb) + le16(chrKb)
        return streamIn(Proto.T_DUMP_ROM, p, progress, Proto.KIND_ROM)
    }

    /** NES/Famicom: `mapper` 1, 4, 5 ou 69 (PRG-RAM com bateria, 8 KB); `ramKb` 16 ou 32 só nos mappers 1 e 5 (0 = 8 KB). */
    fun readSave(system: CartSystem, block: Int = 0, mapper: Int = 0, ramKb: Int = 0, progress: Progress? = null): DumpResult {
        var p = byteArrayOf(system.id.toByte()) + le16(block)
        if (mapper != 0 || ramKb != 0) p += le16(mapper) + le16(ramKb) + le16(0)
        return streamIn(Proto.T_READ_SAVE, p, progress, Proto.KIND_SAVE)
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

    /**
     * Grava [data] (PRG e depois CHR, sem cabeçalho) numa flash (WRITE_ROM). O dispositivo confere o chip e apaga ANTES do primeiro ACK
     * (até ~20 s no A29040B): o comando espera [beginTimeoutMs] e nunca é reenviado, porque reenviar apagaria de novo.
     */
    /** ERASE: apaga o chip inteiro e só responde no fim; nunca é reenviado (reenviar apagaria de novo). */
    fun erase(system: CartSystem, chip: Int, prgKb: Int, chrKb: Int, timeoutMs: Long = 90_000) {
        request(Proto.T_ERASE, byteArrayOf(system.id.toByte()) + le16(chip) + le16(prgKb) + le16(chrKb), nextSeq(), setOf(Proto.T_D_ACK), timeoutMs, resend = 0)
    }

    fun writeRom(system: CartSystem, data: ByteArray, chip: Int, prgKb: Int, chrKb: Int, block: Int = Proto.DEFAULT_BLOCK, progress: Progress? = null, beginTimeoutMs: Long = 90_000): Int {
        val seq = nextSeq()
        request(Proto.T_WRITE_ROM, byteArrayOf(system.id.toByte()) + le32(data.size) + le16(block) + le16(chip) + le16(prgKb) + le16(chrKb), seq, setOf(Proto.T_D_ACK), beginTimeoutMs,
            resend = 0) { it.payload.u32(0) == 0 }
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
