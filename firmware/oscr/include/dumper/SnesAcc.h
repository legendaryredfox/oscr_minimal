// SPDX-License-Identifier: GPL-3.0-or-later
// Acessórios do SNES (F-10, D178): Sufami Turbo (slots A e B do adaptador) e Game Processor RAM Cassette (GPC, 512 KB). Regras puras testadas no PC em pc-tests/test_snesacc.cpp.
// O acessório vai no terceiro campo opcional do SNES (`chr_kb`, o do tipo de ROM forçado de F-2, que só aceita 0 a 4): valores a partir de 0x8000.
// Firmware sem este recurso recusa esses valores (E_ARGUMENTO) em vez de ler o cartucho como um SNES comum.
#pragma once
#include <stdint.h>

namespace oscr { namespace snesacc {
  constexpr uint16_t kFlag = 0x8000, kSufamiA = 0x8001, kSufamiB = 0x8002, kGpc = 0x8003;
  constexpr uint32_t kGpcBytes = 0x80000UL;                // 8 bancos ($C0 a $C7) de 64 KB
  constexpr uint32_t kSufamiBank = 0x8000UL;               // `readLoRomBanks`: bancos LoROM de 32 KB

  inline bool isAcc(uint16_t field) { return (field & kFlag) != 0; }
  inline bool valid(uint16_t field) { return field == kSufamiA || field == kSufamiB || field == kGpc; }
  inline bool isSufami(uint16_t field) { return field == kSufamiA || field == kSufamiB; }
  inline bool sufamiSlotB(uint16_t field) { return field == kSufamiB; }

  /// Primeiro banco do slot no espaço do adaptador (o `readSlot` do OSCR): slot A em 32, slot B em 64. O cartucho tem 16 bancos de 32 KB (512 KB) se há cabeçalho em `início + 16`, senão 32 (1 MB).
  inline uint16_t sufamiStartBank(bool slotB) { return slotB ? 64 : 32; }
  inline uint32_t sufamiBytes(bool headerAtPlus16) { return (headerAtPlus16 ? 16UL : 32UL) * kSufamiBank; }
} }  // namespace oscr::snesacc
