// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

/** Base de jogos de N64 do projeto (recurso `oscr/json/n64.json`, do oscr-databases), por CRC1 do cabeçalho. Igual a load_games de host/oscr_host/n64.py. */
object N64Games {
    val byCrc1: Map<Long, List<N64.Game>> by lazy {
        val text = N64Games::class.java.classLoader.getResourceAsStream("oscr/json/n64.json")?.use { it.readBytes().toString(Charsets.UTF_8) } ?: return@lazy emptyMap()
        val d = try { DatabaseLoader.readJson(text) } catch (e: DatabaseError) { return@lazy emptyMap() }
        val out = LinkedHashMap<Long, MutableList<N64.Game>>()
        for (r in ((d as? Map<*, *>)?.get("records") as? List<*>).orEmpty()) {
            if (r !is Map<*, *>) continue
            val crc1 = (r["crc1"] as? String)?.toLongOrNull(16) ?: continue
            val crc32 = (r["crc32"] as? String)?.toLongOrNull(16) ?: continue
            val size = (r["size"] as? Long)?.toInt() ?: continue
            val save = (r["saveType"] as? Long)?.toInt() ?: 0
            out.getOrPut(crc1) { ArrayList() } += N64.Game(r["name"]?.toString() ?: "", crc1, crc32, size, save)
        }
        out
    }
}
