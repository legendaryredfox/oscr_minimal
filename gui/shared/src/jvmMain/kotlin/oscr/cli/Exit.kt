// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Códigos de saída e versão (estáveis; docs/referencia/cli.md). */
const val EXIT_OK = 0; const val EXIT_ERROR = 1; const val EXIT_NO_CART = 2; const val EXIT_NO_DEVICE = 3
const val EXIT_REFUSED = 4; const val EXIT_USAGE = 64; const val EXIT_INTERRUPTED = 130
const val VERSION = "0.1.0"

internal val EXIT_MEANING = linkedMapOf(
    EXIT_OK to "success", EXIT_ERROR to "device, protocol, timeout or file error",
    EXIT_NO_CART to "no cartridge", EXIT_NO_DEVICE to "serial port not found or device not responding",
    EXIT_REFUSED to "refused: save-write without --yes outside a terminal", EXIT_USAGE to "invalid arguments",
    EXIT_INTERRUPTED to "interrupted (Ctrl+C)",
)
