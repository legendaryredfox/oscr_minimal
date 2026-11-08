// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Códigos de saída e versão (estáveis; docs/referencia/cli.md). */
const val EXIT_OK = 0; const val EXIT_ERROR = 1; const val EXIT_NO_CART = 2; const val EXIT_NO_DEVICE = 3
const val EXIT_REFUSED = 4; const val EXIT_USAGE = 64; const val EXIT_INTERRUPTED = 130
const val VERSION = "0.1.0"

internal val EXIT_CODES = listOf(EXIT_OK, EXIT_ERROR, EXIT_NO_CART, EXIT_NO_DEVICE, EXIT_REFUSED, EXIT_USAGE, EXIT_INTERRUPTED)
internal fun exitMeaning(code: Int): String = Msg.t("exit.$code")
