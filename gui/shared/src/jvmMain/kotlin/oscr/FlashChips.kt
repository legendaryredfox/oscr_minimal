// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/**
 * Tabela de chips de flash do OSCR (flash.json do oscr-databases, em `database/oscr/chips/`): do ID que o chip responde ao nome, tipo, tamanho,
 * setor e buffer. Igual a host/oscr_host/flashdb.py. No OSCR era o banco CRDB `flash` do cartão SD; aqui só **sugere**: nada é escolhido sozinho.
 */
object FlashChips {
    data class Chip(val routine: String, val id: String, val name: String, val type: String, val flashType: String, val size: Long, val sectorKb: Int?, val buffer: Int?, val voltage: Int?)

    private val typeName = SnesLayouts.FLASH_TYPES.entries.associate { it.value to it.key }

    private data class Rec(val id: String, val bits: Int, val name: String, val typeName: String, val type: Int, val size: Long, val sector: Long?, val buffer: Int?, val voltage: Int?, val variant: String?)

    private val records: List<Rec> by lazy {
        val text = FlashChips::class.java.classLoader.getResourceAsStream("oscr/chips/flash.json")?.use { it.readBytes().toString(Charsets.UTF_8) } ?: return@lazy emptyList()
        val d = try { DatabaseLoader.readJson(text) } catch (e: DatabaseError) { return@lazy emptyList() }
        ((d as? Map<*, *>)?.get("records") as? List<*>).orEmpty().mapNotNull { r ->
            if (r !is Map<*, *>) return@mapNotNull null
            val t = (r["type"] as? Long)?.toInt() ?: return@mapNotNull null
            if (t !in typeName) return@mapNotNull null                                   // tipo 0 = chips de GBA, fora daqui
            Rec((r["id"] as? String)?.uppercase() ?: return@mapNotNull null, (r["bits"] as? Long)?.toInt() ?: 8, r["name"]?.toString() ?: "", r["typeName"]?.toString() ?: "", t,
                (r["size"] as? Long) ?: return@mapNotNull null, r["sector"] as? Long, (r["buffer"] as? Long)?.toInt(), (r["voltage"] as? Long)?.toInt(), r["variant"]?.toString())
        }
    }

    fun count(): Int = records.size

    private val HEX = Regex("""\b([IABS])=([0-9A-Fa-f]{4})\b|\bID ([0-9A-Fa-f]{4})\b""")

    /** O texto que o firmware devolve ("I=XXXX A=XXXX B=XXXX S=XXXX" ou "ID XXXX") -> [(rotina, ID)], sem 0000 nem FFFF. */
    fun idsFromText(text: String): List<Pair<String, String>> = HEX.findAll(text).mapNotNull { m ->
        val label = m.groupValues[1]; val id = (if (label.isNotEmpty()) m.groupValues[2] else m.groupValues[3]).uppercase()
        if (id == "0000" || id == "FFFF") null else label to id
    }.toList()

    /** Chips da tabela com algum dos IDs de `text` e o barramento (8 e plcc32 = 8 bits; 16 = 16 bits). */
    fun candidates(text: String, bus: String): List<Chip> {
        val want = if (bus == "16") 16 else 8
        val seen = HashSet<Triple<String, String, String?>>(); val out = ArrayList<Chip>()
        for ((routine, id) in idsFromText(text)) for (r in records) {
            if (r.id != id || r.bits != want || !seen.add(Triple(id, r.name, r.variant))) continue
            out += Chip(routine, id, r.name, r.typeName, typeName.getValue(r.type), r.size, r.sector?.let { (it / 1024).toInt() }, r.buffer, r.voltage)
        }
        return out
    }

    /** Opções da CLI para o chip: no flash de 16 bits só o tamanho; no de 8 bits também o tipo e, se a tabela tiver, setor e buffer. */
    fun commandHint(c: Chip, bus: String): String {
        var s = "--flash-kb ${c.size / 1024}"
        if (bus != "16") {
            s = "--flash-type ${c.flashType} $s"
            if (c.sectorKb != null && c.buffer != null) s += " --sector-kb ${c.sectorKb} --buffer ${c.buffer}"
        }
        return s
    }
}
