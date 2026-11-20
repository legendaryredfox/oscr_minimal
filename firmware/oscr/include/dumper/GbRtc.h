// SPDX-License-Identifier: GPL-3.0-or-later
// Game Boy: relógio (RTC) do MBC3 (F-17, D192). O OSCR não tem código para o RTC; esta é a sequência do MBC3 (documentada em Pan Docs), escrita nas costuras
// do dumper sobre `readByte`, `writeByte`, `readByteSRAM` e `writeByteSRAM` do núcleo do GB. O arquivo tem 5 bytes, na ordem dos registradores 08h a 0Ch:
// segundos, minutos, horas, dias (byte baixo) e dias (byte alto: bit 0 = bit 8 dos dias, bit 6 = parado, bit 7 = estouro).
#pragma once
#include <stdint.h>

namespace OSCR::Dumper::GbRtc
{
  constexpr uint8_t kRegs = 5;
  constexpr uint8_t kFirstReg = 0x08;             // seleção do registrador em 0x4000-0x5FFF: 08h (segundos) a 0Ch (dias, byte alto)
  constexpr uint8_t kHalt = 0x40, kCarry = 0x80, kDayHigh = 0x01;
  constexpr uint8_t kDhMask = kHalt | kCarry | kDayHigh;

  /// Tipos de cartucho (byte 0x0147) com o RTC: 0Fh = MBC3+TIMER+BATTERY, 10h = MBC3+TIMER+RAM+BATTERY.
  inline bool hasRtc(uint8_t cartType) { return cartType == 0x0F || cartType == 0x10; }

  /// Confere os 5 bytes que o PC manda: segundos e minutos 0 a 59, horas 0 a 23, e só os bits 0, 6 e 7 do byte alto dos dias.
  inline bool valid(const uint8_t * r)
  {
    return r[0] < 60 && r[1] < 60 && r[2] < 24 && (r[4] & ~kDhMask) == 0;
  }
}
