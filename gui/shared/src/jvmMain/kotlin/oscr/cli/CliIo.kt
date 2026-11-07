// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Erro estruturado da CLI e o que ela usa do mundo exterior (trocável nos testes). */
class CliError(val kind: String, override val message: String, val exit: Int = EXIT_ERROR, val hint: String? = null,
               val extra: Map<String, Any?> = emptyMap()) : Exception(message)

/** Tudo o que a CLI usa do mundo exterior, para os testes poderem trocar. */
class CliIo(
    val out: (String) -> Unit,
    val err: (String) -> Unit,
    val interactive: Boolean,
    val stderrTty: Boolean,
    val readLine: () -> String?,
    val listPorts: () -> List<String>,
    val openPort: (String, Int) -> Transport,
    val home: String,
    val stdoutTty: Boolean = false,      // stdout é um terminal: cor e arte ASCII (Ui)
) {
    companion object {
        fun system() = CliIo(
            out = { println(it) }, err = { System.err.println(it) },
            interactive = System.console() != null, stderrTty = System.console() != null, stdoutTty = System.console() != null,
            readLine = { readlnOrNull() },
            listPorts = { SerialTransport.ports().map { it.name } },
            openPort = { p, b -> SerialTransport(p, b) },
            home = System.getProperty("user.home") ?: ".",
        )
    }
}
