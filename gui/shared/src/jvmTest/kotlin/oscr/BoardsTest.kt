// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import java.io.File
import java.security.MessageDigest
import kotlin.test.*

/** Perfis das placas e a decisão de gravar o firmware (D162). Espelha host/tests/test_boards.py. */
class BoardsTest {
    private val all = (1..11).toSet()
    private fun info(systems: Set<Int> = all, firmware: String = "0.2.0", board: Boolean = true, volt: Boolean = false): DeviceInfo =
        DeviceInfo(1, firmware, (if (board) 128 else 0) or (if (volt) 32 else 0), systems.sumOf { 1 shl it }, 1024)
    private fun img(systems: Set<Int> = all, fw: Triple<Int, Int, Int> = Triple(0, 2, 0), id: String = "completa") = FirmwareImage(id, File("/x.hex"), fw, systems, "0".repeat(64))
    private fun plan(p: BoardProfile, i: DeviceInfo?, st: BoardState?, imgs: List<FirmwareImage>) = BoardPlanner.plan(p, i, st, imgs)

    @Test fun cadaPlacaResolveNaVersaoAtualEEmUmaVersaoDada() {
        for (n in BoardPlanner.names()) { val p = BoardPlanner.resolve(n); assertTrue(p.systems.isNotEmpty() && p.slots.isNotEmpty()); assertEquals(BoardPlanner.boards.first { it.board == n }.current, p.version) }
        assertFalse(BoardPlanner.resolve("16_bits@v1.2").voltageSelect)
        assertTrue(BoardPlanner.resolve("16_bits@1.3").voltageSelect)               // o "v" é opcional
        assertEquals(all, BoardPlanner.resolve("completa").systems)
    }

    @Test fun placaOuVersaoDesconhecida() {
        assertEquals("unknown_board", assertFailsWith<BoardException> { BoardPlanner.resolve("zx_spectrum") }.kind)
        assertEquals("unknown_version", assertFailsWith<BoardException> { BoardPlanner.resolve("snes@v9.9") }.kind)
    }

    @Test fun seletorSoNasVersoesComOJumperJ1() {
        assertFalse(BoardPlanner.resolve("snes").voltageSelect); assertFalse(BoardPlanner.resolve("n64").voltageSelect)
        assertFalse(BoardPlanner.resolve("nes@v1.0").voltageSelect); assertTrue(BoardPlanner.resolve("nes@v1.1").voltageSelect)
    }

    @Test fun tudoCertoNaoFazNada() = assertEquals(BoardAction.NONE, plan(BoardPlanner.resolve("snes"), info(), BoardState(true, false), listOf(img())).action)

    @Test fun perfilAindaNaoGuardadoSoGravaOPerfil() {
        val pl = plan(BoardPlanner.resolve("nes@v1.1"), info(volt = false), BoardState(false, false), listOf(img()))
        assertEquals(BoardAction.SET_PROFILE, pl.action); assertEquals(Board.VOLT_SELECT, pl.profileFlags)
    }

    @Test fun seletorDiferenteComBoardSoGravaOPerfil() {
        val pl = plan(BoardPlanner.resolve("nes@v1.0"), info(volt = true), BoardState(true, true), listOf(img()))
        assertEquals(BoardAction.SET_PROFILE, pl.action); assertEquals(0, pl.profileFlags)
    }

    @Test fun sistemaQueFaltaPedeGravarAImagem() {
        val pl = plan(BoardPlanner.resolve("n64"), info(systems = all - 11), BoardState(true, false), listOf(img()))
        assertEquals(BoardAction.FLASH, pl.action); assertNotNull(pl.image)
        assertTrue(pl.reasons.any { it.code == "missing_systems" && "n64" in it.params["systems"]!! })
    }

    @Test fun firmwareSemBoardESeletorErradoPedeGravacao() {
        val pl = plan(BoardPlanner.resolve("nes@v1.1"), info(board = false, volt = false), null, listOf(img()))
        assertEquals(BoardAction.FLASH, pl.action); assertTrue(pl.reasons.any { it.code == "no_board" })
    }

    @Test fun firmwareSemBoardMasQueServeNaoRegrava() = assertEquals(BoardAction.NONE, plan(BoardPlanner.resolve("nes@v1.0"), info(board = false, volt = false), null, listOf(img())).action)

    @Test fun semRespostaDoArduinoGravaAImagem() {
        val pl = plan(BoardPlanner.resolve("snes"), null, null, listOf(img()))
        assertEquals(BoardAction.FLASH, pl.action); assertEquals("no_response", pl.reasons[0].code)
    }

    @Test fun semImagemConhecidaENaoSuportado() {
        assertEquals(BoardAction.UNSUPPORTED, plan(BoardPlanner.resolve("snes"), null, null, emptyList()).action)
        assertEquals(BoardAction.UNSUPPORTED, plan(BoardPlanner.resolve("n64"), info(systems = all - 11), BoardState(true, false), emptyList()).action)
        assertEquals(BoardAction.UNSUPPORTED, plan(BoardPlanner.resolve("n64"), info(systems = all - 11), BoardState(true, false), listOf(img(all - 11))).action)
    }

    @Test fun escolheAMenorImagemQueCobreEAMaisNovaNoEmpate() {
        val pequena = img(setOf(1, 4, 7), id = "pequena"); val grande = img(all, id = "grande"); val nova = img(setOf(1, 4, 7), Triple(0, 3, 0), "nova")
        assertEquals("pequena", BoardPlanner.bestImage(listOf(grande, pequena), setOf(1, 4))!!.id)
        assertEquals("nova", BoardPlanner.bestImage(listOf(pequena, nova), setOf(1))!!.id)
        assertNull(BoardPlanner.bestImage(listOf(pequena), setOf(11)))
    }

    @Test fun manifestoIgnoraHexAusenteEShaErrado() {
        val d = kotlin.io.path.createTempDirectory("img").toFile().also { it.deleteOnExit() }
        val hex = File(d, "a.hex").also { it.writeText(":00000001FF\n") }
        val sha = MessageDigest.getInstance("SHA-256").digest(hex.readBytes()).joinToString("") { "%02x".format(it) }
        File(d, "manifest.tsv").writeText("# id\thex\tfirmware\tsistemas\tsha256\ncompleta\ta.hex\t0.2.0\t1,7\t$sha\nruim\ta.hex\t0.2.0\t1\t${"0".repeat(64)}\nfalta\tnao.hex\t0.2.0\t1\t$sha\n")
        val imgs = BoardPlanner.loadImages(d.path)
        assertEquals(listOf("completa"), imgs.map { it.id }); assertEquals(Triple(0, 2, 0), imgs[0].firmware); assertEquals(setOf(1, 7), imgs[0].systems)
    }

    @Test fun perfisDoKotlinSaoOsMesmosDoJsonDoPython() {
        val json = generateSequence(File(".").absoluteFile.normalize()) { it.parentFile }.map { File(it, "boards/perfis.json") }.first { it.isFile }.readText()
        for (b in BoardPlanner.boards) {
            assertTrue("\"${b.board}\"" in json, b.board)
            for ((v, sel) in b.versions) assertEquals(sel, BoardPlanner.resolve("${b.board}@$v").voltageSelect)
        }
    }
}
