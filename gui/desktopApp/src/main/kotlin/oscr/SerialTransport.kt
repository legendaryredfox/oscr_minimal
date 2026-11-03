// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import com.fazecast.jSerialComm.SerialPort

/** Uma porta serial para mostrar ao usuário: nome do sistema e descrição amigável (ex.: "Arduino Mega 2560"). */
data class PortInfo(val name: String, val description: String) {
    val label: String get() = if (description.isBlank() || description == name) name else "$name — $description"
}

/** Porta serial real via jSerialComm (Linux, macOS e Windows). */
class SerialTransport(private val portName: String, baud: Int) : Transport {
    private val lock = Any()   // o botão Cancelar escreve de outra thread: dois quadros não podem se intercalar
    private val port: SerialPort = SerialPort.getCommPort(portName).also {
        it.setBaudRate(baud); it.setNumDataBits(8); it.setNumStopBits(1); it.setParity(SerialPort.NO_PARITY)
        it.setFlowControl(SerialPort.FLOW_CONTROL_DISABLED)
        if (!it.openPort()) throw ProtocolError(Fail.OPEN_PORT, portName)
    }

    override val isOpen: Boolean get() = port.isOpen

    override fun write(data: ByteArray) {
        val n = synchronized(lock) { port.writeBytes(data, data.size) }
        if (n < 0) throw ProtocolError(Fail.DISCONNECTED)
        if (n != data.size) throw ProtocolError(Fail.PARTIAL_WRITE, "$n/${data.size}")
    }

    override fun read(max: Int, timeoutMs: Long): ByteArray {
        port.setComPortTimeouts(SerialPort.TIMEOUT_READ_SEMI_BLOCKING, timeoutMs.toInt().coerceAtLeast(1), 0)
        val buf = ByteArray(max)
        val n = port.readBytes(buf, max)
        if (n < 0) throw ProtocolError(Fail.DISCONNECTED)   // jSerialComm devolve -1 quando a porta some (cabo desligado)
        return if (n > 0) buf.copyOf(n) else ByteArray(0)
    }

    override fun close() { port.closePort() }

    companion object {
        fun ports(): List<PortInfo> = SerialPort.getCommPorts().map { PortInfo(it.systemPortName, it.descriptivePortName ?: "") }
    }
}
