// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*
import java.io.File
import java.io.IOException
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

/**
 * CLI em Kotlin, com o mesmo contrato da CLI Python (docs/cli.md): comandos, opções, saída --json e códigos de saída.
 * Textos desta CLI (ajuda, dicas) são em inglês; erros do dispositivo e do protocolo vêm do I18n da GUI (--lang).
 * Agentes devem usar `ok`, `error.kind` e o código de saída, não o texto.
 */
class CliError(val kind: String, override val message: String, val exit: Int = Cli.EXIT_ERROR, val hint: String? = null,
               val extra: Map<String, Any?> = emptyMap()) : Exception(message)

/** Tudo o que a CLI usa do mundo exterior, para os testes poderem trocar. */
class CliIo(
    val out: (String) -> Unit,
    val err: (String) -> Unit,
    val interactive: Boolean,
    val stderrTty: Boolean,
    val readLine: () -> String?,
    val listPorts: () -> List<String>,
    val openPort: (String, Int) -> Transport,
    val home: String,
) {
    companion object {
        fun system() = CliIo(
            out = { println(it) }, err = { System.err.println(it) },
            interactive = System.console() != null, stderrTty = System.console() != null,
            readLine = { readlnOrNull() },
            listPorts = { SerialTransport.ports().map { it.name } },
            openPort = { p, b -> SerialTransport(p, b) },
            home = System.getProperty("user.home") ?: ".",
        )
    }
}

private class Args(val cmd: String?, val opts: Map<String, String>, val flags: Set<String>, val positional: List<String> = emptyList()) {
    val json get() = "json" in flags
    fun int(name: String): Int {
        val v = opts[name] ?: return 0
        return v.toIntOrNull()?.takeIf { it >= 0 } ?: throw CliError("usage", "--$name needs a non-negative integer, got '$v'", Cli.EXIT_USAGE)
    }
}

object Cli {
    const val EXIT_OK = 0; const val EXIT_ERROR = 1; const val EXIT_NO_CART = 2; const val EXIT_NO_DEVICE = 3
    const val EXIT_REFUSED = 4; const val EXIT_USAGE = 64; const val EXIT_INTERRUPTED = 130
    const val VERSION = "0.1.0"

    private val EXIT_MEANING = linkedMapOf(
        EXIT_OK to "success", EXIT_ERROR to "device, protocol, timeout or file error",
        EXIT_NO_CART to "no cartridge", EXIT_NO_DEVICE to "serial port not found or device not responding",
        EXIT_REFUSED to "refused: save-write without --yes outside a terminal", EXIT_USAGE to "invalid arguments",
        EXIT_INTERRUPTED to "interrupted (Ctrl+C)",
    )
    private val VALUED = mapOf("p" to "port", "b" to "baud", "s" to "system", "o" to "output", "i" to "input")
    private val LONG_VALUED = setOf("port", "baud", "system", "output", "input", "progress", "lang", "block", "mapper", "prg", "chr", "ram", "backup-dir", "db", "game", "limit", "chip", "begin-timeout")
    private val FLAGS = setOf("simulate", "json", "yes", "no-backup", "help", "version")
    private val COMMANDS = setOf("ports", "systems", "errors", "info", "detect", "dump", "save-read", "save-write", "identify", "search", "rom-write")
    private val OPTIONS = mapOf("snes" to listOf("prg"), "nes" to listOf("mapper", "prg", "chr", "ram"), "famicom" to listOf("mapper", "prg", "chr", "ram"),
        "md" to listOf("prg"), "gba" to listOf("mapper"), "gb" to emptyList(), "mock" to emptyList())
    private val STATUS = mapOf(0 to "cartridge detected", 1 to "no cartridge", 2 to "not supported", 3 to "hardware error",
        4 to "invalid header (data present but the header checksum fails: clean the contacts and reseat)")

