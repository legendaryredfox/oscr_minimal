// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em flash de cartucho repro de Mega Drive. Usa direto as funções do OSCR original em MegaDrive.cpp
// (idFlash, eraseFlash, resetFlash, write29F1610, write29GL), na mesma ordem do menu "Flash Repro".
// Diferença: o arquivo do OSCR é o fluxo serial (StreamFile), e o ID e o apagamento rodam ANTES do primeiro ACK (rom_prepare).
// Limite conhecido: os laços de espera do OSCR (busyCheck e o status do write29GL) não têm limite de tempo; um chip com defeito
// trava o firmware até o PC desistir (o host tem limite de tempo). A conferência do `verifyFlash` (que relê o arquivo) é feita pelo PC.
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

namespace OSCR::Dumper::MdFlash
{
  namespace MD = OSCR::Cores::MegaDrive;
  namespace F = OSCR::Cores::Flash;

  namespace
  {
    constexpr uint16_t kIdMx29f1610 = 0xC2F1;      // 2 MB
    constexpr uint16_t kIdS29gl064n = 0x017E;      // 4 MB

    inline void csLow() { PORTH &= ~(1 << 3); }
    inline void csHigh() { PORTH |= (1 << 3); }
  }

  uint16_t check(uint8_t chip, uint32_t sizeBytes)
  {
    if (chip != kAuto) return oscr::E_ARGUMENTO;
    if (sizeBytes == 0 || (sizeBytes & 1) || sizeBytes > 4UL * 1024UL * 1024UL) return oscr::E_ARGUMENTO;
    return 0;
  }

  uint16_t prepare(uint32_t sizeBytes)
  {
    MD::cartOn();
    csLow();

    MD::resetFlash();
    MD::idFlash();
    MD::resetFlash();

    if (F::flashid == kIdMx29f1610) F::flashSize = 2097152UL;
    else if (F::flashid == kIdS29gl064n) F::flashSize = 4194304UL;
    else { csHigh(); return oscr::E_FLASH; }

    if (sizeBytes > F::flashSize) { csHigh(); return oscr::E_ARGUMENTO; }

    MD::eraseFlash();
    MD::resetFlash();

    csHigh();
    return 0;
  }

  uint16_t program()
  {
    MD::cartOn();
    csLow();

    if (F::flashid == kIdMx29f1610) MD::write29F1610();
    else if (F::flashid == kIdS29gl064n) MD::write29GL();
    else { csHigh(); return oscr::E_FLASH; }

    MD::resetFlash();
    delay(1000);
    MD::resetFlash();
    delay(1000);

    csHigh();
    return 0;
  }
}

#endif /* OSCR_DUMPER && HAS_MD && HAS_FLASH */
