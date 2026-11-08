// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.io.File
import java.io.FileInputStream
import javax.xml.stream.XMLInputFactory
import javax.xml.stream.XMLStreamConstants
import javax.xml.stream.XMLStreamException
import javax.xml.stream.XMLStreamReader

/** Erro de leitura da base (caminho inexistente, XML inválido). */
class DatabaseError(message: String) : Exception(message)

/**
 * Leitura streaming (StAX) de .dat/.xml e da base .txt do OSCR; igual a parse_file/Database.load de host/oscr_host/database.py.
 * A base que vem no projeto (database/oscr/) é empacotada como recurso (`oscr/INDEX.txt` lista os arquivos) e carregada por `loadAll`.
 */
object DatabaseLoader {
    private val NOT_DB = setOf("origem.txt", "index.txt", "leiame.txt", "readme.txt")
    private val ROM_EXT = Regex("\\.(nes|sfc|smc|gba|gbc|gb|md|gen|gg|sms|pce|sgx|sg|32x|vb|bin)$", RegexOption.IGNORE_CASE)
    private val CRC8 = Regex("[0-9A-Fa-f]{8}")

    /** Mapper e tamanhos do cabeçalho iNES / NES 2.0 de 16 bytes; null se inválido ou de tamanho exponencial. */
    class InesInfo(val mapper: Int, val submapper: Int, val prgKb: Int, val chrKb: Int, val ramKb: Int, val battery: Boolean)

    fun ines(h: ByteArray): InesInfo? {
        if (h.size != 16 || h[0] != 'N'.code.toByte() || h[1] != 'E'.code.toByte() || h[2] != 'S'.code.toByte() || h[3] != 0x1A.toByte()) return null
        fun b(i: Int) = h[i].toInt() and 0xFF
        val nes2 = (b(7) and 0x0C) == 0x08
        var mapper = (b(6) shr 4) or (b(7) and 0xF0)
        var prg = b(4); var chr = b(5); var sub = 0
        val ram: Int
        if (nes2) {
            mapper = mapper or ((b(8) and 0x0F) shl 8); sub = b(8) shr 4
            if ((b(9) and 0x0F) == 0x0F || (b(9) shr 4) == 0x0F) return null
            prg = prg or ((b(9) and 0x0F) shl 8); chr = chr or ((b(9) shr 4) shl 8)
            val nv = b(10) shr 4; val vol = b(10) and 0x0F
            ram = (if (nv != 0) 64 shl nv else if (vol != 0) 64 shl vol else 0) / 1024
        } else {
            ram = if (b(8) != 0) b(8) * 8 else if (b(6) and 2 != 0) 8 else 0
        }
        return InesInfo(mapper, sub, prg * 16, chr * 8, ram, b(6) and 2 != 0)
    }

    /** Lê o texto de uma base .txt do OSCR legado: pares nome + linha de dados (CRC32 primeiro). Linhas fora do formato são ignoradas. */
    fun parseOscr(text: String, source: String): List<DbEntry> {
        val stem = source.substringBeforeLast('.').lowercase()
        val lines = text.lineSequence().map { it.trim() }.filter { it.isNotEmpty() }.toList()
        val out = ArrayList<DbEntry>()
        var i = 0
        while (i + 1 < lines.size) {
            val f = lines[i + 1].split(",")
            if (!CRC8.matches(f[0])) { i++; continue }
            val name = ROM_EXT.replace(lines[i], ""); i += 2
            val crc = f[0].toLong(16).toInt()
            var e = DbEntry(name, crc, 0, source, "oscr")
            if (stem == "nes" && f.size >= 3) {
                val hdr = f[2].takeIf { it.length == 32 && it.all { c -> c in "0123456789abcdefABCDEF" } }
                    ?.let { h -> ByteArray(16) { h.substring(it * 2, it * 2 + 2).toInt(16).toByte() } }
                val n = hdr?.let { ines(it) }
                if (n != null) e = e.copy(size = (n.prgKb + n.chrKb) * 1024L, mapper = n.mapper, submapper = n.submapper, prgKb = n.prgKb, chrKb = n.chrKb, ramKb = n.ramKb, battery = n.battery)
            } else if (stem == "gba" && f.size >= 3 && f[2].all { it.isDigit() } && f[2].isNotEmpty()) {
                e = e.copy(size = f[2].toLong() * 1024 * 1024)
            }
            out += e
        }
        return out
    }

