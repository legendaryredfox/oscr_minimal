// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Prepara um arquivo para o WRITE_ROM: tira o cabeçalho iNES e acha chip, PRG e CHR. Igual a host/oscr_host/romimage.py.
 * No OSCR original isso era feito pelo firmware lendo o arquivo do SD; aqui é o PC.
 */
enum class FlashChip(val key: String, val code: Int, val mapper: Int, val label: String, val snes: Boolean = false, val md: Boolean = false, val generic: Boolean = false, val gba: Boolean = false, val gb: Boolean = false) {
    NESMAKER("nesmaker", 1, 30, "NES Maker (SST 39SF040, mapper 30)"),
    A29040B("a29040b", 2, 0, "A29040B (mapper 0)"),
    /** SNES: flash CFI de um chip só, com a fiação de LoROM ou de HiROM (menu "CFI LoROM / CFI HiROM" do OSCR). */
    SNES_LOROM("snes-lorom", 1, 0, "SNES flash CFI (fiação LoROM)", true),
    SNES_HIROM("snes-hirom", 2, 0, "SNES flash CFI (fiação HiROM)", true),
    /** SNES, menus "LoROM/HiROM (P0)" e "ExLoROM/ExHiROM (P1)": flash de 8 bits de tipo informado pelo usuário (no OSCR vinha do banco CRDB). */
    SNES_LOROM_P0("snes-lorom-p0", 1, 0, "SNES flash de 8 bits, LoROM (P0)", true, generic = true),
    SNES_HIROM_P0("snes-hirom-p0", 2, 0, "SNES flash de 8 bits, HiROM (P0)", true, generic = true),
    SNES_EXLOROM_P1("snes-exlorom-p1", 3, 0, "SNES flash de 8 bits, ExLoROM (P1)", true, generic = true),
    SNES_EXHIROM_P1("snes-exhirom-p1", 4, 0, "SNES flash de 8 bits, ExHiROM (P1)", true, generic = true),
    /** Game Boy (GB.cpp): menus "GB 29F/39SF Repro" (seis variantes) e "GB CFI Repro"; o campo chip é o número do item. */
    GB_DIY_MBC3("gb-diy-mbc3", 1, 0, "GB flash 29F, DIY MBC3 (WR)", gb = true),
    GB_DIY_MBC5("gb-diy-mbc5", 2, 0, "GB flash 29F, DIY MBC5 (WR)", gb = true),
    GB_HDR_MBC30("gb-hdr-mbc30", 3, 0, "GB flash 29F, HDR MBC30 (WE no pino de áudio)", gb = true),
    GB_CAM_FIRST("gb-cam-first", 4, 0, "GB flash 29F, HDR GameBoy Cam, 1º jogo (apaga)", gb = true),
    GB_CAM_SECOND("gb-cam-second", 5, 0, "GB flash 29F, HDR GameBoy Cam, 2º jogo (sem apagar)", gb = true),
    GB_ORANGE_FM("gb-orange-fm", 6, 0, "GB flash 39SF010 sem MBC, Orange FM (32 KB)", gb = true),
    GB_39SF_MBC5("gb-39sf-mbc5", 7, 0, "GB flash 39SF040, MBC5 (WE no pino de áudio)", gb = true),
    GB_CFI("gb-cfi", 8, 0, "GB flash CFI", gb = true),
    /** GBA: o firmware identifica o chip pelo ID (Intel 4000/4400, MX29GL128E, MSP55LV128, PC28F256M29, M29W128GH, 369-in-1). */
    GBA_FLASH("gba-flash", 1, 0, "GBA flash (Intel 4000/4400, MX29GL128E, MSP55LV128, PC28F256M29, M29W128GH, 369-in-1)", gba = true),
    /** Mega Drive: o firmware identifica o chip (MX29F1610 de 2 MB ou S29GL064N de 4 MB) pelo ID. */
    MD_FLASH("md-flash", 1, 0, "Mega Drive flash (o firmware identifica o chip: MX29F1610, S29GL064N, M29W/MX29LV 32 e 64 Mbit, MX29L3211, PA28F400, SST39VF)", md = true);

    companion object {
        fun byKey(k: String) = entries.firstOrNull { it.key == k }
        /** Chips que o sistema aceita ([CartSystem.MOCK] aceita todos, para o simulador). */
        fun forSystem(s: CartSystem) = entries.filter { s == CartSystem.MOCK || (it.snes == (s == CartSystem.SNES) && it.md == (s == CartSystem.MD) && it.gba == (s == CartSystem.GBA) && it.gb == (s == CartSystem.GB)) }
    }
}

