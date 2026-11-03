// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em flash de cartucho repro de Game Boy. Usa direto as funções do OSCR original em GameBoy.cpp (cartOn, writeByte, readByte,
// sendFlashCommand, sendCFICommand, identifyCFI, readByteCompensated) e em Flash.cpp (os ajustes do CFI).
// Por que não chamar `GB::writeFlash` e `GB::writeCFI` inteiras: elas consultam o banco CRDB do cartão SD (que o fork não tem; o ponteiro do banco é nulo),
// lêem o tamanho do cabeçalho do arquivo com seek/rewind e releem o arquivo para verificar. Aqui só o laço de gravação é daqui (o dos bancos, igual ao do OSCR),
// com limite de tempo em toda espera; a conferência do OSCR é feita pelo PC, lendo o cartucho de volta. O chip de 29F não é conferido contra uma lista
// de IDs (no OSCR vinha do CRDB): o usuário escolhe a variante e o firmware só recusa ID 0000 ou FFFF.
#include "syslibinc.h"
#include "config.h"

#if OSCR_DUMPER && HAS_GBX && HAS_FLASH

# include "hardware.h"
# include "api.h"
# include "common.h"
# include "cores/include.h"
# include "cores/GameBoy.h"
# include "cores/Flash.h"
# include "dumper/GbFlash.h"

namespace OSCR::Dumper::GbFlash
{
  namespace GB = OSCR::Cores::GameBoy;
  namespace F = OSCR::Cores::Flash;

  namespace
  {
    struct Variant { uint8_t mbc; bool commandSet; bool erase; bool audio; };

    Variant variantOf(uint8_t chip)
    {
      switch (chip)
      {
      case kDiyMbc3: return {3, false, true, false};
      case kDiyMbc5: return {5, false, true, false};
      case kHdrMbc30: return {3, false, true, true};
      case kCamFirst: return {3, false, true, false};
      case kCamSecond: return {3, false, false, false};
      case kOrangeFm: return {0, true, true, false};
      case kSst39Mbc5: return {5, true, true, true};
      default: return {0, false, false, false};
      }
    }

    /// Lê exatamente `n` bytes do fluxo (o fluxo entrega em pedaços). false = o arquivo acabou antes.
    bool readFull(oscr::StreamSource & in, uint8_t * dst, size_t n)
    {
      size_t got = 0;
      while (got < n)
      {
        size_t k = in.read(dst + got, n - got);
        if (k == 0) return false;
        got += k;
      }
      return true;
    }

    /// Espera DQ7 do endereço igualar o do dado (como o `busyCheck` do OSCR), com limite. `data` = 0x80 serve para o apagamento.
    bool pollDq7(uint32_t addr, uint8_t data, uint32_t tries, uint16_t gapUs)
    {
      for (uint32_t t = 0; t < tries; t++)
      {
        if ((GB::readByte(addr) & 0x80) == (data & 0x80)) return true;
        if (gapUs >= 1000) delay(gapUs / 1000); else if (gapUs) delayMicroseconds(gapUs);
      }
      return false;
    }

    void selectBank0(uint8_t mbc)
    {
      if (mbc > 0)
      {
        GB::writeByte(0x3000, 0);                        // ROM bank hi 0
        GB::writeByte(0x2000, 0);                        // ROM bank low 0
        delay(100);
      }
    }
  }

  uint16_t check(uint8_t chip, uint32_t sizeBytes)
  {
    if (chip < kDiyMbc3 || chip > kCfi) return oscr::E_ARGUMENTO;
    if (sizeBytes < 32768UL || sizeBytes % 16384UL != 0 || sizeBytes > 4UL * 1024UL * 1024UL) return oscr::E_ARGUMENTO;   // bancos de 8 bits: até 256
    if (chip == kOrangeFm && sizeBytes != 32768UL) return oscr::E_ARGUMENTO;                                           // o OSCR limita esse a 32 KB
    return 0;
  }

  uint16_t prepare(uint8_t chip, uint32_t sizeBytes)
  {
    if (chip == kCfi)
    {
      if (!GB::identifyCFI()) return oscr::E_FLASH;       // liga e desliga o cartucho; calcula flashBanks
      if (sizeBytes / 16384UL > F::flashBanks) return oscr::E_ARGUMENTO;

      GB::cartOn();
      GB::writeByte(0x3000, 0);
      GB::writeByte(0x2000, 0);
      delay(100);
      GB::writeByteCompensated(0xAAA, 0xF0);              // reset duplo, como no `writeCFI`
      delay(100);
      GB::writeByte(0x555, 0xF0);
      delay(100);

      GB::sendCFICommand(0x80);                           // apagar o chip
      GB::sendCFICommand(0x10);
      if (!pollDq7(0, 0x80, 1600, 50000)) { GB::cartOff(); return oscr::E_CARTUCHO_IO; }     // até 80 s (o PC espera 90 s pelo primeiro ACK)
      GB::cartOff();
      return 0;
    }

    Variant v = variantOf(chip);
    GB::audioWE = v.audio;
    GB::cartOn();
    selectBank0(v.mbc);

    GB::sendFlashCommand(0xF0, v.commandSet);             // reset
    delay(100);
    GB::sendFlashCommand(0x90, v.commandSet);             // ID
    F::flashid = uint16_t(GB::readByte(0)) << 8;
    F::flashid |= GB::readByte(1);
    if (F::flashid == 0x0000 || F::flashid == 0xFFFF) { GB::sendFlashCommand(0xF0, v.commandSet); GB::cartOff(); return oscr::E_FLASH; }

    GB::sendFlashCommand(0xF0, v.commandSet);
    delay(100);

    if (v.erase)
    {
      GB::sendFlashCommand(0x80, v.commandSet);
      GB::sendFlashCommand(0x10, v.commandSet);
      if (!pollDq7(0, 0x80, 1600, 50000)) { GB::cartOff(); return oscr::E_CARTUCHO_IO; }     // até 80 s
    }
    GB::cartOff();
    return 0;
  }

