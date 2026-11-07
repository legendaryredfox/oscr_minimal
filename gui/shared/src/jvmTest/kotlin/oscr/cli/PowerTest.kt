package oscr.cli

import oscr.*
import kotlin.test.*

/** POWER: chave de 5V dos slots (D115). Igual a host/tests/test_power.py. */
class PowerTest {
    private fun run(vararg argv: String, simPower: Boolean = true): Triple<Int, String, String> {
        val out = StringBuilder(); val err = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { err.appendLine(it) }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".", simPower = simPower)
        return Triple(Cli.run(argv.toList(), io), out.toString().trim(), err.toString())
    }

    @Test fun placaComChaveComecaDesligadaERecusaCartucho() {
        val dev = SimDevice(powerSwitch = true); val c = OscrClient(dev, 500, 5000)
        assertTrue(c.info().powerSwitch)
        assertFalse(c.power(Power.STATUS).on)
        assertEquals(12, assertFailsWith<DeviceError> { c.detect(CartSystem.SNES) }.code)
        assertEquals("MOCK", c.detect(CartSystem.MOCK).name)                         // o MOCK não precisa de cartucho
        val on = c.power(Power.ON)
        assertTrue(on.on); assertNull(on.switch); assertNull(on.railLow)
        assertEquals(1, c.detect(CartSystem.SNES).status)                            // ligado: o simulador diz "nenhum cartucho"
        assertFalse(c.power(Power.OFF).on); assertEquals(listOf(1, 0), dev.powerCalls)
    }

    @Test fun placaSemChaveNaoMudaNada() {
        val dev = SimDevice(); val c = OscrClient(dev, 500, 5000)
        assertFalse(c.info().powerSwitch)
        assertTrue(c.power(Power.STATUS).on); assertTrue(c.power(Power.ON).on)
        assertEquals(1, assertFailsWith<DeviceError> { c.power(Power.OFF) }.code)
        assertEquals(4, assertFailsWith<DeviceError> { c.power(7) }.code)
        assertTrue(dev.powerCalls.isEmpty())
    }

    @Test fun cliPowerStatusOnOffEJson() {
        val (c1, o1, _) = run("--simulate", "--json", "power", "status")
        assertEquals(0, c1); assertTrue("\"state\":\"off\"" in o1.replace(" ", "") && "\"power_switch\":true" in o1.replace(" ", ""))
        assertTrue("\"state\":\"on\"" in run("--simulate", "--json", "power", "on").second.replace(" ", ""))
        assertTrue("\"state\":\"off\"" in run("--simulate", "--json", "power", "off").second.replace(" ", ""))
        assertEquals(64, run("--simulate", "power").first)                            // falta a ação
    }

    @Test fun cliLigaSozinhaOuRespeitaKeep() {
        val (code, out, _) = run("--simulate", "--json", "detect", "-s", "snes")
        assertEquals(2, code); assertTrue("\"status\":1" in out.replace(" ", ""))
        val (c2, o2, _) = run("--simulate", "--json", "--power", "keep", "detect", "-s", "snes")
        assertEquals(1, c2); assertTrue("device_error" in o2 && "\"device_code\":12" in o2.replace(" ", ""))
        assertEquals(64, run("--simulate", "--power", "talvez", "detect").first)
        assertEquals(0, run("--simulate", "--json", "info").first)                    // info nunca liga o 5V
    }

    @Test fun cliSemChave() {
        val (code, out, _) = run("--simulate", "--json", "power", "status", simPower = false)
        assertEquals(0, code); assertTrue("\"state\":\"on\"" in out.replace(" ", "") && "\"power_switch\":false" in out.replace(" ", ""))
        assertEquals(1, run("--simulate", "--json", "power", "off", simPower = false).first)
    }
}
