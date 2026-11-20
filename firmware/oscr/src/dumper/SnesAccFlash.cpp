// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação do Memory Pack do BS-X e da flash e do mapeamento do SF Memory Cassette (D190, F-11 parte 2), pelo WRITE_ROM do SNES.
// As sequências são as do OSCR, na mesma ordem: `Satellaview::writeFlash` (destrava a proteção, apaga o chip, confere em branco, grava byte a byte com `writeCheck`)
// e `SFM::write`, `SFM::eraseMapping` e `SFM::writeMapping` (destrava o HiROM, confere o ID C2F3, apaga, confere, grava páginas de 128 bytes).
// Divergências, todas para o fluxo serial no lugar do cartão SD: o `busyWait`, o `busyCheck` e os laços de espera do OSCR não têm limite de tempo e aqui têm;
// os dados vêm do fluxo (o OSCR relia o arquivo); a conferência final é do PC (lê de volta); o apagamento e a gravação são dois passos (`prepare` e `program`)
// e a energia do cartucho cai entre eles, então `program` refaz o destrave. A flash do SFM é apagada sempre (o OSCR só apagava se não estivesse em branco)
// e os dois chips apagam ao mesmo tempo (o OSCR apagava um por vez), dentro de um limite só.
#include "syslibinc.h"
#include "config.h"

#if OSCR_DUMPER && HAS_ST && HAS_GPC && HAS_SATELLAVIEW && HAS_SFM

# include "hardware.h"
# include "api.h"
# include "common.h"
# include "cores/include.h"
# include "cores/SNES.h"
# include "cores/Satellaview.h"
# include "cores/SFM.h"
# include "dumper/SnesAcc.h"
# include "dumper/SnesAccIo.h"
# include "dumper/oscr_proto.h"

namespace OSCR::Dumper::SnesAcc
{
  namespace V = OSCR::Cores::Satellaview;
  namespace F = OSCR::Cores::SFM;

  namespace
  {
    constexpr uint32_t kBsxEraseMs = 30000UL;          // apagar o chip de 8 Mbit do Memory Pack (típico de 1 a 3 s)
    constexpr uint32_t kBsxByteMs = 20UL;              // programar um byte (típico 10 us)
    constexpr uint32_t kSfmEraseMs = 120000UL;         // as duas MX29F1601 apagam juntas; limite para as duas
    constexpr uint32_t kSfmPageMs = 100UL;             // página de 128 bytes (típico 1 ms)
    constexpr uint32_t kSfmMapMs = 10000UL;            // apagar ou gravar uma página do mapeamento
    constexpr uint8_t kSfmChip1 = 0xC0, kSfmChip2 = 0xE0;     // primeiro banco de cada chip
    constexpr uint8_t kSfmMapChip1 = 0xD0, kSfmMapChip2 = 0xE0;   // bancos que o OSCR passa a `eraseMapping` e `writeMapping`
    constexpr uint8_t kSfmBanksPerChip = 32;           // 2 MiB por chip, bancos de 64 KB
    constexpr uint16_t kSfmPage = 128;

    /// Lê exatamente `n` bytes do fluxo (ele entrega em pedaços). false = o arquivo acabou antes.
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

    // ---------------------------------------------------------------- BS-X

    /// O `busyWait` do OSCR com limite de tempo: espera o bit `flag` do registrador de status em `address` do banco $C0.
    bool bsxWait(uint16_t address, uint8_t flag, uint32_t ms)
    {
      uint32_t t0 = millis();
      do
      {
        if (V::readBank(0xC0, address) & flag) return true;

        // CE ou OE precisa alternar a cada leitura do status, senão o fim da operação não aparece (o `busyWait` do OSCR).
        OSCR::Cores::SNES::controlOut();
        PORTH |= (1 << 3);
        __asm__("nop\n\tnop\n\tnop\n\tnop\n\tnop\n\tnop\n\t");
        OSCR::Cores::SNES::controlIn();
        __asm__("nop\n\tnop\n\tnop\n\tnop\n\tnop\n\tnop\n\t");
      }
      while (uint32_t(millis() - t0) <= ms);
      return false;
    }

    /// Desliga a proteção contra gravação do Memory Pack de 8 Mbit (início do `writeFlash` do OSCR).
    void bsxUnlock()
    {
      V::writeBank(0x0C, 0x5000, 0x80);                // modifica o registrador de gravação
      V::writeBank(0x0E, 0x5000, 0x80);                // confirma
    }

