// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/** Protocolo serial v1 (docs/protocolo.md). Código comum a todas as plataformas. */
object Proto {
    const val VERSION = 1
    const val MAX_PAYLOAD = 1024
    const val DEFAULT_BLOCK = 512
    const val T_INFO = 0x01; const val T_DETECT = 0x02; const val T_DUMP_ROM = 0x03
    const val T_READ_SAVE = 0x04; const val T_WRITE_SAVE = 0x05; const val T_ACK = 0x06
    const val T_NAK = 0x07; const val T_ABORT = 0x08; const val T_H_DATA = 0x09; const val T_H_END = 0x0A
    const val T_INFO_RESP = 0x81; const val T_DETECT_RESP = 0x82; const val T_BEGIN = 0x83
    const val T_DATA = 0x84; const val T_END = 0x85; const val T_D_ACK = 0x86; const val T_ERRO = 0x87
    const val T_PROGRESSO = 0x88
    const val KIND_ROM = 1; const val KIND_SAVE = 2
    /** Maior leitura aceita (GBA: 32 MB). Acima disso o BEGIN é tratado como defeito. */
    const val MAX_STREAM = 64 shl 20
}

/** Sistemas e extensão do arquivo de ROM. */
enum class CartSystem(val id: Int, val ext: String) {
    SNES(1, ".sfc"), NES(2, ".nes"), FAMICOM(3, ".nes"), MD(4, ".md"), GBA(5, ".gba"), GB(6, ".gb"), MOCK(255, ".bin");
}

/** Motivos de falha do lado do programa. O texto para o usuário vem de `describeError` (traduzido); nenhuma mensagem fixa aqui. */
enum class Fail { NO_RESPONSE, STALLED, OPEN_PORT, SHORT_REPLY, BAD_END, BAD_PAYLOAD, BAD_KIND, BAD_SIZE, PARTIAL_WRITE, DISCONNECTED }

/** O dispositivo respondeu ERRO com este código (docs/protocolo.md, seção de erros). */
class DeviceError(val code: Int, val text: String = "") : Exception("0x${code.toString(16).padStart(4, '0')}${if (text.isNotEmpty()) " ($text)" else ""}")
class ProtocolError(val fail: Fail, val detail: String = "") : Exception("${fail.name}${if (detail.isNotEmpty()) ": $detail" else ""}")
class TimeoutError(val fail: Fail = Fail.NO_RESPONSE, val detail: String = "") : Exception("${fail.name}${if (detail.isNotEmpty()) ": $detail" else ""}")

private val CRC_TABLE = IntArray(256) { n ->
    var c = n
    repeat(8) { c = if (c and 1 != 0) (c ushr 1) xor 0xEDB88320.toInt() else c ushr 1 }
    c
}

/** CRC32 IEEE (igual ao zlib). `start` é o CRC acumulado anterior. */
fun crc32(data: ByteArray, off: Int = 0, len: Int = data.size - off, start: Int = 0): Int {
    var c = start.inv()
    for (i in off until off + len) c = CRC_TABLE[(c xor data[i].toInt()) and 0xFF] xor (c ushr 8)
    return c.inv()
}

class Frame(val type: Int, val seq: Int, val payload: ByteArray)

fun le16(v: Int) = byteArrayOf(v.toByte(), (v shr 8).toByte())
fun le32(v: Int) = byteArrayOf(v.toByte(), (v shr 8).toByte(), (v shr 16).toByte(), (v shr 24).toByte())
fun ByteArray.u8(i: Int) = this[i].toInt() and 0xFF
fun ByteArray.u16(i: Int) = u8(i) or (u8(i + 1) shl 8)
fun ByteArray.u32(i: Int) = u8(i) or (u8(i + 1) shl 8) or (u8(i + 2) shl 16) or (u8(i + 3) shl 24)

fun encodeFrame(type: Int, seq: Int, payload: ByteArray = ByteArray(0)): ByteArray {
    if (payload.size > Proto.MAX_PAYLOAD) throw ProtocolError(Fail.BAD_PAYLOAD, "${payload.size}")
    val body = byteArrayOf(type.toByte(), seq.toByte()) + le16(payload.size) + payload
    return byteArrayOf(0xA5.toByte(), 0x5A) + body + le32(crc32(body))
}

/** Decodificador em fluxo: descarta quadros inválidos e ressincroniza na próxima magia. */
class FrameDecoder {
    private var buf = ByteArray(0)
    var badFrames = 0
        private set

    fun feed(data: ByteArray): List<Frame> {
        buf += data
        val out = ArrayList<Frame>()
        while (true) {
            var i = 0
            while (i + 1 < buf.size && !(buf[i] == 0xA5.toByte() && buf[i + 1] == 0x5A.toByte())) i++
            if (i + 1 >= buf.size) {  // sem magia completa: guarda só um possível 0xA5 final
                buf = if (buf.isNotEmpty() && buf.last() == 0xA5.toByte()) byteArrayOf(0xA5.toByte()) else ByteArray(0)
                break
            }
            if (i > 0) buf = buf.copyOfRange(i, buf.size)
            if (buf.size < 6) break
            val len = buf.u16(4)
            if (len > Proto.MAX_PAYLOAD) { badFrames++; buf = buf.copyOfRange(2, buf.size); continue }
            val total = 6 + len + 4
            if (buf.size < total) break
            val body = buf.copyOfRange(2, 6 + len)
            if (buf.u32(6 + len) != crc32(body)) { badFrames++; buf = buf.copyOfRange(2, buf.size); continue }
            out += Frame(buf.u8(2), buf.u8(3), buf.copyOfRange(6, 6 + len))
            buf = buf.copyOfRange(total, buf.size)
        }
        return out
    }
}

data class DeviceInfo(val proto: Int, val firmware: String, val flags: Int, val systemsMask: Int, val maxPayload: Int) {
    val mock get() = flags and 1 != 0
    val si5351 get() = flags and 2 != 0
}

data class DetectResult(val system: Int, val status: Int, val romSize: Long, val saveSize: Long, val saveType: Int, val name: String)

class DumpResult(val data: ByteArray, val crc32: Int, val kind: Int) {
    val crcHex get() = (crc32.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')
}

/** Padrão do modo MOCK (docs/protocolo.md, seção 9). */
fun mockData(size: Int = 32768) = ByteArray(size) { i -> (i * 7 + (i shr 8)).toByte() }
