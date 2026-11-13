// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.security.MessageDigest

/** MD5 e SHA-1 (maiúsculos) de um dump. Igual a hashlib em host/oscr_host/cli/output.py. */
object Hashes {
    class Result(val md5: String, val sha1: String)

    fun of(data: ByteArray): Result = Result(hex("MD5", data), hex("SHA-1", data))

    private fun hex(alg: String, data: ByteArray) = MessageDigest.getInstance(alg).digest(data).joinToString("") { "%02X".format(it) }
}