/**
 * [flashKb] só no SNES: capacidade do flash em KB (vai no campo prg_kb do WRITE_ROM); [prgKb] é o tamanho da ROM.
 * [layout] só no SNES: disposição ([SnesLayouts]) ou [SnesLayouts.GENERIC]; [wireChr]: campo chr_kb do WRITE_ROM no modo genérico (tipo | setor << 4 | buffer << 9);
 * [rom]: a ROM original, que a conferência compara com a leitura ([body] vem reordenado e completado).
 */
class RomImage(val body: ByteArray, val prgKb: Int, val chrKb: Int, val mapper: Int?, val flashKb: Int = 0,
               val layout: Int = 0, val wireChr: Int = 0, val rom: ByteArray? = null, val block: Int = 0)

/** Disposições do flash CFI do SNES (parte alta do campo chip do WRITE_ROM); igual a SNES_LAYOUTS em romimage.py e a SnesPlan.h no firmware. */
/** Campos do comando do programador de flash genérico (sistema 7); [body] é o que vai ao chip e [rom] o arquivo original, que a conferência compara com a leitura. */
class FlashJob(val chip: Int, val prgKb: Int, val chrWord: Int, val body: ByteArray = ByteArray(0), val rom: ByteArray = ByteArray(0))

/** Programador de flash genérico (firmware/oscr/include/dumper/FlashProg.h). Igual a flashprog_params e split_flashprog em romimage.py. */
object FlashProg {
    val BUS = linkedMapOf("8" to 1, "plcc32" to 2, "16" to 3, "eprom" to 4, "md" to 5)    // "md" só identifica (flash-id)
    val LABEL = mapOf("8" to "8-bit flash (flash adapter)", "plcc32" to "8-bit flash PLCC32 (SNES adapter)", "16" to "16-bit flash", "eprom" to "EPROM 27C322 (4 MB)",
        "md" to "Mega Drive cartridge flash")
    /** Barramentos que só valem em flash-id; ler, apagar e gravar o cartucho de Mega Drive são `dump` e `rom-write`. */
    val DETECT_ONLY = setOf("md")
    const val EPROM_KB = 4096

    fun params(bus: String, flashKb: Int?, flashType: String? = null, sectorKb: Int? = null, buffer: Int? = null, needType: Boolean = false, detect: Boolean = false): FlashJob {
        val code = BUS[bus] ?: throw RomImageException(RomImageProblem.FP_BUS)
        if (bus in DETECT_ONLY) {
            if (!detect) throw RomImageException(RomImageProblem.FP_DETECT_ONLY)
            if ((flashKb ?: 0) != 0 || flashType != null || sectorKb != null || buffer != null) throw RomImageException(RomImageProblem.FP_MD_OPTIONS)
            return FlashJob(code, 0, 0)
        }
        if (bus == "eprom") return FlashJob(code, EPROM_KB, 0)
        if (flashKb == null || flashKb !in 1..8192) throw RomImageException(RomImageProblem.FP_KB)
        var word = 0
        if (bus == "8" || bus == "plcc32") {
            if (flashType == null) { if (needType) throw RomImageException(RomImageProblem.FP_NEEDS_TYPE) }
            else word = RomImages.typeWord(flashType, sectorKb, buffer)
        }
        return FlashJob(code, flashKb, word)
    }

    fun split(data: ByteArray, bus: String, flashKb: Int?, flashType: String? = null, sectorKb: Int? = null, buffer: Int? = null): FlashJob {
        val j = params(bus, flashKb, flashType, sectorKb, buffer, needType = bus == "8" || bus == "plcc32")
        if (data.isEmpty() || data.size % 512 != 0) throw RomImageException(RomImageProblem.FP_SIZE)
        if (data.size > j.prgKb * 1024) throw RomImageException(RomImageProblem.FP_NO_FIT, data.size / 1024, j.prgKb)
        var body = data
        if (flashType == "29gl" && (bus == "8" || bus == "plcc32")) {
            val sector = sectorKb!! * 1024
            body = data + ByteArray((sector - data.size % sector) % sector) { 0xFF.toByte() }
            if (body.size > j.prgKb * 1024) throw RomImageException(RomImageProblem.FP_PADDED_NO_FIT, body.size / 1024, j.prgKb)
        }
        return FlashJob(j.chip, j.prgKb, j.chrWord, body, data)
    }
}

