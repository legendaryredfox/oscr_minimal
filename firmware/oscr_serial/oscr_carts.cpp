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
      if (off < 16) {                                  // cabeçalho iNES sintético (mapper 0)
        uint8_t h[16] = {'N', 'E', 'S', 0x1A, uint8_t(c_.prg >> 14), uint8_t(c_.chr >> 13), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
        return h[off];
      }
      uint32_t o = off - 16;
      if (o < c_.prg) return nes_->prg(uint16_t(0x8000 + o));
      return nes_->chr(uint16_t(o - c_.prg));
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
    if (all_same(a, 64) && (a[0] == 0xFF || a[0] == 0x00)) { o.status = 1; return false; }
    o.prg = (memcmp(a, b, 64) == 0) ? 16384UL : 32768UL;          // 16 KB espelhado ou 32 KB
    o.chr = (all_same(ch, 64) && (ch[0] == 0xFF || ch[0] == 0x00)) ? 0 : 8192UL;
    o.rom = 16 + o.prg + o.chr;
    strcpy(o.name, "NROM (mapper 0)");
    o.status = 0;
    c_ = o;
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

// ---------------------------------------------------------------- leitura
bool CartBackend::open_read(uint8_t sys, uint8_t kind, uint32_t& size, uint16_t& err) {
  if (!supports(sys)) { err = E_SISTEMA; return false; }
  Cart c;
  if (!probe(sys, c)) { release(); err = (c.status == 2) ? E_SISTEMA : E_SEM_CARTUCHO; return false; }
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