    /** Leitor mínimo de JSON (objeto, lista, texto, número, true, false, null) para as bases do oscr-databases; levanta [DatabaseError] se inválido. */
    private class Json(val s: String) {
        var i = 0
        fun ws() { while (i < s.length && s[i].isWhitespace()) i++ }
        fun value(): Any? {
            ws()
            if (i >= s.length) throw DatabaseError("JSON truncated")
            return when (val c = s[i]) {
                '{' -> { i++; val m = LinkedHashMap<String, Any?>(); ws()
                    if (s[i] == '}') { i++; return m }
                    while (true) { ws(); val k = str(); ws(); expect(':'); m[k] = value(); ws(); if (s[i] == ',') { i++; continue }; expect('}'); return m } }
                '[' -> { i++; val l = ArrayList<Any?>(); ws()
                    if (s[i] == ']') { i++; return l }
                    while (true) { l += value(); ws(); if (s[i] == ',') { i++; continue }; expect(']'); return l } }
                '"' -> str()
                't' -> lit("true", true)
                'f' -> lit("false", false)
                'n' -> lit("null", null)
                else -> { val st = i; while (i < s.length && (s[i].isDigit() || s[i] in "+-.eE")) i++
                    if (st == i) throw DatabaseError("JSON: unexpected '$c' at $i")
                    s.substring(st, i).let { it.toLongOrNull() ?: it.toDoubleOrNull() ?: throw DatabaseError("JSON: bad number $it") } }
            }
        }
        fun expect(c: Char) { if (i >= s.length || s[i] != c) throw DatabaseError("JSON: expected '$c' at $i"); i++ }
        fun lit(w: String, v: Any?): Any? { if (!s.startsWith(w, i)) throw DatabaseError("JSON: bad literal at $i"); i += w.length; return v }
        fun str(): String {
            expect('"'); val sb = StringBuilder()
            while (true) {
                if (i >= s.length) throw DatabaseError("JSON: unterminated string")
                val c = s[i++]
                when (c) {
                    '"' -> return sb.toString()
                    '\\' -> { val e = s[i++]
                        when (e) { 'n' -> sb.append('\n'); 't' -> sb.append('\t'); 'r' -> sb.append('\r'); 'b' -> sb.append('\b'); 'f' -> sb.append('\u000c')
                            'u' -> { sb.append(s.substring(i, i + 4).toInt(16).toChar()); i += 4 }
                            else -> sb.append(e) } }
                    else -> sb.append(c)
                }
            }
        }
    }

    /** JSON genérico (mapas, listas, textos, números Long/Double, booleanos, null); para outros leitores do projeto, como a tabela de chips. */
    fun readJson(text: String): Any? = Json(text).value()

