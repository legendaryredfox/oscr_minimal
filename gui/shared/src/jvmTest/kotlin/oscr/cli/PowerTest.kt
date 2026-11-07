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
        assertTrue(on.on); assertNull(on.railLow)
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

/** Sensor do rail e tentativas do SA-1 (D119; sem chave física, D123). Igual a host/tests/test_power.py. */
class PowerHwTest {
    private fun run(sense: Boolean, vararg argv: String): Triple<Int, String, String> {
        val out = StringBuilder(); val err = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { err.appendLine(it) }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".", simSense = sense)
        return Triple(Cli.run(argv.toList(), io), out.toString().trim(), err.toString())
    }

    @Test fun sensorDoRailAcompanhaO5v() {
        val c = OscrClient(SimDevice(railSensor = true), 500, 5000)
        assertTrue(c.info().powerSwitch)                                            // o sensor implica a chave de 5V em software
        val st = c.power(Power.STATUS)
        assertTrue(st.railSensor); assertFalse(st.on); assertEquals(true, st.railLow)
        assertEquals(12, assertFailsWith<DeviceError> { c.detect(CartSystem.SNES) }.code)    // 5V desligado: recusa
        val on = c.power(Power.ON)
        assertTrue(on.on); assertEquals(false, on.railLow)
        val off = c.power(Power.OFF)
        assertFalse(off.on); assertEquals(true, off.railLow)
    }

    @Test fun detectInformaAsTentativasDoSa1() {
        val c = OscrClient(SimDevice(railSensor = true, detectAttempts = 3), 500, 5000)
        c.power(Power.ON)
        assertEquals(3, c.detect(CartSystem.SNES).attempts)
        assertEquals(1, c.detect(CartSystem.MOCK).attempts)
        assertEquals(1, OscrClient(SimDevice(), 500, 5000).detect(CartSystem.SNES).attempts)   // sem o byte extra: 1
    }

    @Test fun cliSensorDoRail() {
        val (c1, o1, _) = run(true, "--simulate", "--json", "power", "status")
        val j1 = o1.replace(" ", "")
        assertEquals(0, c1); assertTrue("\"rail_low\":true" in j1 && "\"switch\"" !in j1)
        val (c2, o2, _) = run(true, "--simulate", "--json", "detect", "-s", "snes")
        assertEquals(2, c2); assertTrue("\"attempts\":3" in o2.replace(" ", ""))
    }
}
