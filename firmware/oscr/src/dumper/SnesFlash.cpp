// SPDX-License-Identifier: GPL-3.0-or-later
// Gravação de ROM em flash CFI de cartucho repro de SNES. Usa direto as funções do OSCR original em Flash.cpp (setup8, identifyCFIbyIds,
// sendCFICommand, writeByte, readByte...), que exigem HAS_FLASH8 (SNES + flash em user.ini).
// Diferença deliberada: o laço de apagar e gravar é daqui, porque o `writeCFI` do OSCR espera para sempre (busyWait) e lê o arquivo do SD;
// aqui toda espera tem limite e termina com erro, e os dados vêm do fluxo serial. A conferência do `verifyFlash` (que relê o arquivo)
// é feita pelo PC, lendo o cartucho de volta.
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

    /// Liga o cartucho e põe o barramento no modo do programador de flash de 8 bits, com a fiação do chip escolhido.
    void begin(uint8_t chip)
    {
      OSCR::Cores::SNES::cartOn();
      F::mapping = (chip == kCfiLoRom) ? 1 : 2;       // igual a "CFI LoROM" / "CFI HiROM" no menu do SNES
      F::setup8();
    }
  }

  uint16_t check(uint8_t chip, uint16_t capacityKb, uint32_t sizeBytes)
  {
    if (chip != kCfiLoRom && chip != kCfiHiRom) return oscr::E_ARGUMENTO;
    if (capacityKb != 2048 && capacityKb != 4096) return oscr::E_ARGUMENTO;
    if (sizeBytes == 0 || sizeBytes % 512UL != 0 || sizeBytes > uint32_t(capacityKb) * 1024UL) return oscr::E_ARGUMENTO;
    return 0;
  }

  uint16_t prepare(uint8_t chip, uint16_t capacityKb)
  {
    begin(chip);

    // Mesma identificação do `identifyCFI` do OSCR, sem a espera por botão quando falha.
    F::writeByteCompensated(0xAAA, 0xF0);
    delay(100);
    if (!F::identifyCFIbyIds(false) && !F::identifyCFIbyIds(true)) return oscr::E_FLASH;

    uint8_t sizeExp = F::readByteCompensated(0x4E);                       // CFI: tamanho do chip = 2^N bytes
    F::writeByteCompensated(0xAAA, 0xF0);                                  // reset, como no `identifyCFI`
    delay(100);
    if (sizeExp < 10 || sizeExp > 24 || (1UL << sizeExp) < uint32_t(capacityKb) * 1024UL) return oscr::E_FLASH;

    // Como no `writeCFI`: reset duplo, apagar o chip inteiro e esperar DQ7 = 1.
    F::writeByteCompensated(0xAAA, 0xF0);
    delay(100);
    F::writeByte(0x555, 0xF0);
    delay(100);

    F::sendCFICommand(0x80);
    F::sendCFICommand(0x10);
    if (!pollDq7(0, 0x80, 1600, 50000)) return oscr::E_CARTUCHO_IO;       // até 80 s (o PC espera 90 s pelo primeiro ACK)
    return 0;
  }

  uint16_t program(uint8_t chip, uint32_t sizeBytes, oscr::StreamSource & in)
  {
    begin(chip);                                                           // flashX16Mode e flashSwitchLastBits ficaram da identificação

    uint8_t * buf = OSCR::Storage::Shared::buffer;
    for (uint32_t addr = 0; addr < sizeBytes; addr += 512)
    {
      if (!readFull(in, buf, 512)) return oscr::E_CARTUCHO_IO;
      for (uint16_t i = 0; i < 512; i++)
      {
        F::sendCFICommand(0xA0);                                           // sequência de programar byte
        F::writeByte(addr + i, buf[i]);
        if (!pollDq7(addr + i, buf[i], 2000, 5)) return oscr::E_CARTUCHO_IO;   // até 10 ms por byte (típico 10 us)
      }
    }

    F::writeByteCompensated(0xAAA, 0xF0);                                  // reset, como no fim do `writeCFI`
    delay(100);
    return 0;
  }
}

#endif /* OSCR_DUMPER && HAS_SNES && HAS_FLASH && HAS_FLASH8 */
