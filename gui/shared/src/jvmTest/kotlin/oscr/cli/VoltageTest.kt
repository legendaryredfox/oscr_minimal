package oscr.cli

import oscr.*
import kotlin.test.*

/** Seletor de tensão do cartucho (D138): padrão 5 V, 3,3 V opcional, alerta e confirmação ao passar de 3,3 V para 5 V. Igual a host/tests/test_voltage.py. */
class VoltageTest {
    private fun run(vararg argv: String, simVolt: Boolean = true, simCart5v: Boolean = false): Triple<Int, String, String> {
        val out = StringBuilder(); val err = StringBuilder()
        val io = CliIo({ out.appendLine(it) }, { err.appendLine(it) }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".",
            simVolt = simVolt, simCart5v = simCart5v, simPower = true)
        return Triple(Cli.run(argv.toList(), io), out.toString().trim(), err.toString())
    }


    @Test fun simuladorLigaEm5vEVoltaA5vDepoisDeDesligar() {
        val dev = SimDevice(powerSwitch = true, voltSelect = true); val c = OscrClient(dev, 500, 5000)
        assertEquals("5v", c.power(Power.STATUS).voltage)
        val on = c.power(Power.ON)
        assertTrue(on.on); assertTrue(on.voltageSelect); assertEquals("5v", on.voltage)
        assertEquals("3v3", c.power(Power.ON_3V3).voltage)
        assertEquals("5v", c.power(Power.OFF).voltage)                              // desligado, volta ao padrão
    }

    @Test fun padraoLigaA5vSemAlerta() {
        val (code, out, err) = run("--simulate", "--json", "power", "on")
        assertEquals(0, code); assertTrue("\"voltage\":\"5v\"" in out); assertEquals("", err)
        val (code2, out2, err2) = run("--simulate", "--json", "power", "on", "--voltage", "5v")
        assertEquals(0, code2); assertTrue("\"voltage\":\"5v\"" in out2); assertEquals("", err2)    // 5 V com o slot desligado: nada a avisar
    }

    @Test fun voltage3v3Liga3v3() {
        val (code, out, _) = run("--simulate", "--json", "power", "on", "--voltage", "3v3")
        assertEquals(0, code); assertTrue("\"voltage\":\"3v3\"" in out)
    }

    @Test fun voltage3v3SemSeletorRecusa() {
        val (code, out, _) = run("--simulate", "--json", "detect", "-s", "md", "--voltage", "3v3", simVolt = false)
        assertEquals(EXIT_USAGE, code); assertTrue("no_selector" in out)
    }

    @Test fun falhaDeLeituraA3v3NaoSobePara5v() {
        val (code, _, err) = run("--simulate", "--json", "dump", "-s", "md", "--voltage", "3v3", "--allow-5v", "-o", "/tmp/oscr-nao-deve-existir.md", simCart5v = true)
        assertNotEquals(0, code)
        assertFalse("ATENÇÃO" in err || "WARNING" in err || "RISK OF" in err)                          // nem alerta nem subida automática
    }

    @Test fun de3v3Para5vRecusaEmScriptEMantem3v3() {
        val dev = SimDevice(powerSwitch = true, voltSelect = true); val c = Conn(OscrClient(dev, 500, 5000), dev, OscrClient(dev, 500, 5000).info())
        val err = StringBuilder()
        val io = CliIo({ }, { err.appendLine(it) }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        val args3 = Args("x", mapOf("voltage" to "3v3"), emptySet())
        setVoltage(io, args3, c, c.client.power(Power.STATUS))
        assertEquals("3v3", c.client.power(Power.STATUS).voltage)
        val args5 = Args("x", mapOf("voltage" to "5v"), setOf("json"))
        val e = assertFailsWith<CliError> { setVoltage(io, args5, c, c.client.power(Power.STATUS)) }
        assertEquals(EXIT_REFUSED, e.exit); assertEquals("refused", e.kind)
        assertEquals("3v3", c.client.power(Power.STATUS).voltage)
    }

    @Test fun de3v3Para5vComAllow5vMostraOAlertaESobe() {
        val dev = SimDevice(powerSwitch = true, voltSelect = true); val c = Conn(OscrClient(dev, 500, 5000), dev, OscrClient(dev, 500, 5000).info())
        val err = StringBuilder()
        val io = CliIo({ }, { err.appendLine(it) }, false, false, { null }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        setVoltage(io, Args("x", mapOf("voltage" to "3v3"), emptySet()), c, c.client.power(Power.STATUS))
        val r = setVoltage(io, Args("x", mapOf("voltage" to "5v"), setOf("allow-5v")), c, c.client.power(Power.STATUS))
        assertEquals("5v", r.voltage); assertEquals(2, dev.volt)
        assertTrue("#".repeat(78) in err.toString() && ("RISCO DE DANIFICAR" in err.toString() || "RISK OF DAMAGING" in err.toString()))
    }

    @Test fun de3v3Para5vInterativoPedeConfirmacao() {
        val dev = SimDevice(powerSwitch = true, voltSelect = true); val c = Conn(OscrClient(dev, 500, 5000), dev, OscrClient(dev, 500, 5000).info())
        var answer = "nao"
        val io = CliIo({ }, { }, true, false, { answer }, { emptyList() }, { _, _ -> error("sem porta") }, ".")
        setVoltage(io, Args("x", mapOf("voltage" to "3v3"), emptySet()), c, c.client.power(Power.STATUS))
        val a5 = Args("x", mapOf("voltage" to "5v"), emptySet())
        assertFailsWith<CliError> { setVoltage(io, a5, c, c.client.power(Power.STATUS)) }
        assertEquals(1, dev.volt)
        answer = "5V"
        assertEquals("5v", setVoltage(io, a5, c, c.client.power(Power.STATUS)).voltage); assertEquals(2, dev.volt)
    }
}