    /** Lê uma base `data/NOME.json` do repositório oscartreader/oscr-databases (D127), igual a parse_oscr_json de host/oscr_host/database.py: só `type` CART, só registros com CRC32. */
    fun parseOscrJson(text: String, source: String): List<DbEntry> {
        val d = try { Json(text).value() } catch (e: DatabaseError) { throw DatabaseError("$source: invalid JSON (${e.message})") }
        if (d !is Map<*, *> || d["type"] != "CART" || d["records"] !is List<*>) return emptyList()
        val stem = source.substringAfterLast('/').substringBeforeLast('.').lowercase()
        val out = ArrayList<DbEntry>()
        for (r in d["records"] as List<*>) {
            if (r !is Map<*, *>) continue
            val c = r["crc32"] as? String ?: continue
            if (c.isEmpty() || c.length > 8 || !c.all { it in "0123456789abcdefABCDEF" }) continue
            val crc = c.toLong(16).toInt()
            if (crc == 0) continue
            var e = DbEntry(ROM_EXT.replace(r["name"]?.toString() ?: "", ""), crc, 0, source.substringAfterLast('/'), "oscr")
            val hdr = (r["header"] as? String)?.takeIf { stem == "nes" && it.length == 32 && it.all { ch -> ch in "0123456789abcdefABCDEF" } }
                ?.let { h -> ByteArray(16) { h.substring(it * 2, it * 2 + 2).toInt(16).toByte() } }
            val n = hdr?.let { ines(it) }
            if (n != null) e = e.copy(size = (n.prgKb + n.chrKb) * 1024L, mapper = n.mapper, submapper = n.submapper, prgKb = n.prgKb, chrKb = n.chrKb, ramKb = n.ramKb, battery = n.battery)
            else if (stem == "gba" && r["size"] is Long) e = e.copy(size = (r["size"] as Long) * 1024 * 1024)
            else if (stem == "snes" && r["size"] is Long) e = e.copy(size = r["size"] as Long)
            out += e
        }
        return out
    }

    /** Carrega a base que vem no projeto (recurso `oscr/INDEX.txt` e os .txt listados nele). Devolve quantas entradas entraram (0 se o recurso não existe). */
    fun loadBuiltin(db: Database): Int {
        val loader = DatabaseLoader::class.java.classLoader
        val index = loader.getResourceAsStream("oscr/INDEX.txt")?.use { String(it.readBytes(), Charsets.UTF_8) } ?: return 0
        var n = 0
        for (name in index.lines().map { it.trim() }.filter { it.isNotEmpty() }) {
            val text = loader.getResourceAsStream("oscr/$name")?.use { String(it.readBytes(), Charsets.UTF_8) } ?: continue
            if (name.endsWith(".json")) { for (e in parseOscrJson(text, name)) if (!db.has(e.crc)) { db.add(e); n++ } }       // base nova (D127): só o CRC32 que ainda não está na base antiga
            else for (e in parseOscr(text, name)) { db.add(e); n++ }
            db.files += "oscr/$name"
        }
        return n
    }

    private fun hex(v: String?): Int? = v?.takeIf { it.isNotEmpty() }?.toLongOrNull(16)?.toInt()
    private fun num(v: String?): Long = v?.toLongOrNull() ?: 0L

    private class Node(val name: String, val attrs: Map<String, String>)

    private class Game(val attrs: Map<String, String>) {
        val children = ArrayList<Node>()
        fun first(n: String) = children.firstOrNull { it.name == n }
    }

    private fun kb(n: Node?) = if (n == null) 0 else ((num(n.attrs["size"]) + 1023) / 1024).toInt()

    private fun nes20(g: Game, source: String): DbEntry? {
        val pcb = g.first("pcb"); val prg = g.first("prgrom"); val chr = g.first("chrrom")
        if (pcb == null || prg == null) return null
        val rom = g.first("rom")
        val nv = g.first("prgnvram"); val ram = g.first("prgram")
        val mapper = num(pcb.attrs["mapper"]).toInt()
        val prgCrc = hex(prg.attrs["crc32"] ?: prg.attrs["crc"])
        var name = g.attrs["name"] ?: rom?.attrs?.get("name") ?: ""
        val prgKb = kb(prg); val chrKb = kb(chr)
        if (name.isEmpty()) name = "mapper $mapper, PRG $prgKb KB, CHR $chrKb KB" + (prgCrc?.let { " (${(it.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')})" } ?: "")
        return DbEntry(name, hex(rom?.attrs?.get("crc32") ?: rom?.attrs?.get("crc")) ?: 0, num(rom?.attrs?.get("size")), source, "nes20",
            prgCrc, if (chr != null) hex(chr.attrs["crc32"] ?: chr.attrs["crc"]) else null, mapper, num(pcb.attrs["submapper"]).toInt(),
            prgKb, chrKb, if (kb(nv) != 0) kb(nv) else kb(ram), pcb.attrs["battery"] == "1" || nv != null)
    }

