// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.io.File

/** Falha ao preparar ou gravar o firmware. `kind`: no_hex, no_avrdude (a GUI traduz pelo `kind`; `message` e `hint` são em inglês, para a CLI). */
class FirmwareException(val kind: String, message: String, val hint: String? = null) : Exception(message)

/**
 * Gravação do firmware do fork (`firmware/oscr`) no Arduino Mega pela USB, com o avrdude (D131). Usada pela CLI (`firmware-flash`) e pela GUI.
 * O `.hex` vem de `given`, de OSCR_FIRMWARE_HEX ou da compilação do projeto (`firmware/oscr/.pio/build/<env>/firmware.hex`, procurada da pasta atual para cima);
 * o avrdude, de `given`, de AVRDUDE, do PATH ou do PlatformIO.
 */
object FirmwareFlash {
    const val DEFAULT_ENV = "SerialASCII"
    private val PCT = Regex("""(Writing|Reading)\s*\|[# ]*\|\s*(\d+)%""")

    /** O `.hex` que seria usado sem `given`, ou null se a compilação do projeto não existe. */
    fun projectHex(env: String = DEFAULT_ENV): File? {
        var d: File? = File(".").absoluteFile.normalize()
        while (d != null) { File(d, "firmware/oscr/.pio/build/$env/firmware.hex").takeIf { it.isFile }?.let { return it }; d = d.parentFile }
        return null
    }

    fun findHex(given: String?, env: String = DEFAULT_ENV): File {
        val g = given ?: System.getenv("OSCR_FIRMWARE_HEX")
        val f = if (g != null) File(g.replaceFirst("~", System.getProperty("user.home") ?: "~")) else projectHex(env) ?: File("firmware/oscr/.pio/build/$env/firmware.hex")
        if (!f.isFile) throw FirmwareException("no_hex", "firmware file not found: ${f.path}", "use --hex FILE.hex, or build first: `cd firmware/oscr && pio run -e $env`")
        return f
    }

    fun findAvrdude(given: String?): String {
        fun onPath(name: String): String? = System.getenv("PATH")?.split(File.pathSeparator)?.map { File(it, name) }?.firstOrNull { it.isFile && it.canExecute() }?.path
        (given ?: System.getenv("AVRDUDE"))?.let {
            if (File(it).isFile || onPath(it) != null) return it
            throw FirmwareException("no_avrdude", "avrdude not found: $it", "check the path given in --avrdude")
        }
        onPath("avrdude")?.let { return it }
        onPath("avrdude.exe")?.let { return it }
        val pio = File(System.getProperty("user.home") ?: ".", ".platformio/packages").listFiles { f -> f.name.startsWith("tool-avrdude") }
            ?.flatMap { d -> d.listFiles { f -> f.isFile && f.name.startsWith("avrdude") && !f.name.endsWith(".conf") && !f.name.endsWith(".txt") }?.toList() ?: emptyList() }
        pio?.minByOrNull { it.path }?.let { return it.path }
        throw FirmwareException("no_avrdude", "avrdude not found",
            "install avrdude (Linux: `sudo apt install avrdude`; macOS: `brew install avrdude`; Windows: winget or the Arduino package) or use --avrdude PATH")
    }

    fun command(exe: String, port: String, hex: File, verify: Boolean): List<String> =
        listOf(exe, "-p", "atmega2560", "-c", "wiring", "-P", port, "-b", "115200", "-D") + (if (verify) emptyList() else listOf("-V")) + listOf("-U", "flash:w:${hex.path}:i")

    /** Roda o avrdude e traduz as barras dele ("Writing | ### | 45%") em `onProgress("writing" ou "verifying", percentual)`. Devolve (código, últimas linhas de mensagem). */
    fun run(cmd: List<String>, onProgress: (label: String, percent: Int) -> Unit): Pair<Int, String> {
        val nul = File(if (System.getProperty("os.name").startsWith("Windows")) "NUL" else "/dev/null")
        val proc = ProcessBuilder(cmd).redirectInput(ProcessBuilder.Redirect.from(nul)).start()
        Thread { proc.inputStream.readBytes() }.apply { isDaemon = true }.start()                          // esvazia o stdout
        val tail = ArrayList<String>(); val buf = StringBuilder()
        fun line() {
            val s = buf.toString(); buf.setLength(0)
            val m = PCT.find(s)
            if (m != null) onProgress(if (m.groupValues[1] == "Writing") "writing" else "verifying", m.groupValues[2].toInt())
            else if (s.isNotBlank()) { tail += s.trim(); if (tail.size > 8) tail.removeAt(0) }
        }
        proc.errorStream.bufferedReader().use { r -> while (true) { val c = r.read(); if (c < 0) break; if (c == '\r'.code || c == '\n'.code) line() else buf.append(c.toChar()) } }
        if (buf.isNotEmpty()) line()
        return proc.waitFor() to tail.joinToString(" | ")
    }
}
