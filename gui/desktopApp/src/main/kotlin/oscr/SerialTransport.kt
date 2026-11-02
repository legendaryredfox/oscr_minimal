// SPDX-License-Identifier: GPL-3.0-or-later
package oscr

import com.fazecast.jSerialComm.SerialPort

/** Porta serial real via jSerialComm (Linux, macOS e Windows). */
class SerialTransport(portName: String, baud: Int) : Transport {
    private val port: SerialPort = SerialPort.getCommPort(portName).also {
        it.setBaudRate(baud); it.setNumDataBits(8); it.setNumStopBits(1); it.setParity(SerialPort.NO_PARITY)
        it.setFlowControl(SerialPort.FLOW_CONTROL_DISABLED)
        if (!it.openPort()) throw ProtocolError("não foi possível abrir $portName")
    }

    override fun write(data: ByteArray) { port.writeBytes(data, data.size) }

    override fun read(max: Int, timeoutMs: Long): ByteArray {
        port.setComPortTimeouts(SerialPort.TIMEOUT_READ_SEMI_BLOCKING, timeoutMs.toInt().coerceAtLeast(1), 0)
        val buf = ByteArray(max)
        val n = port.readBytes(buf, max)
        return if (n > 0) buf.copyOf(n) else ByteArray(0)
    }

    override fun close() { port.closePort() }

    companion object {
        fun ports(): List<String> = SerialPort.getCommPorts().map { it.systemPortName }
    }
}
