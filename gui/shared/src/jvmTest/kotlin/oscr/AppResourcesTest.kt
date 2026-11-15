// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.io.File
import java.security.MessageDigest
import kotlin.test.*

/** H-7: programa instalado acha as imagens do firmware e o avrdude na pasta de recursos do instalador, sem PlatformIO nem PATH. */
class AppResourcesTest {
    private val saved = System.getProperty(AppResources.PROPERTY)
    @AfterTest fun restore() { if (saved == null) System.clearProperty(AppResources.PROPERTY) else System.setProperty(AppResources.PROPERTY, saved) }

    private fun sha(b: ByteArray) = MessageDigest.getInstance("SHA-256").digest(b).joinToString("") { "%02x".format(it) }

    private fun fakeInstall(withAvrdude: Boolean): File {
        val root = kotlin.io.path.createTempDirectory("oscrres").toFile().also { it.deleteOnExit() }
        val fw = File(root, "firmware").also { it.mkdirs() }
        val small = ":00000001FF\n".toByteArray(); val big = ":10000000AA\n:00000001FF\n".toByteArray()
        File(fw, "a.hex").writeBytes(small); File(fw, "b.hex").writeBytes(big)
        File(fw, "manifest.tsv").writeText("# id\thex\tfirmware\tsistemas\tsha256\n" +
            "pequena\ta.hex\t0.2.0\t1,2\t${sha(small)}\n" + "completa\tb.hex\t0.2.0\t1,2,3,4\t${sha(big)}\n" + "adulterada\ta.hex\t0.2.0\t1,2,3,4,5,6\t${"0".repeat(64)}\n")
        if (withAvrdude) File(root, "avrdude").also { it.mkdirs() }.let { File(it, "avrdude").apply { writeText("#!/bin/sh\n"); setExecutable(true) } }
        return root
    }

    @Test fun semInstaladorNadaMuda() {
        System.clearProperty(AppResources.PROPERTY)
        assertNull(AppResources.dir()); assertNull(AppResources.firmwareDir()); assertNull(AppResources.avrdude()); assertNull(FirmwareFlash.bundledHex())
    }

    @Test fun achaAsImagensEOAvrdudeDoInstalador() {
        val root = fakeInstall(true)
        System.setProperty(AppResources.PROPERTY, root.path)
        assertEquals(File(root, "firmware"), AppResources.firmwareDir())
        assertEquals(File(root, "avrdude/avrdude").path, AppResources.avrdude()?.path)
        assertEquals(File(root, "avrdude/avrdude").path, FirmwareFlash.findAvrdude(null))          // vem antes do PATH e do PlatformIO
        assertEquals(File(root, "firmware"), BoardPlanner.imageDir(null))
        assertEquals(setOf("completa", "pequena"), BoardPlanner.loadImages(null).map { it.id }.toSet())                  // a de SHA errado é ignorada
        assertEquals("b.hex", FirmwareFlash.bundledHex()?.name)                                      // a que cobre mais sistemas; a de SHA errado é ignorada
    }

    @Test fun semAvrdudeEmbutidoCaiNosCaminhosDeSempre() {
        System.setProperty(AppResources.PROPERTY, fakeInstall(false).path)
        assertNull(AppResources.avrdude())
    }

    @Test fun pastaDadaVenceOInstalador() {
        System.setProperty(AppResources.PROPERTY, fakeInstall(true).path)
        val other = kotlin.io.path.createTempDirectory("oscrother").toFile().also { it.deleteOnExit() }
        assertEquals(other, BoardPlanner.imageDir(other.path))
    }
}
