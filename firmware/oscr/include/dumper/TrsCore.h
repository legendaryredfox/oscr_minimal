// SPDX-License-Identifier: GPL-3.0-or-later
// TRS-80 Color Computer (F-20, D248): 5 V, adaptador de 40 pinos no slot SNES (pinagem no cabeçalho de src/cores/TRS80.cpp do OSCR).
// As regras que o fork acrescenta em volta do núcleo: tamanho em KB -> índice da tabela `romSizes` do núcleo {2, 4, 8, 10, 16, 32, 64, 128},
// tamanho do arquivo e classificação do que o slot devolveu. A leitura (com a troca de banco do Predator e do RoboCop) é o `readROM` do OSCR.
// Código puro: testado no PC em pc-tests/test_trs.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace trs
{
  enum : uint8_t
  {
    kOk = 0,           ///< o barramento devolve dados variados: há cartucho (a ROM do CoCo não tem assinatura fixa)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
  };

  constexpr uint16_t kBase = 0xC000;     ///< todo cartucho começa em $C000 (/CTS); a sondagem lê daí
  constexpr uint8_t kSizeCount = 8;
  constexpr uint8_t kBadIndex = 0xFF;

  /// Tamanhos do menu "Set Size" do OSCR (tabela `romSizes` do núcleo), em KB. A ordem é a da tabela: o índice vai para `romSize`.
  /// 32 KB = segundo chip pelo /SCS (Mind-Roll); 64 e 128 KB = troca de banco por escrita em $FF40 (Predator, RoboCop).
  inline uint8_t sizeKb(uint8_t index)
  {
    static const uint8_t kTab[kSizeCount] = { 2, 4, 8, 10, 16, 32, 64, 128 };
    return index < kSizeCount ? kTab[index] : 0;
  }

  /// KB informado pelo PC -> índice da tabela do núcleo (`kBadIndex` se o tamanho não existe).
  inline uint8_t sizeIndex(uint16_t kb)
  {
    for (uint8_t i = 0; i < kSizeCount; i++) if (sizeKb(i) == kb) return i;
    return kBadIndex;
  }

  /// Bytes que o `readROM` do núcleo grava para o tamanho pedido (0 se o tamanho não existe).
  inline uint32_t fileBytes(uint16_t kb)
  {
    return sizeIndex(kb) == kBadIndex ? 0 : uint32_t(kb) * 1024UL;
  }

  /// O `readROM` do núcleo escreve em $FF40 (troca de banco) só nos tamanhos acima de 32 KB.
  inline bool bankSwitched(uint16_t kb)
  {
    uint8_t i = sizeIndex(kb);
    return i != kBadIndex && i > 5;
  }

  /// `sample` são `n` bytes lidos a partir de $C000. Slot vazio = amostra com um valor só, $00 ou $FF (a mesma heurística do Pyuuta, ColecoVision e NES).
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) return kOk;
    return (sample[0] == 0xFF || sample[0] == 0x00) ? kNoCart : kOk;
  }
} }  // namespace oscr::trs
