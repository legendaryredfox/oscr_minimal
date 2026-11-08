// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/** Texto de ajuda e rótulos fixos. */
internal fun statusText(status: Int): String = if (status in 0..4) Msg.t("detect.status.$status") else status.toString()

/** Texto de `--help` no idioma da execução (catálogo, chave `usage.text`). */
internal fun helpText(): String = Msg.t("usage.text")
