// SPDX-License-Identifier: GPL-3.0-or-later
// Acessórios do SNES (F-10, D178). Sufami Turbo: `ST::readSlot` do OSCR chamado direto (a costura só confere os cabeçalhos antes, para devolver "sem cartucho" em vez
// de erro de leitura). GPC: `GPC::readRAM` direto; a gravação é daqui porque o `GPC::writeRAM` do OSCR escolhe o arquivo no cartão SD e confere relendo o arquivo com `rewind`
// (o fluxo serial não volta); o laço de gravação abaixo é o dele, na mesma ordem (protege desligada, 8 bancos de 64 KB, protege religada), sem a conferência, que é do PC.
#include "syslibinc.h"
#include "config.h"

#if OSCR_DUMPER && HAS_ST && HAS_GPC && HAS_SATELLAVIEW && HAS_SFM

# include "hardware.h"
# include "api.h"
# include "common.h"
# include "cores/include.h"
# include "cores/SNES.h"
# include "cores/ST.h"
# include "cores/GPC.h"
# include "cores/Satellaview.h"
# include "cores/SFM.h"
# include "ui.h"
# include "dumper/SnesAcc.h"
# include "dumper/Dumper.h"
# include "dumper/SnesAccIo.h"
# include "dumper/oscr_proto.h"

namespace OSCR::Dumper::SnesAcc
{
  uint16_t probeSufami(bool slotB, uint32_t & bytes)
  {
    namespace S = OSCR::Cores::ST;
    S::cartOn();                                        // mesmo preparo do `readSlot`
    OSCR::Cores::SNES::dataIn();
    OSCR::Cores::SNES::controlIn();

    if (!S::getHeader(0)) return oscr::E_SEM_CARTUCHO;  // adaptador ausente (o `checkAdapter` do OSCR faz a mesma pergunta)

    uint16_t start = oscr::snesacc::sufamiStartBank(slotB);
    bytes = oscr::snesacc::sufamiBytes(S::getHeader(start + 16));
    if (!S::getHeader(start)) return oscr::E_SEM_CARTUCHO;   // sem cartucho no slot; deixa `fileName` com o nome do cartucho
    return 0;
  }

  void writeGpc()
  {
    namespace G = OSCR::Cores::GPC;
    G::cartOn();

    for (int i = 0; i < 15; i++) G::writeBank(0x20, 0x6000, 0x00);     // desliga a proteção de gravação do cassete

    for (uint8_t bank = 0xC0; bank < 0xC8; bank++)
    {
      for (uint32_t addr = 0x0000; addr < 0x10000; addr += 512)
      {
        OSCR::Storage::Shared::fill();
        for (uint16_t c = 0; c < 512; c++) G::writeBank(bank, addr + c, OSCR::Storage::Shared::buffer[c]);
      }
    }

    uint8_t keep = G::readBank(0x20, 0x6000);            // religa a proteção
    delay(100);
    G::writeBank(0x20, 0x6000, keep);
    delay(100);

    G::cartOff();
    OSCR::Storage::Shared::close();
  }

  uint16_t probeBsx()
  {
    namespace V = OSCR::Cores::Satellaview;
    V::cartOn();
    bool ok = V::readBank(0, 65503) == 0x8B && V::readBank(0, 65502) == 0x86;     // o `writeFlash` do OSCR: sem 8B86 não há cartucho BS-X
    V::cartOff();
    return ok ? 0 : oscr::E_SEM_CARTUCHO;
  }

  void writeBsxSram()
  {
    namespace V = OSCR::Cores::Satellaview;
    V::cartOn();
    for (uint8_t bank = 0x10; bank < 0x18; bank++)
    {
      for (uint32_t addr = 0x5000; addr < 0x6000; addr += 512)
      {
        OSCR::Storage::Shared::fill();
        for (uint16_t c = 0; c < 512; c++) V::writeBank(bank, addr + c, OSCR::Storage::Shared::buffer[c]);
      }
    }
    delay(100);
    V::cartOff();
    OSCR::Storage::Shared::close();
  }

  void readSfmGame(uint8_t idx)
  {
    namespace F = OSCR::Cores::SFM;
    OSCR::Cores::romType = 1;                              // como o menu do OSCR: HiROM para destravar
    if (!F::unlockHirom(false)) return;                    // sem o cassete o OSCR dá erro "suave" e volta: o chamador vê zero bytes
    delay(300);

    OSCR::UI::MenuOptions<7, 20> games;
    bool hasMenu = F::getGames(games);
    if (idx >= games.count) { OSCR::Dumper::noteError(); OSCR::Power::disableCartridge(); return; }

    if (hasMenu)
    {
      uint8_t tries = 0;
      do
      {
        F::send(uint8_t(idx + 0x80));
        delay(200);
        if (++tries > 5) OSCR::UI::fatalError(FS(OSCR::Strings::Errors::TimedOut));      // mesmo limite do `gameMenu` do OSCR
      }
      while (F::readBank(0, 0x2400) != 0x7D);
    }
    else
    {
      F::send(0x80);                                       // cassete com um jogo só, sem menu
      delay(200);
    }

    F::checkcart();                                        // preenche romType, numBanks e checksum para o `readROM`
    F::readROM();
    OSCR::Power::disableCartridge();
  }

  void readSfmMap()
  {
    namespace F = OSCR::Cores::SFM;
    OSCR::Cores::romType = 1;
    if (!F::unlockHirom(false)) return;
    if (!F::checkFlashIds()) { OSCR::Power::disableCartridge(); return; }
    F::resetFlash();
    delay(100);
    F::readMapping();
    F::resetFlash();
    OSCR::Power::disableCartridge();
  }
}

#endif /* OSCR_DUMPER && HAS_ST && HAS_GPC && HAS_SATELLAVIEW && HAS_SFM */
