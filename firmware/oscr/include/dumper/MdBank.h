// SPDX-License-Identifier: GPL-3.0-or-later
// Mega Drive: leitura de ROM por troca de banco de 32 KiB (Lion King 3 e Pokémon Stadium / Kaiju; F-16, D181). NÃO vem do OSCR: o mapa de registrador
// é o do MAME (src/devices/bus/megadrive/rom.cpp, BSD-3-Clause), nunca conferido em cartucho. O PC escolhe o mapper (campo `mapper` do DUMP_ROM); sem detecção
// automática, porque escrever em $700000 num cartucho de outro tipo (flash repro) pode ser perigoso.
//   Escrita de byte em $700000 a $7FFFFF = banco (LK3: valor & 0xFF; Pokémon: & 0x7F).
//   Leitura em $000000 a $0FFFFF: byte da ROM = ((endereço) | (banco << 15)) & (tamanho - 1).
// Para ler o byte X da ROM basta gravar o banco X >> 15 e ler o endereço X & 0x7FFF: um banco por pedaço de 32 KiB.
#pragma once
#include <stdint.h>

namespace OSCR::Dumper::MdBank
{
  enum : uint16_t { kNone = 0, kLionKing3 = 1, kPokemonStadium = 2 };
  constexpr uint32_t kChunkBytes = 0x8000UL;
  constexpr uint32_t kRegWordAddr = 0x380000UL;      // $700000 em bytes; `MD::writeWord` e `readWord` usam endereço de palavra

  inline bool valid(uint16_t mapper) { return mapper == kLionKing3 || mapper == kPokemonStadium; }
  inline uint16_t bankMask(uint16_t mapper) { return mapper == kPokemonStadium ? 0x7F : 0xFF; }

  /// `kb` = tamanho da ROM: potência de 2 de 128 KB a 4 MB (a fórmula do MAME mascara com tamanho - 1) e que cabe nos bancos do mapper.
  inline bool sizeValid(uint16_t mapper, uint32_t kb)
  {
    if (!valid(mapper) || kb < 128 || kb > 4096 || (kb & (kb - 1)) != 0) return false;
    return (kb * 1024UL) / kChunkBytes <= uint32_t(bankMask(mapper)) + 1;
  }

  inline uint32_t chunks(uint32_t kb) { return (kb * 1024UL) / kChunkBytes; }

  /// Byte da ROM que o cartucho entrega ao ler `addr` (0 a $FFFFF) com o banco `bank` gravado.
  inline uint32_t romAddress(uint32_t addr, uint16_t bank, uint32_t romBytes) { return (addr | (uint32_t(bank) << 15)) & (romBytes - 1); }
}
