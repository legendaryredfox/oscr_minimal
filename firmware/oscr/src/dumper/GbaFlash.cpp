// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em flash de cartucho repro de GBA. Usa direto as funções do OSCR original em GameBoyAdvance.cpp (idFlashrom, eraseIntel4000,
// eraseIntel4400, sectorEraseMX29GL128E, sectorEraseMSP55LV128, erase369in1, writeIntel4000, writeMX29GL128E, writeMSP55LV128, write369in1 e os resets),
// na mesma ordem do `flashRepro`. Diferenças: o "arquivo" é o fluxo serial (StreamFile); ID e apagamento rodam ANTES do primeiro ACK (rom_prepare);
// o `verifyFlashrom` do OSCR (que relê o arquivo) é feito pelo PC lendo o cartucho de volta.
// Limite conhecido: os laços de espera do OSCR não têm limite de tempo; um chip com defeito trava o firmware até o PC desistir.
#include "syslibinc.h"
#include "config.h"

#if OSCR_DUMPER && HAS_GBX && HAS_FLASH

# include "hardware.h"
# include "api.h"
# include "common.h"
# include "cores/include.h"
# include "cores/GameBoyAdvance.h"
# include "cores/Flash.h"
# include "dumper/GbaFlash.h"

namespace OSCR::Dumper::GbaFlash
{
  namespace G = OSCR::Cores::GameBoyAdvance;
  using OSCR::Cores::Flash::flashid;

  namespace
  {
    constexpr uint16_t kIntel4000 = 0x8802, kIntel4400 = 0x8816, kGl128 = 0x227E, k369 = 0x8812;
    constexpr uint32_t kMB = 1UL << 20;

    bool is369() { return flashid == k369; }

    /// Para o ID 0x227E o fabricante (romType) diz qual rotina serve: 0xC2 Macronix, 0x89 Intel PC28F256M29 e 0x20 ST usam a do MX29GL128E; 0x01 e 0x04 a do MSP55LV128.
    bool glMx() { return OSCR::Cores::romType == 0xC2 || OSCR::Cores::romType == 0x89 || OSCR::Cores::romType == 0x20; }
    bool glMsp() { return OSCR::Cores::romType == 0x01 || OSCR::Cores::romType == 0x04; }
  }

  uint16_t check(uint16_t chip, uint32_t sizeBytes)
  {
    if ((chip & 0xFF) != 1 || blockOf(chip) > 63) return oscr::E_ARGUMENTO;
    if (sizeBytes == 0 || sizeBytes % 1024UL != 0) return oscr::E_ARGUMENTO;
    if (sizeBytes > (blockOf(chip) == 0 ? 256UL * kMB : 4UL * kMB * (64 - blockOf(chip)))) return oscr::E_ARGUMENTO;     // 369-in-1: 64 blocos de 4 MB
    return 0;
  }

  uint16_t prepare(uint16_t chip, uint32_t sizeBytes)
  {
    G::cartOn();
    G::idFlashrom();                                   // sem ID conhecido o OSCR faz fatalError (E_CARTUCHO_IO); o ID 0x227E exige o fabricante abaixo

    bool known = flashid == kIntel4000 || flashid == kIntel4400 || flashid == k369 || (flashid == kGl128 && (glMx() || glMsp()));
    if (!known) return oscr::E_FLASH;

    if (blockOf(chip) != 0 && !is369()) return oscr::E_ARGUMENTO;       // bloco só existe no 369-in-1
    if (!is369() && sizeBytes > 32UL * kMB) return oscr::E_ARGUMENTO;
    if (flashid == kGl128 && sizeBytes > 16UL * kMB) return oscr::E_ARGUMENTO;   // `idFlashrom` dá 16 MB a esses chips

    OSCR::Cores::fileSize = sizeBytes;                  // as funções do OSCR percorrem `fileSize`

    if (flashid == kIntel4000)
    {
      G::eraseIntel4000();
      G::resetIntel(0x200000);
    }
    else if (flashid == kIntel4400)
    {
      G::eraseIntel4400();
      G::resetIntel(0x200000);
    }
    else if (is369())
    {
      G::erase369in1(blockOf(chip));
      G::reset369in1();                                 // "Reset or blankcheck will fail"
    }
    else if (glMx())
    {
      G::sectorEraseMX29GL128E();
    }
    else
    {
      G::sectorEraseMSP55LV128();
    }
    return 0;
  }

  uint16_t program(uint16_t chip, uint32_t sizeBytes)
  {
    G::cartOn();
    OSCR::Cores::fileSize = sizeBytes;

    if (flashid == kIntel4000 || flashid == kIntel4400) G::writeIntel4000();
    else if (is369())
    {
      G::write369in1(blockOf(chip));
      G::reset369in1();
    }
    else if (glMx()) G::writeMX29GL128E();
    else G::writeMSP55LV128();

    OSCR::Storage::Shared::close();

    // Resets que o `flashRepro` fazia antes de verificar (a verificação em si é do PC).
    if (flashid == kIntel4000)
    {
      G::resetIntel(0x8000);                            // "Don't know the correct size so just take some guesses"
      delay(1000);
      G::resetIntel(0x100000);
      delay(1000);
      G::resetIntel(0x200000);
    }
    else if (flashid == kIntel4400) G::resetIntel(0x200000);
    else if (flashid == kGl128) G::resetMX29GL128E();
    delay(1000);
    return 0;
  }
}

#endif /* OSCR_DUMPER && HAS_GBX && HAS_FLASH */