    fun parseFile(f: File): List<DbEntry> {
        if (f.extension.equals("txt", true)) return parseOscr(f.readText(Charsets.UTF_8), f.name)
        if (f.extension.equals("json", true)) return parseOscrJson(f.readText(Charsets.UTF_8), f.name)
        val out = ArrayList<DbEntry>()
        val factory = XMLInputFactory.newInstance().apply {
            setProperty(XMLInputFactory.SUPPORT_DTD, false)
            setProperty(XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES, false)
        }
        try {
            FileInputStream(f).use { ins ->
                val r: XMLStreamReader = factory.createXMLStreamReader(ins)
                var game: Game? = null
                while (r.hasNext()) {
                    when (r.next()) {
                        XMLStreamConstants.START_ELEMENT -> {
                            val attrs = HashMap<String, String>()
                            for (i in 0 until r.attributeCount) attrs[r.getAttributeLocalName(i)] = r.getAttributeValue(i)
                            val tag = r.localName
                            if (game == null && (tag == "game" || tag == "machine" || tag == "software")) game = Game(attrs)
                            else game?.children?.add(Node(tag, attrs))
                        }
                        XMLStreamConstants.END_ELEMENT -> {
                            val tag = r.localName
                            val g = game
                            if (g != null && (tag == "game" || tag == "machine" || tag == "software")) {
                                val n20 = nes20(g, f.name)
                                if (n20 != null) out += n20
                                else for (rom in g.children.filter { it.name == "rom" }) {
                                    val crc = hex(rom.attrs["crc"] ?: rom.attrs["crc32"]) ?: continue
                                    out += DbEntry(g.attrs["name"] ?: rom.attrs["name"] ?: "", crc, num(rom.attrs["size"]), f.name)
                                }
                                game = null
                            }
                        }
                    }
                }
            }
        } catch (e: XMLStreamException) {
            throw DatabaseError("${f.path}: invalid XML (${e.message?.lineSequence()?.firstOrNull() ?: e})")
        }
        return out
    }

    /** Carrega um arquivo, ou todos os .dat, .xml, .json e .txt (base do OSCR) de uma pasta (recursivo). Devolve quantas entradas entraram. */
    fun load(db: Database, path: String): Int {
        val p = File(if (path.startsWith("~")) (System.getProperty("user.home") ?: ".") + path.substring(1) else path)
        if (!p.exists()) throw DatabaseError("database not found: $p")
        val files = if (p.isDirectory) p.walkTopDown().filter { it.isFile && (it.extension.lowercase() in setOf("dat", "xml", "json") || (it.extension.equals("txt", true) && it.name.lowercase() !in NOT_DB)) }.sortedWith(compareBy({ it.extension.equals("json", true) }, { it.path })).toList() else listOf(p)     // .json por último: só entra o CRC32 novo
        var n = 0
        for (f in files) {
            val novo = f.extension.equals("json", true)
            for (e in parseFile(f)) { if (novo && db.has(e.crc)) continue; db.add(e); n++ }
            db.files += f.path
        }
        return n
    }

    /** A base do projeto (se [builtin]) vem primeiro e vence em CRC32 repetido; depois as do usuário. */
    fun loadAll(paths: List<String>, builtin: Boolean = true): Database = Database().also { db ->
        if (builtin) loadBuiltin(db)
        paths.forEach { load(db, it) }
    }

    /** Caminhos da variável OSCR_DB. */
    fun pathsFromEnv(): List<String> = (System.getenv("OSCR_DB") ?: "").split(File.pathSeparator).filter { it.isNotEmpty() }
}
