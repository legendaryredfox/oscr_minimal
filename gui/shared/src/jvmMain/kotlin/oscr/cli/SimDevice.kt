// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/**
 * Dispositivo simulado e síncrono (modo MOCK, sistemas 0 e 255) para `--simulate` e testes: responde dentro de `write`, sem threads.
 * Igual em comportamento a host/oscr_host/sim.py (sem injeção de falhas). O comportamento por sistema real é testado no firmware C++.
 */
class SimDevice(val rom: ByteArray = mockData(), var save: ByteArray = ByteArray(8192) { ((it * 3 + 1) and 0xFF).toByte() }, val powerSwitch: Boolean = false,
                 val railSensor: Boolean = false, val detectAttempts: Int = 1, val voltSelect: Boolean = false, val cartNeeds5v: Boolean = false) : Transport {
    /** Com o sensor do rail a placa tem a chave de 5V em software (D123: não há chave física). */
    private val hasPower get() = powerSwitch || railSensor
    var powered = !(powerSwitch || railSensor)                  // placa com a chave de 5V: começa desligada e recusa comandos de cartucho (D115)
    val powerCalls = mutableListOf<Int>()
    var volt = 2                                                // 1 = 3,3 V, 2 = 5 V (seletor, D138): padrão 5 V; 3,3 V só quando pedido
    val voltCalls = mutableListOf<Int>()
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
    private fun error(code: Int, text: String = "") = push(Proto.T_ERRO, le16(code) + byteArrayOf(text.length.toByte()) + text.encodeToByteArray())
    private fun sendData(off: Int) { val n = minOf(block, data.size - off); push(Proto.T_DATA, le32(off) + data.copyOfRange(off, off + n)) }

    override fun write(data: ByteArray) {
        for (f in dec.feed(data)) { seq = f.seq; handle(f) }
    }

    private fun pushPower() = push(Proto.T_POWER_RESP, byteArrayOf(if (powered) 1 else 0, ((if (railSensor) 2 else 0) or (if (voltSelect) 8 else 0)).toByte(),
        0xFF.toByte(), (if (railSensor) (if (powered) 1 else 0) else 0xFF).toByte(), (if (voltSelect) volt else 0).toByte()))

    private fun handle(f: Frame) {
        val needsCart = f.type in setOf(Proto.T_DETECT, Proto.T_DUMP_ROM, Proto.T_READ_SAVE, Proto.T_WRITE_SAVE, Proto.T_WRITE_ROM, Proto.T_ERASE)
        val first = f.payload.getOrNull(0)?.toInt()?.and(0xFF)
        if (needsCart && first != null && first != 0 && first != 255 && hasPower && !powered) return error(12, "off")    // o MOCK não precisa de cartucho
        when (f.type) {
            Proto.T_POWER -> {
                val action = first ?: 9
                when {
                    action > Power.ON_5V -> error(4, "args")
                    action == Power.ON_3V3 || action == Power.ON_5V -> {
                        if (!(hasPower && voltSelect)) error(1, "sem seletor")
                        else { volt = if (action == Power.ON_3V3) 1 else 2; voltCalls += volt; powered = true; pushPower() }
                    }
                    action == Power.OFF && !hasPower -> error(1, "sem chave")
                    else -> {
                        if (action != Power.STATUS && hasPower) { powerCalls += action; powered = action == Power.ON; if (!powered && voltSelect) volt = 2 }
                        pushPower()
                    }
                }
            }
            Proto.T_INFO -> push(Proto.T_INFO_RESP, byteArrayOf(1, 0, 1, 0, if (hasPower) 57 else 25) + le16(0) + le16(Proto.MAX_PAYLOAD))
            Proto.T_DETECT -> {
                val sys = f.payload.getOrNull(0)?.toInt()?.and(0xFF) ?: 0
                if (sys == 0 || sys == 255) push(Proto.T_DETECT_RESP, byteArrayOf(255.toByte(), 0) + le32(rom.size) + le32(save.size) + byteArrayOf(1, 4) + "MOCK".encodeToByteArray())
                else if (cartReadable) push(Proto.T_DETECT_RESP, byteArrayOf(sys.toByte(), 0) + le32(65536) + le32(0) + byteArrayOf(0, 8) + "SIM CART".encodeToByteArray())
                else push(Proto.T_DETECT_RESP, byteArrayOf(sys.toByte(), 1) + ByteArray(8) + byteArrayOf(0, 0) + (if (detectAttempts > 1) byteArrayOf(detectAttempts.toByte()) else ByteArray(0)))
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
                if (wSize < 0 || (chip < 0x100 && wSize != (prg + chr) * 1024 && !(chr == 0 && wSize in 1..(prg * 1024) && wSize % 2 == 0))) return error(4, "tamanho")   // NES: PRG+CHR; SNES e MD: ROM dentro do flash
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
            Proto.T_ERASE -> {                      // chip 9 "não é reconhecido"; o simulador só entende o sistema MOCK
                val sys = f.payload.getOrNull(0)?.toInt()?.and(0xFF) ?: 0
                if (f.payload.size < 7) return error(4, "args")
                if (sys != 0 && sys != 255) return error(2)
                val chip = f.payload.u16(1)
                if (chip == 9) return error(11, "id")
                lastErase = Triple(chip, f.payload.u16(3), f.payload.u16(5))
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
