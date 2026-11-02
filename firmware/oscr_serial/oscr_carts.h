// SPDX-License-Identifier: GPL-3.0-or-later
// Backend dos cartuchos reais: SNES (LoROM/HiROM), NES/Famicom (mapper 0), Mega Drive, GBA.
// A lógica (cabeçalhos, tamanhos, mapeamento de endereços) é testada no PC com cartuchos simulados.
// Limites desta versão estão em docs/protocolo.md e docs/uso.md.
#pragma once
#include "oscr_bus.h"
#include "oscr_session.h"

namespace oscr {

class CartBackend : public Backend {
 public:
  CartBackend(SnesBus* snes, NesBus* nes, MdBus* md, GbaBus* gba) : snes_(snes), nes_(nes), md_(md), gba_(gba) {}

  uint8_t flags() override { return 0; }
  uint16_t systems() override;
  bool supports(uint8_t sys) override;
  void detect(uint8_t sys, DetectInfo& out) override;
  bool open_read(uint8_t sys, uint8_t kind, uint32_t& size, uint16_t& err) override;
  bool read(uint8_t sys, uint8_t kind, uint32_t off, uint8_t* buf, uint16_t len) override;
  void close_read() override { release(); }
  bool write_begin(uint8_t sys, uint32_t size, uint16_t& err) override;
  bool write_block(uint32_t off, const uint8_t* buf, uint16_t len) override;
  bool write_commit() override { release(); return true; }
  void write_abort() override { release(); }

 private:
  struct Cart {
    uint8_t status = 1;          // como DetectInfo.status
    uint32_t rom = 0, save = 0;
    uint8_t save_type = 0;
    char name[33] = {0};
    bool hirom = false;          // SNES
    uint32_t prg = 0, chr = 0;   // NES (bytes)
  };
  SnesBus* snes_; NesBus* nes_; MdBus* md_; GbaBus* gba_;
  Cart c_;
  uint8_t active_ = 0;           // sistema com barramento aberto (0 = nenhum)

  bool probe(uint8_t sys, Cart& out);   // abre o barramento e lê o cabeçalho
  void acquire(uint8_t sys);
  void release();
  uint8_t snes_save_byte_read(uint32_t i);
  void snes_save_addr(uint32_t i, uint8_t& bank, uint16_t& addr) const;
  uint8_t byte_at(uint8_t sys, uint32_t off);   // ROM, leitura de 1 byte (cabeçalhos e dados)
  bool all_same(const uint8_t* p, uint8_t n) const;
};

}  // namespace oscr
