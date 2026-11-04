// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em flash de cartucho repro de SNES. Usa direto as funções do OSCR original em Flash.cpp, que exigem HAS_FLASH8 (SNES + flash em user.ini).
//
//  - Flash CFI com 1, 2 ou 4 chips e 1x 8 MB (menus "CFI LoROM / CFI HiROM" do SNES.cpp): o laço de apagar e gravar é daqui, porque o `writeCFI`
//    do OSCR lê o SD, usa `seekSet` e `busyWait` sem limite; aqui toda espera tem limite e os dados vêm do fluxo, na ordem de SnesPlan.h.
//    Reaproveitado: setup8, identifyCFIbyIds, sendCFICommand, writeByte, readByte, writeByteCompensated, readByteCompensated, mapping.
//  - Menus "LoROM/HiROM (P0)" e "ExLoROM/ExHiROM (P1)" (kGeneric): chama direto as funções do `menuFlash8` do OSCR (eraseFlash*, writeFlash*, idFlash*),
//    sem reescrever nada. O tipo do flash vem do PC (no OSCR vinha do banco CRDB do cartão SD). Os laços dessas funções do OSCR NÃO têm limite de tempo.
// A conferência do `verifyFlash` (que relê o arquivo) é feita pelo PC, lendo o cartucho de volta.
#include "syslibinc.h"
#include "config.h"

#if OSCR_DUMPER && HAS_SNES && HAS_FLASH && HAS_FLASH8

# include "hardware.h"
# include "api.h"
# include "common.h"
# include "cores/include.h"
# include "cores/SNES.h"
# include "cores/Flash.h"
# include "dumper/SnesFlash.h"

namespace OSCR::Dumper::SnesFlash
{
  namespace F = OSCR::Cores::Flash;
  using F::FlashType;

  namespace
  {
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

    /// Espera o bit 7 (DQ7) do endereço igualar o do dado gravado; com `data` = 0x80 serve para o apagamento (DQ7 = 1 quando termina).
    bool pollDq7(uint32_t addr, uint8_t data, uint32_t tries, uint16_t gapUs)
    {
      for (uint32_t t = 0; t < tries; t++)
      {
        if ((F::readByte(addr) & 0x80) == (data & 0x80)) return true;
        if (gapUs >= 1000) delay(gapUs / 1000); else delayMicroseconds(gapUs);
      }
      return false;
    }

    /// `mapping` do OSCR para a fiação (menu) e o chip (1 a 4): os valores do `nextCFI` do SNES.cpp.
    uint8_t mappingFor(uint8_t wiring, bool generic, uint8_t chipIdx)
    {
      if (generic)
      {
        static uint8_t const m[] = {0, 1, 2, 124, 224, 0, 3};    // LoRom (P0), HiRom (P0), ExLoRom (P1), ExHiRom (P1), adaptador de flash, PLCC32
        return wiring >= 1 && wiring <= 6 ? m[wiring] : 1;
      }
      static uint8_t const lo[] = {1, 122, 124, 142};            // chip 1 a 4, LoROM
      static uint8_t const hi[] = {2, 222, 224, 242};            // chip 1 a 4, HiROM
      uint8_t i = chipIdx >= 1 && chipIdx <= 4 ? chipIdx - 1 : 0;
      return wiring == 2 ? hi[i] : lo[i];
    }

    /// Liga o cartucho e põe o barramento no modo do programador de flash de 8 bits.
    void begin(uint16_t chip, uint8_t chipIdx = 1)
    {
      OSCR::Cores::SNES::cartOn();
      F::mapping = mappingFor(uint8_t(chip & 0xFF), isGeneric(chip), chipIdx);
      F::setup8();
    }

    uint32_t genericFlashBytes(uint16_t prgKb) { return uint32_t(prgKb) * 1024UL; }

