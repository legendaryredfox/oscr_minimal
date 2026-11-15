// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.io.File

/**
 * Arquivos que o instalador leva junto (H-7): as imagens do firmware (`firmware/`, com `manifest.tsv` e os `.hex`) e o avrdude (`avrdude/`).
 * O Compose Desktop aponta a pasta pela propriedade `compose.application.resources.dir` quando o programa roda instalado; fora disso (CLI,
 * `gradlew run`, testes) a propriedade não existe e tudo se procura como antes (variáveis de ambiente, PATH, PlatformIO, pasta do projeto).
 */
object AppResources {
    const val PROPERTY = "compose.application.resources.dir"

    fun dir(): File? = System.getProperty(PROPERTY)?.let { File(it) }?.takeIf { it.isDirectory }

    /** `firmware/` embutida, se tiver o manifest. */
    fun firmwareDir(): File? = dir()?.let { File(it, "firmware") }?.takeIf { File(it, "manifest.tsv").isFile }

    /** O avrdude embutido (`avrdude/avrdude` ou `avrdude/avrdude.exe`), se existir e puder ser executado. */
    fun avrdude(): File? {
        val d = dir()?.let { File(it, "avrdude") } ?: return null
        return listOf("avrdude", "avrdude.exe").map { File(d, it) }.firstOrNull { it.isFile && (it.canExecute() || it.setExecutable(true)) }
    }
}
