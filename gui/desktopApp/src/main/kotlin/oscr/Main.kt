// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.ui.graphics.Color
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.selection.SelectionContainer
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.focusable
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.input.key.*
import androidx.compose.ui.unit.DpSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import androidx.compose.ui.window.rememberWindowState
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.awt.FileDialog
import java.awt.Frame
import java.awt.Toolkit
import java.awt.datatransfer.StringSelection
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

const val APP_VERSION = "0.1.0"

private fun pickFile(title: String, save: Boolean, name: String = ""): File? {
    val d = FileDialog(null as Frame?, title, if (save) FileDialog.SAVE else FileDialog.LOAD)
    if (name.isNotEmpty()) d.file = name
    if (Prefs.lastDir.isNotEmpty() && File(Prefs.lastDir).isDirectory) d.directory = Prefs.lastDir
    d.isVisible = true
    val f = d.file?.let { File(d.directory, it) }
    if (f != null) f.parent?.let { Prefs.lastDir = it }
    return f
}

/** Leitura pronta na memória, à espera de um arquivo. Cancelar o "Salvar como" não a perde. */
private class Pending(val data: ByteArray, val defaultName: String, val label: String, val report: String)

/** Gravação à espera da confirmação do usuário. */
private class WriteRequest(val file: File, val data: ByteArray)

/** Gravação de ROM em flash à espera da confirmação (apaga o chip). */
private class RomWriteRequest(val file: File, val chip: FlashChip, val image: RomImage)

fun main() = application {
    val state = rememberWindowState(size = DpSize(Prefs.winW.dp, Prefs.winH.dp))
    Window(onCloseRequest = {
        Prefs.winW = state.size.width.value.toInt(); Prefs.winH = state.size.height.value.toInt()
        exitApplication()
    }, title = "oscr_minimal", state = state) {
        MaterialTheme(colorScheme = if (isSystemInDarkTheme()) darkColorScheme() else lightColorScheme()) { App() }
    }
}

