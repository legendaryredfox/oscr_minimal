// SPDX-License-Identifier: GPL-3.0-or-later
#include "oscr_carts.h"

#include <string.h>

namespace oscr {

static void copy_ascii(char* dst, const uint8_t* src, uint8_t n) {
  uint8_t o = 0;
  for (uint8_t i = 0; i < n && o < 32; i++) dst[o++] = (src[i] >= 0x20 && src[i] < 0x7F) ? char(src[i]) : ' ';
  while (o > 0 && dst[o - 1] == ' ') o--;   // tira espaços finais
  dst[o] = 0;
}

uint16_t CartBackend::systems() {
  uint16_t m = 0;
  if (snes_) m |= 1 << SYS_SNES;
  if (nes_) m |= (1 << SYS_NES) | (1 << SYS_FAMICOM);
  if (md_) m |= 1 << SYS_MD;
  if (gba_) m |= 1 << SYS_GBA;
  return m;
}

bool CartBackend::supports(uint8_t sys) { return sys >= 1 && sys <= 5 && (systems() & (1 << sys)); }

bool CartBackend::all_same(const uint8_t* p, uint8_t n) const {
  for (uint8_t i = 1; i < n; i++) if (p[i] != p[0]) return false;
  return true;
}

void CartBackend::acquire(uint8_t sys) {
  if (active_ == sys) return;
  release();
  switch (sys) {
    case SYS_SNES: snes_->begin(); break;
    case SYS_NES: case SYS_FAMICOM: nes_->begin(); break;
    case SYS_MD: md_->begin(); break;
    case SYS_GBA: gba_->begin(); break;
  }
  active_ = sys;
}

void CartBackend::release() {
  switch (active_) {
    case SYS_SNES: snes_->end(); break;
    case SYS_NES: case SYS_FAMICOM: nes_->end(); break;
    case SYS_MD: md_->end(); break;
    case SYS_GBA: gba_->end(); break;
  }
  active_ = 0;
}

// ---------------------------------------------------------------- leitura de 1 byte da ROM
uint8_t CartBackend::byte_at(uint8_t sys, uint32_t off) {
  switch (sys) {
    case SYS_SNES:
      if (c_.hirom) return snes_->read(uint8_t(0xC0 + (off >> 16)), uint16_t(off & 0xFFFF));
      return snes_->read(uint8_t(off >> 15), uint16_t(0x8000 | (off & 0x7FFF)));
    case SYS_NES: case SYS_FAMICOM: {
      if (off < 16) {                                  // cabeçalho iNES sintético
        uint8_t m = uint8_t(mapper_);
        uint8_t h[16] = {'N', 'E', 'S', 0x1A, uint8_t(c_.prg >> 14), uint8_t(c_.chr >> 13), uint8_t((m & 0x0F) << 4), uint8_t(m & 0xF0), 0, 0, 0, 0, 0, 0, 0, 0};
        return h[off];
      }
      uint32_t o = off - 16;
      return o < c_.prg ? nes_prg_byte(o) : nes_chr_byte(o - c_.prg);
    }
    case SYS_MD: { uint16_t w = md_->word(off >> 1); return (off & 1) ? uint8_t(w & 0xFF) : uint8_t(w >> 8); }
    case SYS_GBA: { uint16_t w = gba_->word(off & ~1UL); return (off & 1) ? uint8_t(w >> 8) : uint8_t(w & 0xFF); }
  }
  return 0xFF;
}

// ---------------------------------------------------------------- detecção
bool CartBackend::probe(uint8_t sys, Cart& o) {
  o = Cart();
  c_ = o;
  acquire(sys);
  uint8_t h[48];
  if (sys == SYS_SNES) {
    for (uint8_t i = 0; i < 32; i++) h[i] = snes_->read(0x00, uint16_t(0xFFC0 + i));
    uint16_t comp = h[0x1C] | (h[0x1D] << 8), sum = h[0x1E] | (h[0x1F] << 8);
    if (all_same(h, 32) || uint16_t(comp ^ sum) != 0xFFFF) { o.status = 1; return false; }  // sem cartucho
    uint8_t map = h[0x15], mode = map & 0x0F, rs = h[0x17], ss = h[0x18];
    if (mode > 1 || rs == 0 || rs > 12) { o.status = 2; copy_ascii(o.name, h, 21); return false; }   // SA-1, ExHiROM etc.
    o.hirom = (mode == 1);
    o.rom = 1024UL << rs;
    o.save = (ss >= 1 && ss <= 8) ? (1024UL << ss) : 0;
    o.save_type = o.save ? 1 : 0;
    copy_ascii(o.name, h, 21);
    o.status = 0;
    c_ = o;
    return true;
  }
  if (sys == SYS_NES || sys == SYS_FAMICOM) {
    uint8_t a[64], b[64], ch[64];
    for (uint8_t i = 0; i < 64; i++) { a[i] = nes_->prg(uint16_t(0x8000 + i)); b[i] = nes_->prg(uint16_t(0xC000 + i)); ch[i] = nes_->chr(i); }
    if (all_same(a, 64) && all_same(b, 64) && (a[0] == 0xFF || a[0] == 0x00)) { o.status = 1; return false; }
    if (opt_mapper_ == 0 && opt_prg_ == 0) {                         // automático: NROM
      o.prg = (memcmp(a, b, 64) == 0) ? 16384UL : 32768UL;
      o.chr = (all_same(ch, 64) && (ch[0] == 0xFF || ch[0] == 0x00)) ? 0 : 8192UL;
      mapper_ = 0;
      strcpy(o.name, "NROM (mapper 0)");
    } else {                                                          // mapper e tamanhos informados
      uint16_t m = opt_mapper_;
      bool known = m == 0 || m == 1 || m == 2 || m == 3 || m == 4 || m == 7;
      if (!known) { o.status = 2; return false; }
      if (opt_prg_ == 0 || opt_prg_ % 16 != 0 || opt_chr_ % 8 != 0) { o.status = 3; return false; }
      if ((m == 2 || m == 7) && opt_chr_ != 0) { o.status = 3; return false; }              // CHR-RAM
      if (m == 1 && opt_prg_ > 256) { o.status = 2; return false; }                          // SUROM etc.
      if (m == 7 && opt_prg_ % 32 != 0) { o.status = 3; return false; }
      o.prg = uint32_t(opt_prg_) * 1024UL; o.chr = uint32_t(opt_chr_) * 1024UL;
      mapper_ = m;
      strcpy(o.name, "mapper ");
      uint8_t n = 7; if (m >= 10) o.name[n++] = char('0' + m / 10); o.name[n++] = char('0' + m % 10); o.name[n] = 0;
    }
    o.rom = 16 + o.prg + o.chr;
    o.status = 0;
    c_ = o;
    nes_setup_mapper();
    return true;
  }
  if (sys == SYS_MD) {
    for (uint8_t i = 0; i < 4; i++) { uint16_t w = md_->word(0x80 + i / 2); h[i] = (i & 1) ? uint8_t(w) : uint8_t(w >> 8); }
    if (memcmp(h, "SEGA", 4) != 0) { o.status = 1; return false; }
    uint8_t t[48];
    for (uint8_t i = 0; i < 48; i += 2) { uint16_t w = md_->word((0x150 + i) >> 1); t[i] = uint8_t(w >> 8); t[i + 1] = uint8_t(w); }
    copy_ascii(o.name, t, 48);
    uint32_t end = 0;
    for (uint8_t i = 0; i < 4; i += 2) { uint16_t w = md_->word((0x1A4 + i) >> 1); end = (end << 16) | w; }
    o.rom = (end >= 0x1FF && end < 0x400000UL) ? end + 1 : 0x400000UL;   // tamanho do cabeçalho; se inválido, 4 MB
    o.status = 0;
    c_ = o;
    return true;
  }
  if (sys == SYS_GBA) {
    for (uint8_t i = 0; i < 8; i += 2) { uint16_t w = gba_->word(i); h[i] = uint8_t(w); h[i + 1] = uint8_t(w >> 8); }
    if (h[4] != 0x24 || h[5] != 0xFF || h[6] != 0xAE || h[7] != 0x51) { o.status = 1; return false; }  // logo da Nintendo
    uint8_t t[16];
    for (uint8_t i = 0; i < 16; i += 2) { uint16_t w = gba_->word(0xA0 + i); t[i] = uint8_t(w); t[i + 1] = uint8_t(w >> 8); }
    copy_ascii(o.name, t, 12);
    // tamanho: o menor deslocamento em que a ROM se repete (espelho); sem espelho até 16 MB = 32 MB
    uint32_t sz = 32UL << 20;
    for (uint32_t cand = 256UL << 10; cand <= (16UL << 20); cand <<= 1) {
      bool mirror = true;
      for (uint8_t i = 0; i < 64 && mirror; i += 2) mirror = gba_->word(cand + i) == gba_->word(i);
      if (mirror) { sz = cand; break; }
    }
    o.rom = sz;
    o.status = 0;
    c_ = o;
    return true;
  }
  return false;
}

void CartBackend::detect(uint8_t sys, DetectInfo& out) {
  if (!supports(sys)) { out.status = 2; return; }
  Cart c;
  probe(sys, c);
  release();
  out.status = c.status; out.rom_size = c.rom; out.save_size = c.save; out.save_type = c.save_type;
  strncpy(out.name, c.name, 32); out.name[32] = 0;
}

// ---------------------------------------------------------------- NES: mappers 0, 1, 2, 3, 4, 7
void CartBackend::nes_reg(uint8_t value, uint16_t first_addr, uint16_t scan) {
  // Evita conflito de barramento: escreve num endereço da ROM cujo byte já é igual ao valor.
  for (uint16_t i = 0; i < scan; i++) {
    uint16_t a = uint16_t(first_addr + i);
    if (nes_->prg(a) == value) { nes_->prg_write(a, value); return; }
  }
  nes_->prg_write(first_addr, value);
}

void CartBackend::mmc1_write(uint16_t addr, uint8_t v) {
  for (uint8_t i = 0; i < 5; i++) nes_->prg_write(addr, (v >> i) & 1);   // 5 escritas, bit 0 primeiro
}

void CartBackend::mmc3_write(uint8_t reg, uint8_t v) {
  nes_->prg_write(0x8000, reg);   // seleção de registrador (PRG em modo 0, CHR sem inversão)
  nes_->prg_write(0x8001, v);
}

void CartBackend::nes_setup_mapper() {
  cur_prg_ = cur_chr_ = -1;
  if (mapper_ == 1) { nes_->prg_write(0x8000, 0x80); mmc1_write(0x8000, 0x1C); }   // reset; PRG modo 3, CHR 4 KB
}

uint8_t CartBackend::nes_prg_byte(uint32_t o) {
  uint32_t fixed = c_.prg > 16384UL ? c_.prg - 16384UL : 0;          // início do último banco de 16 KB
  switch (mapper_) {
    case 0: case 3: return nes_->prg(uint16_t(0x8000 + o));
    case 7: {
      int16_t bank = int16_t(o >> 15);
      if (bank != cur_prg_) { nes_reg(uint8_t(bank), 0x8000, 2048); cur_prg_ = bank; }
      return nes_->prg(uint16_t(0x8000 + (o & 0x7FFF)));
    }
    case 2: case 1: case 4: {
      if (o >= fixed) return nes_->prg(uint16_t(0xC000 + (o - fixed)));
      int16_t bank = int16_t(o >> 14);
      if (bank != cur_prg_) {
        if (mapper_ == 2) nes_reg(uint8_t(bank), 0xC000, 2048);
        else if (mapper_ == 1) mmc1_write(0xE000, uint8_t(bank));
        else { mmc3_write(6, uint8_t(bank * 2)); mmc3_write(7, uint8_t(bank * 2 + 1)); }
        cur_prg_ = bank;
      }
      return nes_->prg(uint16_t(0x8000 + (o & 0x3FFF)));
    }
  }
  return 0xFF;
}

uint8_t CartBackend::nes_chr_byte(uint32_t o) {
  switch (mapper_) {
    case 0: return nes_->chr(uint16_t(o));
    case 3: {
      int16_t bank = int16_t(o >> 13);
      if (bank != cur_chr_) { nes_reg(uint8_t(bank), 0x8000, 2048); cur_chr_ = bank; }
      return nes_->chr(uint16_t(o & 0x1FFF));
    }
    case 1: {
      int16_t k = int16_t(o >> 12);                                  // 4 KB por vez
      if (k != cur_chr_) { mmc1_write(0xA000, uint8_t(k)); cur_chr_ = k; }
      return nes_->chr(uint16_t(o & 0x0FFF));
    }
    case 4: {
      int16_t k = int16_t(o >> 12);
      if (k != cur_chr_) { mmc3_write(0, uint8_t(k * 4)); mmc3_write(1, uint8_t(k * 4 + 2)); cur_chr_ = k; }
      return nes_->chr(uint16_t(o & 0x0FFF));
    }
  }
  return 0xFF;
}

// ---------------------------------------------------------------- leitura
bool CartBackend::open_read(uint8_t sys, uint8_t kind, uint32_t& size, uint16_t& err) {
  if (!supports(sys)) { err = E_SISTEMA; return false; }
  Cart c;
  if (!probe(sys, c)) { release(); err = (c.status == 2) ? E_SISTEMA : (c.status == 3 ? E_ARGUMENTO : E_SEM_CARTUCHO); return false; }
  if (kind == KIND_SAVE) {
    if (sys != SYS_SNES || c_.save == 0) { release(); err = E_SEM_SAVE; return false; }
    size = c_.save;
  } else {
    size = c_.rom;
  }
  return true;
}

void CartBackend::snes_save_addr(uint32_t i, uint8_t& bank, uint16_t& addr) const {
  if (c_.hirom) { bank = uint8_t(0x30 + (i >> 13)); addr = uint16_t(0x6000 + (i & 0x1FFF)); }
  else { bank = uint8_t(0x70 + (i >> 15)); addr = uint16_t(i & 0x7FFF); }
}

bool CartBackend::read(uint8_t sys, uint8_t kind, uint32_t off, uint8_t* buf, uint16_t len) {
  if (active_ != sys) return false;
  for (uint16_t i = 0; i < len; i++) {
    if (kind == KIND_SAVE) {
      uint8_t bank; uint16_t addr;
      snes_save_addr(off + i, bank, addr);
      buf[i] = snes_->read(bank, addr);
    } else {
      buf[i] = byte_at(sys, off + i);
    }
  }
  return true;
}

// ---------------------------------------------------------------- escrita de save (SNES SRAM)
bool CartBackend::write_begin(uint8_t sys, uint32_t size, uint16_t& err) {
  if (!supports(sys)) { err = E_SISTEMA; return false; }
  if (sys != SYS_SNES) { err = E_SEM_SAVE; return false; }
  Cart c;
  if (!probe(sys, c)) { release(); err = (c.status == 2) ? E_SISTEMA : E_SEM_CARTUCHO; return false; }
  if (c_.save == 0) { release(); err = E_SEM_SAVE; return false; }
  if (size != c_.save) { release(); err = E_ARGUMENTO; return false; }
  return true;
}

bool CartBackend::write_block(uint32_t off, const uint8_t* buf, uint16_t len) {
  if (active_ != SYS_SNES) return false;
  for (uint16_t i = 0; i < len; i++) {
    uint8_t bank; uint16_t addr;
    snes_save_addr(off + i, bank, addr);
    snes_->write(bank, addr, buf[i]);
    if (snes_->read(bank, addr) != buf[i]) return false;       // confere o que gravou
  }
  return true;
}

}  // namespace oscr
