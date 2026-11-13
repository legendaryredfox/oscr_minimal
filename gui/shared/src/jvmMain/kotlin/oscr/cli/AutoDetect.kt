// SPDX-License-Identifier: GPL-3.0-or-later
package oscr.cli

import oscr.*

/**
 * Descobrir o sistema do cartucho no slot (P5, D160). Igual a host/oscr_host/autodetect.py: só leituras (o `DETECT` de cada sistema), N64, GBA, GB, Mega Drive, SNES e
 * Master System, e o NES por último (o `DETECT` dele aceita qualquer dado que não seja um valor só). Para no primeiro que responde "detectado". Só vale em detect, dump
 * e save-read; gravar exige o sistema explícito.
 */
val AUTO_ORDER = listOf(CartSystem.N64, CartSystem.GBA, CartSystem.GB, CartSystem.MD, CartSystem.SNES, CartSystem.SMS, CartSystem.NES)

/** O primeiro sistema detectado, ou null. `supported` = ids que o firmware informa (null = todos). */
fun autoDetect(client: OscrClient, supported: Set<Int>? = null): CartSystem? {
    for (s in AUTO_ORDER) {
        if (!supported.isNullOrEmpty() && s.id !in supported) continue      // lista vazia = o firmware não informa (simulador): tenta todos
        val r = try { client.detect(s) } catch (e: Exception) { if (e is DeviceError || e is ProtocolError || e is TimeoutError) continue else throw e }
        if (r.status == 0) return s
    }
    return null
}

/** Resolve `-s auto` com a conexão já aberta: devolve os argumentos com o sistema achado; sem cartucho fecha a porta e sai com "nenhum cartucho". */
internal fun resolveAuto(io: CliIo, c: Conn, a: Args): Args {
    val s = autoDetect(c.client, c.info.supportedIds()) ?: run { c.transport.close(); throw CliError("no_cartridge", Msg.t("auto.none"), EXIT_NO_CART) }
    if (!a.json) io.err(Msg.t("auto.found", "system" to s.name.lowercase()))
    return a.withOpt("system", s.name.lowercase())
}

fun DeviceInfo.supportedIds(): Set<Int> = (0..15).filter { systemsMask and (1 shl it) != 0 }.toSet()