private fun safeName(title: String, fallback: String): String = title.replace(Regex("[^A-Za-z0-9._ -]+"), "_").trim(' ', '.', '_').ifEmpty { fallback }

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun App() {
    var lang by remember { mutableStateOf(Lang.entries.firstOrNull { it.tag == Prefs.lang } ?: I18n.fromLocale(Locale.getDefault().toString())) }
    fun t(k: S) = I18n.t(lang, k)
    fun f(k: S, vararg a: Any) = I18n.f(lang, k, *a)

    var ports by remember { mutableStateOf(SerialTransport.ports()) }
    var port by remember { mutableStateOf(Prefs.port.takeIf { p -> ports.any { it.name == p } } ?: ports.firstOrNull()?.name ?: "") }
    var baud by remember { mutableStateOf(Prefs.baud) }
    var planned by remember { mutableStateOf<PlannedSystem?>(null) }   // cartucho do OSCR ainda sem suporte (stub): nada é enviado ao dispositivo
    var system by remember { mutableStateOf(CartSystem.entries.firstOrNull { it.name == Prefs.system && it != CartSystem.MOCK } ?: CartSystem.SNES) }
    var client by remember { mutableStateOf<OscrClient?>(null) }
    var transport by remember { mutableStateOf<Transport?>(null) }
    var info by remember { mutableStateOf<DeviceInfo?>(null) }
    var busy by remember { mutableStateOf(false) }
    var showSettings by remember { mutableStateOf(false) }
    var db by remember { mutableStateOf<Database?>(null) }
    var dbPaths by remember { mutableStateOf(Prefs.dbPaths) }
    var dbLoading by remember { mutableStateOf(false) }
    var dbError by remember { mutableStateOf<String?>(null) }
    var gameQuery by remember { mutableStateOf("") }
    var showAdvanced by remember { mutableStateOf(false) }
    var firstRun by remember { mutableStateOf(!Prefs.firstRunDone) }
    var mapper by remember { mutableStateOf("0") }
    var gbaType by remember { mutableStateOf("3") }
    var prgKb by remember { mutableStateOf("0") }
    var chrKb by remember { mutableStateOf("0") }
    var ramKb by remember { mutableStateOf("0") }
    var progress by remember { mutableStateOf(0f) }
    var stage by remember { mutableStateOf<S?>(null) }
    var speed by remember { mutableStateOf("") }
    var slowNote by remember { mutableStateOf(false) }
    var pending by remember { mutableStateOf<Pending?>(null) }
    var writeReq by remember { mutableStateOf<WriteRequest?>(null) }
    var romReq by remember { mutableStateOf<RomWriteRequest?>(null) }
    var verifyRom by remember { mutableStateOf(Prefs.verifyRom) }
    var romChip by remember { mutableStateOf<FlashChip?>(null) }          // null = automático (pelo mapper do cabeçalho)
    var snesLayout by remember { mutableStateOf("1x") }                  // flash CFI do SNES: disposição dos chips
    var snesCapacity by remember { mutableStateOf("") }                  // "" = a menor em que a ROM cabe (só na disposição 1x)
    var flashType by remember { mutableStateOf("29f032") }               // P0/P1: tipo do flash de 8 bits
    var flashMb by remember { mutableStateOf("4") }
    var block369 by remember { mutableStateOf("0") }                    // GBA 369-in-1: bloco de 4 MB onde a gravação começa
    var sectorKb by remember { mutableStateOf("") }
    var bufferBytes by remember { mutableStateOf("") }
    var backupFirst by remember { mutableStateOf(true) }
    var saveReport by remember { mutableStateOf(Prefs.saveReport) }
    val detectedNames = remember { mutableStateMapOf<CartSystem, String>() }
    val log = remember { mutableStateListOf<String>() }
    var lastMessage by remember { mutableStateOf("") }
    val scope = rememberCoroutineScope()
    val logScroll = rememberScrollState()
    val clock = remember { SimpleDateFormat("HH:mm:ss") }

    fun say(s: String) { lastMessage = s; log += "${clock.format(Date())}  $s" }
    LaunchedEffect(log.size) { logScroll.animateScrollTo(logScroll.maxValue) }

    // ---- base de dados de jogos (identificação por CRC32 no PC; o firmware não a usa)
    fun loadDatabases(paths: List<String>) {
        dbPaths = paths; Prefs.dbPaths = paths; dbError = null
        if (paths.isEmpty()) { db = null; return }
        scope.launch {
            dbLoading = true
            try { db = withContext(Dispatchers.IO) { DatabaseLoader.loadAll(paths) } }
            catch (e: Exception) { db = null; dbError = e.message ?: e.toString() }
            finally { dbLoading = false }
        }
    }
    LaunchedEffect(Unit) { if (Prefs.dbPaths.isNotEmpty()) loadDatabases(Prefs.dbPaths) }
    val dbHasNes = remember(db) { db?.entries?.any { it.nesOptions() != null } == true }
    fun addDatabase() {
        val ch = javax.swing.JFileChooser(Prefs.lastDir.takeIf { File(it).isDirectory }).apply {
            fileSelectionMode = javax.swing.JFileChooser.FILES_AND_DIRECTORIES; dialogTitle = I18n.t(lang, S.DB_CHOOSE)
        }
        if (ch.showOpenDialog(null) == javax.swing.JFileChooser.APPROVE_OPTION) {
            ch.selectedFile.parent?.let { Prefs.lastDir = it }
            val path = ch.selectedFile.path
            if (path !in dbPaths) loadDatabases(dbPaths + path)
        }
    }

    // ---- validação enquanto digita (mesmas regras do firmware)
    val isNes = system == CartSystem.NES || system == CartSystem.FAMICOM
    val isSnes = system == CartSystem.SNES
    val isMd = system == CartSystem.MD
    val isGba = system == CartSystem.GBA
    val canWriteRom = isNes || isSnes || isMd || isGba                                    // gravação de ROM: flash do NES e flash CFI do SNES
    val chipChoice: FlashChip? = romChip?.takeIf { it in FlashChip.forSystem(system) }     // a escolha vale só para o sistema atual
    val prgN = prgKb.toIntOrNull() ?: 0; val chrN = chrKb.toIntOrNull() ?: 0; val ramN = ramKb.toIntOrNull() ?: 0; val mapN = mapper.toIntOrNull() ?: 0
    val problem: Problem? = when {
        isNes -> Rules.nes(mapN, prgN, chrN)
        system == CartSystem.SNES || system == CartSystem.MD -> Rules.romSize(system, prgN)
        else -> null
    }
    val ramProblem: Problem? = if (isNes) Rules.nesRam(mapN, ramN) else null

    fun dropConnection(msg: S? = S.NOT_CONNECTED) {
        transport?.close(); client = null; transport = null; info = null
        if (msg != null) say(t(msg))
    }

    fun run(stageKey: S, block: suspend () -> Unit) {
        scope.launch {
            busy = true; progress = 0f; speed = ""; stage = stageKey
            try { block() } catch (e: Exception) {
                say(describeError(lang, e))
                if ((e is ProtocolError && e.fail == Fail.DISCONNECTED) || transport?.isOpen == false) { dropConnection(null); say(t(S.STATUS_DISCONNECTED)) }
            } finally { busy = false; stage = null; speed = ""; slowNote = false }
        }
    }

    fun ticker(): Progress {
        val start = System.nanoTime()
        return { done, total ->
            progress = if (total > 0) done.toFloat() / total else 0f
            val secs = (System.nanoTime() - start) / 1e9
            if (secs > 1.0 && done > 0 && total > 0) {   // total 0 = tamanho desconhecido (modo fluxo): sem estimativa
                val bps = done / secs
                speed = f(S.SPEED_ETA, String.format(Locale.ROOT, "%.1f", bps / 1024.0), ((total - done) / bps).toInt())
            }
        }
    }

    fun mapperArg() = (if (system == CartSystem.GBA) gbaType else mapper).toIntOrNull() ?: 0
    fun ramArg() = if (isNes) ramN else 0

    fun reportText(p: String, crc: String, size: Int, extra: List<String>) =
        (listOf("oscr_minimal $APP_VERSION", "${t(S.SYSTEM)}: ${system.name}", p, "${t(S.RESULT_SIZE)}: $size ${t(S.BYTES)}", "CRC32: $crc") + extra).joinToString("\n") + "\n"

    fun savePending(file: File) {
        val p = pending ?: return
        file.writeBytes(p.data)
        if (saveReport) File(file.path + ".txt").writeText(p.report)
        say("${t(S.SAVED_TO)} $file")
        pending = null
    }

    fun offerSave(p: Pending) {
        pending = p
        val f = pickFile(t(S.CHOOSE_FILE), true, p.defaultName)
        if (f != null) savePending(f)          // se cancelar, a leitura continua na memória, com o botão "Salvar como..."
    }

    // ---- ações
    fun actConnect() {
        run(S.STAGE_IDLE) {
            val order = listOf(baud) + listOf(1_000_000, 115_200).filter { it != baud }
            var last: Exception? = null
            for (b in order) {
                var tr: SerialTransport? = null
                try {
                    val (tr2, c, i) = withContext(Dispatchers.IO) {
                        val x = SerialTransport(port, b); tr = x
                        val cl = OscrClient(x, 500)
                        Triple(x, cl, cl.info())
                    }
                    if (b != baud) { say(f(S.BAUD_FALLBACK, baud, b)); baud = b }
                    transport = tr2; client = c; info = i
                    Prefs.port = port; Prefs.baud = baud; Prefs.firstRunDone = true; firstRun = false
                    say("${t(S.CONNECTED)}: ${t(S.DEVICE_INFO)} ${i.firmware}" + if (i.mock) " — ${t(S.MOCK_MODE)}" else "")
                    return@run
                } catch (e: TimeoutError) { last = e; tr?.close() }
                catch (e: Exception) { tr?.close(); throw e }
            }
            throw last ?: TimeoutError()
        }
    }

    fun actDetect() {
        if (planned != null) return
        val c = client ?: return
        run(S.STAGE_DETECTING) {
            val r = withContext(Dispatchers.IO) { c.detect(system) }
            val st = when (r.status) { 0 -> S.CART_FOUND; 1 -> S.CART_NONE; 2 -> S.CART_UNSUPPORTED; 4 -> S.CART_BAD_HEADER; else -> S.CART_HW_ERROR }
            if (r.status == 0) detectedNames[system] = r.name
            say(t(st) + if (r.status == 0) " — ${t(S.TITLE_LABEL)}: ${r.name.ifEmpty { "?" }}, ${t(S.ROM_LABEL)}: ${r.romSize}, ${t(S.SAVE_LABEL)}: ${r.saveSize}" else "")
        }
    }

    fun actDumpRom() {
        if (planned != null) return
        val c = client ?: return
        if (problem != null) { say(describeProblem(lang, problem)); return }
        run(S.STAGE_READING_ROM) {
            val res = withContext(Dispatchers.IO) { c.dumpRom(system, 0, mapN, prgN, chrN, ticker()) }
            val chk = verifyRom(system, res.data)
            val extra = mutableListOf<String>()
            if (chk.status == CheckStatus.OK) { val m = "${t(S.CHECKSUM_OK)} (${chk.name} ${chk.hex(chk.expected)})"; say(m); extra += m }
            else if (chk.status == CheckStatus.MISMATCH) { val m = "${t(S.CHECKSUM_BAD)}: ${chk.hex(chk.expected)} / ${chk.hex(chk.computed)}"; say(m); extra += m }
            if (system == CartSystem.GBA) {
                val h = gbaSaveHint(res.data)
                val m = if (h != null) "${t(S.GBA_SAVE_IN_ROM)}: ${h.tag}, ${h.label} → ${t(S.GBA_SAVE_TYPE)}: ${h.type}" else t(S.GBA_SAVE_NONE)
                say(m); extra += m
            }
            val ext = if (system == CartSystem.GB && res.data.size > 0x143 && (res.data[0x143].toInt() and 0x80) != 0) ".gbc" else system.ext
            val game = db?.identify(system, res.data)
            if (db != null) {
                val m = if (game != null) "${t(S.GAME_LABEL)}: ${game.entry.name} (${game.entry.source})" else t(S.GAME_NOT_FOUND)
                say(m); extra += m
            }
            val title = game?.entry?.name ?: detectedNames[system].orEmpty()
            say("CRC32 ${res.crcHex} — ${t(S.RESULT_SIZE)} ${res.data.size} ${t(S.BYTES)}")
            val report = reportText(title, res.crcHex, res.data.size, extra)
            offerSave(Pending(res.data, safeName(title, "rom_${system.name.lowercase()}") + ext, "ROM", report))
        }
    }

    fun actReadSave() {
        if (planned != null) return
        val c = client ?: return
        if (ramProblem != null) { say(describeProblem(lang, ramProblem)); return }
        run(S.STAGE_READING_SAVE) {
            val res = withContext(Dispatchers.IO) { c.readSave(system, 0, mapperArg(), ramArg(), ticker()) }
            say("CRC32 ${res.crcHex} — ${t(S.RESULT_SIZE)} ${res.data.size} ${t(S.BYTES)}")
            val title = detectedNames[system].orEmpty()
            offerSave(Pending(res.data, safeName(title, "save_${system.name.lowercase()}") + ".sav", "save", reportText(title, res.crcHex, res.data.size, emptyList())))
        }
    }

    fun actWriteChoose() {
        if (planned != null) return
        if (ramProblem != null) { say(describeProblem(lang, ramProblem)); return }
        val file = pickFile(t(S.CHOOSE_FILE), false) ?: return
        writeReq = WriteRequest(file, file.readBytes())
    }

    fun actWriteConfirmed(req: WriteRequest) {
        val c = client ?: return
        slowNote = system == CartSystem.GBA || system == CartSystem.MD
        run(S.STAGE_WRITING_SAVE) {
            if (backupFirst) {                                   // lê o save atual e guarda uma cópia ANTES de sobrescrever
                stage = S.BACKUP_SAVED
                val cur = withContext(Dispatchers.IO) { c.readSave(system, 0, mapperArg(), ramArg(), ticker()) }
                val dir = File(System.getProperty("user.home"), "oscr_backups").also { it.mkdirs() }
                val bf = File(dir, "${system.name.lowercase()}_${SimpleDateFormat("yyyyMMdd-HHmmss").format(Date())}.sav")
                bf.writeBytes(cur.data)
                say("${t(S.BACKUP_SAVED)}: $bf — CRC32 ${cur.crcHex}")
                stage = S.STAGE_WRITING_SAVE; progress = 0f
            }
            val crc = withContext(Dispatchers.IO) { c.writeSave(system, req.data, Proto.DEFAULT_BLOCK, mapperArg(), ramArg(), ticker()) }
            say("${t(S.DONE)}: ${req.data.size} ${t(S.BYTES)}, CRC32 ${(crc.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')}")
        }
    }

    fun describeRomImage(e: RomImageException): String = when (e.problem) {
        RomImageProblem.TRUNCATED_HEADER -> t(S.RIMG_TRUNCATED)
        RomImageProblem.TRAINER -> t(S.RIMG_TRAINER)
        RomImageProblem.SIZE_MISMATCH -> f(S.RIMG_SIZE, e.a, e.b, e.c)
        RomImageProblem.NEEDS_HEADER -> t(S.RIMG_NEEDS_HEADER)
        RomImageProblem.RAW_SIZE -> t(S.RIMG_RAW)
        RomImageProblem.CHIP_UNKNOWN -> t(S.RIMG_CHIP)
        RomImageProblem.SNES_SIZE -> t(S.RIMG_SNES_SIZE)
        RomImageProblem.SNES_TOO_BIG -> f(S.RIMG_SNES_TOO_BIG, e.a)
        RomImageProblem.SNES_NO_FIT -> f(S.RIMG_SNES_NO_FIT, e.a, e.b)
        RomImageProblem.SNES_CAPACITY -> t(S.RIMG_SNES_CAPACITY)
        RomImageProblem.SNES_NEEDS_CHIP -> t(S.RIMG_SNES_NEEDS_CHIP)
        RomImageProblem.GBA_BLOCK -> t(S.RIMG_GBA_BLOCK)
        RomImageProblem.GBA_SIZE -> t(S.RIMG_GBA_SIZE)
        RomImageProblem.GBA_TOO_BIG -> f(S.RIMG_GBA_TOO_BIG, e.a, e.b)
        RomImageProblem.MD_SIZE -> t(S.RIMG_MD_SIZE)
        RomImageProblem.MD_TOO_BIG -> f(S.RIMG_MD_TOO_BIG, e.a)
        RomImageProblem.MD_SMD -> t(S.RIMG_MD_SMD)
        RomImageProblem.SNES_LAYOUT -> t(S.RIMG_SNES_LAYOUT)
        RomImageProblem.SNES_BAD_LAYOUT -> f(S.RIMG_SNES_BAD_LAYOUT, e.a)
        RomImageProblem.SNES_CAPACITY_FIXED -> t(S.RIMG_SNES_CAPACITY_FIXED)
        RomImageProblem.GEN_TYPE -> t(S.RIMG_GEN_TYPE)
        RomImageProblem.GEN_MB -> t(S.RIMG_GEN_MB)
        RomImageProblem.GEN_NO_FIT -> f(S.RIMG_GEN_NO_FIT, e.a, e.b)
        RomImageProblem.GEN_NEEDS_SECTOR -> t(S.RIMG_GEN_NEEDS_SECTOR)
        RomImageProblem.GEN_SECTOR -> t(S.RIMG_GEN_SECTOR)
        RomImageProblem.GEN_BUFFER -> t(S.RIMG_GEN_BUFFER)
        RomImageProblem.GEN_PADDED_NO_FIT -> f(S.RIMG_GEN_PADDED, e.a, e.b)
    }

    fun actRomWriteChoose() {
        if (planned != null || !canWriteRom) return
        if (isSnes && chipChoice == null) { say(t(S.ERR_PREFIX) + ": " + t(S.RIMG_SNES_NEEDS_CHIP)); return }
        val file = pickFile(t(S.CHOOSE_FILE), false) ?: return
        try {
            val (chip, img) = RomImages.prepare(file.readBytes(), if (isMd) FlashChip.MD_FLASH else if (isGba) FlashChip.GBA_FLASH else chipChoice,
                if (snesLayout == "1x") snesCapacity.toIntOrNull() else null, snesLayout, flashMb.toIntOrNull(), flashType, sectorKb.toIntOrNull(), bufferBytes.toIntOrNull(), block369.toIntOrNull() ?: 0)
            romReq = RomWriteRequest(file, chip, img)
        } catch (e: RomImageException) { say(t(S.ERR_PREFIX) + ": " + describeRomImage(e)) }
    }

    fun actRomWriteConfirmed(req: RomWriteRequest) {
        val c = client ?: return
        if (info?.writeRom != true) { say(t(S.ERR_PREFIX) + ": " + t(S.ROM_NO_FW)); return }
        run(S.STAGE_WRITING_ROM) {
            val crc = withContext(Dispatchers.IO) { c.writeRom(system, req.image.body, req.chip.code, if (req.image.flashKb > 0) req.image.flashKb else req.image.prgKb, req.image.chrKb, Proto.DEFAULT_BLOCK, ticker()) }
            say("${t(S.ROM_WRITTEN)}: ${req.chip.label}, " + (if (req.chip.md || req.chip.gba) "${req.image.body.size} bytes" else if (req.image.flashKb > 0) "ROM ${req.image.prgKb} KB / flash ${req.image.flashKb} KB" else "PRG ${req.image.prgKb} KB, CHR ${req.image.chrKb} KB") + ", CRC32 ${(crc.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')}")
            val gbaSkip = req.chip.gba && (req.image.block != 0 || req.image.body.size > RomImages.GBA_VERIFY_MAX_BYTES)
            if (verifyRom && !gbaSkip) {
                stage = S.STAGE_VERIFYING_ROM; progress = 0f
                val v = withContext(Dispatchers.IO) { verifyWritten(c, system, req.chip, req.image, ticker()) }
                fun hex(x: Int) = (x.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')
                say(if (v.ok) f(S.ROM_VERIFY_OK, v.readBytes, hex(v.readCrc)) else t(S.ERR_PREFIX) + ": " + f(S.ROM_VERIFY_BAD, v.firstDiff ?: 0, hex(v.readCrc), hex(v.expectedCrc)))
            } else say(t(S.ROM_VERIFY_HINT))
        }
    }

    fun actAbort() { client?.abort() }

    fun copyLog() {
        Toolkit.getDefaultToolkit().systemClipboard.setContents(StringSelection(logText(info, log)), null)
        lastMessage = t(S.LOG_COPIED)
    }

    fun saveLog() {
        val f = pickFile(t(S.SAVE_LOG), true, "oscr_log_${SimpleDateFormat("yyyyMMdd-HHmmss").format(Date())}.txt") ?: return
        f.writeText(logText(info, log))
    }

    // ---- interface
    val focus = remember { FocusRequester() }
    LaunchedEffect(Unit) { focus.requestFocus() }
    val connected = client != null
    val stub = planned
    var logOpen by remember { mutableStateOf(true) }
    val dbStatus = when { dbLoading -> t(S.DB_LOADING); dbError != null -> f(S.DB_ERROR, dbError ?: ""); db != null -> f(S.DB_LOADED, db?.size ?: 0, db?.files?.size ?: 0); else -> t(S.DB_NONE) }
    val canRun = connected && !busy && stub == null

    // Cartão "Conexão": porta, conectar, baud (em "Avançado")
    val connectionCard: @Composable () -> Unit = {
        SectionCard(t(S.CONNECTION_TITLE)) {
            LabeledField(t(S.PORT)) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    ComboBox(value = ports.firstOrNull { it.name == port }?.label ?: "—", enabled = !connected && ports.isNotEmpty(), modifier = Modifier.weight(1f)) { close ->
                        ports.forEach { p -> DropdownMenuItem(text = { Text(p.label) }, onClick = { port = p.name; close() }) }
                    }
                    TextButton(enabled = !connected, onClick = { ports = SerialTransport.ports(); if (ports.none { it.name == port }) port = ports.firstOrNull()?.name ?: "" }) { Text(t(S.REFRESH)) }
                }
            }
            if (ports.isEmpty()) Callout(t(S.NO_PORTS), Tone.ERROR)
            if (!connected) {
                Button(enabled = port.isNotEmpty() && !busy, onClick = { actConnect() }, modifier = Modifier.fillMaxWidth().height(48.dp)) {
                    Text(if (lastMessage.startsWith(t(S.ERR_PREFIX)) && info == null && log.isNotEmpty()) t(S.RECONNECT) else t(S.CONNECT))
                }
            } else {
                OutlinedButton(enabled = !busy, onClick = { dropConnection() }, modifier = Modifier.fillMaxWidth().height(48.dp)) { Text(t(S.DISCONNECT)) }
            }
            TextButton(onClick = { showAdvanced = !showAdvanced }) { Text((if (showAdvanced) "▾ " else "▸ ") + t(S.ADVANCED)) }
            if (showAdvanced) LabeledField(t(S.BAUD)) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf(1_000_000, 115_200).forEach { b -> FilterChip(selected = baud == b, enabled = !connected, onClick = { baud = b }, label = { Text("$b") }) }
                }
            }
        }
    }

    // Cartão "Cartucho": sistema e as opções do sistema escolhido
    val cartridgeCard: @Composable () -> Unit = {
        SectionCard(t(S.CARTRIDGE_TITLE)) {
            LabeledField(t(S.SYSTEM)) {
                SystemPicker(
                    systems = CartSystem.entries.filter { info?.mock == true || it != CartSystem.MOCK },
                    selected = system, stub = planned, soonTitle = t(S.SOON_TITLE),
                    onSystem = { sys ->
                        planned = null
                        if (sys != system) { system = sys; prgKb = "0"; chrKb = "0"; ramKb = "0"; mapper = "0"; Prefs.system = sys.name }   // cada sistema começa limpo: nada "vaza" de um para outro
                    },
                    onStub = { planned = it },
                )
            }
            if (stub != null) Callout(f(S.STUB_NOTICE, stub.label), Tone.INFO)
            if (stub == null && system == CartSystem.GB) Callout(t(S.GB_WARNING), Tone.WARN)
            if (stub == null && system == CartSystem.GBA) {
                Callout(t(S.GBA_WARNING), Tone.WARN)
                OutlinedTextField(gbaType, { gbaType = it.filter(Char::isDigit).take(1) }, label = { Text(t(S.GBA_SAVE_TYPE)) }, singleLine = true,
                    supportingText = { Text(t(S.GBA_SAVE_HINT)) }, modifier = Modifier.fillMaxWidth())
            }
            if (stub == null && (system == CartSystem.MD || system == CartSystem.SNES)) {
                OutlinedTextField(prgKb, { prgKb = it.filter(Char::isDigit).take(5) }, label = { Text(t(S.ROM_SIZE_KB)) }, singleLine = true, isError = problem != null,
                    supportingText = { problem?.let { Text(describeProblem(lang, it)) } }, modifier = Modifier.fillMaxWidth())
            }
            if (stub == null && isNes) {
                Text(t(S.NES_OPTIONS), style = MaterialTheme.typography.titleSmall)
                if (dbHasNes) {
                    OutlinedTextField(gameQuery, { gameQuery = it }, label = { Text(t(S.GAME_SEARCH)) }, singleLine = true, modifier = Modifier.fillMaxWidth())
                    if (gameQuery.trim().length >= 2) {
                        val found = remember(gameQuery, db) { db?.searchNes(gameQuery, 8).orEmpty() }
                        if (found.isEmpty()) Text(t(S.GAME_NO_RESULTS), style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.outline)
                        found.forEach { g ->
                            val o = g.nesOptions() ?: return@forEach
                            TextButton(onClick = {
                                mapper = o.mapper.toString(); prgKb = o.prgKb.toString(); chrKb = o.chrKb.toString()
                                ramKb = if (o.ramKb in setOf(8, 16, 32)) o.ramKb.toString() else "0"
                                say(f(S.GAME_FILLED, g.name)); gameQuery = ""
                            }) { Text("${g.name} — mapper ${o.mapper}, PRG ${o.prgKb} KB, CHR ${o.chrKb} KB") }
                        }
                    }
                }
                val prgBad = problem?.key in setOf(S.V_PRG_REQUIRED, S.V_PRG_MULTIPLE16, S.V_PRG_MULTIPLE32, S.V_TOO_BIG_PRG)
                val chrBad = problem?.key in setOf(S.V_CHR_MULTIPLE8, S.V_NO_CHR, S.V_NEEDS_CHR, S.V_TOO_BIG_CHR)
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    OutlinedTextField(mapper, { mapper = it.filter(Char::isDigit).take(3) }, label = { Text(t(S.MAPPER)) }, singleLine = true, isError = problem?.key == S.V_UNSUPPORTED_MAPPER,
                        supportingText = { Text(Rules.mapperName(mapN) ?: "?") }, modifier = Modifier.width(170.dp))
                    OutlinedTextField(prgKb, { prgKb = it.filter(Char::isDigit).take(5) }, label = { Text(t(S.PRG_KB)) }, singleLine = true, isError = prgBad, modifier = Modifier.width(120.dp))
                    OutlinedTextField(chrKb, { chrKb = it.filter(Char::isDigit).take(5) }, label = { Text(t(S.CHR_KB)) }, singleLine = true, isError = chrBad, modifier = Modifier.width(120.dp))
                    OutlinedTextField(ramKb, { ramKb = it.filter(Char::isDigit).take(3) }, label = { Text(t(S.RAM_KB)) }, singleLine = true, isError = ramProblem != null, modifier = Modifier.width(120.dp))
                }
                (problem ?: ramProblem)?.let { Callout(describeProblem(lang, it), Tone.ERROR) }
                Text(t(S.NES_HINT), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
            }
        }
    }

    // Leitura (segura) e gravação (destrutiva) em cartões separados: a gravação tem cor própria e fica longe dos botões de leitura
    val readCard: @Composable () -> Unit = {
        SectionCard(t(S.READ_SECTION)) {
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(enabled = canRun && problem == null, onClick = { actDumpRom() }) { Text(t(S.DUMP_ROM)) }
                FilledTonalButton(enabled = canRun && ramProblem == null, onClick = { actReadSave() }) { Text(t(S.READ_SAVE)) }
                OutlinedButton(enabled = canRun, onClick = { actDetect() }) { Text(t(S.DETECT)) }
                if (busy) Button(onClick = { actAbort() }, colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)) { Text(t(S.ABORT)) }
            }
            Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(saveReport, { saveReport = it; Prefs.saveReport = it }); Text(t(S.SAVE_REPORT), style = MaterialTheme.typography.bodyMedium)
            }
            Text(t(S.SHORTCUTS), style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
        }
    }
    val writeCard: @Composable () -> Unit = {
        SectionCard(t(S.WRITE_SECTION), container = MaterialTheme.colorScheme.errorContainer.copy(alpha = 0.35f), titleColor = MaterialTheme.colorScheme.error) {
            val dangerBorder = BorderStroke(1.dp, MaterialTheme.colorScheme.error)
            val dangerColors = ButtonDefaults.outlinedButtonColors(contentColor = MaterialTheme.colorScheme.error)
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(enabled = canRun && ramProblem == null, onClick = { actWriteChoose() }, border = dangerBorder, colors = dangerColors) { Text(t(S.WRITE_SAVE)) }
                OutlinedButton(enabled = canRun && canWriteRom && info?.writeRom == true, onClick = { actRomWriteChoose() }, border = dangerBorder, colors = dangerColors) { Text(t(S.WRITE_ROM)) }
            }
            if (stub == null && canWriteRom && !isMd && !isGba) LabeledField(t(S.FLASH_CHIP)) {
                ComboBox(value = chipChoice?.label ?: (if (isSnes) "—" else t(S.FLASH_CHIP_AUTO)), modifier = Modifier.fillMaxWidth()) { close ->
                    if (isNes) DropdownMenuItem(text = { Text(t(S.FLASH_CHIP_AUTO)) }, onClick = { close(); romChip = null })
                    FlashChip.forSystem(system).forEach { ch -> DropdownMenuItem(text = { Text(ch.label) }, onClick = { close(); romChip = ch }) }
                }
            }
            if (stub == null && isGba) OutlinedTextField(block369, { block369 = it.filter(Char::isDigit).take(2) }, label = { Text(t(S.LBL_BLOCK369)) }, singleLine = true, modifier = Modifier.width(200.dp))
            if (stub == null && isSnes && chipChoice != null) {
                if (chipChoice.generic) {
                    LabeledField(t(S.LBL_FLASH_TYPE)) {
                        ComboBox(value = flashType, modifier = Modifier.fillMaxWidth()) { close ->
                            SnesLayouts.FLASH_TYPES.keys.forEach { k -> DropdownMenuItem(text = { Text(k) }, onClick = { close(); flashType = k }) }
                        }
                    }
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(flashMb, { flashMb = it.filter(Char::isDigit).take(1) }, label = { Text(t(S.LBL_FLASH_MB)) }, singleLine = true, modifier = Modifier.width(120.dp))
                        if (flashType in SnesLayouts.NEED_SECTOR) {
                            OutlinedTextField(sectorKb, { sectorKb = it.filter(Char::isDigit).take(5) }, label = { Text(t(S.LBL_SECTOR_KB)) }, singleLine = true, modifier = Modifier.width(140.dp))
                            OutlinedTextField(bufferBytes, { bufferBytes = it.filter(Char::isDigit).take(3) }, label = { Text(t(S.LBL_BUFFER)) }, singleLine = true, modifier = Modifier.width(140.dp))
                        }
                    }
                } else {
                    LabeledField(t(S.LBL_LAYOUT)) {
                        ComboBox(value = snesLayout, modifier = Modifier.fillMaxWidth()) { close ->
                            SnesLayouts.NAMES.keys.forEach { k -> DropdownMenuItem(text = { Text(k) }, onClick = { close(); snesLayout = k }) }
                        }
                    }
                    if (snesLayout == "1x") LabeledField(t(S.LBL_CAPACITY)) {
                        ComboBox(value = if (snesCapacity.isEmpty()) t(S.LBL_CAPACITY_AUTO) else "$snesCapacity KB", modifier = Modifier.fillMaxWidth()) { close ->
                            DropdownMenuItem(text = { Text(t(S.LBL_CAPACITY_AUTO)) }, onClick = { close(); snesCapacity = "" })
                            RomImages.SNES_CAPACITIES_KB.forEach { c -> DropdownMenuItem(text = { Text("$c KB") }, onClick = { close(); snesCapacity = c.toString() }) }
                        }
                    }
                }
            }
            if (stub == null && canWriteRom) Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(verifyRom, { verifyRom = it; Prefs.verifyRom = it }); Text(t(S.VERIFY_AFTER), style = MaterialTheme.typography.bodyMedium)
            }
            Text(if (stub == null && canWriteRom) (if (info?.writeRom == false && connected) t(S.ROM_NO_FW) else t(if (isSnes) S.ROM_WRITE_HINT_SNES else if (isMd) S.ROM_WRITE_HINT_MD else if (isGba) S.ROM_WRITE_HINT_GBA else S.ROM_WRITE_HINT)) else t(S.ROM_ONLY_NES),
                style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.outline)
        }
    }
    val pendingCard: @Composable () -> Unit = {
        pending?.let { p ->
            SectionCard("${t(S.PENDING_TITLE)}: ${p.label}, ${p.data.size} ${t(S.BYTES)}", container = MaterialTheme.colorScheme.tertiaryContainer, titleColor = MaterialTheme.colorScheme.onTertiaryContainer) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = { pickFile(t(S.CHOOSE_FILE), true, p.defaultName)?.let { savePending(it) } }) { Text(t(S.SAVE_AS)) }
                    OutlinedButton(onClick = { pending = null }) { Text(t(S.DISCARD)) }
                }
            }
        }
    }

    Column(
        Modifier.fillMaxSize().background(MaterialTheme.colorScheme.surface).focusRequester(focus).focusable().onPreviewKeyEvent { ev ->
            if (ev.type != KeyEventType.KeyDown) return@onPreviewKeyEvent false
            when {
                ev.key == Key.Escape && busy -> { actAbort(); true }
                ev.isCtrlPressed && ev.key == Key.D && connected && !busy -> { actDetect(); true }
                ev.isCtrlPressed && ev.key == Key.R && connected && !busy -> { actDumpRom(); true }
                ev.isCtrlPressed && ev.key == Key.S && connected && !busy -> { actReadSave(); true }
                else -> false
            }
        },
    ) {
        // cabeçalho: título, estado da conexão e configurações; o aviso de segurança fica logo abaixo, sempre visível
        Row(Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 16.dp), horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(t(S.TITLE), style = MaterialTheme.typography.headlineSmall, modifier = Modifier.weight(1f))
            StatusPill(connected, if (connected) "${t(S.STATUS_CONNECTED)}: ${info?.firmware ?: ""}${if (info?.mock == true) " — ${t(S.MOCK_MODE)}" else ""}" else t(S.STATUS_DISCONNECTED))
            OutlinedButton(onClick = { showSettings = !showSettings }) { Text((if (showSettings) "▾ " else "▸ ") + t(S.SETTINGS)) }
        }
        Box(Modifier.padding(horizontal = 24.dp)) { Callout(t(S.ONE_CART_ONLY), Tone.ERROR) }

        // área central: rola se a janela for pequena; duas colunas quando larga (conexão à esquerda, trabalho à direita), uma coluna quando estreita
        BoxWithConstraints(Modifier.weight(1f).fillMaxWidth()) {
            val wide = maxWidth >= 840.dp
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                Column(Modifier.widthIn(max = 1120.dp).fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(16.dp)) {
                    if (showSettings) SettingsPanel(lang, { lang = it; Prefs.lang = it.tag }, dbPaths, dbStatus, dbLoading, { addDatabase() }, { loadDatabases(emptyList()) })
                    if (firstRun) FirstRunCard(lang) { firstRun = false; Prefs.firstRunDone = true }
                    if (wide) Row(horizontalArrangement = Arrangement.spacedBy(16.dp), verticalAlignment = Alignment.Top) {
                        Column(Modifier.weight(0.38f), verticalArrangement = Arrangement.spacedBy(16.dp)) { connectionCard() }
                        Column(Modifier.weight(0.62f), verticalArrangement = Arrangement.spacedBy(16.dp)) { pendingCard(); cartridgeCard(); readCard(); writeCard() }
                    } else Column(verticalArrangement = Arrangement.spacedBy(16.dp)) { connectionCard(); pendingCard(); cartridgeCard(); readCard(); writeCard() }
                }
            }
        }

        // painel de estado: sempre visível (etapa, progresso, última mensagem e registro)
        Surface(tonalElevation = 3.dp, modifier = Modifier.fillMaxWidth()) {
            Column(Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp), verticalAlignment = Alignment.CenterVertically) {
                    Text(t(stage ?: S.STAGE_IDLE), style = MaterialTheme.typography.titleSmall)
                    if (speed.isNotEmpty()) Text(speed, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.outline)
                }
                LinearProgressIndicator(progress = { progress }, modifier = Modifier.fillMaxWidth().height(6.dp), strokeCap = androidx.compose.ui.graphics.StrokeCap.Round)
                if (slowNote && busy) Text("⏳ " + t(S.SLOW_NOTE), style = MaterialTheme.typography.bodyMedium)
                if (lastMessage.isNotEmpty()) Text(lastMessage, style = MaterialTheme.typography.bodyLarge,
                    color = if (lastMessage.startsWith(t(S.ERR_PREFIX) + ":")) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                    TextButton(onClick = { logOpen = !logOpen }) { Text((if (logOpen) "▾ " else "▸ ") + t(S.LOG), style = MaterialTheme.typography.titleSmall) }
                    Spacer(Modifier.weight(1f))
                    TextButton(enabled = log.isNotEmpty(), onClick = { copyLog() }) { Text(t(S.COPY_LOG)) }
                    TextButton(enabled = log.isNotEmpty(), onClick = { saveLog() }) { Text(t(S.SAVE_LOG)) }
                }
                if (logOpen) SelectionContainer {
                    Column(Modifier.fillMaxWidth().height(88.dp).background(MaterialTheme.colorScheme.surfaceContainerLowest, RoundedCornerShape(8.dp)).padding(8.dp).verticalScroll(logScroll)) {
                        log.forEach { Text(it, style = MaterialTheme.typography.bodySmall) }
                    }
                }
            }
        }
    }

    romReq?.let { req ->
        AlertDialog(
            onDismissRequest = { romReq = null },
            title = { Text(t(S.CONFIRM_ROM_TITLE)) },
            text = { Text(f(S.CONFIRM_ROM_BODY, req.file.name, "PRG ${req.image.prgKb} KB, CHR ${req.image.chrKb} KB", req.chip.label)) },
            confirmButton = { Button(onClick = { romReq = null; actRomWriteConfirmed(req) }, colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)) { Text(t(S.WRITE_ROM)) } },
            dismissButton = { OutlinedButton(onClick = { romReq = null }) { Text(t(S.CANCEL)) } },
        )
    }

    writeReq?.let { req ->
        AlertDialog(
            onDismissRequest = { writeReq = null },
            title = { Text(t(S.CONFIRM_WRITE_TITLE)) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(f(S.CONFIRM_WRITE_BODY, req.file.name, req.data.size, system.name))
                    Row(verticalAlignment = Alignment.CenterVertically) { Checkbox(backupFirst, { backupFirst = it }); Text(t(S.BACKUP_FIRST), style = MaterialTheme.typography.bodyMedium) }
                }
            },
            confirmButton = { Button(onClick = { writeReq = null; actWriteConfirmed(req) }, colors = ButtonDefaults.buttonColors(containerColor = MaterialTheme.colorScheme.error)) { Text(t(S.WRITE)) } },
            dismissButton = { OutlinedButton(onClick = { writeReq = null }) { Text(t(S.CANCEL)) } },
        )
    }
}

