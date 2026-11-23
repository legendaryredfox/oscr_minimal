// SPDX-License-Identifier: GPL-3.0-or-later
// Neo Geo Pocket / Color (F-20, D202): 3,3 V, ROM flash de 4 a 32 Mbit. As regras que o fork acrescenta em volta do núcleo
// NeoGeoPocket.cpp do OSCR: classificação do que o slot devolveu e tamanho final da ROM. O núcleo lê o ID do chip (autoselect) e o
// cabeçalho "COPYRIGHT BY SNK CORPORATION"; aqui só ficam as decisões. Código puro: testado no PC em pc-tests/test_ngp.cpp.
#pragma once
#include <stdint.h>

namespace oscr { namespace ngp
{
  enum : uint8_t
  {
    kOk = 0,           ///< cabeçalho SNK lido: nome e (se o chip é conhecido) tamanho valem
    kNoCart = 1,       ///< o ID do chip veio $FFFF: nada respondeu no barramento
    kNoHeader = 4,     ///< o chip respondeu mas o cabeçalho não é da SNK (contato sujo, flashcart, ROM de outro sistema)
  };

  constexpr uint16_t kNoChip = 0xFFFF;

  /// Tamanhos do menu "Set ROM size" do OSCR, em KB: 4, 8, 16 e 32 Mbit.
  inline bool sizeKbValid(uint16_t kb) { return kb == 512 || kb == 1024 || kb == 2048 || kb == 4096; }

  /// `chipId` = (fabricante << 8 | dispositivo) como o núcleo monta; `headerOk` = o `getCartInfo` do OSCR devolveu true.
  inline uint8_t classify(uint16_t chipId, bool headerOk)
  {
    if (chipId == kNoChip) return kNoCart;
    return headerOk ? kOk : kNoHeader;
  }

  /// Tamanho final em bytes: o informado pelo PC vale sempre; sem ele só o chip conhecido serve (0 = o PC precisa informar).
  inline uint32_t romBytes(uint32_t coreBytes, uint16_t kb) { return kb ? uint32_t(kb) * 1024UL : coreBytes; }
} }  // namespace oscr::ngp