    private val HELP = """
usage: dumper [options] <command> [options]

commands:
  ports        list serial ports
  systems      list systems, extensions and per-system options (does not open the port)
  errors       list device error codes and CLI exit codes (does not open the port)
  info         firmware version and supported systems
  detect       detect the cartridge            (-s SYSTEM)
  identify     identify saved ROMs by CRC32 in the database (--db), without opening the port
  search       search games by name in the database (--db), without opening the port
  dump         read the ROM                    (-s SYSTEM [-o FILE])
  save-read    read the save                   (-s SYSTEM [-o FILE])
  save-write   write the save                  (-s SYSTEM -i FILE --yes)
  rom-write    write the ROM to a flash cartridge, ERASES the chip (-i FILE [--chip nesmaker|a29040b] --yes)

options (accepted before or after the command):
  -p, --port PORT      serial port (default: first ttyUSB/ttyACM/COM)
  -b, --baud N         baud (default: 1000000, then 115200)
  --simulate           in-memory simulator (no hardware; only system 'mock' has a cartridge)
  --json               one JSON line on stdout, always with "ok"; errors: {"ok":false,"error":{kind,message,hint}}
  --progress MODE      auto | none | jsonl (one JSON line per 1% on stderr)
  --lang TAG           language of device error texts: en (default), pt-BR, ru, zh-CN
  -s, --system NAME    snes nes famicom md gba gb mock (default: mock)
  -o, --output FILE    output file (the right extension is added if missing; overwrites)
  -i, --input FILE     save file to write
  --block N            block size (default 512)
  --mapper N --prg KB --chr KB --ram KB     NES/Famicom/GBA options (see 'systems')
  --db PATH            game database: file or folder of .dat (No-Intro) or nes20db.xml; repeatable; also reads env OSCR_DB
  --game NAME          dump, NES/Famicom: game name in the NES 2.0 XML database; fills --mapper/--prg/--chr left at 0
  --limit N            search: maximum results (default 20)
  --chip NAME          rom-write: nesmaker (SST 39SF040, mapper 30) or a29040b (mapper 0); default: from the file's iNES mapper
  --begin-timeout S    rom-write: seconds to wait for the erase before the data (default 90)
  --yes                do not ask before writing (required outside a terminal)
  --no-backup          save-write: do not read the current save first
  --backup-dir DIR     save-write: backup folder (default ~/oscr_backups)

exit codes: 0 ok | 1 error | 2 no cartridge | 3 no port/device | 4 refused (needs --yes) | 64 usage | 130 Ctrl+C
Full contract: docs/cli.md
""".trim()

    private fun parse(argv: List<String>): Args {
        var cmd: String? = null
        val opts = linkedMapOf<String, String>(); val flags = linkedSetOf<String>(); val positional = ArrayList<String>()
        var i = 0
        while (i < argv.size) {
            val a = argv[i++]
            when {
                a == "-h" -> flags += "help"
                a.startsWith("--") -> {
                    val body = a.substring(2); val eq = body.indexOf('=')
                    val name = if (eq >= 0) body.substring(0, eq) else body
                    when {
                        name in FLAGS -> { if (eq >= 0) throw CliError("usage", "--$name does not take a value", EXIT_USAGE); flags += name }
                        name in LONG_VALUED -> {
                            val v = if (eq >= 0) body.substring(eq + 1) else argv.getOrNull(i++) ?: throw CliError("usage", "--$name needs a value", EXIT_USAGE)
                            opts[name] = if (name == "db" && name in opts) opts[name] + "\n" + v else v      // --db pode repetir
                        }
                        else -> throw CliError("usage", "unknown option: --$name", EXIT_USAGE)
                    }
                }
                a.length == 2 && a[0] == '-' && a[1].toString() in VALUED ->
                    opts[VALUED.getValue(a[1].toString())] = argv.getOrNull(i++) ?: throw CliError("usage", "$a needs a value", EXIT_USAGE)
                a.startsWith("-") && a.length > 1 -> throw CliError("usage", "unknown option: $a", EXIT_USAGE)
                cmd == null -> cmd = a
                cmd == "identify" || cmd == "search" -> positional += a
                else -> throw CliError("usage", "unexpected argument: $a", EXIT_USAGE)
            }
        }
        return Args(cmd, opts, flags, positional)
    }