    uint16_t prepareBsx()
    {
      V::cartOn();
      if (V::readBank(0, 65503) != 0x8B || V::readBank(0, 65502) != 0x86) { V::cartOff(); return oscr::E_SEM_CARTUCHO; }   // o OSCR: sem 8B86 não é um BS-X
      bsxUnlock();

      // `eraseAll` do OSCR
      V::writeBank(0xC0, 0x0000, 0x50);                // limpa os registradores de status
      V::writeBank(0xC0, 0x0000, 0x71);                // modo status
      uint16_t rc = 0;
      if (!bsxWait(0x0004, 0x08, 1000)) rc = oscr::E_FLASH;                  // tensão de programação presente
      else
      {
        V::writeBank(0xC0, 0x0000, 0xA7);              // apagar o chip
        V::writeBank(0xC0, 0x0000, 0xD0);              // confirma
        V::writeBank(0xC0, 0x0000, 0x71);              // modo status
        if (!bsxWait(0x0004, 0x80, kBsxEraseMs)) rc = oscr::E_CARTUCHO_IO;
      }
      V::writeBank(0xC0, 0x0000, 0xFF);                // termina (volta ao modo leitura)
      if (rc) { V::cartOff(); return rc; }

      for (int bank = 0xC0; bank < 0xD0; bank++)       // conferir em branco
      {
        for (long b = 0; b < 0x10000; b++)
        {
          if (V::readBank(bank, b) != 0xFF) { V::cartOff(); return oscr::E_FLASH; }
        }
      }
      V::cartOff();
      return 0;
    }

    uint16_t programBsx(oscr::StreamSource & in)
    {
      V::cartOn();
      if (V::readBank(0, 65503) != 0x8B || V::readBank(0, 65502) != 0x86) { V::cartOff(); return oscr::E_SEM_CARTUCHO; }
      bsxUnlock();

      uint8_t * buf = OSCR::Storage::Shared::buffer;
      for (int bank = 0xC0; bank < 0xD0; bank++)
      {
        for (long off = 0; off < 0x10000; off += 512)
        {
          if (!readFull(in, buf, 512)) { V::cartOff(); return oscr::E_CARTUCHO_IO; }
          for (uint16_t i = 0; i < 512; i++)
          {
            V::writeBank(0xC0, 0x0000, 0x10);          // programar byte
            V::writeBank(bank, off + i, buf[i]);
            V::writeBank(0xC0, 0x0000, 0x70);          // `writeCheck`: modo status e espera
            if (!bsxWait(0x0000, 0x80, kBsxByteMs)) { V::writeBank(0xC0, 0x0000, 0xFF); V::cartOff(); return oscr::E_CARTUCHO_IO; }
          }
        }
      }
      V::writeBank(0xC0, 0x0000, 0xFF);                // termina a gravação
      V::cartOff();
      return 0;
    }

    // ---------------------------------------------------------------- SFM

    /// O `busyCheck` do OSCR com limite: lê o registrador e espera o bit 7 (D7) de PINC subir, alternando RD a cada leitura.
    bool sfmWait(uint8_t startBank, uint32_t ms)
    {
      F::readBank(startBank, 0x0000);
      uint32_t t0 = millis();
      while (!(PINC & (1 << 7)))
      {
        PORTH |= (1 << 6);
        __asm__("nop\n\t");
        PORTH &= ~(1 << 6);
        __asm__("nop\n\t");
        if (uint32_t(millis() - t0) > ms) return false;
      }
      return true;
    }

    /// Prepara as variáveis do OSCR que as funções dele leem (HiROM e 32 bancos por chip) e destrava o cassete. false = sem cassete (o OSCR já desligou o cartucho).
    bool sfmUnlock()
    {
      OSCR::Cores::romType = 1;
      OSCR::Cores::numBanks = kSfmBanksPerChip;
      return F::unlockHirom(true);
    }

    uint16_t prepareSfmFlash()
    {
      if (!sfmUnlock()) return oscr::E_SEM_CARTUCHO;
      if (!F::checkFlashId(kSfmChip1) || !F::checkFlashId(kSfmChip2)) return oscr::E_FLASH;      // C2F3; o OSCR já desligou o cartucho
      F::resetFlash(kSfmChip1);
      F::resetFlash(kSfmChip2);
      delay(1000);

      static const uint8_t chips[2] = {kSfmChip1, kSfmChip2};
      for (uint8_t i = 0; i < 2; i++)                  // `eraseFlash`: apagar o chip inteiro (os dois começam juntos)
      {
        F::writeBankSequence(0x80, chips[i]);
        F::writeBankSequence(0x10, chips[i]);
      }
      uint32_t t0 = millis();
      for (uint8_t i = 0; i < 2; i++)
      {
        uint32_t spent = millis() - t0;
        if (spent > kSfmEraseMs || !sfmWait(chips[i], kSfmEraseMs - spent)) { F::resetFlash(); OSCR::Cores::SNES::cartOff(); return oscr::E_CARTUCHO_IO; }
      }

      uint16_t rc = 0;
      for (uint8_t i = 0; i < 2 && !rc; i++)
      {
        F::resetFlash(chips[i]);
        if (!F::blankcheck(chips[i])) rc = oscr::E_FLASH;
      }
      F::resetFlash();
      OSCR::Cores::SNES::cartOff();
      return rc;
    }

