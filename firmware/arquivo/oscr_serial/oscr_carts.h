// SPDX-License-Identifier: GPL-3.0-or-later
// Backend dos cartuchos reais: SNES (LoROM/HiROM), NES/Famicom (mapper 0), Mega Drive, GBA.
// A lógica (cabeçalhos, tamanhos, mapeamento de endereços) é testada no PC com cartuchos simulados.
// Limites desta versão estão em docs/referencia/protocolo.md e docs/referencia/uso.md.
#pragma once
#include "oscr_bus.h"
#include "oscr_session.h"

namespace oscr {

class CartBackend : public Backend {
 public:
  CartBackend(SnesBus* snes, NesBus* nes, MdBus* md, GbaBus* gba, GbBus* gb = nullptr) : snes_(snes), nes_(nes), md_(md), gba_(gba), gb_(gb) {}

  uint8_t flags() override { return (snes_ && snes_->clocks_available()) ? 2 : 0; }   // bit1: Si5351 respondendo
  uint16_t systems() override;
  bool supports(uint8_t sys) override;
  void detect(uint8_t sys, DetectInfo& out) override;
  bool open_read(uint8_t sys, uint8_t kind, uint32_t& size, uint16_t& err) override;
  bool read(uint8_t sys, uint8_t kind, uint32_t off, uint8_t* buf, uint16_t len) override;
  void close_read() override { release(); clear_options(); }
  void set_options(uint16_t mapper, uint16_t prg_kb, uint16_t chr_kb) override { opt_mapper_ = mapper; opt_prg_ = prg_kb; opt_chr_ = chr_kb; }
  bool write_begin(uint8_t sys, uint32_t size, uint16_t& err) override;
  bool write_block(uint32_t off, const uint8_t* buf, uint16_t len) override;
  bool write_commit() override { bool ok = sa1_finish(); release(); clear_options(); return ok; }
  void write_abort() override { release(); clear_options(); }