    fun run(argv: List<String>, io: CliIo): Int {
        val jsonWanted = "--json" in argv
        var lang = Lang.EN
        try {
            val a = parse(argv)
            a.opts["lang"]?.let { t -> lang = Lang.entries.firstOrNull { it.tag.equals(t, true) || it.tag.substringBefore('-').equals(t, true) } ?: throw CliError("usage", "unknown --lang: $t", EXIT_USAGE) }
            if ("version" in a.flags) { io.out("dumper-kt $VERSION (protocol ${Proto.VERSION})"); return EXIT_OK }
            if ("help" in a.flags || a.cmd == null) { io.out(HELP); return if (a.cmd == null && "help" !in a.flags) EXIT_USAGE else EXIT_OK }
            if (a.cmd !in COMMANDS) throw CliError("usage", "unknown command: ${a.cmd}. Use: ${COMMANDS.joinToString(" ")}", EXIT_USAGE)
            a.opts["progress"]?.let { if (it !in setOf("auto", "none", "jsonl")) throw CliError("usage", "--progress must be auto, none or jsonl", EXIT_USAGE) }
            return when (a.cmd) {
                "ports" -> cmdPorts(io, a)
                "systems" -> cmdSystems(io, a)
                "errors" -> cmdErrors(io, a, lang)
                "info" -> cmdInfo(io, a)
                "detect" -> cmdDetect(io, a)
                "dump" -> cmdDump(io, a)
                "save-read" -> cmdSaveRead(io, a)
                "identify" -> cmdIdentify(io, a)
                "search" -> cmdSearch(io, a)
                "rom-write" -> cmdRomWrite(io, a)
                else -> cmdSaveWrite(io, a)
            }
        } catch (e: CliError) {
            return fail(io, jsonWanted, e)
        } catch (e: DeviceError) {
            val (kind, code) = when (e.code) { 3 -> "no_cartridge" to EXIT_NO_CART; 10 -> "no_save" to EXIT_ERROR; else -> "device_error" to EXIT_ERROR }
            return fail(io, jsonWanted, CliError(kind, describeError(lang, e), code, extra = mapOf("device_code" to e.code)))
        } catch (e: TimeoutError) {
            return fail(io, jsonWanted, CliError("timeout", describeError(lang, e), EXIT_ERROR, "the device stopped responding; check the cable and retry"))
        } catch (e: ProtocolError) {
            val open = e.fail == Fail.OPEN_PORT
            return fail(io, jsonWanted, CliError(if (open) "open_port" else "protocol", describeError(lang, e), if (open) EXIT_NO_DEVICE else EXIT_ERROR))
        } catch (e: IOException) {
            return fail(io, jsonWanted, CliError("io", e.message ?: e.toString()))
        } catch (e: Throwable) {
            return fail(io, jsonWanted, CliError("internal", e.toString()))
        }
    }

    private fun fail(io: CliIo, json: Boolean, e: CliError): Int {
        if (json) {
            val err = linkedMapOf<String, Any?>("kind" to e.kind, "message" to e.message)
            e.hint?.let { err["hint"] = it }
            err.putAll(e.extra)
            io.out(Json.encode(Json.obj("ok" to false, "error" to err)))
        } else io.err("error: ${e.message}" + (e.hint?.let { ". Hint: $it" } ?: ""))
        return e.exit
    }

    private fun emit(io: CliIo, a: Args, obj: Map<String, Any?>, lines: List<String>) {
        if (a.json) io.out(Json.encode(if ("ok" in obj) obj else linkedMapOf<String, Any?>("ok" to true) + obj)) else lines.forEach(io.out)
    }

    // ------------------------------------------------------------------ conexão
    private class Conn(val client: OscrClient, val transport: Transport, val info: DeviceInfo)