private fun logText(info: DeviceInfo?, log: List<String>): String =
    (listOf("oscr_minimal GUI $APP_VERSION", "java ${System.getProperty("java.version")} / ${System.getProperty("os.name")} ${System.getProperty("os.version")}",
        info?.let { "firmware ${it.firmware} proto ${it.proto} flags 0x${it.flags.toString(16)} sistemas 0x${it.systemsMask.toString(16)} payload ${it.maxPayload}" } ?: "firmware: -", "") + log).joinToString("\n") + "\n"

fun describeProblem(lang: Lang, p: Problem): String { val a = p.arg; return if (a != null) I18n.f(lang, p.key, a) else I18n.t(lang, p.key) }

@Composable
fun FirstRunCard(lang: Lang, onDismiss: () -> Unit) {
    fun t(k: S) = I18n.t(lang, k)
    Card(colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer), modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
            Text(t(S.FIRST_RUN_TITLE), style = MaterialTheme.typography.titleSmall)
            listOf(S.FIRST_RUN_1, S.FIRST_RUN_2, S.FIRST_RUN_3, S.FIRST_RUN_4).forEach { Text(t(it), style = MaterialTheme.typography.bodyMedium) }
            OutlinedButton(onClick = onDismiss) { Text(t(S.FIRST_RUN_DISMISS)) }
        }
    }
}

