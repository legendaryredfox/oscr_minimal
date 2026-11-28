#pragma once
#if !defined(OSCR_CORE_GAMEBOYSMART_H_)
# define OSCR_CORE_GAMEBOYSMART_H_

# include "config.h"

# if HAS_GBX
#   include "syslibinc.h"
#   include "common/Types.h"

/**
 * @brief System core for Game Boy Smart Modules
 */
#   define GB_SMART_GAMES_PER_PAGE 6

namespace OSCR::Cores::GameBoySmart
{
  // fork oscr_minimal (D249): a struct e o tamanho da página saíram do .cpp para a costura do dumper chamar o `getGames` (o "Game Menu" pela serial).
  struct GBSmartGameInfo {
    uint8_t start_bank;
    uint8_t rom_type;
    uint8_t rom_size;
    uint8_t sram_size;
    char title[16];
  };

  extern uint16_t gameMenuStartBank;   // fork (D249): banco onde o `getGames` começa a procurar; avança uma página por chamada

  void menu();
  void gameMenu();
  bool gameOptionsMenu();
  void flashMenu();

  void cartOn();   // fork (D189): exportada para a costura de gravação do dumper
  void cartOff();
  uint8_t readByte(uint16_t myAddress);

  void getOneGame(struct GBSmartGameInfo *gbSmartGames, uint8_t bank, uint16_t base);
  void getGames(struct GBSmartGameInfo * gbSmartGames, bool & hasMenu, uint8_t & numGames);

  void readFlash();

  void writeFlash();
  void writeFlash(uint32_t start_bank);
  void writeFlashByte(uint32_t myAddress, uint8_t myData);

  void writeFlashFromMyFile(uint32_t addr);

  uint8_t blankCheckingFlash(uint8_t flash_start_bank);
  void eraseFlash(uint8_t flash_start_bank);

  void remapStartBank(uint8_t rom_start_bank, uint8_t rom_size, uint8_t sram_size);
  uint8_t getResizeParam(uint8_t rom_size, uint8_t sram_size);

  void resetFlash(uint8_t flash_start_bank);
} /* namespace OSCR::Cores::GameBoySmart */

# endif /* HAS_GBX */
#endif /* OSCR_CORE_GAMEBOYSMART_H_ */