    private fun connect(io: CliIo, a: Args): Conn {
        if ("simulate" in a.flags) {
            val t = SimDevice(); val c = OscrClient(t, 500, 5000)
            return Conn(c, t, c.info())
        }
        val port = a.opts["port"] ?: io.listPorts().firstOrNull { p -> listOf("ttyUSB", "ttyACM", "cu.usb", "COM").any { it in p } }
            ?: throw CliError("no_port", "no serial port found", EXIT_NO_DEVICE, "connect the device, use --port, or --simulate without hardware (Linux: dialout group)")
        val bauds = a.opts["baud"]?.let { listOf(a.int("baud")) } ?: listOf(1_000_000, 115_200)
        var last: Exception? = null
        for (b in bauds) {
            val t = io.openPort(port, b)
            val c = OscrClient(t, 500, 10_000)
            try { return Conn(c, t, c.info()) } catch (e: TimeoutError) { last = e; t.close() }
        }
        throw CliError("no_response", "no response from the device on $port (${bauds.joinToString(", ")} baud): ${last?.message}", EXIT_NO_DEVICE,
            "check that the firmware is flashed, the port, and the baud (--baud 115200)")
    }

    private fun system(a: Args): CartSystem {
        val n = (a.opts["system"] ?: "mock").lowercase()
        return CartSystem.entries.firstOrNull { it.name.lowercase() == n }
            ?: throw CliError("usage", "unknown system: $n. Use: ${CartSystem.entries.joinToString(", ") { it.name.lowercase() }}", EXIT_USAGE)
    }

    private fun progress(io: CliIo, a: Args, label: String): Progress {
        val mode = a.opts["progress"] ?: "auto"
        var last = -1
        return { done, total ->
            if (mode != "none" && total > 0) {
                val pct = (done * 100 / total).toInt()
                if (pct != last) {
                    last = pct
                    if (mode == "jsonl") io.err(Json.encode(Json.obj("event" to "progress", "label" to label, "done" to done, "total" to total, "percent" to pct)))
                    else if (io.stderrTty) System.err.print("\r$label: ${pct.toString().padStart(3)}%  ($done/$total bytes)" + if (done >= total) "\n" else "")
                }
            }
        }
    }

    private fun outPath(a: Args, ext: String, default: String): File {
        val f = File(a.opts["output"] ?: default)
        return if (f.name.lastIndexOf('.') <= 0) File(f.path + ext) else f
    }

    private fun safeName(title: String, default: String): String =
        title.replace(Regex("[^A-Za-z0-9._ -]+"), "_").trim(' ', '.', '_').ifEmpty { default }

    private fun saveResult(io: CliIo, a: Args, res: DumpResult, ext: String, default: String, extra: Map<String, Any?> = emptyMap(), notes: List<String> = emptyList()) {
        val f = outPath(a, ext, default)
        f.absoluteFile.parentFile?.mkdirs()
        f.writeBytes(res.data)
        val obj = linkedMapOf<String, Any?>("file" to f.path, "bytes" to res.data.size, "crc32" to res.crcHex) + extra
        emit(io, a, obj, listOf("${f.path}  ${res.data.size} bytes  CRC32 ${res.crcHex}") + notes)
    }

    // ------------------------------------------------------------------ comandos
    private fun cmdPorts(io: CliIo, a: Args): Int {
        val p = io.listPorts()
        emit(io, a, Json.obj("ports" to p), p)
        return EXIT_OK
    }

    private fun cmdSystems(io: CliIo, a: Args): Int {
        val rows = CartSystem.entries.map { Json.obj("name" to it.name.lowercase(), "id" to it.id, "extension" to it.ext,
            "options" to OPTIONS.getValue(it.name.lowercase()), "needs_cartridge" to (it != CartSystem.MOCK)) }
        val planned = PLANNED_SYSTEMS.map { Json.obj("name" to it.key, "label" to it.label, "supported" to false) }
        emit(io, a, Json.obj("systems" to rows, "planned" to planned),
            rows.map { "${(it["name"] as String).padEnd(8)} id ${it["id"]}  ${it["extension"]}  options: ${(it["options"] as List<*>).joinToString(", ").ifEmpty { "-" }}" } +
                listOf("", "coming soon (other OSCR cartridges, no hardware, firmware or protocol id yet):") + PLANNED_SYSTEMS.map { "  ${it.key.padEnd(13)} ${it.label}" })
        return EXIT_OK
    }

