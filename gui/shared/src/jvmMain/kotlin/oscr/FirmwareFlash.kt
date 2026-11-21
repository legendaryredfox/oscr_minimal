// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.io.File

/** Falha ao preparar ou gravar o firmware. `kind`: no_hex, no_avrdude (a GUI traduz pelo `kind`; `message` e `hint` são em inglês, para a CLI). */
class FirmwareException(val kind: String, message: String, val hint: String? = null, val key: String = "fw.$kind", val args: Map<String, String> = emptyMap()) : Exception(message)

/**
 * Gravação do firmware do fork (`firmware/oscr`) no Arduino Mega pela USB, com o avrdude (D131). Usada pela CLI (`firmware-flash`) e pela GUI.
 * O `.hex` vem de `given`, de OSCR_FIRMWARE_HEX ou da compilação do projeto (`firmware/oscr/.pio/build/<env>/firmware.hex`, procurada da pasta atual para cima);
 * o avrdude, de `given`, de AVRDUDE, do instalador, do PATH ou do PlatformIO. Instalado, o `.hex` sem a compilação do projeto vem do instalador (H-7).
 */
object FirmwareFlash {
    const val DEFAULT_ENV = "SerialASCII"
    const val TIMEOUT_S = 300L                       // gravar e verificar 230 KB leva cerca de 70 s a 115200 baud
    private val PCT = Regex("""(Writing|Reading)\s*\|[# ]*\|\s*(\d+)%""")

    /** O `.hex` que seria usado sem `given`, ou null se a compilação do projeto não existe. */
    fun projectHex(env: String = DEFAULT_ENV): File? {
        var d: File? = File(".").absoluteFile.normalize()
        while (d != null) { File(d, "firmware/oscr/.pio/build/$env/firmware.hex").takeIf { it.isFile }?.let { return it }; d = d.parentFile }
        return null
    }

    /** O `.hex` que cobre mais sistemas entre os do instalador (a imagem "completa"), ou null fora do programa instalado. */
    fun bundledHex(): File? = AppResources.firmwareDir()?.let { BoardPlanner.loadImages(it.path) }?.maxByOrNull { it.systems.size }?.hex

    fun findHex(given: String?, env: String = DEFAULT_ENV): File {
        val g = given ?: System.getenv("OSCR_FIRMWARE_HEX")
        val f = if (g != null) File(g.replaceFirst("~", System.getProperty("user.home") ?: "~")) else projectHex(env) ?: bundledHex() ?: File("firmware/oscr/.pio/build/$env/firmware.hex")
        if (!f.isFile) throw FirmwareException("no_hex", "firmware file not found: ${f.path}", "use --hex FILE.hex, or build first: `cd firmware/oscr && pio run -e $env`", args = mapOf("path" to f.path, "env" to env))
        return f
    }

    fun findAvrdude(given: String?): String {
        fun onPath(name: String): String? = System.getenv("PATH")?.split(File.pathSeparator)?.map { File(it, name) }?.firstOrNull { it.isFile && it.canExecute() }?.path
        (given ?: System.getenv("AVRDUDE"))?.let {
            if (File(it).isFile || onPath(it) != null) return it
            throw FirmwareException("no_avrdude", "avrdude not found: $it", "check the path given in --avrdude", key = "fw.no_avrdude_given", args = mapOf("path" to it))
        }
        AppResources.avrdude()?.let { return it.path }              // programa instalado: o avrdude vem no instalador (H-7)
        onPath("avrdude")?.let { return it }
        onPath("avrdude.exe")?.let { return it }
        val pio = File(System.getProperty("user.home") ?: ".", ".platformio/packages").listFiles { f -> f.name.startsWith("tool-avrdude") }
            ?.flatMap { d -> d.listFiles { f -> f.isFile && f.name.startsWith("avrdude") && !f.name.endsWith(".conf") && !f.name.endsWith(".txt") }?.toList() ?: emptyList() }
        pio?.minByOrNull { it.path }?.let { return it.path }
        throw FirmwareException("no_avrdude", "avrdude not found",
            "install avrdude (Linux: `sudo apt install avrdude`; macOS: `brew install avrdude`; Windows: winget or the Arduino package) or use --avrdude PATH")
    }

    /** O jSerialComm lista `ttyUSB0`; o avrdude 8 não acha a porta por esse nome e fica em laço a 100 % de CPU sem abrir nada (D197). Usa o caminho `/dev/...`. */
    fun avrdudePort(port: String): String = if (!port.startsWith("/") && File("/dev/$port").exists()) "/dev/$port" else port

    fun command(exe: String, port: String, hex: File, verify: Boolean): List<String> =
        listOf(exe, "-p", "atmega2560", "-c", "wiring", "-P", avrdudePort(port), "-b", "115200", "-D") + (if (verify) emptyList() else listOf("-V")) + listOf("-U", "flash:w:${hex.path}:i")

    /** Roda o avrdude e traduz as barras dele ("Writing | ### | 45%") em `onProgress("writing" ou "verifying", percentual)`. Devolve (código, últimas linhas de mensagem). */
    fun run(cmd: List<String>, onProgress: (label: String, percent: Int) -> Unit): Pair<Int, String> {
        val nul = File(if (System.getProperty("os.name").startsWith("Windows")) "NUL" else "/dev/null")
        val proc = ProcessBuilder(cmd).redirectInput(ProcessBuilder.Redirect.from(nul)).start()
        Thread { proc.inputStream.readBytes() }.apply { isDaemon = true }.start()                          // esvazia o stdout
        val timedOut = java.util.concurrent.atomic.AtomicBoolean(false)
        Thread { if (!proc.waitFor(TIMEOUT_S, java.util.concurrent.TimeUnit.SECONDS)) { timedOut.set(true); proc.destroyForcibly() } }   // avrdude 8 travado fica em laço para sempre (D197, D199)
            .apply { isDaemon = true }.start()
        val tail = ArrayList<String>(); val buf = StringBuilder()
        fun line() {
            val s = buf.toString(); buf.setLength(0)
            val m = PCT.find(s)
            if (m != null) onProgress(if (m.groupValues[1] == "Writing") "writing" else "verifying", m.groupValues[2].toInt())
            else if (s.isNotBlank()) { tail += s.trim(); if (tail.size > 8) tail.removeAt(0) }
        }
        proc.errorStream.bufferedReader().use { r -> while (true) { val c = r.read(); if (c < 0) break; if (c == '\r'.code || c == '\n'.code) line() else buf.append(c.toChar()) } }
        if (buf.isNotEmpty()) line()
        val code = proc.waitFor()
        if (timedOut.get()) { tail += "avrdude timeout after $TIMEOUT_S s"; if (tail.size > 8) tail.removeAt(0); return 124 to tail.joinToString(" | ") }
        return code to tail.joinToString(" | ")
    }
}
