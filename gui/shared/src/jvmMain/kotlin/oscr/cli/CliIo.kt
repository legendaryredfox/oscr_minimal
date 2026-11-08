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
    val simSense: Boolean = false,        // OSCR_SIM_SENSE=1: --simulate finge também o sensor do rail e 3 tentativas do SA-1 (a placa com sensor tem a chave de 5V em software)
    val env: (String) -> String? = { null },   // variáveis de ambiente (OSCR_LANG, LANG...); nos testes, nenhuma
    val simVolt: Boolean = false,         // OSCR_SIM_VOLT=1: o simulador finge o seletor 3,3 V/5 V (com OSCR_SIM_POWER=1)
    val simCart5v: Boolean = false,       // OSCR_SIM_5V_CART=1: o cartucho simulado só é lido a 5 V
    val simPower: Boolean = false,        // --simulate finge uma placa com a chave de 5V (variável OSCR_SIM_POWER=1)      // stdout é um terminal: cor e arte ASCII (Ui)
) {
    companion object {
        fun system() = CliIo(
            env = { System.getenv(it) },
            out = { println(it) }, err = { System.err.println(it) },
            interactive = System.console() != null, stderrTty = System.console() != null, stdoutTty = System.console() != null, simPower = System.getenv("OSCR_SIM_POWER") == "1", simVolt = System.getenv("OSCR_SIM_VOLT") == "1", simCart5v = System.getenv("OSCR_SIM_5V_CART") == "1", simSense = System.getenv("OSCR_SIM_SENSE") == "1",
            readLine = { readlnOrNull() },
            listPorts = { SerialTransport.ports().map { it.name } },
            openPort = { p, b -> SerialTransport(p, b) },
            home = System.getProperty("user.home") ?: ".",
        )
    }
}
