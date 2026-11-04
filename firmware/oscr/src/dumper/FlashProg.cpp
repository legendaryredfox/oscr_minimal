// SPDX-License-Identifier: GPL-3.0-or-later
// Programador de flash genérico. Usa direto as funções do OSCR original em Flash.cpp: setup8, setup16, setup_Eprom, os IDs, readFlash, readFlash16,
// read_Eprom, eraseFlash*, writeFlash*, write_Eprom e os resets, na ordem dos menus. Flash de 8 bits: a gravação é o modo genérico do SnesFlash
// (as mesmas chamadas do `menuFlash8`); aqui só a leitura, o ID, o apagamento de 16 bits e o EPROM.
// Diferença: o "arquivo" é o fluxo serial (StreamFile). Os laços de espera do OSCR não têm limite de tempo (iguais aos menus originais).
#include "syslibinc.h"
#include "config.h"

#if OSCR_DUMPER && HAS_SNES && HAS_FLASH && HAS_FLASH8 && defined(ENABLE_FLASH16)

# include "hardware.h"
# include "api.h"
# include "common.h"
# include "cores/include.h"
# include "cores/SNES.h"
# include "cores/Flash.h"
# include "dumper/SnesFlash.h"
# include "dumper/FlashProg.h"

namespace OSCR::Dumper::FlashProg
{
  namespace F = OSCR::Cores::Flash;
  using F::FlashType;

  namespace
  {
    uint8_t kind(uint16_t chip) { return uint8_t(chip & 0xFF); }
    bool is8(uint16_t chip) { return kind(chip) == k8Adapter || kind(chip) == k8Plcc32; }
    uint16_t snesCode(uint16_t chip) { return SnesFlash::code(SnesFlash::kGeneric, kind(chip) == k8Adapter ? 5 : 6); }

    bool plausible(uint16_t id) { return id != 0x0000 && id != 0xFFFF; }

    /// Liga o cartucho (5 V) e põe o barramento no modo do chip.
    void begin(uint16_t chip, uint16_t prgKb)
    {
      OSCR::Cores::SNES::cartOn();
      switch (kind(chip))
      {
      case k8Adapter: F::mapping = 0; F::setup8(); break;
      case k8Plcc32: F::mapping = 3; F::setup8(); break;
      case k16: F::setup16(); break;
      default: F::setup_Eprom(); break;
      }
      if (kind(chip) != kEprom) F::flashSize = uint32_t(prgKb) * 1024UL;
    }

    bool isLv640(uint16_t id)
    {
      return id == 0xC2C4 || id == 0xC249 || id == 0xC2A7 || id == 0xC2A8 || id == 0xC2C9 || id == 0xC2CB || id == 0x0149 || id == 0x01C4
          || id == 0x01F9 || id == 0x01F6 || id == 0x01D7 || id == 0xC2FC;     // a lista do `menuFlash16` do OSCR
    }

    char hexDigit(uint8_t v) { return char(v < 10 ? '0' + v : 'A' + v - 10); }
    void putHex(char * dst, uint16_t v) { for (int i = 0; i < 4; i++) dst[i] = hexDigit((v >> (12 - 4 * i)) & 0xF); }
  }

  uint16_t check(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes)
  {
    if ((chip >> 8) != 0 || kind(chip) < k8Adapter || kind(chip) > kEprom) return oscr::E_ARGUMENTO;
    uint32_t cap = kind(chip) == kEprom ? 4UL << 20 : uint32_t(prgKb) * 1024UL;
    if (kind(chip) != kEprom && (prgKb == 0 || prgKb > 8192)) return oscr::E_ARGUMENTO;
    if (!is8(chip) && chrKb != 0) return oscr::E_ARGUMENTO;
    if (sizeBytes != 0 && (sizeBytes % 512UL != 0 || sizeBytes > cap)) return oscr::E_ARGUMENTO;
    if (sizeBytes != 0 && is8(chip)) return SnesFlash::check(snesCode(chip), prgKb, chrKb, sizeBytes);    // tipo, setor e buffer do 8 bits
    return 0;
  }

  uint16_t checkDetect(uint16_t chip, uint16_t prgKb, uint16_t chrKb)
  {
    if (chip == kMdCart) return (prgKb == 0 && chrKb == 0) ? 0 : oscr::E_ARGUMENTO;
    return check(chip, prgKb, chrKb, 0);
  }