object SnesLayouts {
    val NAMES = linkedMapOf("1x" to 0, "2x2mb" to 1, "2x4mb" to 2, "4x2mb" to 3, "1x8mb" to 4)
    const val GENERIC = 0x10
    const val MB = 1 shl 20
    val TOTAL_KB = mapOf(1 to 4096, 2 to 8192, 3 to 8192, 4 to 8192)
    /** FlashType do OSCR (Flash.h). */
    val FLASH_TYPES = linkedMapOf("29f032" to 1, "29f1610" to 2, "lh28f0xx" to 3, "29f1601" to 4, "29lv640" to 5, "29f800" to 6, "29gl" to 7, "e28fxxxj3a" to 8)
    val NEED_SECTOR = setOf("29gl", "lh28f0xx", "e28fxxxj3a")

    /** (chip 1..4, endereço no chip, bytes, deslocamento no arquivo). */
    data class Seg(val chip: Int, val addr: Int, val len: Int, val src: Int)

    /** Espelho de `plan()` em SnesPlan.h. Lista vazia = tamanho ou disposição inválidos. */
    fun plan(layout: Int, size: Int, capBytes: Int = 0): List<Seg> {
        if (size == 0 || size % 512 != 0) return emptyList()
        return when (layout) {
            0 -> if ((capBytes == 2 * MB || capBytes == 4 * MB) && size <= capBytes) listOf(Seg(1, 0, size, 0)) else emptyList()
            1 -> if (size <= 4 * MB) listOf(Seg(1, 0, minOf(size, 2 * MB), 0), Seg(2, 0, maxOf(size - 2 * MB, 0), 2 * MB)) else emptyList()
            2 -> if (size in 6 * MB..8 * MB) listOf(Seg(1, 0, size - 4 * MB, 4 * MB), Seg(2, 0, 4 * MB, 0)) else emptyList()
            3 -> if (size in 6 * MB..8 * MB) listOf(Seg(1, 0, 2 * MB, 4 * MB), Seg(2, 0, if (size > 6 * MB) 2 * MB else 0, 6 * MB), Seg(3, 0, 2 * MB, 0), Seg(4, 0, 2 * MB, 2 * MB)) else emptyList()
            4 -> if (size == 6 * MB || size == 8 * MB) listOf(Seg(1, 0, size - 4 * MB, 4 * MB), Seg(1, 4 * MB, 4 * MB, 0)) else emptyList()
            else -> emptyList()
        }
    }
}

