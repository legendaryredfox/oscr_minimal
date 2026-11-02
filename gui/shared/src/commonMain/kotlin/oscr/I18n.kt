// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/** Idiomas da interface. Inglês é o reserva (qualquer chave faltando cai nele). Novos idiomas: acrescente aqui. */
enum class Lang(val tag: String, val label: String) { PT("pt-BR", "Português"), EN("en", "English") }

/** Todas as chaves de texto da interface. Nenhum texto fixo fora deste arquivo. */
enum class S {
    TITLE, LANGUAGE, PORT, REFRESH, BAUD, CONNECT, DISCONNECT, CONNECTED, NOT_CONNECTED, SYSTEM,
    DETECT, DUMP_ROM, READ_SAVE, WRITE_SAVE, ABORT, PROGRESS, RESULT_FILE, RESULT_CRC, RESULT_SIZE,
    CART_FOUND, CART_NONE, CART_UNSUPPORTED, CART_HW_ERROR, TITLE_LABEL, ROM_LABEL, SAVE_LABEL,
    ERROR, NO_PORTS, DEVICE_INFO, MOCK_MODE, ONE_CART_ONLY, GBA_WARNING, SAVED_TO, CHOOSE_FILE, DONE,
}

object I18n {
    private val pt = mapOf(
        S.TITLE to "Dumper de cartuchos", S.LANGUAGE to "Idioma", S.PORT to "Porta serial", S.REFRESH to "Atualizar",
        S.BAUD to "Baud", S.CONNECT to "Conectar", S.DISCONNECT to "Desconectar", S.CONNECTED to "Conectado",
        S.NOT_CONNECTED to "Desconectado", S.SYSTEM to "Sistema", S.DETECT to "Detectar", S.DUMP_ROM to "Ler ROM",
        S.READ_SAVE to "Ler save", S.WRITE_SAVE to "Gravar save", S.ABORT to "Cancelar", S.PROGRESS to "Progresso",
        S.RESULT_FILE to "Arquivo", S.RESULT_CRC to "CRC32 (compare com o No-Intro)", S.RESULT_SIZE to "Tamanho",
        S.CART_FOUND to "Cartucho detectado", S.CART_NONE to "Nenhum cartucho", S.CART_UNSUPPORTED to "Sistema não suportado",
        S.CART_HW_ERROR to "Erro de hardware", S.TITLE_LABEL to "Título", S.ROM_LABEL to "ROM", S.SAVE_LABEL to "Save",
        S.ERROR to "Erro", S.NO_PORTS to "Nenhuma porta serial encontrada (Linux: grupo dialout)",
        S.DEVICE_INFO to "Firmware", S.MOCK_MODE to "modo de teste (sem cartucho)",
        S.ONE_CART_ONLY to "Um cartucho por vez. Desligue o USB antes de trocar de cartucho.",
        S.GBA_WARNING to "O slot GBA é 3,3 V: só cartuchos GBA nele.", S.SAVED_TO to "Salvo em", S.CHOOSE_FILE to "Escolha o arquivo",
        S.DONE to "Concluído",
    )
    private val en = mapOf(
        S.TITLE to "Cartridge dumper", S.LANGUAGE to "Language", S.PORT to "Serial port", S.REFRESH to "Refresh",
        S.BAUD to "Baud", S.CONNECT to "Connect", S.DISCONNECT to "Disconnect", S.CONNECTED to "Connected",
        S.NOT_CONNECTED to "Disconnected", S.SYSTEM to "System", S.DETECT to "Detect", S.DUMP_ROM to "Dump ROM",
        S.READ_SAVE to "Read save", S.WRITE_SAVE to "Write save", S.ABORT to "Cancel", S.PROGRESS to "Progress",
        S.RESULT_FILE to "File", S.RESULT_CRC to "CRC32 (compare with No-Intro)", S.RESULT_SIZE to "Size",
        S.CART_FOUND to "Cartridge detected", S.CART_NONE to "No cartridge", S.CART_UNSUPPORTED to "System not supported",
        S.CART_HW_ERROR to "Hardware error", S.TITLE_LABEL to "Title", S.ROM_LABEL to "ROM", S.SAVE_LABEL to "Save",
        S.ERROR to "Error", S.NO_PORTS to "No serial port found (Linux: dialout group)",
        S.DEVICE_INFO to "Firmware", S.MOCK_MODE to "test mode (no cartridge)",
        S.ONE_CART_ONLY to "One cartridge at a time. Unplug USB before swapping cartridges.",
        S.GBA_WARNING to "The GBA slot is 3.3 V: GBA cartridges only.", S.SAVED_TO to "Saved to", S.CHOOSE_FILE to "Choose the file",
        S.DONE to "Done",
    )
    private val tables = mapOf(Lang.PT to pt, Lang.EN to en)

    fun t(lang: Lang, key: S): String = tables[lang]?.get(key) ?: en.getValue(key)

    /** Idioma padrão a partir do locale do sistema (ex.: "pt_BR" -> PT). */
    fun fromLocale(tag: String): Lang = if (tag.lowercase().startsWith("pt")) Lang.PT else Lang.EN
}
