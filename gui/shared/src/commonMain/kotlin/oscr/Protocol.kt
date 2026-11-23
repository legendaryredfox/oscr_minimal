// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/** Protocolo serial v1 (docs/referencia/protocolo.md). Código comum a todas as plataformas. */
object Proto {
    const val VERSION = 1
    const val MAX_PAYLOAD = 1024
    const val DEFAULT_BLOCK = 512
    const val MIN_BLOCK = 64          // abaixo disso a leitura fica lenta demais (D199)
    const val MAX_BLOCK = 516         // OSCR_MAX_PAYLOAD (520) menos o offset de 4 bytes
    const val T_INFO = 0x01; const val T_DETECT = 0x02; const val T_DUMP_ROM = 0x03
    const val T_READ_SAVE = 0x04; const val T_WRITE_SAVE = 0x05; const val T_WRITE_ROM = 0x0B; const val T_ERASE = 0x0C; const val T_VOLT = 0x0D; const val T_SELFTEST = 0x0E; const val T_BOARD = 0x0F; const val T_CLOCK = 0x10; const val T_ACK = 0x06
    const val T_NAK = 0x07; const val T_ABORT = 0x08; const val T_H_DATA = 0x09; const val T_H_END = 0x0A
    const val T_INFO_RESP = 0x81; const val T_DETECT_RESP = 0x82; const val T_BEGIN = 0x83
    const val T_DATA = 0x84; const val T_END = 0x85; const val T_D_ACK = 0x86; const val T_ERRO = 0x87
    const val T_PROGRESSO = 0x88; const val T_VOLT_RESP = 0x89; const val T_SELFTEST_RESP = 0x8A; const val T_BOARD_RESP = 0x8B; const val T_CLOCK_RESP = 0x8C
    const val KIND_ROM = 1; const val KIND_SAVE = 2
    /** Ordem em que o host tenta conectar (H-3); o firmware abre um só, escolhido na compilação (OSCR_DUMPER_BAUD). */
    val BAUDS = listOf(1_000_000, 500_000, 115_200)
    /** Etapa do PROGRESSO (F-1): o firmware avisa antes de um trabalho longo; 0 = não informada. */
    const val STAGE_NONE = 0; const val STAGE_ERASE = 1; const val STAGE_WRITE = 2; const val STAGE_READ = 3; const val STAGE_SELFTEST = 4
    val STAGE_NAMES = mapOf(STAGE_ERASE to "erasing", STAGE_WRITE to "writing", STAGE_READ to "reading", STAGE_SELFTEST to "selftest")
    /** Acessórios do SNES (F-10, D178): no 3º campo do SNES, a partir de 0x8000 (firmware/oscr/include/dumper/SnesAcc.h). Sufami Turbo: só ROM; GPC: só save de 512 KB. */
    val SNES_ACCESSORIES: Map<String, Int> = linkedMapOf("sufami-a" to 0x8001, "sufami-b" to 0x8002, "gpc" to 0x8003,
        "bsx-pack" to 0x8004, "bsx-sram" to 0x8005, "sfm-flash" to 0x8006, "sfm-map" to 0x8007) + (0..6).associate { "sfm-game-$it" to 0x8010 + it }     // F-11 (D187): Satellaview BS-X e SF Memory Cassette
    const val GPC_BYTES = 0x80000
    /** Acessórios que são RAM (save-read e save-write) e o tamanho do arquivo; os outros são só ROM (dump). */
    val SNES_SAVE_ACCESSORIES: Map<String, Int> = mapOf("gpc" to GPC_BYTES, "bsx-sram" to 0x8000)
    fun snesAccExt(name: String): String = when (name) { "sufami-a", "sufami-b" -> ".st"; "bsx-pack" -> ".bs"; "sfm-flash" -> ".bin"; "sfm-map" -> ".map"; else -> ".sfc" }
    /** Maior leitura aceita (GBA 369-in-1: 256 MB, D174; as outras vão até 64 MB). Acima disso o BEGIN é tratado como defeito. */
    const val MAX_STREAM = 256 shl 20
}

/** Sistemas e extensão do arquivo de ROM. */
enum class CartSystem(val id: Int, val ext: String) {
    SNES(1, ".sfc"), NES(2, ".nes"), FAMICOM(3, ".nes"), MD(4, ".md"), GBA(5, ".gba"), GB(6, ".gb"), FLASH(7, ".bin"), SMS(8, ".sms"), GG(9, ".gg"), SG1000(10, ".sg"), N64(11, ".z64"), COLECO(12, ".col"), NGP(13, ".ngp"), VECTREX(14, ".vec"), A2600(15, ".a26"), MOCK(255, ".bin");
}

/** Motivos de falha do lado do programa. O texto para o usuário vem de `describeError` (traduzido); nenhuma mensagem fixa aqui. */
enum class Fail { NO_RESPONSE, STALLED, OPEN_PORT, SHORT_REPLY, BAD_END, BAD_PAYLOAD, BAD_KIND, BAD_SIZE, PARTIAL_WRITE, DISCONNECTED }

/** O dispositivo respondeu ERRO com este código (docs/referencia/protocolo.md, seção de erros). */
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
    val writeRom get() = flags and 8 != 0
    val flashProg get() = flags and 16 != 0
    /** Placa com o seletor de tensão 3,3 V/5 V (D138). O 5V dos slots fica sempre ligado (D139). */
    val voltageSelect get() = flags and 32 != 0
    /** O firmware tem o autoteste da placa (SELFTEST, P-12). */
    val selftest get() = flags and 64 != 0
    /** O firmware aceita o perfil da placa (BOARD, D162). */
    val boardProfile get() = flags and 128 != 0
    /** Ids dos sistemas que o firmware lê (a máscara `sistemas` do INFO; bit = id do sistema). */
    val systemIds: Set<Int> get() = (0 until 16).filter { systemsMask and (1 shl it) != 0 }.toSet()
}

