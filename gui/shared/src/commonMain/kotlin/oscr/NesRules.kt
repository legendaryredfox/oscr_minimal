// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/** Um problema nos campos digitados: a chave do texto e um número para o marcador {0} (ou null). */
data class Problem(val key: S, val arg: Int? = null)

/**
 * Regras do firmware para os campos de tamanho e mapper (iguais a oscr_carts_nes.cpp e docs/protocolo.md), para avisar enquanto o usuário
 * digita em vez de só depois do envio. O firmware continua sendo a palavra final (erro 0x0002 ou 0x0004).
 */
object Rules {
    val mapperNames: Map<Int, String> = mapOf(
        0 to "NROM", 1 to "MMC1", 2 to "UxROM", 3 to "CNROM", 4 to "MMC3", 5 to "MMC5", 7 to "AxROM", 9 to "MMC2", 10 to "MMC4",
        11 to "Color Dreams", 33 to "Taito TC0190", 48 to "Taito TC0190", 66 to "GxROM", 69 to "FME-7", 70 to "Jaleco/Bandai", 71 to "Camerica",
        75 to "VRC1", 78 to "Irem 74HC161", 79 to "NINA-003/006", 87 to "Jaleco JF-xx", 118 to "TxSROM", 206 to "Namco 108",
        13 to "CPROM", 30 to "UNROM 512", 34 to "BxROM/NINA-001", 67 to "Sunsoft 3", 68 to "Sunsoft 4", 72 to "Jaleco JF-17", 73 to "VRC3", 86 to "Jaleco JF-13",
        92 to "Jaleco JF-19", 93 to "Sunsoft 2", 94 to "UN1ROM", 140 to "Jaleco JF-11/14", 152 to "Bandai 74161", 180 to "UNROM invertido", 184 to "Sunsoft 1",
    )

    /** (PRG máx., CHR máx.) em KB por mapper, como no `probe` do firmware. */
    private val limits: Map<Int, Pair<Int, Int>> = mapOf(
        1 to (256 to 128), 4 to (512 to 256), 5 to (1024 to Int.MAX_VALUE), 9 to (128 to 128), 10 to (256 to 128), 11 to (128 to 128),
        33 to (256 to 256), 48 to (256 to 256), 66 to (128 to 32), 69 to (512 to 256), 70 to (256 to 128), 75 to (128 to 128), 78 to (128 to 128),
        79 to (64 to 64), 87 to (32 to 32), 118 to (512 to 256), 206 to (128 to 64),
        13 to (32 to 0), 30 to (512 to 0), 34 to (512 to 64), 67 to (128 to 128), 68 to (256 to 256), 72 to (128 to 128), 73 to (128 to 0), 86 to (128 to 64), 92 to (256 to 128),
        93 to (128 to 0), 94 to (128 to 0), 140 to (128 to 128), 152 to (128 to 128), 180 to (128 to 0), 184 to (32 to 32),
    )
    private val chrRam = setOf(2, 7, 71, 13, 30, 73, 93, 94, 180)
    private val chrRom = setOf(79, 87, 78, 75, 70, 33, 48, 118, 206, 67, 68, 72, 92, 86, 140, 152, 184)
    private val prg32 = setOf(7, 11, 66, 79, 34, 86, 140, 13)

    fun mapperName(m: Int): String? = mapperNames[m]

    /** null = campos aceitáveis. Mapper 0 com PRG 0 é o modo automático. */
    fun nes(mapper: Int, prg: Int, chr: Int): Problem? {
        if (mapper == 0 && prg == 0 && chr == 0) return null
        if (mapper !in mapperNames) return Problem(S.V_UNSUPPORTED_MAPPER, mapper)
        if (prg == 0) return Problem(S.V_PRG_REQUIRED)
        if (prg % 16 != 0) return Problem(S.V_PRG_MULTIPLE16)
        if (mapper in prg32 && prg % 32 != 0) return Problem(S.V_PRG_MULTIPLE32)
        if (chr % 8 != 0) return Problem(S.V_CHR_MULTIPLE8)
        if (mapper in chrRam && chr != 0) return Problem(S.V_NO_CHR)
        if (mapper in chrRom && chr == 0) return Problem(S.V_NEEDS_CHR)
        limits[mapper]?.let { (p, c) ->
            if (prg > p) return Problem(S.V_TOO_BIG_PRG, p)
            if (chr > c) return Problem(S.V_TOO_BIG_CHR, c)
        }
        return null
    }

    /** RAM do save do NES: 0 (8 KB), 8, 16 ou 32; 16 e 32 só nos mappers 1 e 5. */
    fun nesRam(mapper: Int, ram: Int): Problem? = when {
        ram == 0 || ram == 8 -> null
        (ram == 16 || ram == 32) && (mapper == 1 || mapper == 5) -> null
        else -> Problem(S.V_RAM_VALUES)
    }

    /** Campo "Tamanho da ROM" do SNES (só vale para ExHiROM) e do Mega Drive. */
    fun romSize(system: CartSystem, kb: Int): Problem? = when (system) {
        CartSystem.SNES -> if (kb == 0 || (kb % 64 == 0 && kb <= 8064)) null else Problem(S.V_SNES_SIZE)
        CartSystem.MD -> if (kb == 0 || kb in 32..8192) null else Problem(S.V_MD_SIZE)
        else -> null
    }
}
