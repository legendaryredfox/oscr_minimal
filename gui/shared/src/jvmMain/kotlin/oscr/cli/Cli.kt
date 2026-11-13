// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.IOException

/**
 * CLI em Kotlin, com o mesmo contrato da CLI Python (docs/referencia/cli.md): comandos, opções, saída --json e códigos de saída.
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

    /** --sound (D160): um aviso sonoro (BEL na saída de erro) ao terminar com sucesso e três se falhou. */
    fun run(argv: List<String>, io: CliIo): Int {
        val rc = runCommand(argv, io)
        if ("--sound" in argv) io.err("\u0007".repeat(if (rc == EXIT_OK) 1 else 3))
        return rc
    }

    private fun runCommand(argv: List<String>, io: CliIo): Int {
        val jsonWanted = "--json" in argv
        val colorMode = argv.zipWithNext().firstOrNull { it.first == "--color" }?.second ?: argv.firstOrNull { it.startsWith("--color=") }?.substringAfter('=')
        val lang = Msg.detect(argv, io.env)
        Msg.lang = lang
        try {
            val a = parseArgs(argv)
            a.opts["lang"]?.let { t -> if (Msg.parse(t) == null) throw CliError("usage", Msg.t("args.unknown_lang", "tag" to t), EXIT_USAGE) }
            if ("version" in a.flags) { io.out("dumper-kt $VERSION (protocol ${Proto.VERSION})"); return EXIT_OK }
            if ("help" in a.flags || a.cmd == null) { if (Ui.on(colorMode, io.stdoutTty, jsonWanted)) io.out(Ui.banner(true, VERSION) + "\n"); io.out(helpText()); return if (a.cmd == null && "help" !in a.flags) EXIT_USAGE else EXIT_OK }
            if (a.cmd !in COMMANDS) throw CliError("usage", Msg.t("args.unknown_cmd", "cmd" to a.cmd, "cmds" to COMMANDS.joinToString(" ")), EXIT_USAGE)
            a.opts["voltage"]?.let { if (it !in setOf("auto", "3v3", "5v")) throw CliError("usage", Msg.t("args.voltage"), EXIT_USAGE) }
            a.opts["color"]?.let { if (it !in setOf("auto", "always", "never")) throw CliError("usage", Msg.t("args.color"), EXIT_USAGE) }
            a.opts["progress"]?.let { if (it !in setOf("auto", "none", "jsonl")) throw CliError("usage", Msg.t("args.progress"), EXIT_USAGE) }
            return when (a.cmd) {
                "ports" -> cmdPorts(io, a)
                "voltage" -> cmdVoltage(io, a)
                "selftest" -> cmdSelftest(io, a)
                "firmware-flash" -> cmdFirmwareFlash(io, a)
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
            return fail(io, jsonWanted, colorMode = colorMode, e = CliError("timeout", describeError(lang, e), EXIT_ERROR, Msg.t("err.timeout")))
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
