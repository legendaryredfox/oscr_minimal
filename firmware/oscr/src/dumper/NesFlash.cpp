// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em flash do NES. Usa direto as funções do OSCR original em NES.cpp (NESmaker_*, A29040B_*), que exigem HAS_FLASH (user.ini: flash = true).
// Diferença deliberada: o laço de gravação é daqui, porque o OSCR espera para sempre (do { } while) por um byte que talvez nunca confira
// e lê o arquivo do SD; aqui toda espera tem limite e termina com erro, e os dados vêm do fluxo serial.
#include "syslibinc.h"
#include "config.h"

#if OSCR_DUMPER && HAS_NES && HAS_FLASH

# include "hardware.h"
# include "api.h"
# include "common.h"
# include "cores/include.h"
# include "cores/NES.h"
# include "dumper/NesFlash.h"

namespace OSCR::Cores::NES { extern bool flashfound; }     // definida em NES.cpp, sem declaração no cabeçalho

namespace OSCR::Dumper::NesFlash
{
  namespace NE = OSCR::Cores::NES;

  namespace
  {
    inline uint8_t rd(uint16_t a) { return NE::read_prg_byte(a); }
    inline void wr(uint16_t a, uint8_t d) { NE::write_prg_byte(a, d); }

    inline uint8_t rdChr(uint16_t a) { return NE::read_chr_byte(a); }

    /// Lê (PRG) até `tries` vezes, com `gapUs` entre as leituras, esperando `value`.
    bool waitPrg(uint16_t addr, uint8_t value, uint16_t tries, uint16_t gapUs)
    {
      for (uint16_t t = 0; t < tries; t++)
      {
        if (rd(addr) == value) return true;
        if (gapUs >= 1000) delay(gapUs / 1000); else delayMicroseconds(gapUs);
      }
      return false;
    }

    bool waitChr(uint16_t addr, uint8_t value, uint16_t tries, uint16_t gapUs)
    {
      for (uint16_t t = 0; t < tries; t++)
      {
        if (rdChr(addr) == value) return true;
        if (gapUs >= 1000) delay(gapUs / 1000); else delayMicroseconds(gapUs);
      }
      return false;
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

    // ---------------------------------------------------------------- NES Maker (SST 39SF040)
    bool nmId()
    {
      NE::flashfound = false;
      NE::NESmaker_ID();                             // SST 39SF040 (ID 0xBFB7); liga flashfound
      return NE::flashfound;
    }

    uint16_t nmProgram(uint16_t prgKb, oscr::StreamSource & in)
    {
      uint8_t * buf = OSCR::Storage::Shared::buffer;
      uint16_t banks = prgKb / 16;

      for (uint16_t bank = 0; bank < banks; bank++)
      {
        for (uint16_t sector = 0; sector < 0x4000; sector += 0x1000)
        {
          NE::NESmaker_SectorErase(uint8_t(bank), 0x8000 + sector);
          delay(18);                                                        // típico 18 ms
          if (!waitPrg(0x8000 + sector, 0xFF, 100, 18000) || !waitPrg(0x8000 + sector, 0xFF, 5, 18000)) return oscr::E_CARTUCHO_IO;   // apagou? duas vezes

          for (uint16_t off = 0; off < 0x1000; off += 512)
          {
            if (!readFull(in, buf, 512)) return oscr::E_CARTUCHO_IO;
            for (uint16_t x = 0; x < 512; x++)
            {
              uint16_t loc = uint16_t(0x8000 + sector + off + x);
              NE::NESmaker_ByteProgram(uint8_t(bank), loc, buf[x]);
              delayMicroseconds(14);                                        // típico 14 us
              if (!waitPrg(loc, buf[x], 200, 14) || !waitPrg(loc, buf[x], 5, 14)) return oscr::E_CARTUCHO_IO;   // gravou? duas vezes
            }
          }
        }
      }
      return 0;
    }

    // ---------------------------------------------------------------- A29040B
    bool aId()
    {
      NE::flashfound = false;
      NE::A29040B_ID();                              // ID 0x3786; liga flashfound e já faz o reset do chip
      return NE::flashfound;
    }

    uint16_t aProgram(uint16_t prgKb, uint16_t chrKb, oscr::StreamSource & in)
    {
      uint8_t * buf = OSCR::Storage::Shared::buffer;

      NE::A29040B_PRG_ResetFlash();
      uint32_t addr = 0x8000, left = uint32_t(prgKb) * 1024UL;
      while (left)
      {
        uint16_t n = left > 512 ? 512 : uint16_t(left);
        if (!readFull(in, buf, n)) return oscr::E_CARTUCHO_IO;
        for (uint16_t i = 0; i < n; i++, addr++)
        {
          NE::A29040B_PRG_Write(uint16_t(addr), buf[i]);
          delayMicroseconds(14);
          if (!waitPrg(uint16_t(addr), buf[i], 50, 14)) return oscr::E_CARTUCHO_IO;
        }
        left -= n;
      }

      if (chrKb)
      {
        NE::A29040B_CHR_ResetFlash();
        uint16_t caddr = 0;
        left = uint32_t(chrKb) * 1024UL;
        while (left)
        {
          uint16_t n = left > 512 ? 512 : uint16_t(left);
          if (!readFull(in, buf, n)) return oscr::E_CARTUCHO_IO;
          for (uint16_t i = 0; i < n; i++, caddr++)
          {
            NE::A29040B_CHR_Write(caddr, buf[i]);
            delayMicroseconds(14);
            if (!waitChr(caddr, buf[i], 50, 14)) return oscr::E_CARTUCHO_IO;
          }
          left -= n;
        }
      }
      return 0;
    }
  }

  uint16_t check(uint8_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes)
  {
    if (prgKb == 0 || prgKb % 16 != 0) return oscr::E_ARGUMENTO;
    if (sizeBytes != (uint32_t(prgKb) + chrKb) * 1024UL) return oscr::E_ARGUMENTO;
    if (chip == kNesMaker) return (prgKb <= 512 && chrKb == 0) ? 0 : oscr::E_ARGUMENTO;
    if (chip == kA29040B) return ((prgKb == 16 || prgKb == 32) && (chrKb == 0 || chrKb == 8)) ? 0 : oscr::E_ARGUMENTO;
    return oscr::E_ARGUMENTO;
  }

  uint16_t prepare(uint8_t chip, uint16_t prgKb, uint16_t chrKb)
  {
    (void)prgKb;
    if (chip == kNesMaker) return nmId() ? 0 : oscr::E_FLASH;

    if (!aId()) return oscr::E_FLASH;
    NE::A29040B_PRG_ResetFlash();
    NE::A29040B_PRG_ChipErase();                                                           // PRG e CHR são chips separados; apaga os dois antes de receber os dados
    if (!waitPrg(0x8000, 0xFF, 200, 50000)) return oscr::E_CARTUCHO_IO;     // mais até 10 s além dos 8 s
    if (chrKb)
    {
      NE::A29040B_CHR_ResetFlash();
      NE::A29040B_CHR_ChipErase();
      if (!waitChr(0x0000, 0xFF, 200, 50000)) return oscr::E_CARTUCHO_IO;
    }
    return 0;
  }

  uint16_t program(uint8_t chip, uint16_t prgKb, uint16_t chrKb, oscr::StreamSource & in)
  {
    return chip == kNesMaker ? nmProgram(prgKb, in) : aProgram(prgKb, chrKb, in);
  }
}

#endif /* OSCR_DUMPER && HAS_NES && HAS_FLASH */
