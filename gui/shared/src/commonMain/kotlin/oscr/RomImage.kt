// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Prepara um arquivo para o WRITE_ROM: tira o cabeçalho iNES e acha chip, PRG e CHR. Igual a host/oscr_host/romimage.py.
 * No OSCR original isso era feito pelo firmware lendo o arquivo do SD; aqui é o PC.
 */
enum class FlashChip(val key: String, val code: Int, val mapper: Int, val label: String) {
    NESMAKER("nesmaker", 1, 30, "NES Maker (SST 39SF040, mapper 30)"),
    A29040B("a29040b", 2, 0, "A29040B (mapper 0)");

    companion object { fun byKey(k: String) = entries.firstOrNull { it.key == k } }
}

class RomImage(val body: ByteArray, val prgKb: Int, val chrKb: Int, val mapper: Int?)

enum class RomImageProblem { TRUNCATED_HEADER, TRAINER, SIZE_MISMATCH, NEEDS_HEADER, RAW_SIZE, CHIP_UNKNOWN }

class RomImageException(val problem: RomImageProblem, val a: Int = 0, val b: Int = 0, val c: Int = 0) : Exception(problem.name)

object RomImages {
    fun split(data: ByteArray, chip: FlashChip): RomImage {
        if (data.size >= 4 && data[0] == 'N'.code.toByte() && data[1] == 'E'.code.toByte() && data[2] == 'S'.code.toByte() && data[3] == 0x1A.toByte()) {
            if (data.size < 16) throw RomImageException(RomImageProblem.TRUNCATED_HEADER)
            if (data.u8(6) and 4 != 0) throw RomImageException(RomImageProblem.TRAINER)
            val prg = data.u8(4) * 16; val chr = data.u8(5) * 8
            val mapper = (data.u8(6) shr 4) or (data.u8(7) and 0xF0)
            val body = data.copyOfRange(16, data.size)
            if (body.size != (prg + chr) * 1024) throw RomImageException(RomImageProblem.SIZE_MISMATCH, body.size, prg, chr)
            return RomImage(body, prg, chr, mapper)
        }
        if (chip == FlashChip.A29040B) throw RomImageException(RomImageProblem.NEEDS_HEADER)
        if (data.isEmpty() || data.size % 16384 != 0) throw RomImageException(RomImageProblem.RAW_SIZE)
        return RomImage(data, data.size / 1024, 0, null)
    }

    /** [chip] null = pelo mapper do cabeçalho (30 = NES Maker, 0 = A29040B); arquivo cru = NES Maker. */
    fun prepare(data: ByteArray, chip: FlashChip?): Pair<FlashChip, RomImage> {
        if (chip != null) return chip to split(data, chip)
        val first = split(data, FlashChip.NESMAKER)
        val inferred = if (first.mapper == null) FlashChip.NESMAKER else FlashChip.entries.firstOrNull { it.mapper == first.mapper } ?: throw RomImageException(RomImageProblem.CHIP_UNKNOWN)
        return inferred to split(data, inferred)
    }
}

class VerifyResult(val ok: Boolean, val readCrc: Int, val expectedCrc: Int, val firstDiff: Int?, val readBytes: Int)

/**
 * Confere a gravação: lê o cartucho de volta (DUMP_ROM com o mapper do chip e os tamanhos gravados) e compara com o que foi enviado.
 * O OSCR original só confere cada byte durante a gravação; esta leitura completa pega também o que mudou depois. Igual a verify_written em romimage.py.
 */
fun verifyWritten(client: OscrClient, system: CartSystem, chip: FlashChip, img: RomImage, progress: Progress? = null): VerifyResult {
    val res = client.dumpRom(system, 0, chip.mapper, img.prgKb, img.chrKb, progress)
    val d = res.data
    val hasHeader = d.size >= 4 && d[0] == 'N'.code.toByte() && d[1] == 'E'.code.toByte() && d[2] == 'S'.code.toByte() && d[3] == 0x1A.toByte()
    val read = if (hasHeader) d.copyOfRange(16, d.size) else d       // o firmware acrescenta um cabeçalho iNES sintético
    val exp = img.body
    var diff: Int? = null
    if (!read.contentEquals(exp)) {
        val n = minOf(read.size, exp.size)
        diff = (0 until n).firstOrNull { read[it] != exp[it] } ?: n
    }
    return VerifyResult(diff == null, crc32(read), crc32(exp), diff, read.size)
}