  uint8_t detect(uint16_t chip, uint16_t prgKb, uint16_t chrKb, char * text, uint32_t & sizeBytes)
  {
    begin(chip, prgKb);
    sizeBytes = kind(chip) == kEprom ? (4UL << 20) : uint32_t(prgKb) * 1024UL;

    if (kind(chip) == kEprom)
    {
      strlcpy(text, "EPROM 27C322", 32);
      return 0;
    }
    if (kind(chip) == k16)
    {
      F::resetFlash16();
      F::idFlash16();
      F::resetFlash16();
      strlcpy(text, "ID XXXX", 32);
      putHex(text + 3, F::flashid);
      return plausible(F::flashid) ? 0 : 1;
    }

    uint8_t type = chrKb & 0xF;
    if (type != 0)                                        // tipo informado: um ID só (como o item "ID" do menuFlash8)
    {
      F::resetFlash8();
      if (static_cast<FlashType>(type) == FlashType::IC_29F032) F::idFlash29F032();
      else if (static_cast<FlashType>(type) == FlashType::IC_E28FXXXJ3A || static_cast<FlashType>(type) == FlashType::IC_LH28F0XX) F::idFlash28FXXX();
      else F::idFlash29F1610();
      F::resetFlash8();
      strlcpy(text, "ID XXXX", 32);
      putHex(text + 3, F::flashid);
      return plausible(F::flashid) ? 0 : 1;
    }

    // Sem tipo: as quatro rotinas de ID do `id8` do OSCR (Intel 28F, AMD 29F032, AMD 29F1610, SST 39SF040). O PC mostra a legenda.
    strlcpy(text, "I=XXXX A=XXXX B=XXXX S=XXXX", 32);
    uint16_t ids[4];
    for (uint8_t i = 0; i < 4; i++)
    {
      F::resetFlash8();
      if (i == 0) F::idFlash28FXXX(); else if (i == 1) F::idFlash29F032(); else if (i == 2) F::idFlash29F1610(); else F::idFlash39SF040();
      ids[i] = F::flashid;
      putHex(text + 2 + 7 * i, ids[i]);
    }
    F::resetFlash8();
    bool any = false;
    for (uint8_t i = 0; i < 4; i++) any = any || plausible(ids[i]);
    return any ? 0 : 1;
  }

  uint16_t read(uint16_t chip, uint16_t prgKb)
  {
    begin(chip, prgKb);
    if (kind(chip) == kEprom) F::read_Eprom();
    else if (kind(chip) == k16) { F::resetFlash16(); F::readFlash16(); }
    else { F::resetFlash8(); F::readFlash(); }
    return 0;
  }

  uint16_t prepare(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes)
  {
    if (is8(chip)) return SnesFlash::prepare(snesCode(chip), prgKb, chrKb, sizeBytes);     // ID do tipo informado e apagamento do `menuFlash8`

    begin(chip, prgKb);
    if (kind(chip) == kEprom)
    {
      F::blankcheck_Eprom();
      return F::blank ? 0 : oscr::E_CARTUCHO_IO;                          // EPROM não se apaga: precisa estar em branco
    }

    F::resetFlash16();
    F::idFlash16();
    if (!plausible(F::flashid)) return oscr::E_FLASH;
    F::eraseFlash16();
    return 0;
  }

  uint16_t program(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes, oscr::StreamSource & in)
  {
    if (is8(chip)) return SnesFlash::program(snesCode(chip), prgKb, chrKb, sizeBytes, in);

    begin(chip, prgKb);
    OSCR::Cores::fileSize = sizeBytes;

    if (kind(chip) == kEprom)
    {
      F::write_Eprom();
      delay(1000);
      return 0;
    }

    if (F::flashid == 0xC2F3) F::writeFlash16_29F1601();
    else if (isLv640(F::flashid)) F::writeFlash16_29LV640();
    else F::writeFlash16();
    delay(100);
    F::resetFlash16();
    delay(100);
    return 0;
  }
}

#endif /* OSCR_DUMPER && HAS_SNES && HAS_FLASH && HAS_FLASH8 && ENABLE_FLASH16 */
