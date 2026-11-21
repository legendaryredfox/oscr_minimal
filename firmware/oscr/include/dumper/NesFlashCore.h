// SPDX-License-Identifier: GPL-3.0-or-later
// Regras puras da flash SST39SF0x0 do NES Maker (D194, item 3), testadas no PC (pc-tests/test_nes.cpp).
// IDs e tamanhos do datasheet SST39SF010A/020A/040 (S71147-02-000 5/01, Tabela 1): fabricante BFh em 0000H; dispositivo em 0001H = B5h (128 KB),
// B6h (256 KB), B7h (512 KB). Os três usam os mesmos comandos (5555H/2AAAH), setor uniforme de 4 KB e comando 30h para apagar o setor.
#pragma once
#include <stdint.h>

namespace oscr { namespace nes {

constexpr uint16_t kSst39sf010aId = 0xBFB5;
constexpr uint16_t kSst39sf020aId = 0xBFB6;
constexpr uint16_t kSst39sf040Id = 0xBFB7;

/// Tamanho em KB do chip com esse ID (fabricante e dispositivo juntos), ou 0 se não é um SST39SF0x0.
constexpr uint16_t sst39ChipKb(uint16_t id)
{
  return id == kSst39sf010aId ? 128 : id == kSst39sf020aId ? 256 : id == kSst39sf040Id ? 512 : 0;
}

/// A PRG de [prgKb] KB cabe no chip de ID [id]? Falso para ID desconhecido. Os bits de banco acima do tamanho não existem no chip (A15 e acima só valem se o chip os tem), e uma imagem maior se sobreporia.
constexpr bool sst39Fits(uint16_t id, uint16_t prgKb)
{
  return sst39ChipKb(id) != 0 && prgKb <= sst39ChipKb(id);
}

}}