 private:
  struct Cart {
    uint8_t status = 1;          // como DetectInfo.status
    uint32_t rom = 0, save = 0;
    uint8_t save_type = 0;
    char name[33] = {0};
    bool hirom = false;          // SNES
    bool sfx = false;            // SNES SuperFX (chips $13-$15, $1A): ROM como LoROM; BW-RAM em $70 com bancos de 64 KB
    bool sdd1 = false;           // SNES S-DD1 (chips $43/$45): ROM em janelas de 1 MB pelo registrador $4807
    bool spc7110 = false;        // SNES SPC7110 (mapa $3A, chips $F5/$F9): ROM em 4 regiões pelos registradores $4833/$4834
    uint8_t cx4 = 0;             // SNES Cx4 (chips $F3): 2 = X2 (12 Mbit), 3 = X3 (16 Mbit); mapeamento em $7F52
    bool sa1 = false;            // SNES SA-1 (mapa $23, chips $34/$35): precisa do Si5351 e do CIC
    bool exhirom = false;        // SNES ExHiROM (mapa $25/$35): ROM de até 8 MB, cabeçalho em $40FFC0
    uint32_t prg = 0, chr = 0;   // NES (bytes)
    bool ssf = false;            // Mega Drive: mapper SSF2 (ROM acima de 4 MB)
    uint8_t md_save = 0;         // Mega Drive: 0 nenhum, 1 bytes ímpares, 2 bytes pares, 3 ambos
    uint32_t md_base = 0;        // endereço em palavras do início da SRAM
    uint8_t md_eep = 0;          // Mega Drive: tipo da EEPROM serial (1 Acclaim 1, 2 Acclaim 2, 3 Capcom/Sega, 4 EA, 5 Codemasters)
    uint16_t md_eep_size = 0;    // bytes
    uint16_t gb_type = 0;        // Game Boy: byte $147 do cabeçalho (+$100 se MBC1M)
    uint8_t gb_shift = 13;       // Game Boy: log2 dos bytes de cada banco de RAM (9, 11 ou 13)
    bool gba_skip = false;       // GBA: e-Reader, não grava os últimos 128 bytes de cada banco de 64 KB
    uint8_t gba_type = 0;        // GBA, tipo de save pedido: 1 EEPROM 4K, 2 EEPROM 64K, 3 SRAM, 4 Flash 64K, 5 Flash 128K
  };
  SnesBus* snes_; NesBus* nes_; MdBus* md_; GbaBus* gba_; GbBus* gb_;
  Cart c_;
  void clear_options() { opt_mapper_ = opt_prg_ = opt_chr_ = 0; }
  int16_t sdd1_cur_ = -1, sdd1_init_ = 0;   // S-DD1: janela de 1 MB mapeada ($4807) e valor original
  int8_t spc_region_ = -1;                  // SPC7110: região de ROM mapeada
  bool spc_touched_ = false, spc_sram_ = false;
  uint8_t cx4_orig_ = 0; bool cx4_touched_ = false;   // Cx4: valor original de $7F52
  bool gb_ram_on_ = false;       // Game Boy: RAM habilitada ($0000 = $0A)
  void gb_ram_enable();
  bool mbc6_flash_ = false; int16_t cur_flash_ = -1;   // MBC6: a Flash do save está mapeada sobre a ROM; banco de 8 KB atual
  bool mmm_mapped_ = false; int8_t mmm_chunk_ = -1;    // MMM01: o cartucho saiu do menu (precisa de reset para voltar); bloco de 512 KB mapeado
  void mmm01_map(uint8_t chunk);
  void mbc6_mode(bool flash);
  uint8_t mbc6_save_byte(uint32_t off);
  int16_t mbc7_wa_ = -1; uint16_t mbc7_w_ = 0;   // MBC7: última palavra lida da EEPROM
  void mbc7_inst(uint8_t op, uint8_t addr, uint16_t data);
  bool mbc7_read_word(uint8_t a, uint16_t& w);
  bool mbc7_write_word(uint8_t a, uint16_t w);
  bool mbc7_wait_ready();
  bool mbc7_write_range(uint32_t off, const uint8_t* buf, uint16_t len);
  void gb_select(int16_t bank);  // seleciona o banco de ROM em $4000-$7FFF conforme o mapper
  uint16_t gb_ram_addr(uint32_t off);   // endereço em $A000+ de um byte do save; troca o banco de RAM
  bool clocks_on_ = false;       // SNES: Si5351 e CIC ligados (SA-1)
  void snes_clocks_boot();       // clocks lentos + CIC, e lê 1 KB do banco $C0 ("primeira leitura" do OSCR)
  uint8_t sa1_first_[16] = {0};  // SA-1: 16 primeiros bytes do save, regravados no fim
  int16_t sa1_blk_ = -1;         // SA-1: bloco de 8 KB da BW-RAM mapeado em $6000
  bool sa1_finish();             // SA-1: regrava os 16 primeiros bytes, confere, desliga o clock do CPU
  uint8_t active_ = 0;           // sistema com barramento aberto (0 = nenhum)
  uint16_t opt_mapper_ = 0, opt_prg_ = 0, opt_chr_ = 0;   // opções do NES/Famicom (set_options)
  int16_t gba_bank_ = 0;                                  // GBA Flash 128 KB: banco selecionado
  int32_t gba_eep_blk_ = -1;                              // GBA EEPROM: bloco de 8 bytes em cache
  uint8_t gba_eep_[8] = {0};
  void gba_flash_bank(uint8_t bank);
  bool gba_atmel_ = false;                                // Flash Atmel de 64 KB: grava páginas de 128 bytes, sem apagar
  uint8_t wbuf_[128];                                     // acumula 8 bytes (EEPROM) ou 128 (Atmel) até fechar a unidade
  void gba_cmd(uint8_t c);                                // AA@5555, 55@2AAA, c@5555
  uint16_t gba_flash_id();
  bool gba_flash_prepare();                               // identifica o chip, apaga e confere
  bool gba_blank_check();
  bool gba_flash_program(uint32_t off, uint8_t v);
  bool gba_write(uint32_t off, const uint8_t* buf, uint16_t len);
  uint8_t gba_save_byte(uint32_t i);
  bool md_sram_on_ = false;
  uint8_t md_hi_ = 0;                                     // byte alto pendente (SRAM "ambos")
  int16_t md_bank_ = -1;                                  // banco SSF2 já selecionado na janela 1
  void md_sram(bool on);
  // EEPROM serial do Mega Drive (leitura)
  void eep_state(uint8_t st);                             // bit 0 = SDA, bit 1 = SCL
  void eep_run(const char* gen, const char* t2);          // sequência de estados; tipo 2 usa escritas separadas de SDA e SCL
  bool eep_status();                                      // ACK
  void eep_set(bool one);
  bool eep_sda_in();
  void eep_start(); void eep_finish(); void eep_stop();
  bool eep_set_address(uint16_t address);
  bool eep_device(uint16_t page, bool write_mode);
  bool md_eep_read(uint16_t address, uint8_t& out);
  bool md_eep_write(uint16_t address, uint8_t value);
  uint8_t md_save_byte(uint32_t i);
  void md_save_set(uint32_t i, uint8_t v);
  uint16_t mapper_ = 0;                                   // mapper em uso na leitura
  int16_t cur_prg_ = -1, cur_chr_ = -1;                   // banco já selecionado (-1 = nenhum)
  bool nes_ram_on_ = false;
  void nes_ram(bool on);                                  // liga/desliga a PRG-RAM com bateria (MMC1, MMC3)
  void nes_setup_mapper();
  uint16_t nes_ram_addr(uint32_t off);                    // endereço em $6000-$7FFF de um byte do save; troca o banco de RAM do MMC1 de 16/32 KB
  void nes_reg(uint8_t value, uint16_t first_addr, uint16_t scan);  // escreve evitando conflito de barramento
  void mmc1_write(uint16_t addr, uint8_t v);
  void mmc3_write(uint8_t reg, uint8_t v);
  uint8_t nes_prg_byte(uint32_t o);
  uint8_t nes_chr_byte(uint32_t o);

  bool probe(uint8_t sys, Cart& out, bool for_save = false);   // abre o barramento e lê o cabeçalho
  bool probe_snes(uint8_t sys, Cart& o, bool for_save);   // um por sistema, em oscr_carts_<sistema>.cpp
  bool probe_nes(uint8_t sys, Cart& o, bool for_save);
  bool probe_md(uint8_t sys, Cart& o, bool for_save);
  bool probe_gba(uint8_t sys, Cart& o, bool for_save);
  bool probe_gb(uint8_t sys, Cart& o, bool for_save);
  uint8_t snes_byte(uint32_t off);   // byte da ROM no deslocamento `off` (mapa de cada sistema)
  uint8_t nes_byte(uint32_t off);
  uint8_t md_byte(uint32_t off);
  uint8_t gba_byte(uint32_t off);
  uint8_t gb_byte(uint32_t off);
  void acquire(uint8_t sys);
  void release();
  uint8_t snes_save_byte_read(uint32_t i);
  void snes_save_addr(uint32_t i, uint8_t& bank, uint16_t& addr) const;
  uint8_t byte_at(uint8_t sys, uint32_t off);   // ROM, leitura de 1 byte (cabeçalhos e dados)
  bool all_same(const uint8_t* p, uint8_t n) const;
};

}  // namespace oscr
