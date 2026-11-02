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
  void close_read() override { release(); clear_options(); }
  void set_options(uint16_t mapper, uint16_t prg_kb, uint16_t chr_kb) override { opt_mapper_ = mapper; opt_prg_ = prg_kb; opt_chr_ = chr_kb; }
  bool write_begin(uint8_t sys, uint32_t size, uint16_t& err) override;
  bool write_block(uint32_t off, const uint8_t* buf, uint16_t len) override;
  bool write_commit() override { release(); clear_options(); return true; }
  void write_abort() override { release(); clear_options(); }

 private:
  struct Cart {
    uint8_t status = 1;          // como DetectInfo.status
    uint32_t rom = 0, save = 0;
    uint8_t save_type = 0;
    char name[33] = {0};
    bool hirom = false;          // SNES
    uint32_t prg = 0, chr = 0;   // NES (bytes)
    bool ssf = false;            // Mega Drive: mapper SSF2 (ROM acima de 4 MB)
    uint8_t md_save = 0;         // Mega Drive: 0 nenhum, 1 bytes ímpares, 2 bytes pares, 3 ambos
    uint32_t md_base = 0;        // endereço em palavras do início da SRAM
    uint8_t gba_type = 0;        // GBA, tipo de save pedido: 1 EEPROM 4K, 2 EEPROM 64K, 3 SRAM, 4 Flash 64K, 5 Flash 128K
  };
  SnesBus* snes_; NesBus* nes_; MdBus* md_; GbaBus* gba_;
  Cart c_;
  void clear_options() { opt_mapper_ = opt_prg_ = opt_chr_ = 0; }
  uint8_t active_ = 0;           // sistema com barramento aberto (0 = nenhum)
  uint16_t opt_mapper_ = 0, opt_prg_ = 0, opt_chr_ = 0;   // opções do NES/Famicom (set_options)
  int16_t gba_bank_ = 0;                                  // GBA Flash 128 KB: banco selecionado
  int32_t gba_eep_blk_ = -1;                              // GBA EEPROM: bloco de 8 bytes em cache
  uint8_t gba_eep_[8] = {0};
  void gba_flash_bank(uint8_t bank);
  uint8_t gba_save_byte(uint32_t i);
  bool md_sram_on_ = false;
  uint8_t md_hi_ = 0;                                     // byte alto pendente (SRAM "ambos")
  int16_t md_bank_ = -1;                                  // banco SSF2 já selecionado na janela 1
  void md_sram(bool on);
  uint8_t md_save_byte(uint32_t i);
  void md_save_set(uint32_t i, uint8_t v);
  uint16_t mapper_ = 0;                                   // mapper em uso na leitura
  int16_t cur_prg_ = -1, cur_chr_ = -1;                   // banco já selecionado (-1 = nenhum)
  bool nes_ram_on_ = false;
  void nes_ram(bool on);                                  // liga/desliga a PRG-RAM com bateria (MMC1, MMC3)
  void nes_setup_mapper();
  void nes_reg(uint8_t value, uint16_t first_addr, uint16_t scan);  // escreve evitando conflito de barramento
  void mmc1_write(uint16_t addr, uint8_t v);
  void mmc3_write(uint8_t reg, uint8_t v);
  uint8_t nes_prg_byte(uint32_t o);
  uint8_t nes_chr_byte(uint32_t o);

  bool probe(uint8_t sys, Cart& out, bool for_save = false);   // abre o barramento e lê o cabeçalho
  void acquire(uint8_t sys);
  void release();
  uint8_t snes_save_byte_read(uint32_t i);
  void snes_save_addr(uint32_t i, uint8_t& bank, uint16_t& addr) const;
  uint8_t byte_at(uint8_t sys, uint32_t off);   // ROM, leitura de 1 byte (cabeçalhos e dados)
  bool all_same(const uint8_t* p, uint8_t n) const;
};

}  // namespace oscr