  uint16_t program(uint8_t chip, uint32_t sizeBytes, oscr::StreamSource & in)
  {
    uint8_t * buf = OSCR::Storage::Shared::buffer;
    uint16_t banks = uint16_t(sizeBytes / 16384UL);

    if (chip == kCfi)
    {
      GB::cartOn();
      GB::writeByte(0x3000, 0);
      GB::writeByte(0x2000, 0);
      delay(100);

      uint16_t currAddr = 0, endAddr = 0x3FFF;
      for (uint16_t bank = 0; bank < banks; bank++)
      {
        GB::writeByte(0x2100, bank);                      // ROM bank
        GB::writeByte(0x4000, 0x0);                       // "0x2A8000 fix"
        if (bank > 0) { currAddr = 0x4000; endAddr = 0x7FFF; }

        while (currAddr <= endAddr)
        {
          if (!readFull(in, buf, 512)) { GB::cartOff(); return oscr::E_CARTUCHO_IO; }
          for (int b = 0; b < 512; b++)
          {
            GB::sendCFICommand(0xA0);
            GB::writeByte(currAddr + b, buf[b]);

            PORTH &= ~((1 << 3) | (1 << 6));              // CS e OE/RD baixos
            uint16_t i = 0;
            while ((PINC & 0x80) != (buf[b] & 0x80))
            {
              if (++i > 500)
              {
                if (currAddr < 0x4000)                    // MBC5 gravado como se fosse MBC3: o OSCR repete a partir do último byte, como MBC5
                {
                  b--; currAddr += 0x4000; endAddr = 0x7FFF;
                  break;
                }
                PORTH |= (1 << 3) | (1 << 6);
                GB::cartOff();
                return oscr::E_CARTUCHO_IO;
              }
            }
            PORTH |= (1 << 3) | (1 << 6);
            AVR_ASM(AVR_INS("nop") AVR_INS("nop") AVR_INS("nop"));
          }
          currAddr += 512;
        }
      }
      GB::writeByteCompensated(0xAAA, 0xF0);
      delay(100);
      GB::cartOff();
      return 0;
    }

    Variant v = variantOf(chip);
    GB::audioWE = v.audio;
    GB::cartOn();
    selectBank0(v.mbc);
    GB::sendFlashCommand(0xF0, v.commandSet);
    delay(100);

    auto writeBlock = [&](uint16_t addr) -> bool
    {
      if (!readFull(in, buf, 512)) return false;
      for (int b = 0; b < 512; b++)
      {
        GB::sendFlashCommand(0xA0, v.commandSet);
        GB::writeByte(addr + b, buf[b], GB::audioWE);
        PORTH &= ~(1 << 6);                               // OE/RD baixo
        bool ok = pollDq7(addr + b, buf[b], 500, 0);
        PORTH |= (1 << 6);
        if (!ok) return false;
      }
      return true;
    };

    if (v.mbc == 3)
    {
      uint16_t currAddr = 0, endAddr = 0x3FFF;
      for (uint16_t bank = 0; bank < banks; bank++)
      {
        GB::writeByte(0x2100, bank);
        if (banks > 128) GB::writeByte(0x4000, 0x0);      // "Map SRAM Bank to prevent getting stuck at 0x2A8000"
        if (bank > 0) { currAddr = 0x4000; endAddr = 0x7FFF; }
        while (currAddr <= endAddr)
        {
          if (!writeBlock(currAddr)) { GB::cartOff(); return oscr::E_CARTUCHO_IO; }
          currAddr += 512;
        }
      }
    }
    else if (v.mbc == 5)
    {
      for (uint16_t bank = 0; bank < banks; bank++)
      {
        GB::writeByte(0x2000, bank);
        GB::writeByte(0x4000, 0x0);                       // 0x2A8000 fix
        for (uint16_t currAddr = 0x4000; currAddr < 0x7FFF; currAddr += 512)
        {
          if (!writeBlock(currAddr)) { GB::cartOff(); return oscr::E_CARTUCHO_IO; }
        }
      }
    }
    else                                                  // sem MBC: 32 KB
    {
      for (uint16_t currAddr = 0; currAddr < 0x7FFF; currAddr += 512)
      {
        if (!writeBlock(currAddr)) { GB::cartOff(); return oscr::E_CARTUCHO_IO; }
      }
    }

    GB::sendFlashCommand(0xF0, v.commandSet);
    delay(100);
    GB::cartOff();
    return 0;
  }
}

#endif /* OSCR_DUMPER && HAS_GBX && HAS_FLASH */
