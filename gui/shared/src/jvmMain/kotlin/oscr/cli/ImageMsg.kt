// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Texto de um problema de imagem de ROM no idioma da CLI (catálogo `img.*`, o mesmo de `romimage.py`; D133). */
internal fun imageMessage(e: RomImageException, a: Args): String {
    val types = SnesLayouts.FLASH_TYPES.keys.joinToString(", ")
    val kb = e.a
    return when (e.problem) {
        RomImageProblem.TRUNCATED_HEADER -> Msg.t("img.truncated")
        RomImageProblem.TRAINER -> Msg.t("img.trainer")
        RomImageProblem.SIZE_MISMATCH -> Msg.t("img.size_mismatch", "n" to e.a, "prg" to e.b, "chr" to e.c)
        RomImageProblem.NEEDS_HEADER -> Msg.t("img.needs_header")
        RomImageProblem.RAW_SIZE -> Msg.t("img.raw_size")
        RomImageProblem.CHIP_UNKNOWN -> Msg.t("rom.usage.infer")
        RomImageProblem.SNES_SIZE -> Msg.t("img.snes_size")
        RomImageProblem.SNES_TOO_BIG -> Msg.t("img.snes_too_big", "kb" to kb)
        RomImageProblem.SNES_NO_FIT -> Msg.t("img.snes_no_fit", "kb" to kb, "cap" to e.b)
        RomImageProblem.SNES_CAPACITY -> Msg.t("img.snes_capacity")
        RomImageProblem.SNES_NEEDS_CHIP -> Msg.t("rom.usage.snes_wiring")
        RomImageProblem.SNES_LAYOUT -> Msg.t("img.snes_layout", "layout" to (a.opts["layout"] ?: "?"), "layouts" to SnesLayouts.NAMES.keys.joinToString(", "))
        RomImageProblem.SNES_BAD_LAYOUT -> Msg.t("img.snes_bad_layout", "kb" to kb, "layout" to (a.opts["layout"] ?: "1x"))
        RomImageProblem.SNES_CAPACITY_FIXED -> Msg.t("img.snes_capacity_fixed")
        RomImageProblem.GEN_TYPE ->
            if (a.opts["flash-type"] == null) Msg.t("img.needs_flash_type", "types" to types)
            else Msg.t("img.gen_type", "type" to a.opts["flash-type"], "types" to types)
        RomImageProblem.GEN_MB -> Msg.t("img.gen_mb")
        RomImageProblem.GEN_NO_FIT -> Msg.t("img.gen_no_fit", "kb" to e.a, "mb" to e.b)
        RomImageProblem.GEN_NEEDS_SECTOR -> Msg.t("img.gen_needs_sector", "type" to (a.opts["flash-type"] ?: "?"))
        RomImageProblem.GEN_SECTOR -> Msg.t("img.gen_sector")
        RomImageProblem.GEN_BUFFER -> Msg.t("img.gen_buffer")
        RomImageProblem.GEN_PADDED_NO_FIT -> Msg.t("img.gen_padded_no_fit", "kb" to e.a, "mb" to e.b)
        RomImageProblem.GB_SIZE -> Msg.t("img.gb_size")
        RomImageProblem.GB_TOO_BIG -> Msg.t("img.gb_too_big", "kb" to kb)
        RomImageProblem.GB_ORANGE -> Msg.t("img.gb_orange")
        RomImageProblem.GB_NEEDS_CHIP -> Msg.t("rom.usage.gb_chip", "chips" to FlashChip.forSystem(CartSystem.GB).joinToString(", ") { it.key })
        RomImageProblem.GBA_BLOCK -> Msg.t("img.gba_block")
        RomImageProblem.GBA_SIZE -> Msg.t("img.gba_size")
        RomImageProblem.GBA_TOO_BIG -> Msg.t("img.gba_too_big", "kb" to e.a, "block" to e.b)
        RomImageProblem.MD_SIZE -> Msg.t("img.md_size")
        RomImageProblem.MD_TOO_BIG -> Msg.t("img.md_too_big", "kb" to kb)
        RomImageProblem.MD_SMD -> Msg.t("img.md_smd")
        RomImageProblem.FP_BUS -> Msg.t("img.fp_bus", "bus" to (a.opts["bus"] ?: "?"), "buses" to FlashProg.BUS.keys.joinToString(", "))
        RomImageProblem.FP_DETECT_ONLY -> Msg.t("img.fp_detect_only")
        RomImageProblem.FP_MD_OPTIONS -> Msg.t("img.fp_md_options")
        RomImageProblem.FP_KB -> Msg.t("img.fp_kb")
        RomImageProblem.FP_NEEDS_TYPE -> Msg.t("img.needs_flash_type", "types" to types)
        RomImageProblem.FP_SIZE -> Msg.t("img.fp_size")
        RomImageProblem.FP_NO_FIT -> Msg.t("img.fp_no_fit", "kb" to e.a, "cap" to e.b)
        RomImageProblem.FP_PADDED_NO_FIT -> Msg.t("img.fp_padded_no_fit", "kb" to e.a, "cap" to e.b)
    }
}
