// SPDX-License-Identifier: GPL-3.0-or-later
// Nintendo 64 (D158): slot N64 da placa `n64` e da `completa` (3,3 V). As regras que o fork acrescenta em volta do núcleo N64.cpp do OSCR.
// O núcleo faz a leitura (cartOn, idCart, readRom, readSave, writeSave); aqui só ficam a classificação do cabeçalho, os tamanhos de save e do nome do DETECT.
// Código puro (sem hardware): testado no PC em pc-tests/test_n64.cpp e espelhado no host (host/oscr_host/n64.py).
// O OSCR identifica o jogo por uma base de dados no cartão SD (CRC1 do cabeçalho -> tamanho e tipo de save); sem SD, o PC faz essa consulta
// (database/oscr/json/n64.json) e manda o tamanho (`prg_kb` = MB) e o tipo de save (`mapper`) nos comandos.
#pragma once
#include <stdint.h>
#include <string.h>

namespace oscr { namespace n64
{
  /// Resultado de DETECT/prepare (os mesmos números do campo `status` do protocolo).
  enum : uint8_t
  {
    kOk = 0,              ///< cabeçalho z64 ($80 $37 $12 $40) lido
    kNoCart = 1,          ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
    kBadHeader = 4,       ///< há dados mas não é um cabeçalho de N64 (contato sujo, cartucho de outro sistema, Gameshark)
  };

  constexpr uint8_t kMinRomMb = 1, kMaxRomMb = 64;      ///< o menu do OSCR vai a 128 MB; o campo `prg_kb` do protocolo guarda MB e o maior jogo conhecido tem 64 MB

  /// Tipos de save do OSCR (campo `mapper` do protocolo): 0 nenhum, 1 SRAM de 32 KB, 2 SRAM de 96 KB (768 Kbit), 4 Flash de 128 KB (FlashRAM), 5 EEPROM de 4 Kbit, 6 EEPROM de 16 Kbit.
  enum SaveType : uint8_t { kNone = 0, kSram = 1, kSram768 = 2, kFlash = 4, kEeprom4k = 5, kEeprom16k = 6 };

  inline bool saveTypeValid(uint16_t t) { return t == kNone || t == kSram || t == kSram768 || t == kFlash || t == kEeprom4k || t == kEeprom16k; }

  /// Bytes do arquivo de save de cada tipo (o que `readSave` escreve e `writeSave` lê).
  inline uint32_t saveBytes(uint8_t t)
  {
    switch (t)
    {
    case kSram: return 32768UL;
    case kSram768: return 98304UL;
    case kFlash: return 131072UL;
    case kEeprom4k: return 512UL;          // 64 páginas de 8 bytes
    case kEeprom16k: return 2048UL;        // 256 páginas de 8 bytes
    default: return 0;
    }
  }

  /// Páginas de EEPROM (`eepPages` do núcleo): 64 e 256; 0 nos outros tipos.
  inline uint16_t eepromPages(uint8_t t) { return t == kEeprom4k ? 64 : t == kEeprom16k ? 256 : 0; }

  inline bool isEeprom(uint8_t t) { return t == kEeprom4k || t == kEeprom16k; }

  inline bool romMbValid(uint16_t mb) { return mb >= kMinRomMb && mb <= kMaxRomMb; }

  inline bool allSame(uint8_t const * p, uint8_t n)
  {
    for (uint8_t i = 1; i < n; i++) if (p[i] != p[0]) return false;
    return true;
  }

  /**
   * Classifica os 64 primeiros bytes da ROM (ordem z64, big-endian, como a ROM aparece no barramento do cartucho). Slot vazio = um valor só, $00 ou $FF.
   */
  inline uint8_t classify(uint8_t const * hdr, uint8_t len)
  {
    if (len >= 4 && hdr[0] == 0x80 && hdr[1] == 0x37 && hdr[2] == 0x12 && hdr[3] == 0x40) return kOk;
    if (allSame(hdr, len) && (hdr[0] == 0x00 || hdr[0] == 0xFF)) return kNoCart;
    return kBadHeader;
  }

  /**
   * Nome do DETECT (cabe em 32 bytes com o zero final): "CCCCCCCC IIII TÍTULO", onde CCCCCCCC é o CRC1 do cabeçalho (bytes $10 a $13) em hexadecimal,
   * IIII o código do jogo (bytes $3B a $3E) e TÍTULO o nome do cabeçalho (até 20 caracteres; o que passar de 31 é cortado). O PC procura o jogo na
   * base de dados pelo CRC1 e usa o TÍTULO só se não achar.
   */
  inline void formatName(char * out, size_t outSize, uint32_t crc1, char const * id4, char const * title)
  {
    static char const hex[] = "0123456789ABCDEF";
    size_t n = 0;
    auto put = [&](char c) { if (n + 1 < outSize) out[n++] = c; };
    for (int s = 28; s >= 0; s -= 4) put(hex[(crc1 >> s) & 15]);
    put(' ');
    for (int i = 0; i < 4; i++) put(id4[i] >= 0x20 && id4[i] < 0x7F ? id4[i] : '?');
    put(' ');
    for (size_t i = 0; title[i]; i++) put(title[i]);
    if (outSize) out[n] = 0;
  }
} }  // namespace oscr::n64
