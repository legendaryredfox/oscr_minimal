// SPDX-License-Identifier: GPL-3.0-or-later
// V.Smile (F-20, D228): 3,3 V, adaptador de 48 pinos no slot SNES (pinagem no cabeçalho de src/cores/VSmile.cpp do OSCR).
// As regras que o fork acrescenta em volta do núcleo: tamanho em KB -> índice da tabela `romSizes` do núcleo {4, 6, 8, 16} MB,
// tamanho do arquivo e classificação do que o slot devolveu. O núcleo só lê (cartOn, read_rom_word, readROM).
// Código puro: testado no PC em pc-tests/test_vsm.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace vsm
{
  enum : uint8_t
  {
    kOk = 0,           ///< há dados no barramento (o fork não confere assinatura)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
  };

  constexpr uint32_t kBase = 0;          ///< endereço de palavra da sondagem (início da ROM do primeiro chip, CSB1)
  constexpr uint8_t kSizeCount = 4;
  constexpr uint8_t kBadIndex = 0xFF;

  /// Tamanhos do menu "Set Size" do OSCR (tabela `romSizes` do núcleo), em KB. A ordem é a da tabela: o índice vai para `romSize`.
  /// 6 MB = dois chips (4 MB no CSB1 e 2 MB no CSB2); 16 MB = V.Motion (8 MB no CSB1 e 8 MB com CSB1 e CSB2 baixos).
  inline uint16_t sizeKb(uint8_t index)
  {
    static const uint16_t kTab[kSizeCount] = { 4096, 6144, 8192, 16384 };
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

  /// Slot vazio = amostra com um valor só, $00 ou $FF (a mesma heurística do NES e do Master System). `sample` são `n` bytes
  /// na ordem em que o `readROM` os grava (palavra lida com `read_rom_word`, byte alto primeiro).
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) return kOk;
    return (sample[0] == 0x00 || sample[0] == 0xFF) ? kNoCart : kOk;
  }
} }  // namespace oscr::vsm
