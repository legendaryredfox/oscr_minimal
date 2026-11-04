// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em flash de cartucho repro de Mega Drive.
//  - MX29F1610 (C2F1, 2 MB) e S29GL064N (017E): as funções do OSCR original em MegaDrive.cpp (eraseFlash, resetFlash, write29F1610, write29GL),
//    na mesma ordem do menu "Flash Repro".
//  - Os demais chips (família KY / FlashKit, Intel, SST, chips AMD de 32 e 64 Mbit): o núcleo `MdFlashCore.h`, que escolhe o conjunto de
//    comandos (AMD 5555h, AMD 555h ou Intel), apaga por layout e programa palavra a palavra com limite de tempo. Ele usa só as primitivas
//    do OSCR (`MD::writeFlash`, `MD::readFlash`, `MD::dataOut`, `MD::dataIn`) e é testado no PC contra um modelo de chip (pc-tests).
// Diferença: o arquivo do OSCR é o fluxo serial (StreamFile), e o ID e o apagamento rodam ANTES do primeiro ACK (rom_prepare).
// Os laços de espera de `busyCheck` e do `write29GL` ganharam limite de tempo (MegaDrive.h, docs/decisoes.md). A conferência do `verifyFlash`
// (que relê o arquivo) é feita pelo PC.
#include "syslibinc.h"
#include "config.h"

#if OSCR_DUMPER && HAS_MD && HAS_FLASH

# include "hardware.h"
# include "api.h"
# include "common.h"
# include "cores/include.h"
# include "cores/MegaDrive.h"
# include "cores/Flash.h"
# include "dumper/MdFlash.h"
# include "dumper/MdFlashCore.h"

namespace OSCR::Dumper::MdFlash
{
  namespace MD = OSCR::Cores::MegaDrive;
  namespace F = OSCR::Cores::Flash;
  namespace C = OSCR::Dumper::MdFlashCore;

  namespace
  {
    inline void csLow() { PORTH &= ~(1 << 3); }
    inline void csHigh() { PORTH |= (1 << 3); }

    /// Barramento do núcleo: as primitivas do OSCR (`/CE` já está em nível baixo).
    struct OscrBus
    {
      void out() { MD::dataOut(); }
      void in() { MD::dataIn(); }
      void w(uint32_t a, uint16_t d) { MD::writeFlash(a, d); }
      uint16_t r(uint32_t a) { return MD::readFlash(a); }
      uint32_t ms() { return millis(); }
      void wait_ms(uint32_t n) { delay(n); }
    };

    /// Os dados vêm do "arquivo" do OSCR (`sharedFile`), que o chamador ligou ao fluxo: 512 bytes por vez.
    struct OscrSource
    {
      uint8_t const * block(size_t & n)
      {
        n = OSCR::Storage::Shared::readBuffer();
        return OSCR::Storage::Shared::buffer;
      }
    };

    C::Probe probed;            // resultado do `prepare`, usado pelo `program`

    uint16_t map(C::Result r)
    {
      switch (r)
      {
      case C::kOk: return 0;
      case C::kNoChip: return oscr::E_FLASH;
      case C::kTooBig: return oscr::E_ARGUMENTO;
      default: return oscr::E_CARTUCHO_IO;       // apagar ou gravar não terminou dentro do limite de tempo, ou o arquivo acabou
      }
    }

    /// Termina qualquer operação com o chip em modo leitura e o barramento como entrada.
    void finish()
    {
      MD::dataIn();
      csHigh();
    }
  }

  uint16_t check(uint8_t chip, uint32_t sizeBytes)
  {
    if (chip != kAuto) return oscr::E_ARGUMENTO;
    if (sizeBytes == 0 || (sizeBytes & 1) || sizeBytes > 8UL * 1024UL * 1024UL) return oscr::E_ARGUMENTO;
    return 0;
  }

  uint16_t identify(char * text, uint32_t & sizeBytes)
  {
    OscrBus bus;
    MD::cartOn();
    csLow();
    C::probe(bus, probed);
    finish();

    sizeBytes = probed.known ? probed.chip.words * 2UL : (probed.cfi ? probed.cfiWords * 2UL : 0);
    if (!text) return probed.known ? 0 : oscr::E_FLASH;
    static char const hex[] = "0123456789ABCDEF";
    if (probed.known) strlcpy(text, probed.chip.name, 32);
    else if (probed.cfi)                                       // fora da tabela, mas o CFI disse o tamanho: "CFI 32Mbit" (só informação; não grava)
    {
      strlcpy(text, "CFI ", 32);
      size_t k = 4;
      uint32_t mbit = probed.cfiWords >> 16;                   // palavras de 16 bits: 2^16 palavras = 1 Mbit
      char digits[11]; uint8_t nd = 0;
      do { digits[nd++] = char('0' + mbit % 10); mbit /= 10; } while (mbit && nd < 10);
      while (nd) text[k++] = digits[--nd];
      strlcpy(text + k, "Mbit", 32 - k);
    }
    else strlcpy(text, "?", 32);
    size_t n = strlen(text);
    if (n + 6 < 32)
    {
      text[n++] = ' ';
      text[n++] = hex[probed.id[0] >> 4]; text[n++] = hex[probed.id[0] & 15];
      text[n++] = hex[probed.id[1] >> 4]; text[n++] = hex[probed.id[1] & 15];
      text[n] = 0;
    }
    return probed.known ? 0 : oscr::E_FLASH;
  }

  uint16_t prepare(uint32_t sizeBytes)
  {
    OscrBus bus;
    MD::cartOn();
    csLow();

    C::probe(bus, probed);
    if (!probed.known) { finish(); return oscr::E_FLASH; }

    uint32_t chipBytes = probed.chip.words * 2UL;
    if (sizeBytes > chipBytes) { finish(); return oscr::E_ARGUMENTO; }

    uint16_t rc = 0;
    if (probed.chip.impl == C::kNative)
    {
      rc = map(C::prepare(bus, probed, sizeBytes));
    }
    else
    {
      // MX29F1610 e S29GL064N: apagar o chip inteiro com a função do OSCR, agora com limite de tempo.
      F::flashid = uint16_t((uint16_t(probed.chip.mfr) << 8) | probed.chip.dev);
      F::flashSize = chipBytes;
      MD::flashTimedOut = false;
      MD::eraseFlash();
      MD::resetFlash();
      if (MD::flashTimedOut) rc = oscr::E_CARTUCHO_IO;
    }

    finish();
    return rc;
  }

  uint16_t program()
  {
    if (!probed.known) return oscr::E_FLASH;

    OscrBus bus;
    OscrSource src;
    MD::cartOn();
    csLow();

    uint16_t rc = 0;
    if (probed.chip.impl == C::kNative)
    {
      rc = map(C::program(bus, probed, uint32_t(OSCR::Storage::Shared::getSize()), src));
    }
    else
    {
      MD::flashTimedOut = false;
      if (probed.chip.impl == C::kOscrF1610) MD::write29F1610();
      else MD::write29GL();
      if (MD::flashTimedOut) rc = oscr::E_CARTUCHO_IO;

      MD::resetFlash();
      delay(1000);
      MD::resetFlash();
      delay(1000);
    }

    finish();
    return rc;
  }
}

#endif /* OSCR_DUMPER && HAS_MD && HAS_FLASH */
