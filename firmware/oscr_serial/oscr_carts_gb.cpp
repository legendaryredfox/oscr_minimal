// SPDX-License-Identifier: GPL-3.0-or-later
// Game Boy / Game Boy Color: cabeçalho, ROM por mapper e SRAM.
#include "oscr_carts_internal.h"

namespace oscr {

bool CartBackend::probe_gb(uint8_t sys, Cart& o, bool for_save) {
  (void)sys; (void)for_save;
  uint8_t h[48]; (void)h;
    uint8_t g[80];
    bool ok = false;
    gb_->write(0x6000, 0); gb_->write(0x4000, 0);                       // MBC1 em modo 1 com banco superior != 0 (operação anterior) esconderia o banco 0 e o cabeçalho
    for (uint8_t pass = 0; pass < 2 && !ok; pass++) {                  // checksum do cabeçalho; relê uma vez se não bater (como o OSCR)
      for (uint8_t i = 0; i < 80; i++) g[i] = gb_->read(uint16_t(0x100 + i));
      uint8_t sum = 0;
      for (uint8_t i = 0x34; i < 0x4D; i++) sum = uint8_t(sum - g[i] - 1);
      ok = (sum == g[0x4D]) && !all_same(g, 80);
    }
    if (!ok) { o.status = all_same(g, 80) ? 1 : 4; return false; }   // 1 sem cartucho; 4 há dados mas o checksum do cabeçalho não confere
    uint8_t type = g[0x47], rsz = g[0x48], ssz = g[0x49];
    uint16_t t = type;
    if (type >= 1 && type <= 3) {                                      // MBC1M: não dá para saber pelo cabeçalho, tabela de títulos do OSCR
      static const struct { const char* name; uint8_t len, sum; } mm[] = {{"MOMOCOL", 7, 0x28}, {"BOMCOL", 6, 0x86}, {"GENCOL", 6, 0x8A}, {"SUPERCHINESE 123", 16, 0xE4}, {"MORTALKOMBATI&II", 16, 0xB9}, {"MORTALKOMBAT DUO", 16, 0xA7}};
      for (uint8_t k = 0; k < 6; k++) if (strncmp(reinterpret_cast<const char*>(&g[0x34]), mm[k].name, mm[k].len) == 0 && g[0x4D] == mm[k].sum) t = uint16_t(0x100 + type);
    }
    bool known = type == 0x00 || (type >= 1 && type <= 3) || type == 5 || type == 6 || type == 8 || type == 9 || (type >= 0x0F && type <= 0x13)
                 || (type >= 0x19 && type <= 0x1E) || type == 0xFC || type == 0xFE || type == 0xFF;
    if (!known || rsz > 8) { o.status = 2; copy_ascii(o.name, &g[0x34], 15); return false; }   // MBC6, MBC7, MMM01, TAMA5, M161 e tamanhos fora da tabela
    o.gb_type = t;
    o.rom = 16384UL << (rsz + 1);                                      // 2^(n+1) bancos de 16 KB
    uint16_t bank_bytes = 0; uint8_t banks = 0;
    if (type == 6) { bank_bytes = 512; banks = 1; o.gb_shift = 9; }    // MBC2: 512 x 4 bits
    else if (ssz == 1) { bank_bytes = 2048; banks = 1; o.gb_shift = 11; }
    else if (ssz >= 2 && ssz <= 5 && type != 5) { bank_bytes = 8192; banks = (ssz == 2) ? 1 : (ssz == 3 ? 4 : (ssz == 4 ? 16 : 8)); o.gb_shift = 13; }
    o.save = uint32_t(bank_bytes) * banks;
    o.save_type = o.save ? 1 : 0;
    uint8_t cgb = g[0x43], nlen = (cgb == 0x80 || cgb == 0xC0) ? 15 : 16;   // o título perde 1 byte quando $143 é a flag CGB
    copy_ascii(o.name, &g[0x34], nlen);
    o.status = 0;
    c_ = o;
    cur_prg_ = cur_chr_ = -1;
    return true;
}

uint8_t CartBackend::gb_byte(uint32_t off) {
  if (cur_prg_ < 0) { gb_select(1); cur_prg_ = 1; }
  if (off < 0x4000UL) return gb_->read(uint16_t(off));
  int16_t b = int16_t(off >> 14);
  bool alt = c_.gb_type <= 4 && b >= 32 && (b & 0x1F) == 0;        // MBC1: os bancos $20/$40/$60 não aparecem em $4000 (viram $21/$41/$61); só pela janela de $0000, em modo 1
  if (b != cur_prg_) {
    if (alt) { gb_->write(0x6000, 1); gb_->write(0x4000, uint8_t(b >> 5)); }
    else gb_select(b);
    cur_prg_ = b;
  }
  return gb_->read(alt ? uint16_t(off & 0x3FFF) : uint16_t(0x4000 + (off & 0x3FFF)));
}

void CartBackend::gb_select(int16_t bank) {
  uint16_t t = c_.gb_type;
  if (t >= 0x101 && t <= 0x103) {                                      // MBC1M
    gb_->write(0x4000, uint8_t(bank >> 4));
    gb_->write(0x2000, bank < 10 ? uint8_t(bank & 0x1F) : uint8_t(0x10 | (bank & 0x1F)));
  } else if (t >= 5) {                                                 // MBC2, MBC3, MBC5 e afins: registrador em $2100
    if (t >= 0x19 && t <= 0x1E) gb_->write(0x3000, uint8_t(bank >> 8));   // MBC5: bit 9
    gb_->write(0x2100, uint8_t(bank & 0xFF));
  } else {                                                             // sem mapper e MBC1
    gb_->write(0x6000, 0);
    gb_->write(0x4000, uint8_t(bank >> 5));
    gb_->write(0x2000, uint8_t(bank & 0x1F));
  }
}

void CartBackend::gb_ram_enable() {
  gb_->read(0x0134);                                                   // "MBC2 fix" do OSCR
  if (c_.gb_type <= 4) gb_->write(0x6000, 1);                          // MBC1: modo de RAM
  gb_->write(0x0000, 0x0A);                                            // habilita a RAM
  gb_ram_on_ = true; cur_chr_ = -1;
}

uint16_t CartBackend::gb_ram_addr(uint32_t off) {
  int16_t b = int16_t(off >> c_.gb_shift);
  if (b != cur_chr_) { gb_->write(0x4000, uint8_t(b)); cur_chr_ = b; }
  return uint16_t(0xA000 + (off & ((1UL << c_.gb_shift) - 1)));
}

}  // namespace oscr