enum class RomImageProblem { TRUNCATED_HEADER, TRAINER, SIZE_MISMATCH, NEEDS_HEADER, RAW_SIZE, CHIP_UNKNOWN, SNES_SIZE, SNES_TOO_BIG, SNES_NO_FIT, SNES_CAPACITY, SNES_NEEDS_CHIP, MD_SIZE, MD_TOO_BIG, MD_SMD,
    SNES_LAYOUT, SNES_BAD_LAYOUT, SNES_CAPACITY_FIXED, GEN_TYPE, GEN_MB, GEN_NO_FIT, GEN_NEEDS_SECTOR, GEN_SECTOR, GEN_BUFFER, GEN_PADDED_NO_FIT, GBA_BLOCK, GBA_SIZE, GBA_TOO_BIG, GB_SIZE, GB_TOO_BIG, GB_ORANGE, GB_NEEDS_CHIP, FP_BUS, FP_KB, FP_NEEDS_TYPE, FP_SIZE, FP_NO_FIT, FP_PADDED_NO_FIT, FP_DETECT_ONLY, FP_MD_OPTIONS }

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

    val SNES_CAPACITIES_KB = listOf(2048, 4096)     // as opções "1x 2MB" e "1x 4MB" do OSCR

    /**
     * ROM de SNES para o flash CFI: tira o cabeçalho de copiadora (512 bytes, quando o tamanho é múltiplo de 1024 mais 512) e acha a capacidade
     * do chip (a menor de 2 MB ou 4 MB em que a ROM cabe, ou a pedida). Igual a split_snes em romimage.py.
     */
    private fun snesStripHeader(data: ByteArray): ByteArray {
        val d = if (data.size % 1024 == 512) data.copyOfRange(512, data.size) else data
        if (d.isEmpty() || d.size % 1024 != 0) throw RomImageException(RomImageProblem.SNES_SIZE)
        return d
    }

    fun splitSnes(data: ByteArray, capacityKb: Int? = null, layoutName: String = "1x"): RomImage {
        val lay = SnesLayouts.NAMES[layoutName] ?: throw RomImageException(RomImageProblem.SNES_LAYOUT)
        val rom = snesStripHeader(data)
        val kb = rom.size / 1024
        val cap: Int
        if (lay == 0) {
            cap = when {
                capacityKb == null -> SNES_CAPACITIES_KB.firstOrNull { kb <= it } ?: throw RomImageException(RomImageProblem.SNES_TOO_BIG, kb)
                capacityKb !in SNES_CAPACITIES_KB -> throw RomImageException(RomImageProblem.SNES_CAPACITY)
                kb > capacityKb -> throw RomImageException(RomImageProblem.SNES_NO_FIT, kb, capacityKb)
                else -> capacityKb
            }
        } else {
            if (capacityKb != null) throw RomImageException(RomImageProblem.SNES_CAPACITY_FIXED)
            cap = SnesLayouts.TOTAL_KB.getValue(lay)
        }
        val segs = SnesLayouts.plan(lay, rom.size, if (lay == 0) cap * 1024 else 0)
        if (segs.isEmpty()) throw RomImageException(RomImageProblem.SNES_BAD_LAYOUT, kb)
        val out = java.io.ByteArrayOutputStream()
        segs.filter { it.len > 0 }.forEach { out.write(rom, it.src, it.len) }
        return RomImage(out.toByteArray(), kb, 0, null, cap, lay, 0, rom)
    }

    /**
     * ROM de SNES para os menus "LoROM/HiROM (P0)" e "ExLoROM/ExHiROM (P1)": flash de 8 bits de tipo informado. Igual a split_snes_generic em romimage.py.
     * No 29gl o arquivo é completado com 0xFF até um múltiplo do setor.
     */
    /** Campo chr_kb do modo genérico de flash de 8 bits: tipo | (log2 do setor em bytes << 4) | (log2 do buffer << 9). Igual a _type_word em romimage.py. */
    fun typeWord(flashType: String, sectorKbIn: Int?, bufferIn: Int?): Int {
        val typeCode = SnesLayouts.FLASH_TYPES[flashType] ?: throw RomImageException(RomImageProblem.GEN_TYPE)
        var sectorKb = sectorKbIn; var buffer = bufferIn
        if (flashType == "e28fxxxj3a") { sectorKb = sectorKb ?: 128; buffer = buffer ?: 32 }
        var secExp = 0; var bufExp = 0
        if (flashType in SnesLayouts.NEED_SECTOR) {
            if (sectorKb == null || buffer == null || sectorKb == 0 || buffer == 0) throw RomImageException(RomImageProblem.GEN_NEEDS_SECTOR)
            if (sectorKb and (sectorKb - 1) != 0 || sectorKb !in 1..16384) throw RomImageException(RomImageProblem.GEN_SECTOR)
            if (buffer and (buffer - 1) != 0 || buffer !in 2..128) throw RomImageException(RomImageProblem.GEN_BUFFER)
            secExp = Integer.numberOfTrailingZeros(sectorKb * 1024); bufExp = Integer.numberOfTrailingZeros(buffer)
        }
        return typeCode or (secExp shl 4) or (bufExp shl 9)
    }

    fun splitSnesGeneric(data: ByteArray, flashMb: Int, flashType: String, sectorKbIn: Int? = null, bufferIn: Int? = null): RomImage {
        val typeCode = SnesLayouts.FLASH_TYPES[flashType] ?: throw RomImageException(RomImageProblem.GEN_TYPE)
        if (flashMb !in 1..8) throw RomImageException(RomImageProblem.GEN_MB)
        val rom = snesStripHeader(data)
        if (rom.size > flashMb * SnesLayouts.MB) throw RomImageException(RomImageProblem.GEN_NO_FIT, rom.size / 1024, flashMb)
        val typeWordValue = typeWord(flashType, sectorKbIn, bufferIn)
        val sectorKb = if (flashType == "e28fxxxj3a") (sectorKbIn ?: 128) else sectorKbIn
        var body = rom
        if (flashType == "29gl") {
            val sector = sectorKb!! * 1024
            val pad = (sector - rom.size % sector) % sector
            body = rom + ByteArray(pad) { 0xFF.toByte() }
            if (body.size > flashMb * SnesLayouts.MB) throw RomImageException(RomImageProblem.GEN_PADDED_NO_FIT, body.size / 1024, flashMb)
        }
        return RomImage(body, rom.size / 1024, 0, null, flashMb * 1024, SnesLayouts.GENERIC, typeWordValue, rom)
    }

    const val GB_MAX_BYTES = 4 * 1024 * 1024

    /** ROM de Game Boy para o flash repro: múltiplo de 16 KB, de 32 KB a 4 MB; o Orange FM (sem MBC) grava só 32 KB. Igual a split_gb em romimage.py. */
    fun splitGb(data: ByteArray, chip: FlashChip): RomImage {
        if (data.size < 32768 || data.size % 16384 != 0) throw RomImageException(RomImageProblem.GB_SIZE)
        if (data.size > GB_MAX_BYTES) throw RomImageException(RomImageProblem.GB_TOO_BIG, data.size / 1024)
        if (chip == FlashChip.GB_ORANGE_FM && data.size != 32768) throw RomImageException(RomImageProblem.GB_ORANGE)
        return RomImage(data, data.size / 1024, 0, null)
    }

    const val GBA_369_MAX_BYTES = 256 * 1024 * 1024
    const val GBA_VERIFY_MAX_BYTES = 64 * 1024 * 1024 - 1024      // prg_kb do DUMP_ROM é u16 (KB)

    /**
     * ROM de GBA para o flash repro: tamanho múltiplo de 1 KB, até 256 MB no bloco 0 do 369-in-1 (ou até o fim da memória a partir do bloco N, de 4 MB).
     * [RomImage.prgKb] é o tamanho em KB limitado a 65535. Igual a split_gba em romimage.py.
     */
    fun splitGba(data: ByteArray, block: Int = 0): RomImage {
        if (block !in 0..63) throw RomImageException(RomImageProblem.GBA_BLOCK)
        if (data.isEmpty() || data.size % 1024 != 0) throw RomImageException(RomImageProblem.GBA_SIZE)
        val limit = if (block == 0) GBA_369_MAX_BYTES.toLong() else 4L * 1024 * 1024 * (64 - block)
        if (data.size > limit) throw RomImageException(RomImageProblem.GBA_TOO_BIG, data.size / 1024, block)
        return RomImage(data, minOf(data.size / 1024, 65535), 0, null, block = block)
    }

    /** Valor do campo `chip` do WRITE_ROM. No SNES: (disposição << 8) | fiação; no GBA: (bloco << 8) | 1; nos demais, o número do chip. */
    fun chipCode(chip: FlashChip, img: RomImage): Int = if (chip.snes) (img.layout shl 8) or chip.code else if (chip.gba) (img.block shl 8) or 1 else chip.code

    const val MD_MAX_BYTES = 8 * 1024 * 1024

    /**
     * ROM de Mega Drive para o flash repro: arquivo binário de tamanho par, até 4 MB; ROM entrelaçada (.smd) não é aceita.
     * [RomImage.prgKb] é o tamanho arredondado para cima (o firmware recebe o tamanho exato em bytes). Igual a split_md em romimage.py.
     */
    fun splitMd(data: ByteArray): RomImage {
        if (data.isEmpty() || data.size % 2 != 0) throw RomImageException(RomImageProblem.MD_SIZE)
        if (data.size > MD_MAX_BYTES) throw RomImageException(RomImageProblem.MD_TOO_BIG, data.size / 1024)
        fun sega(off: Int) = data.size >= off + 0x104 && String(data, off + 0x100, 4, Charsets.ISO_8859_1) == "SEGA"
        if (data.size % 1024 == 512 && !sega(0) && sega(512)) throw RomImageException(RomImageProblem.MD_SMD)
        return RomImage(data, (data.size + 1023) / 1024, 0, null)
    }

    /** [chip] null = pelo mapper do cabeçalho (30 = NES Maker, 0 = A29040B); arquivo cru = NES Maker. */
    fun prepare(data: ByteArray, chip: FlashChip?, capacityKb: Int? = null, layout: String = "1x",
                flashMb: Int? = null, flashType: String? = null, sectorKb: Int? = null, buffer: Int? = null, block: Int = 0): Pair<FlashChip, RomImage> {
        if (chip != null && chip.generic) {
            if (flashType == null) throw RomImageException(RomImageProblem.GEN_TYPE)
            if (flashMb == null) throw RomImageException(RomImageProblem.GEN_MB)
            return chip to splitSnesGeneric(data, flashMb, flashType, sectorKb, buffer)
        }
        if (chip != null && chip.snes) return chip to splitSnes(data, capacityKb, layout)
        if (chip != null && chip.md) return chip to splitMd(data)
        if (chip != null && chip.gba) return chip to splitGba(data, block)
        if (chip != null && chip.gb) return chip to splitGb(data, chip)
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
    val exp = img.rom ?: img.body
    var diff: Int? = null
    if (!read.contentEquals(exp)) {
        val n = minOf(read.size, exp.size)
        diff = (0 until n).firstOrNull { read[it] != exp[it] } ?: n
    }
    return VerifyResult(diff == null, crc32(read), crc32(exp), diff, read.size)
}