    uint16_t programSfmFlash(oscr::StreamSource & in)
    {
      if (!sfmUnlock()) return oscr::E_SEM_CARTUCHO;
      if (!F::checkFlashId(kSfmChip1) || !F::checkFlashId(kSfmChip2)) return oscr::E_FLASH;

      uint8_t * buf = OSCR::Storage::Shared::buffer;
      static const uint8_t chips[2] = {kSfmChip1, kSfmChip2};
      for (uint8_t i = 0; i < 2; i++)                  // `write(startBank, pos)`: o primeiro chip leva os 2 MiB iniciais, o segundo os finais
      {
        uint8_t start = chips[i];
        F::resetFlash(start);
        for (uint16_t bank = start; bank < uint16_t(start + kSfmBanksPerChip); bank++)       // `writeFlashData`
        {
          for (uint32_t addr = 0; addr < 0x10000; addr += kSfmPage)
          {
            if (!readFull(in, buf, kSfmPage)) { F::resetFlash(); OSCR::Cores::SNES::cartOff(); return oscr::E_CARTUCHO_IO; }
            F::writeBankSequence(0xA0, start);
            for (uint8_t c = 0; c < kSfmPage; c++) F::writeBank(bank, addr + c, buf[c]);
            F::writeBank(bank, addr + kSfmPage - 1, buf[kSfmPage - 1]);            // o último byte de novo, senão a página não grava
            if (!sfmWait(start, kSfmPageMs)) { F::resetFlash(); OSCR::Cores::SNES::cartOff(); return oscr::E_CARTUCHO_IO; }
          }
        }
        F::resetFlash(start);
      }
      OSCR::Cores::SNES::cartOff();
      return 0;
    }

    uint16_t prepareSfmMap()
    {
      if (!sfmUnlock()) return oscr::E_SEM_CARTUCHO;
      static const uint8_t banks[2] = {kSfmMapChip1, kSfmMapChip2};
      for (uint8_t i = 0; i < 2; i++)                  // `eraseMapping(0xD0)` e `eraseMapping(0xE0)`
      {
        if (!F::checkFlashId(banks[i])) return oscr::E_FLASH;
        F::resetFlash(banks[i]);
        F::writeBankSequence(0x77, banks[i]);          // prepara apagar e gravar o buffer de página
        F::writeBankSequence(0xE0, banks[i]);          // apaga o buffer de página
        if (!sfmWait(banks[i], kSfmMapMs)) { F::resetFlash(); OSCR::Cores::SNES::cartOff(); return oscr::E_CARTUCHO_IO; }
      }
      uint16_t rc = F::blankcheckMapping() ? 0 : oscr::E_FLASH;       // já faz `resetFlash`
      OSCR::Cores::SNES::cartOff();
      return rc;
    }

    uint16_t programSfmMap(oscr::StreamSource & in)
    {
      if (!sfmUnlock()) return oscr::E_SEM_CARTUCHO;
      uint8_t * buf = OSCR::Storage::Shared::buffer;
      static const uint8_t banks[2] = {kSfmMapChip1, kSfmMapChip2};
      for (uint8_t i = 0; i < 2; i++)                  // `writeMapping(0xD0, 0)` e `writeMapping(0xE0, 256)`: 256 bytes por chip
      {
        if (!F::checkFlashId(banks[i])) return oscr::E_FLASH;
        F::resetFlash(banks[i]);
        for (uint32_t addr = 0xFF00; addr < 0xFFFF; addr += kSfmPage)
        {
          if (!readFull(in, buf, kSfmPage)) { F::resetFlash(); OSCR::Cores::SNES::cartOff(); return oscr::E_CARTUCHO_IO; }
          F::writeBankSequence(0x77, banks[i]);
          F::writeBankSequence(0x99, banks[i]);        // escrever o buffer de página
          for (uint8_t c = 0; c < kSfmPage; c++) F::writeBank(banks[i], addr + c, buf[c]);
          F::writeBank(banks[i], addr + kSfmPage - 1, buf[kSfmPage - 1]);
          if (!sfmWait(banks[i], kSfmMapMs)) { F::resetFlash(); OSCR::Cores::SNES::cartOff(); return oscr::E_CARTUCHO_IO; }
        }
      }
      F::resetFlash();
      OSCR::Cores::SNES::cartOff();
      return 0;
    }
  }

  uint16_t prepareWrite(uint16_t chip)
  {
    switch (chip)
    {
    case oscr::snesacc::kWriteBsxPack: return prepareBsx();
    case oscr::snesacc::kWriteSfmFlash: return prepareSfmFlash();
    case oscr::snesacc::kWriteSfmMap: return prepareSfmMap();
    }
    return oscr::E_ARGUMENTO;
  }

  uint16_t programWrite(uint16_t chip, oscr::StreamSource & in)
  {
    switch (chip)
    {
    case oscr::snesacc::kWriteBsxPack: return programBsx(in);
    case oscr::snesacc::kWriteSfmFlash: return programSfmFlash(in);
    case oscr::snesacc::kWriteSfmMap: return programSfmMap(in);
    }
    return oscr::E_ARGUMENTO;
  }
}

#endif /* OSCR_DUMPER && HAS_ST && HAS_GPC && HAS_SATELLAVIEW && HAS_SFM */
