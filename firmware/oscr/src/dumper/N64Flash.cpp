// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em flash de cartucho repro de N64. Usa direto as funções do OSCR original em N64.cpp (idFlashrom, eraseSector, eraseMSP55LV100,
// eraseIntel4400, blankcheckFlashrom, writeFlashBuffer, writeMSP55LV100, writeFlashrom, writeIntel4400 e os resets), na mesma ordem do `flashRepro`.
// Diferenças: o "arquivo" é o fluxo serial (StreamFile); ID, apagamento e blankcheck rodam ANTES do primeiro ACK (rom_prepare); o menu de configuração manual
// do chip desconhecido (com um defeito no OSCR: o tamanho do setor sai da tabela de buffers) não existe, chip desconhecido é recusado; o `verifyFlashrom`
// (que relê o arquivo) é feito pelo PC lendo o cartucho de volta.
// Limite conhecido: os laços de espera do OSCR não têm limite de tempo; um chip com defeito trava o firmware até o PC desistir.
#include "syslibinc.h"
#include "config.h"

#if OSCR_DUMPER && HAS_N64 && HAS_FLASH

# include "hardware.h"
# include "api.h"
# include "common.h"
# include "cores/include.h"
# include "cores/N64.h"
# include "cores/Flash.h"
# include "dumper/N64Core.h"
# include "dumper/N64Flash.h"
# include "dumper/oscr_proto.h"

namespace OSCR::Dumper::N64Flash
{
  namespace N = OSCR::Cores::N64;
  using OSCR::Cores::Flash::flashid;

  namespace
  {
    constexpr uint16_t kGl = 0x227E, kMx64Top = 0x22C9, kMx64Bottom = 0x22CB, kIntel4400A = 0x8813, kIntel4400B = 0x8816, kMsp100 = 0x7E7E;

    bool cartIs(char const * id) { return strcmp_P(OSCR::Cores::cartID, id) == 0; }
    bool isMx64() { return flashid == kMx64Top || flashid == kMx64Bottom; }
    bool isIntel4400() { return flashid == kIntel4400A || flashid == kIntel4400B; }
  }

  uint16_t check(uint16_t chip, uint32_t sizeBytes)
  {
    if (chip != kRepro || !oscr::n64::flashBytesValid(sizeBytes)) return oscr::E_ARGUMENTO;
    return 0;
  }

  uint16_t prepare(uint16_t, uint32_t sizeBytes)
  {
    N::cartOn();
    N::idFlashrom();                                   // cartSize = 0 se o ID não é conhecido (ROM de máscara, chip fora da lista)
    if (OSCR::Cores::cartSize == 0) return oscr::E_FLASH;
    if (!oscr::n64::flashFits(sizeBytes, OSCR::Cores::cartSize)) return oscr::E_ARGUMENTO;

    OSCR::Cores::fileSize = sizeBytes;                  // as funções do OSCR percorrem `fileSize`

    if (flashid == kGl) N::eraseSector(0x20000);        // S29GL256N, MSP55LV512 e os outros 227E: setores de 128 KB
    else if (flashid == kMsp100) N::eraseMSP55LV100();
    else if (isIntel4400()) { N::eraseIntel4400(); N::resetIntel4400(); }
    else if (isMx64()) N::eraseSector(0x8000);          // MX29LV640: 0xC9 boot no topo, 0xCB boot embaixo
    else N::eraseFlashrom();

    return N::blankcheckFlashrom() ? 0 : oscr::E_FLASH;  // "Check if erase was successful": sem blankcheck o OSCR não grava
  }

  uint16_t program(uint16_t, uint32_t sizeBytes)
  {
    N::cartOn();
    OSCR::Cores::fileSize = sizeBytes;

    if (flashid == kGl && cartIs(PSTR("3901"))) N::writeFlashBuffer(0x20000, 128);      // Intel 512M29EW (64 MB), buffer de 128 bytes
    else if (flashid == kGl && cartIs(PSTR("2100"))) N::writeFlashBuffer(0x20000, 64);  // ST M29W128GL (16 MB), buffer de 64 bytes
    else if (flashid == kGl) N::writeFlashBuffer(0x20000, 32);                          // S29GL128N, S29GL256N e MSP55LV512, buffer de 32 bytes
    else if (flashid == kMsp100) N::writeMSP55LV100(0x20000);
    else if (isMx64()) N::writeFlashrom(0x8000);                                        // MX29LV640 sem buffer
    else if (isIntel4400()) { N::writeIntel4400(); N::resetIntel4400(); }
    else return oscr::E_FLASH;

    OSCR::Storage::Shared::close();
    delay(1000);
    return 0;
  }
}

#endif /* OSCR_DUMPER && HAS_N64 && HAS_FLASH */
