// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.awt.FileDialog
import java.awt.Frame
import java.io.File
import java.util.Locale

private fun pickFile(title: String, save: Boolean, name: String = ""): File? {
    val d = FileDialog(null as Frame?, title, if (save) FileDialog.SAVE else FileDialog.LOAD)
    if (name.isNotEmpty()) d.file = name
    d.isVisible = true
    return d.file?.let { File(d.directory, it) }
}

fun main() = application {
    Window(onCloseRequest = ::exitApplication, title = "oscr_minimal") {
        MaterialTheme { App() }
    }
}

@Composable
fun App() {
    var lang by remember { mutableStateOf(I18n.fromLocale(Locale.getDefault().toString())) }
    fun t(k: S) = I18n.t(lang, k)

    var ports by remember { mutableStateOf(SerialTransport.ports()) }
    var port by remember { mutableStateOf(ports.firstOrNull() ?: "") }
    var baud by remember { mutableStateOf(1_000_000) }
    var system by remember { mutableStateOf(CartSystem.SNES) }
    var client by remember { mutableStateOf<OscrClient?>(null) }
    var transport by remember { mutableStateOf<Transport?>(null) }
    var info by remember { mutableStateOf<DeviceInfo?>(null) }
    var busy by remember { mutableStateOf(false) }
    var showHelp by remember { mutableStateOf(false) }
    var mapper by remember { mutableStateOf("0") }
    var gbaType by remember { mutableStateOf("3") }
    var prgKb by remember { mutableStateOf("0") }
    var chrKb by remember { mutableStateOf("0") }
    var progress by remember { mutableStateOf(0f) }
    val log = remember { mutableStateListOf<String>() }
    val scope = rememberCoroutineScope()

    fun say(s: String) { log += s }

    fun run(block: suspend () -> Unit) {
        scope.launch {
            busy = true; progress = 0f
            try { block() } catch (e: Exception) { say("${t(S.ERROR)}: ${e.message}") } finally { busy = false }
        }
    }

    Column(Modifier.fillMaxSize().padding(16.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text(t(S.TITLE), style = MaterialTheme.typography.headlineSmall)
        Text(t(S.ONE_CART_ONLY), style = MaterialTheme.typography.bodySmall)

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(t(S.LANGUAGE))
            Lang.entries.forEach { l -> FilterChip(selected = lang == l, onClick = { lang = l }, label = { Text(l.label) }) }
            OutlinedButton(onClick = { showHelp = !showHelp }) { Text(t(S.HELP_BUTTON)) }
        }
        if (showHelp) HelpPanel(lang)

        // ---- conexão
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(t(S.PORT))
            ports.forEach { p -> FilterChip(selected = port == p, onClick = { port = p }, label = { Text(p) }) }
            OutlinedButton(onClick = { ports = SerialTransport.ports(); if (port !in ports) port = ports.firstOrNull() ?: "" }) { Text(t(S.REFRESH)) }
        }
        if (ports.isEmpty()) Text(t(S.NO_PORTS), color = MaterialTheme.colorScheme.error)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
            Text(t(S.BAUD))
            listOf(1_000_000, 115_200).forEach { b -> FilterChip(selected = baud == b, onClick = { baud = b }, label = { Text("$b") }) }
            if (client == null) {
                Button(enabled = port.isNotEmpty() && !busy, onClick = {
                    run {
                        val (tr, c, i) = withContext(Dispatchers.IO) {
                            val tr = SerialTransport(port, baud); val c = OscrClient(tr, 500)
                            Triple(tr, c, try { c.info() } catch (e: Exception) { tr.close(); throw e })
                        }
                        transport = tr; client = c; info = i
                        say("${t(S.CONNECTED)}: ${t(S.DEVICE_INFO)} ${i.firmware}" + if (i.mock) " — ${t(S.MOCK_MODE)}" else "")
                    }
                }) { Text(t(S.CONNECT)) }
            } else {
                Button(enabled = !busy, onClick = { transport?.close(); client = null; transport = null; info = null; say(t(S.NOT_CONNECTED)) }) { Text(t(S.DISCONNECT)) }
            }
        }

        // ---- operações
        val c = client
        Text("${t(S.SYSTEM)}:")
        Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
            val systems = if (info?.mock == true) CartSystem.entries else CartSystem.entries.filter { it != CartSystem.MOCK }
            systems.forEach { s -> FilterChip(selected = system == s, onClick = { system = s }, label = { Text(s.name) }) }
        }
        if (system == CartSystem.GBA) {
            Text(t(S.GBA_WARNING), color = MaterialTheme.colorScheme.error)
            OutlinedTextField(gbaType, { gbaType = it.filter(Char::isDigit).take(1) }, label = { Text(t(S.GBA_SAVE_TYPE)) }, singleLine = true, modifier = Modifier.width(180.dp))
            Text(t(S.GBA_SAVE_HINT), style = MaterialTheme.typography.bodySmall)
        }
        if (system == CartSystem.MD) {
            OutlinedTextField(prgKb, { prgKb = it.filter(Char::isDigit).take(5) }, label = { Text(t(S.ROM_SIZE_KB)) }, singleLine = true, modifier = Modifier.width(260.dp))
        }
        if (system == CartSystem.NES || system == CartSystem.FAMICOM) {
            Text(t(S.NES_OPTIONS), style = MaterialTheme.typography.titleSmall)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(mapper, { mapper = it.filter(Char::isDigit).take(3) }, label = { Text(t(S.MAPPER)) }, singleLine = true, modifier = Modifier.width(110.dp))
                OutlinedTextField(prgKb, { prgKb = it.filter(Char::isDigit).take(5) }, label = { Text(t(S.PRG_KB)) }, singleLine = true, modifier = Modifier.width(130.dp))
                OutlinedTextField(chrKb, { chrKb = it.filter(Char::isDigit).take(5) }, label = { Text(t(S.CHR_KB)) }, singleLine = true, modifier = Modifier.width(130.dp))
            }
            Text(t(S.NES_HINT), style = MaterialTheme.typography.bodySmall)
        }

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(enabled = c != null && !busy, onClick = {
                run {
                    val r = withContext(Dispatchers.IO) { c!!.detect(system) }
                    val st = when (r.status) { 0 -> S.CART_FOUND; 1 -> S.CART_NONE; 2 -> S.CART_UNSUPPORTED; else -> S.CART_HW_ERROR }
                    say(t(st) + if (r.status == 0) " — ${t(S.TITLE_LABEL)}: ${r.name.ifEmpty { "?" }}, ${t(S.ROM_LABEL)}: ${r.romSize}, ${t(S.SAVE_LABEL)}: ${r.saveSize}" else "")
                }
            }) { Text(t(S.DETECT)) }

            Button(enabled = c != null && !busy, onClick = {
                run {
                    val res = withContext(Dispatchers.IO) { c!!.dumpRom(system, 0, mapper.toIntOrNull() ?: 0, prgKb.toIntOrNull() ?: 0, chrKb.toIntOrNull() ?: 0) { d, tot -> progress = d.toFloat() / tot } }
                    val f = pickFile(t(S.CHOOSE_FILE), true, "rom_${system.name.lowercase()}${system.ext}")
                    if (f != null) { f.writeBytes(res.data); say("${t(S.SAVED_TO)} $f — ${t(S.RESULT_SIZE)} ${res.data.size}, CRC32 ${res.crcHex}") }
                    else say("CRC32 ${res.crcHex}")
                    val chk = verifyRom(system, res.data)
                    if (chk.status == CheckStatus.OK) say("${t(S.CHECKSUM_OK)} (${chk.name} ${chk.hex(chk.expected)})")
                    else if (chk.status == CheckStatus.MISMATCH) say("${t(S.CHECKSUM_BAD)}: ${chk.hex(chk.expected)} / ${chk.hex(chk.computed)}")
                    if (system == CartSystem.GBA) {
                        val h = gbaSaveHint(res.data)
                        say(if (h != null) "${t(S.GBA_SAVE_IN_ROM)}: ${h.tag}, ${h.label} → ${t(S.GBA_SAVE_TYPE)}: ${h.type}" else t(S.GBA_SAVE_NONE))
                    }
                }
            }) { Text(t(S.DUMP_ROM)) }

            Button(enabled = c != null && !busy, onClick = {
                run {
                    val res = withContext(Dispatchers.IO) { c!!.readSave(system, 0, (if (system == CartSystem.GBA) gbaType else mapper).toIntOrNull() ?: 0) { d, tot -> progress = d.toFloat() / tot } }
                    val f = pickFile(t(S.CHOOSE_FILE), true, "save_${system.name.lowercase()}.sav")
                    if (f != null) { f.writeBytes(res.data); say("${t(S.SAVED_TO)} $f — ${t(S.RESULT_SIZE)} ${res.data.size}, CRC32 ${res.crcHex}") }
                }
            }) { Text(t(S.READ_SAVE)) }

            Button(enabled = c != null && !busy, onClick = {
                run {
                    val f = pickFile(t(S.CHOOSE_FILE), false)
                    if (f != null) {
                        val data = f.readBytes()
                        val crc = withContext(Dispatchers.IO) { c!!.writeSave(system, data, Proto.DEFAULT_BLOCK, mapper.toIntOrNull() ?: 0) { d, tot -> progress = d.toFloat() / tot } }
                        say("${t(S.DONE)}: ${data.size} bytes, CRC32 ${(crc.toLong() and 0xFFFFFFFFL).toString(16).uppercase().padStart(8, '0')}")
                    }
                }
            }) { Text(t(S.WRITE_SAVE)) }

            OutlinedButton(enabled = busy, onClick = { c?.abort() }) { Text(t(S.ABORT)) }
        }

        Text(t(S.PROGRESS))
        LinearProgressIndicator(progress = { progress }, modifier = Modifier.fillMaxWidth())
        Divider()
        log.asReversed().forEach { Text(it, style = MaterialTheme.typography.bodySmall) }
    }
}

@Composable
fun HelpPanel(lang: Lang) {
    fun t(k: S) = I18n.t(lang, k)
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
            Text(t(S.HELP_TITLE), style = MaterialTheme.typography.titleMedium)
            Text(t(S.HELP_USE_TITLE), style = MaterialTheme.typography.titleSmall)
            listOf(S.HELP_USE_1, S.HELP_USE_2, S.HELP_USE_3, S.HELP_USE_4, S.HELP_USE_5, S.HELP_USE_6)
                .forEach { Text("• " + t(it), style = MaterialTheme.typography.bodySmall) }
            Text(t(S.HELP_FIX_TITLE), style = MaterialTheme.typography.titleSmall)
            listOf(S.HELP_FIX_1, S.HELP_FIX_2, S.HELP_FIX_3, S.HELP_FIX_4, S.HELP_FIX_5, S.HELP_FIX_6, S.HELP_FIX_7, S.HELP_FIX_8)
                .forEach { Text("• " + t(it), style = MaterialTheme.typography.bodySmall) }
        }
    }
}
