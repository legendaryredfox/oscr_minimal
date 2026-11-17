// SPDX-License-Identifier: GPL-3.0-or-later
// Mega Drive: leitura de ROM por troca de banco de 32 KiB (Lion King 3 e Pokémon Stadium / Kaiju; F-16, D181). NÃO vem do OSCR: o mapa de registrador
// é o do MAME (src/devices/bus/megadrive/rom.cpp, BSD-3-Clause), nunca conferido em cartucho. O PC escolhe o mapper (campo `mapper` do DUMP_ROM); sem detecção
// automática, porque escrever em $700000 num cartucho de outro tipo (flash repro) pode ser perigoso.
//   Escrita de byte em $700000 a $7FFFFF = banco (LK3: valor & 0xFF; Pokémon: & 0x7F).
//   Leitura em $000000 a $0FFFFF: byte da ROM = ((endereço) | (banco << 15)) & (tamanho - 1).
// Para ler o byte X da ROM basta gravar o banco X >> 15 e ler o endereço X & 0x7FFF: um banco por pedaço de 32 KiB.
//
// Star Odyssey (mapper 3, mesma origem; Beggar Prince, Legend of Wukong e os multicarts piratas não precisam disto: ligam em modo de ROM linear):
//   Escrita de byte em $000F00 = base: `(valor >> 4) & 7` e liga o modo 1 (cinco bancos de 256 KiB em $000000 a $13FFFF). A base escolhe qual
//   pedaço de 256 KiB da imagem aparece em $000000: byte da ROM = base * 256 KiB + endereço. Até 8 bases, logo imagem de até 2 MiB.
//   Escrever $E00 com o bit 7 limpo TRAVA a troca até o reset: o dumper nunca escreve ali.
#pragma once
#include <stdint.h>

namespace OSCR::Dumper::MdBank
{
  enum : uint16_t { kNone = 0, kLionKing3 = 1, kPokemonStadium = 2, kStarOdyssey = 3 };
  constexpr uint32_t kChunkBytes = 0x8000UL;
  constexpr uint32_t kRegWordAddr = 0x380000UL;      // $700000 em bytes; `MD::writeWord` e `readWord` usam endereço de palavra
  constexpr uint32_t kStarChunkBytes = 0x40000UL, kStarRegWordAddr = 0x780UL;     // $000F00 em bytes

  inline bool valid(uint16_t mapper) { return mapper == kLionKing3 || mapper == kPokemonStadium || mapper == kStarOdyssey; }
  inline uint16_t bankMask(uint16_t mapper) { return mapper == kPokemonStadium ? 0x7F : (mapper == kStarOdyssey ? 0x07 : 0xFF); }
  inline uint32_t chunkBytes(uint16_t mapper) { return mapper == kStarOdyssey ? kStarChunkBytes : kChunkBytes; }
  inline uint32_t regWordAddr(uint16_t mapper) { return mapper == kStarOdyssey ? kStarRegWordAddr : kRegWordAddr; }
  /// O valor que se grava no registrador para o pedaço `n`.
  inline uint16_t regValue(uint16_t mapper, uint32_t n) { return mapper == kStarOdyssey ? uint16_t((n << 4) & 0x70) : uint16_t(n); }

  /// `kb` = tamanho da ROM: potência de 2 de 128 KB a 4 MB (a fórmula do MAME mascara com tamanho - 1) e que cabe nos bancos do mapper.
  inline bool sizeValid(uint16_t mapper, uint32_t kb)
  {
    if (mapper == kStarOdyssey) return kb >= 256 && kb <= 2048 && kb % 256 == 0;       // múltiplo de 256 KiB (a base é o número do pedaço), até 8 bases
    if (!valid(mapper) || kb < 128 || kb > 4096 || (kb & (kb - 1)) != 0) return false;
    return (kb * 1024UL) / kChunkBytes <= uint32_t(bankMask(mapper)) + 1;
  }

  inline uint32_t chunks(uint16_t mapper, uint32_t kb) { return (kb * 1024UL) / chunkBytes(mapper); }

  /// Byte da ROM que o cartucho entrega ao ler `addr` (0 a $FFFFF) com o banco `bank` gravado.
  inline uint32_t romAddress(uint32_t addr, uint16_t bank, uint32_t romBytes) { return (addr | (uint32_t(bank) << 15)) & (romBytes - 1); }
  /// Star Odyssey: base `(valor >> 4) & 7`; o pedaço de 256 KiB da base aparece em $000000 (a janela vai até $13FFFF).
  inline uint32_t starAddress(uint32_t addr, uint16_t value) { return ((uint32_t(value) >> 4) & 7) * kStarChunkBytes + addr; }
}
