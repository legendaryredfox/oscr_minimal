// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import kotlin.system.exitProcess

fun main(args: Array<String>) {
    exitProcess(Cli.run(args.toList(), CliIo.system()))
}
