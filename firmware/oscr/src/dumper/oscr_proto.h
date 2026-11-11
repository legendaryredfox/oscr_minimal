// SPDX-License-Identifier: GPL-3.0-or-later
// Camada de protocolo serial v1 (docs/referencia/protocolo.md). Sem dependência do Arduino:
// compila no AVR e no PC (testes). C++11.
#pragma once
#include <stddef.h>
#include <stdint.h>

#ifndef OSCR_MAX_PAYLOAD
# if defined(ARDUINO) && defined(__AVR__)
#  define OSCR_MAX_PAYLOAD 520   // AVR: poupa RAM (bloco padrão de 512 + 4 de offset cabe)
# else
#  define OSCR_MAX_PAYLOAD 1024  // limite do protocolo
# endif
#endif

namespace oscr {

constexpr uint8_t  PROTO_VERSION = 1;
constexpr uint16_t DEFAULT_BLOCK = 512;
constexpr uint8_t  MAGIC0 = 0xA5, MAGIC1 = 0x5A;

enum : uint8_t {  // host -> dispositivo
  T_INFO = 0x01, T_DETECT = 0x02, T_DUMP_ROM = 0x03, T_READ_SAVE = 0x04, T_WRITE_SAVE = 0x05,
  T_ACK = 0x06, T_NAK = 0x07, T_ABORT = 0x08, T_H_DATA = 0x09, T_H_END = 0x0A, T_WRITE_ROM = 0x0B, T_ERASE = 0x0C, T_VOLT = 0x0D, T_SELFTEST = 0x0E,
  // dispositivo -> host
  T_INFO_RESP = 0x81, T_DETECT_RESP = 0x82, T_BEGIN = 0x83, T_DATA = 0x84, T_END = 0x85,
  T_D_ACK = 0x86, T_ERRO = 0x87, T_PROGRESSO = 0x88, T_VOLT_RESP = 0x89, T_SELFTEST_RESP = 0x8A,
};

enum : uint8_t { KIND_ROM = 1, KIND_SAVE = 2 };

// Achados do SELFTEST (P-12): 1 pino em curto com GND (a), 2 curto entre os pinos a e b, 3 sem o pull-up de 1 kΩ no D7, 4 sem Si5351. Pinos na numeração do Arduino (54 = A0).
enum : uint8_t { ST_GND = 1, ST_PAIR = 2, ST_NO_PULLUP = 3, ST_NO_CLOCKGEN = 4 };

enum : uint8_t { VOLT_STATUS = 0, VOLT_3V3 = 1, VOLT_5V = 2 };   // ação do VOLT: consulta ou escolhe a tensão dos slots (seletor 3,3 V/5 V, D138; docs/referencia/protocolo.md)

enum : uint16_t {  // códigos de ERRO
  E_COMANDO = 1, E_SISTEMA = 2, E_SEM_CARTUCHO = 3, E_ARGUMENTO = 4, E_REENVIOS = 5,
  E_CRC = 6, E_CARTUCHO_IO = 7, E_OCUPADO = 8, E_ABORTADO = 9, E_SEM_SAVE = 10, E_FLASH = 11,   // 12 reservado (era E_DESLIGADO, retirado em D139)

};

enum : uint8_t { SYS_SNES = 1, SYS_NES = 2, SYS_FAMICOM = 3, SYS_MD = 4, SYS_GBA = 5, SYS_GB = 6, SYS_FLASH = 7, SYS_SMS = 8, SYS_GG = 9, SYS_SG1000 = 10, SYS_MOCK = 255 };

// CRC32 IEEE (igual ao zlib). `start` é o CRC acumulado anterior (0 no começo).
uint32_t crc32_update(uint32_t start, const uint8_t* data, size_t len);

// Codifica um quadro em `out` (precisa de 10 + len bytes). Devolve o tamanho total.
size_t encode_frame(uint8_t* out, uint8_t type, uint8_t seq, const uint8_t* payload, uint16_t len);

inline void put_u16(uint8_t* p, uint16_t v) { p[0] = v & 0xFF; p[1] = v >> 8; }
inline void put_u32(uint8_t* p, uint32_t v) { for (int i = 0; i < 4; i++) p[i] = (v >> (8 * i)) & 0xFF; }
inline uint16_t get_u16(const uint8_t* p) { return p[0] | (uint16_t(p[1]) << 8); }
inline uint32_t get_u32(const uint8_t* p) { return p[0] | (uint32_t(p[1]) << 8) | (uint32_t(p[2]) << 16) | (uint32_t(p[3]) << 24); }

// Decodificador byte a byte. O payload fica em `buf` (capacidade `cap`).
class Decoder {
 public:
  Decoder(uint8_t* buf, uint16_t cap) : buf_(buf), cap_(cap) { reset(); }
  void reset() { st_ = S_M0; }
  bool idle() const { return st_ == S_M0; }
  // true quando um quadro válido está pronto (type, seq, len, payload()).
  bool push(uint8_t b);
  const uint8_t* payload() const { return buf_; }
  uint8_t type = 0, seq = 0;
  uint16_t len = 0;
  uint32_t bad = 0;  // quadros descartados (CRC ruim, tamanho inválido)

 private:
  enum State : uint8_t { S_M0, S_M1, S_TYPE, S_SEQ, S_L0, S_L1, S_PAY, S_C0, S_C1, S_C2, S_C3 };
  uint8_t* buf_;
  uint16_t cap_, got_ = 0;
  State st_;
  uint32_t crc_ = 0, rx_ = 0;
  void fail() { bad++; st_ = S_M0; }
};

}  // namespace oscr