@Composable
private fun Section(title: String, content: @Composable ColumnScope.() -> Unit) {
    var open by remember { mutableStateOf(true) }
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        TextButton(onClick = { open = !open }) { Text((if (open) "▾ " else "▸ ") + title, style = MaterialTheme.typography.titleSmall) }
        if (open) content()
    }
}

/** Configurações: idioma, base de dados de jogos e ajuda (a ajuda e o idioma deixaram a tela principal). */
@Composable
private fun SettingsPanel(lang: Lang, onLang: (Lang) -> Unit, dbPaths: List<String>, dbStatus: String, dbLoading: Boolean, onAddDb: () -> Unit, onClearDb: () -> Unit) {
    fun t(k: S) = I18n.t(lang, k)
    var helpOpen by remember { mutableStateOf(false) }
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(t(S.SETTINGS), style = MaterialTheme.typography.titleMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                Text(t(S.LANGUAGE))
                Lang.entries.forEach { l -> FilterChip(selected = lang == l, onClick = { onLang(l) }, label = { Text(l.label) }) }
            }
            HorizontalDivider()
            Text(t(S.DB_TITLE), style = MaterialTheme.typography.titleSmall)
            Text(t(S.DB_HINT), style = MaterialTheme.typography.bodyMedium)
            dbPaths.forEach { Text("• $it", style = MaterialTheme.typography.bodySmall) }
            Text(dbStatus, style = MaterialTheme.typography.bodyMedium)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(enabled = !dbLoading, onClick = onAddDb) { Text(t(S.DB_CHOOSE)) }
                OutlinedButton(enabled = dbPaths.isNotEmpty() && !dbLoading, onClick = onClearDb) { Text(t(S.DB_CLEAR)) }
            }
            HorizontalDivider()
            TextButton(onClick = { helpOpen = !helpOpen }) { Text((if (helpOpen) "▾ " else "▸ ") + t(S.HELP_BUTTON), style = MaterialTheme.typography.titleSmall) }
            if (helpOpen) HelpPanel(lang)
        }
    }
}

