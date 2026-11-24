// SPDX-License-Identifier: GPL-3.0-or-later
// Vectrex (F-20, D205): 5 V, ROM de 4 a 64 KB no barramento do slot SNES (adaptador de 36 pinos; pinagem em src/cores/Vectrex.cpp do OSCR).
// As regras que o fork acrescenta em volta do núcleo Vectrex.cpp: tamanho em KB -> índice da tabela `romSizes` do núcleo (a leitura, com a troca de banco
// PB6 nos 64 KB, é o `readROM` do OSCR) e classificação do que o slot devolveu.
// Código puro: testado no PC em pc-tests/test_vec.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace vec
{
  enum : uint8_t
  {
    kOk = 0,           ///< primeiro byte $67 ("g" de "g GCE 1982"), o que a BIOS do console procura
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
    kNoHeader = 4,     ///< há dados mas o primeiro byte não é $67 (homebrew, contato sujo): o tamanho vem do PC
  };

  constexpr uint8_t kSizeCount = 6;
  constexpr uint8_t kBadIndex = 0xFF;
  constexpr uint8_t kFirstByte = 0x67;

  /// Tamanhos do menu "Set ROM size" do OSCR (tabela `romSizes` do núcleo), em KB. O índice vai para `romSize`.
  inline uint16_t sizeKb(uint8_t index)
  {
    static const uint8_t kTab[kSizeCount] = { 4, 8, 12, 16, 32, 64 };
    return index < kSizeCount ? kTab[index] : 0;
  }

  inline uint8_t sizeIndex(uint16_t kb)
  {
    for (uint8_t i = 0; i < kSizeCount; i++) if (sizeKb(i) == kb) return i;
    return kBadIndex;
  }

  /// `sample` são `n` bytes lidos a partir de $0000 com o PB6 baixo. A BIOS do Vectrex procura $67 no primeiro byte: é convenção do console, não do OSCR.
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    bool same = true;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) { same = false; break; }
    if (same && (sample[0] == 0xFF || sample[0] == 0x00)) return kNoCart;
    return sample[0] == kFirstByte ? kOk : kNoHeader;
  }
} }  // namespace oscr::vec