    bool genericValid(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t size)
    {
      uint8_t wiring = uint8_t(chip & 0xFF);
      uint8_t type = chrKb & 0xF, secExp = (chrKb >> 4) & 0x1F, bufExp = (chrKb >> 9) & 0x7;
      if (wiring < 1 || wiring > 6 || type < 1 || type > 8) return false;
      if (prgKb == 0 || prgKb > 8192) return false;                                   // 1 KB a 8 MB (o `selectFlashSize` do OSCR só dava 1 a 8 MB; o banco CRDB tem chips menores, como o 39SF040)
      if (size == 0 || size % 512UL != 0 || size > genericFlashBytes(prgKb)) return false;
      if (static_cast<FlashType>(type) == FlashType::IC_29GL)                       // grava setor inteiro: o PC completa o arquivo com 0xFF
      {
        if (secExp < 9 || secExp > 24 || bufExp < 1) return false;
        if (size % (1UL << secExp) != 0) return false;
      }
      return true;
    }

    /// Chama a função de ID do tipo, como o item "ID" do `menuFlash8`. false = o chip não responde (ID 0000 ou FFFF).
    bool genericId(FlashType type)
    {
      F::resetFlash8();
      switch (type)
      {
      case FlashType::IC_29F032: F::idFlash29F032(); break;
      case FlashType::IC_E28FXXXJ3A:
      case FlashType::IC_LH28F0XX: F::idFlash28FXXX(); break;
      default: F::idFlash29F1610(); break;
      }
      F::resetFlash8();
      return F::flashid != 0x0000 && F::flashid != 0xFFFF;
    }
  }

  uint16_t check(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes)
  {
    if (isGeneric(chip)) return genericValid(chip, prgKb, chrKb, sizeBytes) ? 0 : oscr::E_ARGUMENTO;

    uint8_t layout = uint8_t(chip >> 8), wiring = uint8_t(chip & 0xFF);
    if (wiring != 1 && wiring != 2) return oscr::E_ARGUMENTO;
    if (chrKb != 0) return oscr::E_ARGUMENTO;
    Seg segs[4];
    uint32_t cap = uint32_t(prgKb) * 1024UL;
    if (layout != kLayout1x && cap != chipBytes(layout, 0) * chipCount(layout)) return oscr::E_ARGUMENTO;   // prg_kb = capacidade total
    return plan(layout, sizeBytes, layout == kLayout1x ? cap : 0, segs) ? 0 : oscr::E_ARGUMENTO;
  }

  uint16_t prepare(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes)
  {
    (void)sizeBytes;
    if (isGeneric(chip))
    {
      FlashType type = static_cast<FlashType>(chrKb & 0xF);
      begin(chip);
      F::flashromType = type;
      F::flashSize = genericFlashBytes(prgKb);
      F::sectorSize = 1UL << ((chrKb >> 4) & 0x1F);
      if (!genericId(type)) return oscr::E_FLASH;

      // Apagar, como o item "Erase" do `menuFlash8`.
      switch (type)
      {
      case FlashType::IC_29F032: F::eraseFlash29F032(); break;
      case FlashType::IC_E28FXXXJ3A:
      case FlashType::IC_LH28F0XX: F::eraseFlash28FXXX(); break;
      default: F::eraseFlash29F1610(); break;
      }
      F::resetFlash8();
      return 0;
    }

    uint8_t layout = uint8_t(chip >> 8), wiring = uint8_t(chip & 0xFF);
    uint8_t n = chipCount(layout);
    uint32_t perChip = chipBytes(layout, uint32_t(prgKb) * 1024UL);

    begin(chip, 1);

    // Mesma identificação do `identifyCFI` do OSCR, sem a espera por botão quando falha.
    F::writeByteCompensated(0xAAA, 0xF0);
    delay(100);
    if (!F::identifyCFIbyIds(false) && !F::identifyCFIbyIds(true)) return oscr::E_FLASH;

    uint8_t sizeExp = F::readByteCompensated(0x4E);                       // CFI: tamanho do chip = 2^N bytes
    F::writeByteCompensated(0xAAA, 0xF0);                                  // reset, como no `identifyCFI`
    delay(100);
    if (perChip == 0 || sizeExp < 10 || sizeExp > 24 || (1UL << sizeExp) < perChip) return oscr::E_FLASH;

    // Como no `writeCFI`, para cada chip: reset duplo e apagar o chip inteiro. Os chips apagam ao mesmo tempo (o OSCR apagava um por vez,
    // com o cartucho na mão); depois espera DQ7 = 1 de cada um, dentro do mesmo limite (o PC espera 90 s pelo primeiro ACK).
    for (uint8_t c = 1; c <= n; c++)
    {
      F::mapping = mappingFor(wiring, false, c);
      F::writeByteCompensated(0xAAA, 0xF0);
      delay(100);
      F::writeByte(0x555, 0xF0);
      delay(100);
      F::sendCFICommand(0x80);
      F::sendCFICommand(0x10);
    }

    uint32_t start = millis();
    for (uint8_t c = 1; c <= n; c++)
    {
      F::mapping = mappingFor(wiring, false, c);
      for (;;)
      {
        if ((F::readByte(0) & 0x80) == 0x80) break;
        if (millis() - start > 80000UL) return oscr::E_CARTUCHO_IO;          // até 80 s no total
        delay(50);
      }
    }
    return 0;
  }

