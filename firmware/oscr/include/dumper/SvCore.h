// SPDX-License-Identifier: GPL-3.0-or-later
// Watara Supervision (F-20, D218): 3,3 V, ROM do cartucho no barramento do slot SNES (adaptador de 40 pinos; pinagem em src/cores/Supervision.cpp do OSCR).
// As regras que o fork acrescenta em volta do núcleo Supervision.cpp: tamanho em KB -> índice da tabela `romSizes` do núcleo (a leitura é o `readROM`
// do OSCR) e classificação do que o slot devolveu. Código puro: testado no PC em pc-tests/test_sv.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace sv
{
  enum : uint8_t
  {
    kOk = 0,           ///< o barramento devolve dados variados: há cartucho (a ROM do Supervision não tem assinatura que o núcleo confira)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
  };

  constexpr uint16_t kBase = 0x8000;     ///< ROMs de 32 KB ficam em $8000-$FFFF; as de 64 KB ou mais cobrem esse trecho: a sondagem lê daí
  constexpr uint8_t kBadIndex = 0xFF;

  /// KB informado pelo PC -> índice da tabela `romSizes` do núcleo {32, 64, 512} (`kBadIndex` se o tamanho não existe).
  inline uint8_t sizeIndex(uint16_t kb)
  {
    return kb == 32 ? 0 : kb == 64 ? 1 : kb == 512 ? 2 : kBadIndex;
  }

  /// `sample` são `n` bytes lidos a partir de $8000. Slot vazio = amostra com um valor só, $00 ou $FF (a mesma heurística do Pyuuta, Arcadia e ColecoVision).
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) return kOk;
    return (sample[0] == 0xFF || sample[0] == 0x00) ? kNoCart : kOk;
  }
} }  // namespace oscr::sv
