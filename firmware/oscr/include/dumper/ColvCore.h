// SPDX-License-Identifier: GPL-3.0-or-later
// ColecoVision (F-20, D201): adaptador de 30 pinos no slot SNES (pinagem no cabeçalho de src/cores/Colecovision.cpp do OSCR).
// As regras que o fork acrescenta em volta do núcleo Colecovision.cpp: tamanho em KB -> índice da tabela `COL` do núcleo,
// e classificação do que o slot devolveu. O núcleo só lê (cartOn, readROM). Código puro: testado no PC em pc-tests/test_colv.cpp
// e espelhado no simulador do host (host/oscr_host/sim.py, SimDevice.kt).
#pragma once
#include <stdint.h>

namespace oscr { namespace colv
{
  enum : uint8_t
  {
    kOk = 0,           ///< assinatura de cartucho de ColecoVision em $8000 ($AA $55 ou $55 $AA)
    kNoCart = 1,       ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
    kNoHeader = 4,     ///< há dados mas sem a assinatura (homebrew, contato sujo): o tamanho vem do PC
  };

  constexpr uint32_t kBase = 0x8000;           ///< endereço inicial da ROM no console
  constexpr uint8_t kSizeCount = 6;
  constexpr uint8_t kBadIndex = 0xFF;

  /// Tamanhos do menu "Set ROM size" do OSCR (tabela `COL` do núcleo), em KB. A ordem é a da tabela: o índice vai para `romSize`.
  inline uint16_t sizeKb(uint8_t index)
  {
    static const uint8_t kTab[kSizeCount] = { 8, 12, 16, 20, 24, 32 };
    return index < kSizeCount ? kTab[index] : 0;
  }

  /// KB informado pelo PC -> índice da tabela do núcleo (`kBadIndex` se o tamanho não existe).
  inline uint8_t sizeIndex(uint16_t kb)
  {
    for (uint8_t i = 0; i < kSizeCount; i++) if (sizeKb(i) == kb) return i;
    return kBadIndex;
  }

  /**
   * Classifica o que o slot devolveu. `sample` são `n` bytes lidos a partir de $8000. A assinatura $AA55 (tela de título)
   * ou $55AA (modo de teste) é a convenção do console, não do OSCR: o núcleo do OSCR não detecta nada.
   * Slot vazio = amostra com um valor só, $00 ou $FF (a mesma heurística do NES e do Master System).
   */
  inline uint8_t classify(uint8_t const * sample, uint8_t n)
  {
    if (n < 2) return kNoCart;
    bool same = true;
    for (uint8_t i = 1; i < n; i++) if (sample[i] != sample[0]) { same = false; break; }
    if (same && (sample[0] == 0xFF || sample[0] == 0x00)) return kNoCart;
    if ((sample[0] == 0xAA && sample[1] == 0x55) || (sample[0] == 0x55 && sample[1] == 0xAA)) return kOk;
    return kNoHeader;
  }
} }  // namespace oscr::colv
