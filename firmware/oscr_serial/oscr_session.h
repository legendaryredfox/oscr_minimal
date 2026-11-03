// SPDX-License-Identifier: GPL-3.0-or-later
// Máquina de estados do dispositivo (lado do firmware) para o protocolo v1.
// Independente de Arduino: a E/S e os dados vêm de `Io` e `Backend`.
#pragma once
#include "oscr_proto.h"

namespace oscr {

struct Io {
  void* ctx;
  int (*read_byte)(void* ctx, uint32_t timeout_ms);          // -1 se esgotar o tempo
  void (*write)(void* ctx, const uint8_t* data, size_t len);
  uint32_t (*now_ms)(void* ctx);
};

struct DetectInfo {
  uint8_t status = 1;       // 0 detectado, 1 nenhum, 2 não suportado, 3 erro de hardware, 4 cabeçalho inválido (há dados, checksum errado)
  uint32_t rom_size = 0, save_size = 0;
  uint8_t save_type = 0;
  char name[33] = {0};      // ASCII, até 32 caracteres
};

// Fornece os dados. No firmware real, cada sistema (SNES, NES, MD, GBA) implementa isto;
// `MockBackend` gera um padrão conhecido sem cartucho.
class Backend {
 public:
  virtual ~Backend() {}
  virtual uint8_t flags() = 0;       // bit0 MOCK, bit1 Si5351, bit2 PIC
  virtual uint16_t systems() = 0;    // máscara: bit = id do sistema (1..6)
  virtual bool supports(uint8_t system) = 0;
  virtual void detect(uint8_t system, DetectInfo& out) = 0;
  // Abre a leitura de ROM/save; devolve false e `err` se não der.
  virtual bool open_read(uint8_t system, uint8_t kind, uint32_t& size, uint16_t& err) = 0;
  // Lê `len` bytes sequenciais a partir de `off` (as chamadas são sempre crescentes).
  virtual bool read(uint8_t system, uint8_t kind, uint32_t off, uint8_t* buf, uint16_t len) = 0;
  virtual void close_read() {}
  // Opções opcionais de DUMP_ROM (NES/Famicom): mapper e tamanhos em KB. 0 = automático.
  virtual void set_options(uint16_t mapper, uint16_t prg_kb, uint16_t chr_kb) { (void)mapper; (void)prg_kb; (void)chr_kb; }
  virtual bool write_begin(uint8_t system, uint32_t size, uint16_t& err) = 0;
  virtual bool write_block(uint32_t off, const uint8_t* buf, uint16_t len) = 0;
  virtual bool write_commit() = 0;   // chamado só depois do CRC32 conferir
  virtual void write_abort() {}
};

class MockBackend : public Backend {
 public:
  static constexpr uint32_t kRomSize = 32768, kSaveSize = 8192;
  uint8_t flags() override { return 1; }
  uint16_t systems() override { return 0; }
  bool supports(uint8_t s) override { return s == SYS_MOCK || s == 0; }
  void detect(uint8_t s, DetectInfo& o) override;
  bool open_read(uint8_t s, uint8_t kind, uint32_t& size, uint16_t& err) override;
  bool read(uint8_t s, uint8_t kind, uint32_t off, uint8_t* buf, uint16_t len) override;
  bool write_begin(uint8_t s, uint32_t size, uint16_t& err) override;
  bool write_block(uint32_t, const uint8_t*, uint16_t) override { return true; }
  bool write_commit() override { return true; }
  static uint8_t rom_byte(uint32_t i) { return uint8_t(i * 7 + (i >> 8)); }
  static uint8_t save_byte(uint32_t i) { return uint8_t(i * 3 + 1); }
};

class Session {
 public:
  Session(Io io, Backend& be, uint8_t* rx, uint16_t rx_cap, uint8_t* tx, uint16_t tx_cap)
      : io_(io), be_(be), dec_(rx, rx_cap), tx_(tx), tx_cap_(tx_cap) {}
  // Chame no loop(): consome os bytes disponíveis e atende no máximo um comando completo.
  void poll();
  uint32_t bad_frames() const { return dec_.bad; }

 private:
  Io io_;
  Backend& be_;
  Decoder dec_;
  uint8_t* tx_;
  uint16_t tx_cap_;
  uint32_t last_byte_ms_ = 0;

  bool next_frame(uint32_t timeout_ms);     // espera um quadro válido (true) ou o tempo esgotar
  void send(uint8_t type, uint8_t seq, const uint8_t* payload, uint16_t len);
  void send_error(uint8_t seq, uint16_t code, const char* text = "");
  void send_offset(uint8_t type, uint8_t seq, uint32_t off);
  void handle();
  void do_info(uint8_t seq);
  void do_detect(uint8_t seq, uint8_t sys);
  void do_read(uint8_t seq, uint8_t type, uint8_t sys, uint16_t block, const uint8_t* opt, uint16_t opt_len);
  void do_write(uint8_t seq, const uint8_t* p, uint16_t len);
  // 1 = ACK(off), 0 = NAK/timeout, -1 = ABORT
  int wait_ack(uint8_t seq, uint32_t off, uint32_t timeout_ms);
  bool in_tx_ok(uint16_t payload) const { return size_t(payload) + 10 <= tx_cap_; }
};

}  // namespace oscr
