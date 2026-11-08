package oscr.cli

import oscr.*
import kotlin.test.*

/** Mensagens da CLI Kotlin em vários idiomas (D133). Igual a host/tests/test_messages.py. */
class MsgTest {
    private fun run(env: Map<String, String> = emptyMap(), vararg argv: String): Triple<Int, String, String> {
        val out = StringBuilder(); val err = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { err.appendLine(it) }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".", env = { env[it] }, simPower = true)
        return Triple(Cli.run(argv.toList(), io), out.toString().trim(), err.toString())
    }

    private val field = Regex("""\{(\w+)(?::[^}]*)?\}""")

    @Test fun todaChaveTemOsQuatroIdiomasEOsMesmosCampos() {
        assertTrue(Msg.keys().size > 150, "catálogo vazio: o recurso oscr/cli-messages.tsv não foi encontrado")
        for (k in Msg.keys()) {
            val row = Msg.row(k)!!
            assertEquals(Lang.entries.toSet(), row.keys, k)
            assertTrue(row.values.all { it.isNotBlank() }, k)
            assertEquals(1, row.values.map { v -> field.findAll(v).map { it.groupValues[1] }.sorted().toList() }.toSet().size, k)
        }
    }

    @Test fun idiomaPorArgumentoVariavelELocale() {
        assertEquals(Lang.RU, Msg.detect(listOf("info", "--lang", "ru"), { null }))
        assertEquals(Lang.ZH, Msg.detect(listOf("--lang=zh"), { "pt_BR.UTF-8" }))
        assertEquals(Lang.PT, Msg.detect(listOf("info"), { if (it == "LANG") "pt_BR.UTF-8" else null }))
        assertEquals(Lang.EN, Msg.detect(listOf("info"), { if (it == "LANG") "C" else null }))
        assertEquals(Lang.RU, Msg.detect(listOf("info"), { mapOf("OSCR_LANG" to "ru", "LANG" to "pt_BR")[it] }))
        assertEquals(Lang.EN, Msg.detect(listOf("--lang", "xx"), { "pt_BR" }))
    }

    @Test fun formatoHexadecimalDoCampo() {
        assertEquals("header checksum (GBA) does NOT match: header 0012, computed 0034", Msg.tIn(Lang.EN, "check.mismatch", "name" to "GBA", "expected" to 0x12, "computed" to 0x34))
    }

    @Test fun erroDeUsoMudaDeTextoMasNaoDeKindNemDeCodigo() {
        val (c1, o1, _) = run(emptyMap(), "--json", "--lang", "en", "power")
        val (c2, o2, _) = run(emptyMap(), "--json", "--lang", "pt-BR", "power")
        val (c3, o3, _) = run(mapOf("OSCR_LANG" to "ru"), "--json", "power")
        assertEquals(64, c1); assertEquals(64, c2); assertEquals(64, c3)
        assertTrue("\"kind\":\"usage\"" in o1 && "\"kind\":\"usage\"" in o2 && "\"kind\":\"usage\"" in o3)
        assertTrue("power needs one action" in o1); assertTrue("power precisa de uma ação" in o2); assertTrue("power требует" in o3)
    }

    @Test fun powerEFirmwareEmOutrosIdiomas() {
        val (_, pt, _) = run(emptyMap(), "--lang", "pt", "--simulate", "power", "status")
        assertTrue("5V dos slots" in pt, pt)
        val (_, zh, _) = run(emptyMap(), "--lang", "zh", "--simulate", "power", "status")
        assertTrue("5V" in zh && "插槽" in zh, zh)
        val (c, o, _) = run(emptyMap(), "--lang", "pt-BR", "firmware-flash", "--hex", "/nao/existe.hex", "--json")
        assertEquals(64, c); assertTrue("\"kind\":\"no_hex\"" in o && "arquivo de firmware não encontrado" in o, o)
    }

    @Test fun langInvalidoEErroDeUso() {
        val (c, o, _) = run(emptyMap(), "--json", "--lang", "xx", "info")
        assertEquals(64, c); assertTrue("unknown --lang: xx" in o, o)
    }
}
