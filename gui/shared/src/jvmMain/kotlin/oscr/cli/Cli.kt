// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.IOException

/**
 * CLI em Kotlin, com o mesmo contrato da CLI Python (docs/cli.md): comandos, opções, saída --json e códigos de saída.
 * Textos desta CLI (ajuda, dicas) são em inglês; erros do dispositivo e do protocolo vêm do I18n da GUI (--lang).
 * Agentes devem usar `ok`, `error.kind` e o código de saída, não o texto.
 *
 * Organização (um assunto por arquivo): Exit, Args, Usage, CliIo, Output, Connection, Cmd*.kt (um por grupo de comandos), DbSupport.
 * Este arquivo só interpreta os argumentos, escolhe o comando e traduz os erros em códigos de saída.
 */
object Cli {
    const val EXIT_OK = oscr.cli.EXIT_OK; const val EXIT_ERROR = oscr.cli.EXIT_ERROR; const val EXIT_NO_CART = oscr.cli.EXIT_NO_CART
    const val EXIT_NO_DEVICE = oscr.cli.EXIT_NO_DEVICE; const val EXIT_REFUSED = oscr.cli.EXIT_REFUSED; const val EXIT_USAGE = oscr.cli.EXIT_USAGE
    const val EXIT_INTERRUPTED = oscr.cli.EXIT_INTERRUPTED
    const val VERSION = oscr.cli.VERSION

    fun run(argv: List<String>, io: CliIo): Int {
        val jsonWanted = "--json" in argv
        val colorMode = argv.zipWithNext().firstOrNull { it.first == "--color" }?.second ?: argv.firstOrNull { it.startsWith("--color=") }?.substringAfter('=')
        var lang = Lang.EN
        try {
            val a = parseArgs(argv)
            a.opts["lang"]?.let { t -> lang = Lang.entries.firstOrNull { it.tag.equals(t, true) || it.tag.substringBefore('-').equals(t, true) } ?: throw CliError("usage", "unknown --lang: $t", EXIT_USAGE) }
            if ("version" in a.flags) { io.out("dumper-kt $VERSION (protocol ${Proto.VERSION})"); return EXIT_OK }
            if ("help" in a.flags || a.cmd == null) { if (Ui.on(colorMode, io.stdoutTty, jsonWanted)) io.out(Ui.banner(true, VERSION) + "\n"); io.out(HELP); return if (a.cmd == null && "help" !in a.flags) EXIT_USAGE else EXIT_OK }
            if (a.cmd !in COMMANDS) throw CliError("usage", "unknown command: ${a.cmd}. Use: ${COMMANDS.joinToString(" ")}", EXIT_USAGE)
            a.opts["power"]?.let { if (it !in setOf("auto", "keep")) throw CliError("usage", "--power must be auto or keep", EXIT_USAGE) }
            a.opts["color"]?.let { if (it !in setOf("auto", "always", "never")) throw CliError("usage", "--color must be auto, always or never", EXIT_USAGE) }
            a.opts["progress"]?.let { if (it !in setOf("auto", "none", "jsonl")) throw CliError("usage", "--progress must be auto, none or jsonl", EXIT_USAGE) }
            return when (a.cmd) {
                "ports" -> cmdPorts(io, a)
                "power" -> cmdPower(io, a)
                "systems" -> cmdSystems(io, a)
                "errors" -> cmdErrors(io, a, lang)
                "info" -> cmdInfo(io, a)
                "detect" -> cmdDetect(io, a)
                "dump" -> cmdDump(io, a)
                "save-read" -> cmdSaveRead(io, a)
                "identify" -> cmdIdentify(io, a)
                "search" -> cmdSearch(io, a)
                "rom-write" -> cmdRomWrite(io, a)
                "flash-id" -> cmdFlashId(io, a)
                "flash-read" -> cmdFlashRead(io, a)
                "flash-blank" -> cmdFlashBlank(io, a)
                "flash-erase" -> cmdFlashErase(io, a)
                "flash-write" -> cmdFlashWrite(io, a)
                else -> cmdSaveWrite(io, a)
            }
        } catch (e: CliError) {
            return fail(io, jsonWanted, e, colorMode)
        } catch (e: DeviceError) {
            val (kind, code) = when (e.code) { 3 -> "no_cartridge" to EXIT_NO_CART; 10 -> "no_save" to EXIT_ERROR; else -> "device_error" to EXIT_ERROR }
            return fail(io, jsonWanted, colorMode = colorMode, e = CliError(kind, describeError(lang, e), code, extra = mapOf("device_code" to e.code)))
        } catch (e: TimeoutError) {
            return fail(io, jsonWanted, colorMode = colorMode, e = CliError("timeout", describeError(lang, e), EXIT_ERROR, "the device stopped responding; check the cable and retry"))
        } catch (e: ProtocolError) {
            val open = e.fail == Fail.OPEN_PORT
            return fail(io, jsonWanted, colorMode = colorMode, e = CliError(if (open) "open_port" else "protocol", describeError(lang, e), if (open) EXIT_NO_DEVICE else EXIT_ERROR))
        } catch (e: IOException) {
            return fail(io, jsonWanted, colorMode = colorMode, e = CliError("io", e.message ?: e.toString()))
        } catch (e: Throwable) {
            return fail(io, jsonWanted, colorMode = colorMode, e = CliError("internal", e.toString()))
        }
    }
}
