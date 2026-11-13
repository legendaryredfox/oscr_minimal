// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File

/** Comando gbcamera: extrai as fotos de um save do Game Boy Camera para PNG (P9, D160). Não abre o dispositivo. */
internal fun cmdGbCamera(io: CliIo, a: Args): Int {
    val input = a.opts["input"] ?: throw CliError("usage", Msg.t("args.needs_input", "cmd" to "gbcamera"), EXIT_USAGE)
    val src = File(input); val data = src.readBytes()
    val palette = a.opts["palette"] ?: "gray"
    if (palette !in GbCamera.PALETTES) throw CliError("usage", Msg.t("args.palette"), EXIT_USAGE)
    val scale = a.opts["scale"]?.toIntOrNull() ?: 1
    if (scale !in 1..8) throw CliError("usage", Msg.t("gbcamera.scale"), EXIT_USAGE)
    val photos = try { GbCamera.extract(data) } catch (e: IllegalArgumentException) { throw CliError("bad_save", Msg.t("gbcamera.bad_size", "size" to data.size, "need" to GbCamera.SAVE_BYTES), EXIT_ERROR) }
    val out = File(a.opts["output"] ?: src.path.substringBeforeLast('.', src.path)).also { it.mkdirs() }
    val files = ArrayList<String>(); val skipped = ArrayList<String>()
    for (p in photos) {
        if ((p.deleted || p.empty) && "all" !in a.flags) { skipped += p.name; continue }
        val f = File(out, p.name + (if (p.deleted) "_apagada" else "") + ".png")
        f.writeBytes(GbCameraPng.encode(p.pixels, p.width, p.height, palette, scale)); files += f.path
    }
    emit(io, a, linkedMapOf("folder" to out.path, "files" to files, "skipped" to skipped, "palette" to palette, "scale" to scale),
        listOf(Msg.t("gbcamera.done", "n" to files.size, "folder" to out.path)) + (if (skipped.isNotEmpty()) listOf(Msg.t("gbcamera.skipped", "n" to skipped.size)) else emptyList()))
    return EXIT_OK
}