    private fun cmdErrors(io: CliIo, a: Args, lang: Lang): Int {
        val dev = (1..11).map { Json.obj("code" to it, "text" to I18n.t(lang, S.valueOf("ERR_DEV_$it"))) }
        val exits = EXIT_MEANING.map { (c, m) -> Json.obj("exit_code" to c, "meaning" to m) }
        emit(io, a, Json.obj("device_errors" to dev, "exit_codes" to exits),
            EXIT_MEANING.map { (c, m) -> "exit $c: $m" } + dev.map { "${it["code"]}: ${it["text"]}" })
        return EXIT_OK
    }

    private fun cmdInfo(io: CliIo, a: Args): Int {
        val c = connect(io, a); val i = c.info
        val names = CartSystem.entries.filter { it.id < 16 && i.systemsMask and (1 shl it.id) != 0 }.map { it.name.lowercase() }
        c.transport.close()
        emit(io, a, Json.obj("proto" to i.proto, "firmware" to i.firmware, "flags" to i.flags, "max_payload" to i.maxPayload, "mock" to i.mock,
            "si5351" to i.si5351, "pic" to (i.flags and 4 != 0), "systems" to names),
            listOf("protocol ${i.proto}  firmware ${i.firmware}  MOCK=${if (i.mock) "yes" else "no"}  Si5351=${if (i.si5351) "yes" else "no"}  systems: ${names.joinToString(", ").ifEmpty { "-" }}  max payload ${i.maxPayload}"))
        return EXIT_OK
    }

    private fun cmdDetect(io: CliIo, a: Args): Int {
        val c = connect(io, a)
        val r = c.client.detect(system(a))
        c.transport.close()
        val text = STATUS[r.status] ?: r.status.toString()
        val lines = mutableListOf("${CartSystem.entries.firstOrNull { it.id == r.system }?.name?.lowercase() ?: r.system}: $text")
        if (r.status == 0) lines += "  title: ${r.name.ifEmpty { "(unknown)" }}  ROM: ${r.romSize} bytes  save: ${r.saveSize} bytes"
        emit(io, a, Json.obj("ok" to (r.status == 0), "system" to r.system, "status" to r.status, "rom_size" to r.romSize, "save_size" to r.saveSize,
            "save_type" to r.saveType, "name" to r.name, "status_text" to text), lines)
        return if (r.status == 0) EXIT_OK else EXIT_NO_CART
    }

    private fun cmdDump(io: CliIo, a: Args): Int {
        val sys = system(a)
        val db = loadDb(a, required = a.opts["game"] != null)
        var mapper = a.int("mapper"); var prg = a.int("prg"); var chr = a.int("chr")
        a.opts["game"]?.let { q ->
            if (sys != CartSystem.NES && sys != CartSystem.FAMICOM) throw CliError("usage", "--game applies to NES and Famicom only", EXIT_USAGE)
            val g = gameOptions(db!!, q); val o = g.nesOptions()!!
            if (mapper == 0) mapper = o.mapper; if (prg == 0) prg = o.prgKb; if (chr == 0) chr = o.chrKb
            if (!a.json) io.err("database game: ${g.name}  mapper ${o.mapper}  PRG ${o.prgKb} KB  CHR ${o.chrKb} KB  (${g.source})")
        }
        val c = connect(io, a)
        var title = ""
        if (a.opts["output"] == null) title = try { c.client.detect(sys).name } catch (e: Exception) { if (e is DeviceError || e is ProtocolError || e is TimeoutError) "" else throw e }
        val res = try { c.client.dumpRom(sys, a.int("block"), mapper, prg, chr, progress(io, a, "rom")) } finally { c.transport.close() }
        val ext = if (sys == CartSystem.GB && res.data.size > 0x143 && res.data[0x143].toInt() and 0x80 != 0) ".gbc" else sys.ext
        val chk = verifyRom(sys, res.data)
        val extra = linkedMapOf<String, Any?>("checksum" to chk.status.name.lowercase())
        val notes = mutableListOf<String>()
        if (chk.status != CheckStatus.NA) notes += (if (chk.status == CheckStatus.MISMATCH) "warning: " else "") + "${chk.name} checksum ${chk.status.name.lowercase()} (header ${chk.hex(chk.expected)}, computed ${chk.hex(chk.computed)})"
        if (sys == CartSystem.GBA) {
            val h = gbaSaveHint(res.data)
            if (h != null) { extra["gba_save_type"] = h.type; notes += "GBA save: ${h.tag}, ${h.label}: use --mapper ${h.type} with save-read" }
            else notes += "GBA save: no save library string in the ROM (no save, or unknown type)"
        }
        if (db != null) {
            val m = db.identify(sys, res.data)
            extra["game"] = m?.let { matchJson(it) }
            if (m != null) { title = m.entry.name; notes += "game: ${m.entry.name} (${m.entry.source}, ${m.how.text}" + (if (m.others > 0) ", ${m.others} identical more" else "") + ")" }
            else notes += "game: not found in the database (${db.size} entries): new dump, variant, or a read error if the CRC32 should be there"
        }
        saveResult(io, a, res, ext, safeName(title, "rom_${sys.name.lowercase()}"), extra, notes)
        return EXIT_OK
    }

