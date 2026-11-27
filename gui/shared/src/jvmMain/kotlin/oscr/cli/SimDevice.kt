// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/**
 * Dispositivo simulado e síncrono (modo MOCK, sistemas 0 e 255) para `--simulate` e testes: responde dentro de `write`, sem threads.
 * Igual em comportamento a host/oscr_host/sim.py (sem injeção de falhas). O comportamento por sistema real é testado no firmware C++.
 */
class SimDevice(val rom: ByteArray = mockData(), var save: ByteArray = ByteArray(8192) { ((it * 3 + 1) and 0xFF).toByte() }, var voltSelect: Boolean = false, val cartNeeds5v: Boolean = false, val selftestReport: List<Triple<Int, Int, Int>> = emptyList(), val mdFlashName: String? = null,
    val boardProfile: Boolean = true, val firmware: Triple<Int, Int, Int> = Triple(0, 2, 0), val systemsMask: Long = 0, val stages: Boolean = true, val clockSupported: Boolean = true, val clockPresent: Boolean = true) : Transport {
    var boardStored = false                                     // o PC gravou o perfil da placa na EEPROM simulada (D162)
    val boardCalls = mutableListOf<Int>()
    var volt = 1                                                // 1 = 3,3 V, 2 = 5 V (seletor, D138): sobe em 3,3 V (estado seguro); o host pede 5 V (padrão)
    var chosen = false                                          // o usuário escolheu 3,3 V
    val voltCalls = mutableListOf<Int>()
    var selftestCalls = 0                                       // achados do autoteste simulado: (tipo, pino a, pino b)
    var clockPpb = 0; var clockStored = false; var clockTest = false                // relógio do Si5351 simulado (F-3)
    val clockCalls = mutableListOf<Pair<Int, Int>>()
    private val cartReadable get() = voltSelect && cartNeeds5v && volt == 2     // cartucho simulado que só lê a 5 V
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
    var lastErase: Triple<Int, Int, Int>? = null

    private fun push(type: Int, payload: ByteArray = ByteArray(0)) { out += encodeFrame(type, seq, payload) }
    /** PROGRESSO com etapa (F-1), como o firmware; `stages = false` imita o firmware antigo, que nunca o emite. */
    private fun stage(stage: Int, total: Int = 0) { if (stages) push(Proto.T_PROGRESSO, le32(0) + le32(total) + byteArrayOf(stage.toByte())) }
    private fun error(code: Int, text: String = "") = push(Proto.T_ERRO, le16(code) + byteArrayOf(text.length.toByte()) + text.encodeToByteArray())
    private fun sendData(off: Int) { val n = minOf(block, data.size - off); push(Proto.T_DATA, le32(off) + data.copyOfRange(off, off + n)) }

    override fun write(data: ByteArray) {
        for (f in dec.feed(data)) { seq = f.seq; handle(f) }
    }

    private fun pushVolt() = push(Proto.T_VOLT_RESP, byteArrayOf(if (voltSelect) 1 else 0, (if (voltSelect) volt else 0).toByte(), if (chosen) 1 else 0))

    private fun handle(f: Frame) {
        val first = f.payload.getOrNull(0)?.toInt()?.and(0xFF)
        when (f.type) {
            Proto.T_VOLT -> {
                val action = first ?: 9
                when {
                    action > Volt.V5V -> error(4, "args")
                    action != Volt.STATUS && !voltSelect -> error(1, "sem seletor")
                    else -> { if (action != Volt.STATUS) { volt = action; chosen = action == Volt.V3V3; voltCalls += volt }; pushVolt() }
                }
            }
            Proto.T_BOARD -> {
                val action = first ?: 255
                when {
                    !boardProfile -> error(1, "board")
                    action > Board.SET || (action == Board.SET && (f.payload.size < 2 || (f.payload[1].toInt() and Board.VOLT_SELECT.inv()) != 0)) -> error(4, "args")
                    else -> {
                        if (action == Board.SET) {
                            boardStored = true; boardCalls += f.payload[1].toInt()
                            val sel = f.payload[1].toInt() and Board.VOLT_SELECT != 0
                            if (sel != voltSelect) { voltSelect = sel; volt = 1; chosen = false }
                        }
                        push(Proto.T_BOARD_RESP, byteArrayOf(if (boardStored) 1 else 0, if (voltSelect) Board.VOLT_SELECT.toByte() else 0))
                    }
                }
            }
            Proto.T_CLOCK -> {
                val pl = f.payload
                val act = if (pl.isNotEmpty()) pl.u8(0) else -1
                when {
                    !clockSupported -> error(1, "sem clock")
                    act !in Clock.STATUS..Clock.TEST_OFF || (act == Clock.SET && pl.size < 5) -> error(4, "args")
                    act == Clock.SET && Math.abs(pl.u32(1)) > Clock.MAX_PPB -> error(4, "ppb")
                    act != Clock.STATUS && !clockPresent -> error(7, "sem Si5351")
                    else -> {
                        val ppb = if (act == Clock.SET) pl.u32(1) else 0
                        clockCalls += act to ppb
                        when (act) { Clock.SET -> { clockPpb = ppb; clockStored = true }; Clock.TEST_ON -> clockTest = true; Clock.TEST_OFF -> clockTest = false }
                        push(Proto.T_CLOCK_RESP, byteArrayOf(if (clockPresent) 1 else 0, if (clockStored) 1 else 0) + le32(clockPpb) + byteArrayOf(if (clockTest) 1 else 0))
                    }
                }
            }
            Proto.T_SELFTEST -> {
                selftestCalls++
                stage(Proto.STAGE_SELFTEST)
                val rep = selftestReport.take(24)
                push(Proto.T_SELFTEST_RESP, byteArrayOf(if (selftestReport.size > 24) 1 else 0, rep.size.toByte()) + rep.flatMap { listOf(it.first.toByte(), it.second.toByte(), it.third.toByte()) }.toByteArray())
            }
            Proto.T_INFO -> push(Proto.T_INFO_RESP, byteArrayOf(1, firmware.first.toByte(), firmware.second.toByte(), firmware.third.toByte(), ((if (voltSelect) 121 else 89) or (if (boardProfile) 128 else 0)).toByte()) + le16((systemsMask and 0xFFFF).toInt()) + le16(Proto.MAX_PAYLOAD) + le16(((systemsMask ushr 16) and 0xFFFF).toInt()) + le32((systemsMask ushr 32).toInt()))
            Proto.T_DETECT -> {
                val sys = f.payload.getOrNull(0)?.toInt()?.and(0xFF) ?: 0
                if (sys == 7 && mdFlashName != null) push(Proto.T_DETECT_RESP, byteArrayOf(sys.toByte(), 0) + le32(8 shl 20) + le32(0) + byteArrayOf(0, mdFlashName.length.toByte()) + mdFlashName.encodeToByteArray())   // chip de flash do Mega Drive simulado (testes do limite de 2 MiB)
                else if (sys == 0 || sys == 255) push(Proto.T_DETECT_RESP, byteArrayOf(255.toByte(), 0) + le32(rom.size) + le32(save.size) + byteArrayOf(1, 4) + "MOCK".encodeToByteArray())
                else if (cartReadable) push(Proto.T_DETECT_RESP, byteArrayOf(sys.toByte(), 0) + le32(65536) + le32(0) + byteArrayOf(0, 8) + "SIM CART".encodeToByteArray())
                else push(Proto.T_DETECT_RESP, byteArrayOf(sys.toByte(), 1) + ByteArray(8) + byteArrayOf(0, 0))
            }
            Proto.T_DUMP_ROM, Proto.T_READ_SAVE -> {
                val sys = f.payload.getOrNull(0)?.toInt()?.and(0xFF) ?: 0
                if (sys != 0 && sys != 255 && !cartReadable) return error(3, "sem cartucho")
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
                    1 -> { phase = 2; stage(Proto.STAGE_READ, data.size); if (data.isEmpty()) { phase = 3; push(Proto.T_END, le32(0) + le32(crc32(data))) } else sendData(0) }
                    2 -> { val next = off + block; if (next < data.size) sendData(next) else { phase = 3; push(Proto.T_END, le32(data.size) + le32(crc32(data))) } }
                    3 -> phase = 0
                }
            }
            Proto.T_WRITE_SAVE -> {
                val sys = f.payload.getOrNull(0)?.toInt()?.and(0xFF) ?: 0
                if (f.payload.size < 7) return error(4, "args")
                wSize = f.payload.u32(1)
                if (sys != 0 && sys != 255 && !(sys == 4 && mdFlashName != null)) return error(2)      // MD só com o chip de flash simulado (testes do limite de 2 MiB)
                if (wSize < 0 || wSize > (1 shl 20)) return error(4)
                wBuf = ByteArray(wSize); wExpected = 0; writing = true
                push(Proto.T_D_ACK, le32(0))
                stage(Proto.STAGE_WRITE, wSize)
            }
            Proto.T_WRITE_ROM -> {                  // chip, PRG e CHR em KB; no simulador o chip 9 "não é reconhecido"
                val sys = f.payload.getOrNull(0)?.toInt()?.and(0xFF) ?: 0
                if (f.payload.size < 13) return error(4, "args")
                wSize = f.payload.u32(1)
                val chip = f.payload.u16(7); val prg = f.payload.u16(9); val chr = f.payload.u16(11)
                lastRomOptions = Triple(chip, prg, chr)
                if (sys != 0 && sys != 255 && !(sys == 4 && mdFlashName != null)) return error(2)      // MD só com o chip de flash simulado (testes do limite de 2 MiB)
                if (chip == 9) return error(11, "id")
                if (wSize < 0 || (chip < 0x100 && wSize != (prg + chr) * 1024 && !(chr == 0 && wSize in 1..(prg * 1024) && wSize % 2 == 0))) return error(4, "tamanho")   // NES: PRG+CHR; SNES e MD: ROM dentro do flash
                wBuf = ByteArray(wSize); wExpected = 0; writing = true; writingRom = true
                stage(Proto.STAGE_ERASE, wSize)
                push(Proto.T_D_ACK, le32(0))
                stage(Proto.STAGE_WRITE, wSize)
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
            Proto.T_ERASE -> {                      // chip 9 "não é reconhecido"; o simulador só entende o sistema MOCK
                val sys = f.payload.getOrNull(0)?.toInt()?.and(0xFF) ?: 0
                if (f.payload.size < 7) return error(4, "args")
                if (sys != 0 && sys != 255 && !(sys == 4 && mdFlashName != null)) return error(2)      // MD só com o chip de flash simulado (testes do limite de 2 MiB)
                val chip = f.payload.u16(1)
                if (chip == 9) return error(11, "id")
                lastErase = Triple(chip, f.payload.u16(3), f.payload.u16(5))
                stage(Proto.STAGE_ERASE)
                push(Proto.T_D_ACK, le32(0))
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
