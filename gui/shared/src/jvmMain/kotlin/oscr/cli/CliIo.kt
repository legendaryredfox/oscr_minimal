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
    val stdoutTty: Boolean = false,
    val env: (String) -> String? = { null },   // variáveis de ambiente (OSCR_LANG, LANG...); nos testes, nenhuma
    val simVolt: Boolean = false,         // OSCR_SIM_VOLT=1: o simulador finge o seletor 3,3 V/5 V (sobe em 3,3 V)
    val simCart5v: Boolean = false,       // OSCR_SIM_5V_CART=1: o cartucho simulado só é lido a 5 V
    val simSelftest: Boolean = false,     // OSCR_SIM_SELFTEST=1: o simulador acha um curto com GND (D30) e um par em curto (D22 e A3)
) {
    companion object {
        fun system() = CliIo(
            env = { System.getenv(it) },
            out = { println(it) }, err = { System.err.println(it) },
            interactive = System.console() != null, stderrTty = System.console() != null, stdoutTty = System.console() != null, simVolt = System.getenv("OSCR_SIM_VOLT") == "1", simCart5v = System.getenv("OSCR_SIM_5V_CART") == "1", simSelftest = System.getenv("OSCR_SIM_SELFTEST") == "1",
            readLine = { readlnOrNull() },
            listPorts = { SerialTransport.ports().map { it.name } },
            openPort = { p, b -> SerialTransport(p, b) },
            home = System.getProperty("user.home") ?: ".",
        )
    }
}
