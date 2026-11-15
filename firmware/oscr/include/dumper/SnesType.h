// SPDX-License-Identifier: GPL-3.0-or-later
// Tipo de ROM do SNES forçado pelo PC (F-2, D164). O OSCR deduz o tipo do cabeçalho em `getCartInfo`; cabeçalhos mentem (repros multijogo, Sufami Turbo),
// então o PC pode impor o tipo. Código puro, testado no PC (pc-tests/test_snes_type.cpp); os mesmos códigos estão em host/oscr_host/protocol.py e SnesType.kt.
// No fio o tipo viaja no terceiro campo opcional (`chr_kb`), que o SNES não usa em DETECT, DUMP_ROM, READ_SAVE e WRITE_SAVE.
#pragma once
#include <stdint.h>

namespace OSCR::Dumper::SnesType
{
  enum : uint8_t { kAuto = 0, kLoRom = 1, kHiRom = 2, kSa1 = 3, kExHiRom = 4, kLast = kExHiRom };

  /// `romType` do OSCR (SNES.cpp: LO 0, HI 1, SA 3, EX 4) para o código do protocolo; 0xFF = código inválido (kAuto também: não força).
  inline uint8_t romType(uint16_t code)
  {
    switch (code)
    {
      case kLoRom: return 0;
      case kHiRom: return 1;
      case kSa1: return 3;
      case kExHiRom: return 4;
      default: return 0xFF;
    }
  }

  inline bool valid(uint16_t code) { return code <= kLast; }

  /// Número de bancos como o `getCartInfo` do OSCR calcula (SNES.cpp, "numBanks"): SA-1 e ExHiROM, 2 por Mbit; LoROM e HiROM, pelo tamanho do banco (32 KB e 64 KB).
  inline long numBanks(uint8_t oscrRomType, uint16_t romSizeMbit)
  {
    return (oscrRomType == 4 || oscrRomType == 3)
      ? long(romSizeMbit) * 2
      : (long(romSizeMbit) * 1024L * 1024L / 8L) / (32768L + (long(oscrRomType) * 32768L));
  }
}
