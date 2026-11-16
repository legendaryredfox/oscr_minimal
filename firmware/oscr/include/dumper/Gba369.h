// SPDX-License-Identifier: GPL-3.0-or-later
// Regras puras da leitura do GBA 369-in-1 (F-18, D174): "Read 256MB" e "Read Offset" do OSCR. Testado no PC em pc-tests/test_gba369.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace gba369 {
  constexpr uint16_t kFlag = 0x8000;        // bit 15 do campo `mapper` do DUMP_ROM do GBA: leitura do 369-in-1; bits 8 a 13 = bloco (0 a 63, de 4 MB); bits 0 a 7 = 0
  constexpr uint32_t kBankMb = 32;          // o mapeador do 369-in-1 enxerga 32 MB por vez
  constexpr uint32_t kTotalMb = 256;

  inline uint16_t code(uint8_t block) { return uint16_t(kFlag | (uint16_t(block) << 8)); }
  inline bool isRead(uint16_t mapper) { return (mapper & kFlag) != 0; }
  inline uint8_t block(uint16_t mapper) { return uint8_t((mapper >> 8) & 0x3F); }

  /**
   * Confere o pedido de leitura. `mb` vai no campo `prg_kb` do protocolo, em MB (não em KB): 0 só vale no bloco 0 e lê os 256 MB ("Read 256MB").
   * Depois do OSCR (`read369in1`, que não confere nada): tamanho de 1 a 32 MB; a partir de 4 MB, múltiplo de 4 (o laço do OSCR lê blocos
   * inteiros de 4 MB); a leitura não pode passar do fim dos 32 MB em que o bloco cai (o OSCR leria além da janela).
   */
  inline bool valid(uint16_t mapper, uint16_t mb)
  {
    if (!isRead(mapper) || (mapper & 0x40FF) != 0) return false;
    uint8_t b = block(mapper);
    if (mb == 0) return b == 0;
    if (mb > kBankMb || (mb >= 4 && mb % 4 != 0)) return false;
    uint32_t startInBank = (uint32_t(b) * 4) % kBankMb;
    return startInBank + mb <= kBankMb;
  }

  /// Bytes que a leitura devolve (valid() já conferido).
  inline uint32_t bytes(uint16_t mb) { return (mb == 0 ? kTotalMb : uint32_t(mb)) << 20; }
} }  // namespace oscr::gba369