  uint16_t program(uint16_t chip, uint16_t prgKb, uint16_t chrKb, uint32_t sizeBytes, oscr::StreamSource & in)
  {
    if (isGeneric(chip))
    {
      FlashType type = static_cast<FlashType>(chrKb & 0xF);
      begin(chip);
      OSCR::Cores::fileSize = sizeBytes;                                     // as funções do OSCR percorrem `fileSize` e leem o "arquivo" (o fluxo)
      F::flashromType = type;
      F::flashSize = genericFlashBytes(prgKb);
      F::sectorSize = 1UL << ((chrKb >> 4) & 0x1F);
      F::bufferSize = uint16_t(1U << ((chrKb >> 9) & 0x7));

      switch (type)
      {
      case FlashType::IC_29F032: F::writeFlash29F032(); break;
      case FlashType::IC_29F1601: F::writeFlash29F1601(); break;
      case FlashType::IC_29F800: F::writeFlash29F800(); break;
      case FlashType::IC_29GL: F::writeFlash29GL(F::sectorSize, F::bufferSize); break;
      case FlashType::IC_29F1610: F::writeFlash29F1610(); break;
      case FlashType::IC_29LV640: F::writeFlash29LV640(); break;
      case FlashType::IC_E28FXXXJ3A:
      case FlashType::IC_LH28F0XX: F::writeFlash28FXXX(); break;
      default: return oscr::E_ARGUMENTO;
      }

      delay(100);
      F::resetFlash8();                                                      // duas vezes, como no `menuFlash8`
      F::resetFlash8();
      return 0;
    }

    uint8_t layout = uint8_t(chip >> 8), wiring = uint8_t(chip & 0xFF);
    Seg segs[4];
    uint8_t count = plan(layout, sizeBytes, layout == kLayout1x ? uint32_t(prgKb) * 1024UL : 0, segs);
    if (count == 0) return oscr::E_ARGUMENTO;

    begin(chip, 1);                                                          // flashX16Mode e flashSwitchLastBits ficaram da identificação

    uint8_t * buf = OSCR::Storage::Shared::buffer;
    uint8_t lastChip = 0;
    for (uint8_t s = 0; s < count; s++)
    {
      if (segs[s].len == 0) continue;
      if (lastChip != 0 && segs[s].chip != lastChip)                         // fim de um chip: reset, como no fim do `writeCFI`
      {
        F::writeByteCompensated(0xAAA, 0xF0);
        delay(300);                                                          // o `nextCFI` espera 300 ms
      }
      lastChip = segs[s].chip;
      F::mapping = mappingFor(wiring, false, segs[s].chip);

      for (uint32_t off = 0; off < segs[s].len; off += 512)
      {
        if (!readFull(in, buf, 512)) return oscr::E_CARTUCHO_IO;
        for (uint16_t i = 0; i < 512; i++)
        {
          uint32_t a = segs[s].addr + off + i;
          F::sendCFICommand(0xA0);                                           // sequência de programar byte
          F::writeByte(a, buf[i]);
          if (!pollDq7(a, buf[i], 2000, 5)) return oscr::E_CARTUCHO_IO;      // até 10 ms por byte (típico 10 us)
        }
      }
    }

    F::writeByteCompensated(0xAAA, 0xF0);                                    // reset, como no fim do `writeCFI`
    delay(100);
    return 0;
  }
}

#endif /* OSCR_DUMPER && HAS_SNES && HAS_FLASH && HAS_FLASH8 */