/** Ações do BOARD e o bit do perfil (D162). */
object Board { const val STATUS = 0; const val SET = 1; const val VOLT_SELECT = 1 }

/** BOARD_RESP (D162). `stored`: há perfil guardado na EEPROM do firmware; `voltageSelect`: o perfil em vigor tem o seletor de tensão. */
data class BoardState(val stored: Boolean, val voltageSelect: Boolean)

/** Ações do VOLT. */
object Volt { const val STATUS = 0; const val V3V3 = 1; const val V5V = 2 }

/** VOLT_RESP (D138). `voltage`: "3v3", "5v" ou "5v-fixed" (placa sem seletor). `chosen`: o usuário escolheu 3,3 V (a placa sobe em 3,3 V sem ninguém ter escolhido;
 *  só a escolha explícita exige confirmação para subir a 5 V). */
data class VoltState(val voltageSelect: Boolean = false, val voltage: String = "5v-fixed", val chosen: Boolean = false)

data class DetectResult(val system: Int, val status: Int, val romSize: Long, val saveSize: Long, val saveType: Int, val name: String)

class DumpResult(val data: ByteArray, val crc32: Int, val kind: Int) {
    val crcHex get() = (crc32.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')
}

/** Padrão do modo MOCK (docs/referencia/protocolo.md, seção 9). */
fun mockData(size: Int = 32768) = ByteArray(size) { i -> (i * 7 + (i shr 8)).toByte() }

/** Achado do SELFTEST: `kind` é "gnd", "pair", "pullup" ou "clockgen"; `pins` são nomes como D30 ou A3. */
data class SelfTestFinding(val kind: String, val pins: List<String>)

/** SELFTEST_RESP (P-12). `truncated`: houve mais achados do que cabem na resposta. */
data class SelfTestResult(val ok: Boolean, val truncated: Boolean, val findings: List<SelfTestFinding>)

/** Nome do pino na numeração do Arduino Mega: 54 em diante são A0... */
fun pinName(pin: Int): String = if (pin >= 54) "A${pin - 54}" else "D$pin"

fun parseSelfTest(p: ByteArray): SelfTestResult {
    if (p.size < 2 || p.size < 2 + p.u8(1) * 3) throw ProtocolError(Fail.SHORT_REPLY, "SELFTEST_RESP")
    val findings = (0 until p.u8(1)).map { i ->
        val k = p.u8(2 + i * 3); val a = p.u8(3 + i * 3); val b = p.u8(4 + i * 3)
        when (k) {
            1 -> SelfTestFinding("gnd", listOf(pinName(a)))
            2 -> SelfTestFinding("pair", listOf(pinName(a), pinName(b)))
            3 -> SelfTestFinding("pullup", listOf(pinName(a)))
            4 -> SelfTestFinding("clockgen", emptyList())
            else -> SelfTestFinding("unknown$k", emptyList())
        }
    }
    return SelfTestResult(findings.isEmpty() && p.u8(0) == 0, p.u8(0) != 0, findings)
}

/** Relógio do Si5351 (CLOCK, F-3; docs/referencia/protocolo.md): ações, limite de segurança do projeto e as saídas de teste com onde medir (wiki do OSCR, P-03). */
object Clock {
    const val STATUS = 0; const val SET = 1; const val TEST_ON = 2; const val TEST_OFF = 3
    const val MAX_PPB = 1_000_000
    val TARGETS = listOf(ClockTarget("CLK0", 4_000_000, "clock.where_ext"), ClockTarget("CLK2", 3_072_000, "clock.where_cic"), ClockTarget("CLK1", 1_000_000, "clock.where_cpu"))
}
data class ClockTarget(val output: String, val hz: Int, val whereKey: String)
data class ClockState(val present: Boolean, val stored: Boolean, val ppb: Int, val test: Boolean)

fun buildClock(action: Int, ppb: Int = 0): ByteArray {
    if (action != Clock.SET) return byteArrayOf(action.toByte())
    require(ppb in -Clock.MAX_PPB..Clock.MAX_PPB) { "fator fora de ±${Clock.MAX_PPB} ppb" }
    return byteArrayOf(action.toByte()) + le32(ppb)
}

fun parseClock(p: ByteArray): ClockState {
    if (p.size < 7) throw ProtocolError(Fail.SHORT_REPLY, "CLOCK_RESP")
    return ClockState(p.u8(0) != 0, p.u8(1) != 0, p.u32(2), p.u8(6) != 0)
}

/** Fator (ppb) que corrige uma saída medida em [measuredHz] quando o alvo é [targetHz], com [currentPpb] já em vigor na medição.
 *  A biblioteca trata a referência como ref*(1+c/1e9): medida/alvo = (1+e)/(1+c0/1e9), então c = ((medida/alvo)*(1+c0/1e9) - 1)*1e9. */
fun clockFactorFromMeasure(measuredHz: Double, targetHz: Double, currentPpb: Int = 0): Long {
    require(measuredHz > 0 && targetHz > 0) { "frequências devem ser positivas" }
    return Math.round(((measuredHz / targetHz) * (1 + currentPpb / 1e9) - 1) * 1e9)
}