    // ------------------------------------------------------------------ base de dados
    private val DbMatch.How.text get() = when (this) { DbMatch.How.CRC32 -> "crc32"; DbMatch.How.CRC32_NO_HEADER -> "crc32 without iNES header"; DbMatch.How.CRC32_PRG_CHR -> "crc32 of PRG and CHR" }
    private fun hex8(v: Int) = (v.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')

    private fun entryJson(e: DbEntry): MutableMap<String, Any?> {
        val d = LinkedHashMap(Json.obj("name" to e.name, "crc32" to hex8(e.crc), "size" to e.size, "source" to e.source, "kind" to e.kind))
        e.nesOptions()?.let { o -> d["mapper"] = o.mapper; d["submapper"] = e.submapper; d["prg_kb"] = o.prgKb; d["chr_kb"] = o.chrKb; d["ram_kb"] = o.ramKb; d["battery"] = e.battery }
        return d
    }

    private fun matchJson(m: DbMatch): Map<String, Any?> = entryJson(m.entry).also { it["match"] = m.how.text; it["others"] = m.others }

    private fun loadDb(a: Args, required: Boolean): Database? {
        val paths = a.opts["db"]?.split("\n").orEmpty().ifEmpty { DatabaseLoader.pathsFromEnv() }
        if (paths.isEmpty()) {
            if (required) throw CliError("no_database", "no database: use --db FILE_OR_FOLDER (No-Intro .dat or NES 2.0 XML) or the OSCR_DB environment variable", EXIT_USAGE)
            return null
        }
        try { return DatabaseLoader.loadAll(paths) }
        catch (e: DatabaseError) { throw CliError("database", e.message ?: "database error", EXIT_ERROR, "check the path and that the file is a Logiqx .dat or nes20db.xml") }
    }

    private fun gameOptions(db: Database, query: String): DbEntry {
        var found = db.searchNes(query, 200)
        val exact = found.filter { it.name.equals(query, true) }
        if (exact.isNotEmpty()) found = exact
        val uniq = LinkedHashMap<List<Int?>, DbEntry>()
        for (e in found) uniq[listOf(e.mapper, e.prgKb, e.chrKb, e.ramKb)] = e
        if (uniq.isEmpty()) throw CliError("game_not_found", "no game with mapper and sizes in the database for: $query", EXIT_USAGE,
            "the database must be the NES 2.0 XML (nes20db.xml); No-Intro has no mapper. Use 'search' to look up names")
        if (uniq.size > 1) throw CliError("game_ambiguous", "${found.size} games match '$query' with different configurations", EXIT_USAGE,
            "be more specific. Examples: " + uniq.values.take(5).joinToString("; ") { "${it.name} (mapper ${it.mapper}, PRG ${it.prgKb} KB, CHR ${it.chrKb} KB)" })
        return uniq.values.first()
    }

    private val EXT_SYSTEM = mapOf("sfc" to CartSystem.SNES, "smc" to CartSystem.SNES, "nes" to CartSystem.NES, "md" to CartSystem.MD, "gen" to CartSystem.MD,
        "smd" to CartSystem.MD, "gba" to CartSystem.GBA, "gb" to CartSystem.GB, "gbc" to CartSystem.GB)

    private fun cmdIdentify(io: CliIo, a: Args): Int {
        val db = loadDb(a, required = true)!!
        if (a.positional.isEmpty()) throw CliError("usage", "identify needs at least one file", EXIT_USAGE)
        val results = a.positional.map { f ->
            val file = File(f); val data = file.readBytes()
            val sys = if (a.opts["system"] != null) system(a) else EXT_SYSTEM[file.extension.lowercase()] ?: CartSystem.MOCK
            val m = db.identify(sys, data)
            Json.obj("file" to f, "bytes" to data.size, "crc32" to hex8(crc32(data)), "game" to m?.let { matchJson(it) })
        }
        emit(io, a, Json.obj("entries_in_database" to db.size, "results" to results), results.map { r ->
            val g = r["game"] as? Map<*, *>
            "${r["file"]}  CRC32 ${r["crc32"]}  " + (g?.let { "${it["name"]} (${it["source"]}, ${it["match"]})" } ?: "not found in the database")
        })
        return if (results.all { it["game"] != null }) EXIT_OK else EXIT_ERROR
    }

    private fun cmdSearch(io: CliIo, a: Args): Int {
        val db = loadDb(a, required = true)!!
        val q = a.positional.joinToString(" ").ifBlank { throw CliError("usage", "search needs a query", EXIT_USAGE) }
        val found = db.search(q, a.opts["limit"]?.let { a.int("limit") } ?: 20)
        emit(io, a, Json.obj("entries_in_database" to db.size, "results" to found.map { entryJson(it) }),
            found.map { e -> "${hex8(e.crc)}  ${e.name}" + (e.nesOptions()?.let { "  [mapper ${it.mapper}, PRG ${it.prgKb} KB, CHR ${it.chrKb} KB, RAM ${it.ramKb} KB]" } ?: "") }.ifEmpty { listOf("no results") })
        return if (found.isNotEmpty()) EXIT_OK else EXIT_ERROR
    }

    private fun cmdRomWrite(io: CliIo, a: Args): Int {
        val input = a.opts["input"] ?: throw CliError("usage", "rom-write needs -i/--input FILE", EXIT_USAGE)
        val sys = if (a.opts["system"] != null) system(a) else CartSystem.NES
        if (sys != CartSystem.NES && sys != CartSystem.FAMICOM && sys != CartSystem.MOCK)
            throw CliError("usage", "rom-write exists only for NES and Famicom so far (NES Maker and A29040B flash); see docs/funcoes-oscr.md", EXIT_USAGE)
        val chipOpt = a.opts["chip"]?.let { FlashChip.byKey(it) ?: throw CliError("usage", "unknown --chip: $it. Use: ${FlashChip.entries.joinToString(", ") { c -> c.key }}", EXIT_USAGE) }
        val (chip, img) = try { RomImages.prepare(File(input).readBytes(), chipOpt) }
        catch (e: RomImageException) {
            val msg = when (e.problem) {
                RomImageProblem.TRUNCATED_HEADER -> "incomplete iNES header"
                RomImageProblem.TRAINER -> "the file has a 512-byte trainer; remove it before writing"
                RomImageProblem.SIZE_MISMATCH -> "the file has ${e.a} bytes after the header, but the header says PRG ${e.b} KB and CHR ${e.c} KB"
                RomImageProblem.NEEDS_HEADER -> "the A29040B needs a .nes file with an iNES header (PRG and CHR come from the header)"
                RomImageProblem.RAW_SIZE -> "raw file: the size must be a multiple of 16 KB (use a .nes with header, or raw PRG)"
                RomImageProblem.CHIP_UNKNOWN -> "cannot tell the chip: use --chip nesmaker (mapper 30) or --chip a29040b (mapper 0)"
            }
            throw CliError(if (e.problem == RomImageProblem.CHIP_UNKNOWN) "usage" else "bad_rom", msg, EXIT_USAGE)
        }
        if (img.mapper != null && img.mapper != chip.mapper && !a.json) io.err("warning: the file is mapper ${img.mapper}, but chip ${chip.key} belongs to mapper ${chip.mapper} cartridges")
        val what = "${chip.label}: PRG ${img.prgKb} KB, CHR ${img.chrKb} KB (${img.body.size} bytes)"
        if ("yes" !in a.flags) {
            if (!io.interactive) throw CliError("refused", "refused: writing the ROM ERASES the cartridge's flash chip. Outside a terminal confirm with --yes.", EXIT_REFUSED, "repeat the command with --yes")
            io.err("Write $what? This ERASES the current ROM of the cartridge. Continue? [y/N] ")
            if (io.readLine()?.trim()?.lowercase() !in setOf("y", "yes", "s", "sim")) { io.out("cancelled"); return EXIT_ERROR }
        }
        val c = connect(io, a)
        val crc: Int
        try {
            if (!c.info.writeRom) throw CliError("unsupported_firmware", "this firmware does not support WRITE_ROM", EXIT_ERROR, "update the firmware (docs/funcoes-oscr.md)")
            val timeout = ((a.opts["begin-timeout"]?.toDoubleOrNull() ?: 90.0) * 1000).toLong()
            crc = c.client.writeRom(sys, img.body, chip.code, img.prgKb, img.chrKb, a.int("block").let { if (it == 0) Proto.DEFAULT_BLOCK else it }, progress(io, a, "write-rom"), timeout)
        } finally { c.transport.close() }
        val hex = (crc.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')
        emit(io, a, Json.obj("chip" to chip.key, "prg_kb" to img.prgKb, "chr_kb" to img.chrKb, "bytes" to img.body.size, "crc32" to hex),
            listOf("ROM written: $what  CRC32 $hex", "to verify, read the cartridge back (dump) and compare the CRC32"))
        return EXIT_OK
    }

    private fun cmdSaveRead(io: CliIo, a: Args): Int {
        val c = connect(io, a); val sys = system(a)
        val res = try { c.client.readSave(sys, a.int("block"), a.int("mapper"), a.int("ram"), progress(io, a, "save")) } finally { c.transport.close() }
        saveResult(io, a, res, ".sav", "save_${sys.name.lowercase()}")
        return EXIT_OK
    }

    private fun cmdSaveWrite(io: CliIo, a: Args): Int {
        val input = a.opts["input"] ?: throw CliError("usage", "save-write needs -i/--input FILE", EXIT_USAGE)
        val data = File(input).readBytes()
        val sys = system(a)
        if ("yes" !in a.flags) {
            if (!io.interactive) throw CliError("refused", "refused: writing the save overwrites the cartridge memory. Outside a terminal confirm with --yes.", EXIT_REFUSED,
                "repeat the command with --yes (the current save is backed up to --backup-dir first, unless --no-backup)")
            io.err("Write ${data.size} bytes to the ${sys.name.lowercase()} save? This overwrites the cartridge save. Continue? [y/N] ")
            if (io.readLine()?.trim()?.lowercase() !in setOf("y", "yes", "s", "sim")) { io.out("cancelled"); return EXIT_ERROR }
        }
        val c = connect(io, a)
        val extra = linkedMapOf<String, Any?>()
        val crc: Int
        try {
            if ("no-backup" !in a.flags) {
                val cur = c.client.readSave(sys, a.int("block"), a.int("mapper"), a.int("ram"), progress(io, a, "backup"))
                val dir = File((a.opts["backup-dir"] ?: "~/oscr_backups").let { if (it.startsWith("~")) io.home + it.substring(1) else it })
                dir.mkdirs()
                val f = File(dir, "${sys.name.lowercase()}_${LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss"))}.sav")
                f.writeBytes(cur.data)
                extra["backup"] = f.path
                if (!a.json) io.out("backup of the current save: ${f.path}  CRC32 ${cur.crcHex}")
            }
            crc = c.client.writeSave(sys, data, a.int("block").let { if (it == 0) Proto.DEFAULT_BLOCK else it }, a.int("mapper"), a.int("ram"), progress(io, a, "write"))
        } finally { c.transport.close() }
        val hex = (crc.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')
        extra["bytes"] = data.size; extra["crc32"] = hex
        emit(io, a, extra, listOf("save written: ${data.size} bytes  CRC32 $hex"))
        return EXIT_OK
    }
}