private enum class Tone { INFO, WARN, ERROR }

/** Cartão com título: agrupa o que é do mesmo assunto (proximidade) e dá um nível de hierarquia. */
@Composable
private fun SectionCard(title: String, container: Color = MaterialTheme.colorScheme.surfaceContainerLow, titleColor: Color = MaterialTheme.colorScheme.onSurface, content: @Composable ColumnScope.() -> Unit) {
    Card(Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = container)) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium, color = titleColor)
            content()
        }
    }
}

/** Rótulo pequeno acima do campo (padrão único para todos os campos do formulário). */
@Composable
private fun LabeledField(label: String, content: @Composable ColumnScope.() -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.outline)
        content()
    }
}

/** Aviso em linha, com cor por gravidade, no lugar de texto vermelho solto. */
@Composable
private fun Callout(text: String, tone: Tone) {
    val cs = MaterialTheme.colorScheme
    val (bg, fg, icon) = when (tone) {
        Tone.ERROR -> Triple(cs.errorContainer, cs.onErrorContainer, "⚠")
        Tone.WARN -> Triple(cs.tertiaryContainer, cs.onTertiaryContainer, "⚠")
        Tone.INFO -> Triple(cs.secondaryContainer, cs.onSecondaryContainer, "ℹ")
    }
    Row(Modifier.fillMaxWidth().background(bg, RoundedCornerShape(12.dp)).padding(horizontal = 12.dp, vertical = 10.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
        Text(icon, color = fg)
        Text(text, color = fg, style = MaterialTheme.typography.bodyMedium)
    }
}

/** Estado da conexão como "pílula": cor e ponto, não só texto. */
@Composable
private fun StatusPill(connected: Boolean, text: String) {
    val color = if (connected) Color(0xFF2E7D32) else MaterialTheme.colorScheme.outline
    Row(Modifier.background(color.copy(alpha = 0.12f), CircleShape).padding(horizontal = 12.dp, vertical = 6.dp), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(Modifier.size(8.dp).background(color, CircleShape))
        Text(text, style = MaterialTheme.typography.labelLarge, color = color)
    }
}

/** Combo box: botão com o valor atual e um menu; [content] recebe a função que fecha o menu. */
@Composable
private fun ComboBox(value: String, modifier: Modifier = Modifier, enabled: Boolean = true, content: @Composable ColumnScope.(close: () -> Unit) -> Unit) {
    var open by remember { mutableStateOf(false) }
    Box(modifier) {
        OutlinedButton(enabled = enabled, onClick = { open = true }, modifier = Modifier.fillMaxWidth().heightIn(min = 48.dp)) {
            Text(value, Modifier.weight(1f), maxLines = 1); Text("▾")
        }
        DropdownMenu(expanded = open, onDismissRequest = { open = false }, modifier = Modifier.heightIn(max = 420.dp)) { content { open = false } }
    }
}

/** Sistemas suportados, depois (sob um título) os stubs dos outros cartuchos do OSCR, que só mostram um aviso. */
private val collator: java.text.Collator = java.text.Collator.getInstance(Locale.ROOT)   // ordem alfabética que ignora maiúsculas e acentos (Pokémon vem com o P)

@Composable
private fun SystemPicker(systems: List<CartSystem>, selected: CartSystem, stub: PlannedSystem?, soonTitle: String, onSystem: (CartSystem) -> Unit, onStub: (PlannedSystem) -> Unit) {
    ComboBox(value = stub?.label ?: selected.name, modifier = Modifier.fillMaxWidth()) { close ->
        systems.sortedWith(compareBy(collator) { it.name }).forEach { s -> DropdownMenuItem(text = { Text(s.name) }, onClick = { close(); onSystem(s) }) }
        HorizontalDivider()
        Text(soonTitle, Modifier.padding(horizontal = 12.dp, vertical = 6.dp), style = MaterialTheme.typography.labelLarge, color = MaterialTheme.colorScheme.outline)
        PLANNED_SYSTEMS.sortedWith(compareBy(collator) { it.label }).forEach { p -> DropdownMenuItem(text = { Text(p.label) }, onClick = { close(); onStub(p) }) }
    }
}

@Composable
fun HelpPanel(lang: Lang) {
    fun t(k: S) = I18n.t(lang, k)
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(t(S.HELP_TITLE), style = MaterialTheme.typography.titleMedium)
            Section(t(S.HELP_USE_TITLE)) {
                listOf(S.HELP_USE_1, S.HELP_USE_2, S.HELP_USE_3, S.HELP_USE_4, S.HELP_USE_5, S.HELP_USE_6).forEach { Text("• " + t(it), style = MaterialTheme.typography.bodyMedium) }
            }
            Section(t(S.HELP_FIX_TITLE)) {
                listOf(S.HELP_FIX_1, S.HELP_FIX_2, S.HELP_FIX_3, S.HELP_FIX_4, S.HELP_FIX_5, S.HELP_FIX_6, S.HELP_FIX_7, S.HELP_FIX_8).forEach { Text("• " + t(it), style = MaterialTheme.typography.bodyMedium) }
            }
            Text(t(S.HELP_DOCS), style = MaterialTheme.typography.bodySmall)
        }
    }
}
