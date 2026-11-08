// SPDX-License-Identifier: GPL-3.0-or-later
// Família Sega de 8 bits (D137): Master System / Mark III (slot direto da placa megadrive_sms ou adaptador), Game Gear e SG-1000 (adaptadores no slot Mega Drive).
// As regras que o fork acrescenta em volta do núcleo SMS.cpp do OSCR.
// O núcleo faz a leitura (cartOn, getCartInfo, readROM, readSRAM, writeSRAM); aqui só ficam a classificação do cabeçalho
// e a conferência do tamanho informado pelo PC. Código puro (sem hardware): testado no PC em pc-tests/test_sms.cpp e espelhado no simulador do host.
#pragma once
#include <stdint.h>
#include <string.h>

namespace oscr { namespace sms
{
  /// Resultado de DETECT/prepare (os mesmos números do campo `status` do protocolo).
  enum : uint8_t
  {
    kOk = 0,              ///< cabeçalho "TMR SEGA" lido: nome e tamanho valem
    kNoCart = 1,          ///< slot vazio: o barramento lê sempre o mesmo valor ($00 ou $FF)
    kNoHeader = 4,        ///< há dados mas não há cabeçalho (Mark III, SG-1000, jogo antigo): o tamanho vem do PC
  };

  constexpr uint32_t kSramBytes = 32768;       ///< `readSRAM`/`writeSRAM` do OSCR sempre tratam 32 KB (8 KB aparecem espelhados)
  constexpr uint16_t kMaxRomKb = 1024;

  /// Console do protocolo (SYS_SMS, SYS_GG, SYS_SG1000).
  enum Console : uint8_t { kSms = 0, kGg = 1, kSg = 2 };

  /// Valores do `SMSMode` do núcleo (SMS.cpp): a ordem do enum é a do OSCR.
  enum Mode : uint8_t { kSmsRetrode = 0, kGgRetrode = 1, kSmsRetron = 2, kGgRetron = 3, kSmsRaphnet = 4, kSg1000Raphnet = 5, kBadMode = 0xFF };

  /**
   * Adaptador pedido pelo PC (campo `mapper` do protocolo) -> modo do núcleo. SMS: 0 slot direto da placa ou adaptador Raphnet, 1 Retrode, 2 Retron 3in1.
   * Game Gear: 0 Retron 3in1, 1 Retrode. SG-1000: 0 adaptador Raphnet. Retrode, Retron e Raphnet ligam no slot Mega Drive.
   */
  inline uint8_t mode(uint8_t console, uint16_t option)
  {
    if (console == kSms) return option == 0 ? kSmsRaphnet : option == 1 ? kSmsRetrode : option == 2 ? kSmsRetron : kBadMode;
    if (console == kGg) return option == 0 ? kGgRetron : option == 1 ? kGgRetrode : kBadMode;
    if (console == kSg) return option == 0 ? kSg1000Raphnet : kBadMode;
    return kBadMode;
  }

  /// Tamanhos de ROM dos menus "Set ROM size" do OSCR. SMS e Game Gear: 32, 64, 128, 256, 512 KB e 1 MB. SG-1000: 8, 16, 24 e 32 KB. 0 = automático (pelo cabeçalho).
  inline bool sizeKbValid(uint8_t console, uint16_t kb)
  {
    if (kb == 0) return true;
    if (console == kSg) return kb == 8 || kb == 16 || kb == 24 || kb == 32;
    return kb == 32 || kb == 64 || kb == 128 || kb == 256 || kb == 512 || kb == 1024;
  }

  inline bool allSame(uint8_t const * p, uint8_t n)
  {
    for (uint8_t i = 1; i < n; i++) if (p[i] != p[0]) return false;
    return true;
  }

  /**
   * Classifica o que o slot devolveu. `name` são os 8 bytes lidos em $7FF0 ("TMR SEGA" nos jogos com cabeçalho) e `sample` 32 bytes
   * lidos em outro trecho da ROM (por exemplo, $0000). Slot vazio = os dois blocos com um valor só, $00 ou $FF (é a mesma heurística do NES).
   */
  inline uint8_t classify(uint8_t const * name, uint8_t const * sample, uint8_t sampleLen, bool fantasyZone)
  {
    if (allSame(name, 8) && allSame(sample, sampleLen) && (name[0] == 0xFF || name[0] == 0x00) && sample[0] == name[0]) return kNoCart;
    if (fantasyZone || memcmp(name, "TMR SEGA", 8) == 0) return kOk;
    return kNoHeader;
  }

  /// Tamanho final da ROM em bytes: o informado pelo PC vale sempre; sem ele só o cabeçalho serve (0 = precisa de `kb`).
  inline uint32_t romBytes(uint8_t status, uint32_t coreBytes, uint16_t kb)
  {
    if (kb) return uint32_t(kb) * 1024UL;
    return status == kOk ? coreBytes : 0;
  }
} }  // namespace oscr::sms
