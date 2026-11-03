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

/** Leitura streaming (StAX) de .dat/.xml; igual a parse_file/Database.load de host/oscr_host/database.py. */
object DatabaseLoader {
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

    /** Carrega um arquivo, ou todos os .dat e .xml de uma pasta (recursivo). Devolve quantas entradas entraram. */
    fun load(db: Database, path: String): Int {
        val p = File(if (path.startsWith("~")) (System.getProperty("user.home") ?: ".") + path.substring(1) else path)
        if (!p.exists()) throw DatabaseError("database not found: $p")
        val files = if (p.isDirectory) p.walkTopDown().filter { it.isFile && it.extension.lowercase() in setOf("dat", "xml") }.sortedBy { it.path }.toList() else listOf(p)
        var n = 0
        for (f in files) { for (e in parseFile(f)) { db.add(e); n++ }; db.files += f.path }
        return n
    }

    fun loadAll(paths: List<String>): Database = Database().also { db -> paths.forEach { load(db, it) } }

    /** Caminhos da variável OSCR_DB. */
    fun pathsFromEnv(): List<String> = (System.getenv("OSCR_DB") ?: "").split(File.pathSeparator).filter { it.isNotEmpty() }
}
