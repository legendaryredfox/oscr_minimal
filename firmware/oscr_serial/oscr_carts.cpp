// SPDX-License-Identifier: GPL-3.0-or-later
#include "oscr_carts.h"

#include <string.h>

#if defined(__AVR__)
#include <avr/pgmspace.h>
#else
#define PROGMEM
#define pgm_read_word(p) (*(p))
#endif

namespace oscr {

// Tabela de EEPROM serial do Mega Drive, do OSCR (MD.ino): {checksum do cabeçalho em $18E, tipo | tamanho}.
// Tipo nos 3 bits baixos (1 Acclaim 1, 2 Acclaim 2, 3 Capcom/Sega, 4 EA, 5 Codemasters); o resto é o tamanho em bytes.
static const uint16_t MD_EEP_TABLE[] PROGMEM = {
  0x5B9F, 0x101, 0x694F, 0x101, 0xBFA9, 0x101,                                           // Acclaim 1: NBA Jam
  0x16B2, 0x102, 0xCC3F, 0x102, 0x8AE1, 0x102, 0xDB97, 0x102, 0x7651, 0x102, 0xDFE4, 0x102,   // Acclaim 2
  0x3DE6, 0x802, 0xCB78, 0x2002, 0x6DD9, 0x2002,
  0xAD23, 0x83, 0xEA80, 0x83,                                                            // Capcom
  0x760F, 0x83, 0x95E7, 0x83, 0x0000, 0x83, 0x7270, 0x83, 0xBACC, 0x83, 0xB939, 0x83,   // Sega
  0x487C, 0x83, 0x740D, 0x83, 0x0278, 0x83, 0x9D79, 0x83,
  0x8512, 0x84, 0xA107, 0x84, 0x246A, 0x84, 0x5807, 0x84, 0x2799, 0x84, 0xFA57, 0x84, 0x8B9F, 0x84,   // EA
  0x7E65, 0x405, 0x9A5C, 0x2005, 0xC4EE, 0x2005, 0x7E50, 0x805, 0x165E, 0x805, 0x168B, 0x405, 0x12C1, 0x2005,   // Codemasters
};
static const uint8_t MD_EEP_COUNT = sizeof(MD_EEP_TABLE) / sizeof(MD_EEP_TABLE[0]) / 2;

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
  if (gb_) m |= 1 << SYS_GB;
  return m;
}

bool CartBackend::supports(uint8_t sys) { return sys >= 1 && sys <= 6 && (systems() & (1 << sys)); }

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
    case SYS_GB: gb_->begin(); break;
  }
  active_ = sys;
}

void CartBackend::release() {
  if (active_ == SYS_GB && gb_ram_on_ && gb_) { gb_->write(0x0000, 0x00); gb_ram_on_ = false; }   // desabilita a RAM do cartucho
  if (active_ == SYS_SNES && snes_) {                               // devolve os registradores dos chips especiais ao valor original
    if (sdd1_cur_ >= 0) snes_->write(0, 0x4807, uint8_t(sdd1_init_));
    if (spc_touched_) { snes_->write(0, 0x4833, 2); snes_->write(0, 0x4834, 0); }
    if (spc_sram_) snes_->write(0, 0x4830, 0);
    if (cx4_touched_) snes_->write(0, 0x7F52, cx4_orig_);
  }
  sdd1_cur_ = -1; spc_region_ = -1; spc_touched_ = spc_sram_ = cx4_touched_ = false;
  if (clocks_on_ && snes_) { snes_->cpu_clock(false); snes_->clocks_stop(); clocks_on_ = false; }
  if (active_ == SYS_MD && md_sram_on_) md_sram(false);
  if ((active_ == SYS_NES || active_ == SYS_FAMICOM) && nes_ram_on_) nes_ram(false);
  md_bank_ = -1;
  if (active_ == SYS_GBA && gba_bank_ != 0) gba_flash_bank(0);     // volta ao banco 0 da Flash
  gba_eep_blk_ = -1;
  switch (active_) {
    case SYS_SNES: snes_->end(); break;
    case SYS_NES: case SYS_FAMICOM: nes_->end(); break;
    case SYS_MD: md_->end(); break;
    case SYS_GBA: gba_->end(); break;
    case SYS_GB: gb_->end(); break;
  }
  active_ = 0;
}

// ---------------------------------------------------------------- leitura de 1 byte da ROM
uint8_t CartBackend::byte_at(uint8_t sys, uint32_t off) {
  switch (sys) {
    case SYS_SNES:
      if (c_.sdd1) {                                                    // S-DD1: o registrador $4807 escolhe qual 1 MB aparece em $F0-$FF
        int16_t m = int16_t(off >> 20);
        if (m != sdd1_cur_) { snes_->write(0, 0x4807, uint8_t(m)); sdd1_cur_ = m; }
        return snes_->read(uint8_t(0xF0 + ((off >> 16) & 0xF)), uint16_t(off & 0xFFFF));
      }
      if (c_.spc7110) {                                                 // SPC7110: 0-2 MB em $C0-$DF; depois $E0-$EF e $F0-$FF (duas vezes) com $4833/$4834
        if (off < 0x200000UL) return snes_->read(uint8_t(0xC0 + (off >> 16)), uint16_t(off & 0xFFFF));
        int8_t r = off < 0x300000UL ? 1 : (off < 0x400000UL ? 2 : 3);
        if (r != spc_region_) { snes_->write(0, 0x4834, 0xFF); snes_->write(0, 0x4833, r == 3 ? 3 : 2); spc_region_ = r; spc_touched_ = true; }
        uint8_t bank = r == 1 ? uint8_t(0xE0 + ((off - 0x200000UL) >> 16)) : uint8_t(0xF0 + ((off >> 16) & 0xF));
        return snes_->read(bank, uint16_t(off & 0xFFFF));
      }
      if (c_.exhirom) {                                                  // ExHiROM: A22 invertido: os primeiros 4 MB em $C0-$FF, o resto em $40-$7D
        if (off < 0x400000UL) return snes_->read(uint8_t(0xC0 + (off >> 16)), uint16_t(off & 0xFFFF));
        return snes_->read(uint8_t(0x40 + ((off - 0x400000UL) >> 16)), uint16_t(off & 0xFFFF));
      }
      if (c_.hirom) return snes_->read(uint8_t(0xC0 + (off >> 16)), uint16_t(off & 0xFFFF));
      if (c_.rom > 0x300000UL) return snes_->read(uint8_t(0x80 + (off >> 15)), uint16_t(0x8000 | (off & 0x7FFF)));   // LoROM de mais de 3 MB: $7E-$7F são a WRAM, usa $80+ (como o OSCR)
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
    case SYS_MD: {
      uint32_t a = off;
      if (c_.ssf && off >= 0x80000UL) {                                // SSF2: janela 1 ($080000-$0FFFFF) varre os bancos de 512 KB
        int16_t bank = int16_t(off >> 19);
        if (bank != md_bank_) { md_->map_write(0x509879UL, uint16_t(bank)); md_bank_ = bank; }
        a = 0x80000UL + (off & 0x7FFFFUL);
      }
      uint16_t w = md_->word(a >> 1);
      return (a & 1) ? uint8_t(w & 0xFF) : uint8_t(w >> 8);
    }
    case SYS_GB: {                                                       // bancos de 16 KB; $0000-$3FFF (banco 0) é lido com o banco 1 já selecionado, como o OSCR
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
    case SYS_GBA: { uint16_t w = gba_->word(off & ~1UL); return (off & 1) ? uint8_t(w >> 8) : uint8_t(w & 0xFF); }
  }
  return 0xFF;
}

// ---------------------------------------------------------------- detecção
bool CartBackend::probe(uint8_t sys, Cart& o, bool for_save) {
  o = Cart();
  c_ = o;
  acquire(sys);
  uint8_t h[48];
  if (sys == SYS_SNES) {
    snes_->cs(false);                                                // volta ao padrão (ROM); a SRAM de HiROM/ExHiROM sobe o CS depois
    bool good = false;
    for (uint8_t pass = 0; pass < 2 && !good; pass++) {
      for (uint8_t i = 0; i < 32; i++) h[i] = snes_->read(0x00, uint16_t(0xFFC0 + i));
      uint16_t comp = h[0x1C] | (h[0x1D] << 8), sum = h[0x1E] | (h[0x1F] << 8);
      good = !all_same(h, 32) && uint16_t(comp ^ sum) == 0xFFFF;
      if (!good && pass == 0 && !clocks_on_ && snes_->clocks_available()) snes_clocks_boot();   // SA-1 e afins só respondem com clock e CIC
    }
    if (!good) { o.status = 1; return false; }                       // sem cartucho
    uint8_t map = h[0x15], mode = map & 0x0F, rs = h[0x17], ss = h[0x18];
    bool sa1 = (mode == 3 && (h[0x16] == 0x34 || h[0x16] == 0x35));   // SA-1 com RAM (e bateria)
    if (sa1 && !clocks_on_) {
      if (!snes_->clocks_available()) { o.status = 2; copy_ascii(o.name, h, 21); return false; }   // sem o Si5351 não há SA-1
      snes_clocks_boot();
    }
    if (clocks_on_) snes_->clocks_run();                              // clocks normais do console
    bool ex = (mode == 5);                                           // ExHiROM: $25 / $35 (cabeçalho em $40FFC0, visível em $00:FFC0)
    uint8_t chips = h[0x16];
    bool sfx = (chips == 0x13 || chips == 0x14 || chips == 0x15 || chips == 0x1A);
    bool sdd1 = (chips == 0x43 || chips == 0x45);
    bool spc = ((chips == 0xF5 || chips == 0xF9) && mode == 0x0A);
    uint8_t cx4 = (chips == 0xF3) ? uint8_t(h[9] & 0x0F) : 0;
    if (cx4 != 2 && cx4 != 3) cx4 = 0;
    bool special = sdd1 || spc;                                      // tamanho fixo pelo chip, como o OSCR
    if ((mode > 1 && !ex && !sa1 && !special) || (!special && (rs == 0 || rs > (ex ? 13 : 12)))) { o.status = 2; copy_ascii(o.name, h, 21); return false; }   // chips sem suporte
    o.hirom = (mode == 1) || ex || sa1 || special;                   // SA-1 lê a ROM como HiROM ($C0-$FF); a SRAM de S-DD1 e SPC7110 também é de HiROM
    o.sa1 = sa1; o.sfx = sfx; o.sdd1 = sdd1; o.spc7110 = spc; o.cx4 = cx4;
    o.exhirom = ex;
    o.rom = 1024UL << rs;
    if (sdd1) o.rom = (chips == 0x45) ? 6144UL * 1024UL : 4096UL * 1024UL;       // 48 Mbit / 32 Mbit
    if (spc) o.rom = (chips == 0xF5) ? 3072UL * 1024UL : 5120UL * 1024UL;       // 24 Mbit / 40 Mbit
    if (cx4 == 2) o.rom = 1536UL * 1024UL; else if (cx4 == 3) o.rom = 2048UL * 1024UL;   // X2 12 Mbit, X3 16 Mbit
    if (ex && rs == 13) o.rom = 6144UL * 1024UL;                    // cabeçalho "8 MB": os ExHiROM conhecidos de mais de 4 MB têm 6 MB (48 Mbit); outro valor, informe o tamanho
    if (ex && opt_prg_ != 0) {                                      // tamanho informado (KB)
      if (opt_prg_ % 64 != 0 || opt_prg_ > 8064) { o.status = 3; return false; }   // $40-$7D vão até $7DFFFF; $7E-$7F são a WRAM do console
      o.rom = uint32_t(opt_prg_) * 1024UL;
    }
    if (sfx) {                                                       // SuperFX: o campo de RAM do cabeçalho não vale; $FFBD se o mapa for $33, senão 32 KB (Star Fox 2: 64 KB)
      char nm[9]; copy_ascii(nm, h, 8);
      ss = (h[0x1A] == 0x33) ? snes_->read(0x00, 0xFFBD) : (strncmp(nm, "STARFOX2", 8) == 0 ? 6 : 5);
    }
    o.save = (ss >= 1 && ss <= 8) ? (1024UL << ss) : 0;
    o.save_type = o.save ? 1 : 0;
    copy_ascii(o.name, h, 21);
    o.status = 0;
    c_ = o;
    // registradores dos chips (devolvidos ao valor original em release)
    if (sdd1) { sdd1_init_ = snes_->read(0, 0x4807); sdd1_cur_ = -1; }
    if (cx4) {
      cx4_orig_ = snes_->read(0, 0x7F52);
      if (cx4 == 2 && cx4_orig_ != 0) { snes_->write(0, 0x7F52, 0); cx4_touched_ = true; }       // X2: mapeamento 0
      else if (cx4 == 3 && cx4_orig_ == 0) { snes_->write(0, 0x7F52, 1); cx4_touched_ = true; }  // X3: mapeamento 1
    }
    return true;
  }
  if (sys == SYS_NES || sys == SYS_FAMICOM) {
    uint8_t a[64], b[64], ch[64];
    for (uint8_t i = 0; i < 64; i++) { a[i] = nes_->prg(uint16_t(0x8000 + i)); b[i] = nes_->prg(uint16_t(0xC000 + i)); ch[i] = nes_->chr(i); }
    if (all_same(a, 64) && all_same(b, 64) && (a[0] == 0xFF || a[0] == 0x00)) { o.status = 1; return false; }
    if (for_save) {                                                   // save: só mapper 1 ou 4, tamanhos não importam
      if (opt_mapper_ != 1 && opt_mapper_ != 4 && opt_mapper_ != 5 && opt_mapper_ != 69 && opt_mapper_ != 118) { o.status = 0; o.save = 0; c_ = o; mapper_ = 0; return true; }
      uint16_t ram_kb = opt_prg_ ? opt_prg_ : 8;                       // para save, prg_kb = tamanho da RAM em KB (padrão 8)
      if (ram_kb != 8 && !((opt_mapper_ == 1 || opt_mapper_ == 5) && (ram_kb == 16 || ram_kb == 32))) { o.status = 3; return false; }   // 16/32 KB só no MMC1 (SOROM/SXROM) e no MMC5
      mapper_ = opt_mapper_; o.save = uint32_t(ram_kb) * 1024UL; o.save_type = 1;
      strcpy(o.name, "mapper ");
      { uint8_t n = 7; if (mapper_ >= 10) o.name[n++] = char('0' + mapper_ / 10); o.name[n++] = char('0' + mapper_ % 10); o.name[n] = 0; }
      o.status = 0; c_ = o;
      nes_setup_mapper();
      return true;
    }
    if (opt_mapper_ == 0 && opt_prg_ == 0) {                         // automático: NROM
      o.prg = (memcmp(a, b, 64) == 0) ? 16384UL : 32768UL;
      o.chr = (all_same(ch, 64) && (ch[0] == 0xFF || ch[0] == 0x00)) ? 0 : 8192UL;
      mapper_ = 0;
      strcpy(o.name, "NROM (mapper 0)");
    } else {                                                          // mapper e tamanhos informados
      uint16_t m = opt_mapper_;
      bool known = m == 0 || m == 1 || m == 2 || m == 3 || m == 4 || m == 5 || m == 7 || m == 9 || m == 10 || m == 11 || m == 33 || m == 48 || m == 66 || m == 69 || m == 70 || m == 71
                   || m == 75 || m == 78 || m == 79 || m == 87 || m == 118 || m == 206;
      if (!known) { o.status = 2; return false; }
      if (opt_prg_ == 0 || opt_prg_ % 16 != 0 || opt_chr_ % 8 != 0) { o.status = 3; return false; }
      if ((m == 2 || m == 7 || m == 71) && opt_chr_ != 0) { o.status = 3; return false; }   // CHR-RAM
      if ((m == 79 || m == 87 || m == 78 || m == 75 || m == 70 || m == 33 || m == 48 || m == 118 || m == 206) && opt_chr_ == 0) { o.status = 3; return false; }   // CHR-ROM
      if (m == 1 && opt_prg_ > 256) { o.status = 2; return false; }                          // SUROM etc.
      if ((m == 7 || m == 11 || m == 66 || m == 79) && opt_prg_ % 32 != 0) { o.status = 3; return false; }
      if ((m == 9 && opt_prg_ > 128) || (m == 10 && opt_prg_ > 256) || (m == 11 && (opt_prg_ > 128 || opt_chr_ > 128))
          || (m == 66 && (opt_prg_ > 128 || opt_chr_ > 32)) || (m == 69 && opt_prg_ > 512) || (m == 5 && opt_prg_ > 1024)
          || ((m == 33 || m == 48) && (opt_prg_ > 256 || opt_chr_ > 256)) || (m == 70 && (opt_prg_ > 256 || opt_chr_ > 128)) || (m == 75 && (opt_prg_ > 128 || opt_chr_ > 128))
          || (m == 78 && (opt_prg_ > 128 || opt_chr_ > 128)) || (m == 79 && (opt_prg_ > 64 || opt_chr_ > 64)) || (m == 87 && (opt_prg_ > 32 || opt_chr_ > 32))
          || (m == 118 && (opt_prg_ > 512 || opt_chr_ > 256)) || (m == 206 && (opt_prg_ > 128 || opt_chr_ > 64))) { o.status = 2; return false; }   // além do registrador
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
  if (sys == SYS_GB) {
    uint8_t g[80];
    bool ok = false;
    gb_->write(0x6000, 0); gb_->write(0x4000, 0);                       // MBC1 em modo 1 com banco superior != 0 (operação anterior) esconderia o banco 0 e o cabeçalho
    for (uint8_t pass = 0; pass < 2 && !ok; pass++) {                  // checksum do cabeçalho; relê uma vez se não bater (como o OSCR)
      for (uint8_t i = 0; i < 80; i++) g[i] = gb_->read(uint16_t(0x100 + i));
      uint8_t sum = 0;
      for (uint8_t i = 0x34; i < 0x4D; i++) sum = uint8_t(sum - g[i] - 1);
      ok = (sum == g[0x4D]) && !all_same(g, 80);
    }
    if (!ok) { o.status = 1; return false; }
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
  if (sys == SYS_MD) {
    for (uint8_t i = 0; i < 8; i += 2) { uint16_t w = md_->word(0x80 + i / 2); h[i] = uint8_t(w >> 8); h[i + 1] = uint8_t(w); }
    if (memcmp(h, "SEGA", 4) != 0) { o.status = 1; return false; }
    o.ssf = memcmp(h, "SEGA SSF", 8) == 0;
    uint8_t t[48];
    for (uint8_t i = 0; i < 48; i += 2) { uint16_t w = md_->word((0x150 + i) >> 1); t[i] = uint8_t(w >> 8); t[i + 1] = uint8_t(w); }
    copy_ascii(o.name, t, 48);
    uint32_t end = 0;
    for (uint8_t i = 0; i < 4; i += 2) { uint16_t w = md_->word((0x1A4 + i) >> 1); end = (end << 16) | w; }
    uint32_t cap = o.ssf ? 0x800000UL : 0x400000UL;
    o.rom = (end >= 0x1FF && end < cap) ? end + 1 : cap;                // tamanho do cabeçalho; se inválido, o máximo
    if (opt_prg_ != 0) {                                                // tamanho informado pelo usuário (KB)
      uint32_t forced = uint32_t(opt_prg_) * 1024UL;
      if (forced < 0x8000UL || forced > cap) { o.status = 3; return false; }
      o.rom = forced;
    } else {
      // Cabeçalho que declara mais do que o chip tem: a ROM aparece repetida (espelhada). Reduz à metade
      // enquanto os dois lados batem em vários pontos com conteúdo (ignora áreas só de 0xFF/0x00).
      while (o.rom >= 0x40000UL && !o.ssf) {
        uint32_t half = o.rom / 2;
        const uint32_t pts[4] = {0x200UL, half / 4, half / 2, half - 64};
        uint8_t informative = 0; bool equal = true;
        for (uint8_t k = 0; k < 4 && equal; k++) {
          bool same_val = true; uint16_t first = md_->word(pts[k] >> 1);
          for (uint8_t i = 0; i < 32; i += 2) {
            uint16_t lo = md_->word((pts[k] + i) >> 1), hi = md_->word((pts[k] + half + i) >> 1);
            if (lo != hi) { equal = false; break; }
            if (lo != first) same_val = false;
          }
          if (equal && !(same_val && (first == 0xFFFF || first == 0x0000))) informative++;
        }
        if (!equal || informative < 2) break;
        o.rom = half;
      }
    }
    // EEPROM serial: tabela por checksum do cabeçalho ($18E), como no OSCR
    uint16_t chk = md_->word(0xC7);
    for (uint8_t i = 0; i < MD_EEP_COUNT; i++) {
      if (pgm_read_word(MD_EEP_TABLE + i * 2) == chk) {
        uint16_t d = pgm_read_word(MD_EEP_TABLE + i * 2 + 1);
        o.md_eep = uint8_t(d & 7); o.md_eep_size = d & 0xFFF8;
        break;
      }
    }
    if (o.md_eep && chk == 0x0000 && md_->word(0xD9) != 0xE840) o.md_eep = 0;                    // checksum em branco: confere o cabeçalho
    if (o.md_eep && (chk == 0x165E || chk == 0x168B) && md_->word(0x00) != 0x444E) o.md_eep = 0;  // Codemasters sem EEPROM
    if (o.md_eep) { o.md_save = 4; o.save = o.md_eep_size; o.save_type = 3; }
    // SRAM: "RA" + tipo em $1B0, início em $1B4 e fim em $1B8 (lógica do OSCR)
    else if (md_->word(0xD8) == 0x5241) {
      uint16_t type = md_->word(0xD9);
      uint32_t base = (uint32_t(md_->word(0xDA)) << 16) | md_->word(0xDB);
      uint32_t last = (uint32_t(md_->word(0xDC)) << 16) | md_->word(0xDD);
      if (type == 0xF820 || type == 0xF840) {
        if (base == 0x20000020UL && last == 0x00010020UL) { base = 0x200001UL; last = 0x203FFFUL; }   // Psy-o-blade
        if (base == 0x200001UL || base == 0x300001UL || base == 0x3C0001UL) { o.md_save = 1; o.save = (last - base + 2) / 2; o.md_base = base >> 1; }
        else if (base == 0x200000UL) { o.md_save = 2; o.save = (last - base + 1) / 2; o.md_base = base / 2; }
      } else if (type == 0xE020) {
        if (base == 0x200001UL) { o.md_save = 3; o.save = last - base + 2; o.md_base = base >> 1; }
        else if (base == 0x200000UL) { o.md_save = 3; o.save = last - base + 1; o.md_base = base >> 1; }
      }
      if (o.save > 0x10000UL) { o.save = 0; o.md_save = 0; }              // proteção contra cabeçalho inválido
      if (o.save) o.save_type = 1;
    }
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
    o.save = 32768;                 // DETECT: o tipo real (SRAM/Flash/EEPROM) é desconhecido
    o.save_type = 255;
    if (for_save) {                 // o tipo vem do usuário (campo mapper): numeração do OSCR
      uint8_t t = opt_mapper_ ? uint8_t(opt_mapper_) : 3;
      static const uint32_t sz_[6] = {0, 512, 8192, 32768, 65536, 131072};
      static const uint8_t ty_[6] = {0, 3, 3, 1, 2, 2};
      if (opt_mapper_ > 5) { o.status = 3; return false; }
      o.gba_type = t; o.save = sz_[t]; o.save_type = ty_[t];
      uint16_t g0 = gba_->word(0xAC), g1 = gba_->word(0xAE);       // código do jogo: e-Reader não deixa gravar os últimos 128 bytes
      char code[5] = {char(g0 & 0xFF), char(g0 >> 8), char(g1 & 0xFF), char(g1 >> 8), 0};
      o.gba_skip = (t == 4 && strcmp(code, "PEAJ") == 0) || (t == 5 && (strcmp(code, "PSAE") == 0 || strcmp(code, "PSAJ") == 0));
    }
    o.status = 0;
    c_ = o;
    return true;
  }
  return false;
}

void CartBackend::detect(uint8_t sys, DetectInfo& out) {
  if (!supports(sys)) { out.status = 2; return; }
  Cart c;
  uint16_t sm = opt_mapper_, sp = opt_prg_, sc = opt_chr_;   // DETECT ignora as opções do último dump
  opt_mapper_ = opt_prg_ = opt_chr_ = 0;
  probe(sys, c);
  release();
  opt_mapper_ = sm; opt_prg_ = sp; opt_chr_ = sc;
  out.status = c.status; out.rom_size = c.rom; out.save_size = c.save; out.save_type = c.save_type;
  strncpy(out.name, c.name, 32); out.name[32] = 0;
}

// ---------------------------------------------------------------- NES: mappers 0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 66, 69, 71
void CartBackend::nes_ram(bool on) {
  if (mapper_ == 1) mmc1_write(0xE000, on ? 0x00 : 0x10);          // PRG reg bit 4: 0 liga, 1 desliga a RAM (MMC1B)
  else if (mapper_ == 4 || mapper_ == 118) nes_->prg_write(0xA001, on ? 0x80 : 0x00);  // MMC3: bit 7 liga; desliga ao terminar
  else if (mapper_ == 5) { nes_->prg_write(0x5102, 0); nes_->prg_write(0x5103, 0); }   // MMC5: RAM sempre visível; só a proteção de escrita (liberada a cada byte)
  else if (mapper_ == 69) { nes_->prg_write(0x8000, 8); nes_->prg_write(0xA000, on ? 0xC0 : 0x00); }   // FME-7: comando 8; bit 7 liga a RAM, bit 6 escolhe RAM em vez de ROM
  nes_ram_on_ = on;
}

uint16_t CartBackend::nes_ram_addr(uint32_t off) {
  if (mapper_ == 1 && c_.save > 8192UL) {                           // SOROM (16 KB) e SXROM (32 KB): banco de 8 KB pelo registrador CHR 0
    int16_t b = int16_t(off >> 13);
    if (b != cur_chr_) {
      nes_->prg_write(0x8000, 0x80);                                // reset do registrador (como writeRAM do OSCR)
      mmc1_write(0x8000, 1 << 3);
      mmc1_write(0xE000, 0);                                        // RAM ligada
      mmc1_write(0xA000, uint8_t(c_.save == 32768UL ? b << 2 : b << 3));
      cur_chr_ = b;
    }
  }
  if (mapper_ == 5) {                                               // MMC5: $5113 escolhe o banco de 8 KB; 16 KB = dois chips de 8 KB (bancos 0 e 4)
    int16_t b = c_.save == 16384UL ? int16_t((off >> 13) ? 4 : 0) : int16_t(off >> 13);
    if (b != cur_chr_) { nes_->prg_write(0x5113, uint8_t(b)); cur_chr_ = b; }
  }
  return uint16_t(0x6000 + (off & 0x1FFF));
}

void CartBackend::nes_reg(uint8_t value, uint16_t first_addr, uint16_t scan) {
  // Evita conflito de barramento: escreve num endereço da ROM cujo byte já é igual ao valor.
  for (uint16_t i = 0; i < scan; i++) {
    uint16_t a = uint16_t(first_addr + i);
    if (nes_->prg(a) == value) { nes_->prg_write(a, value); return; }
  }
  nes_->prg_write(first_addr, value);
}

void CartBackend::mmc1_write(uint16_t addr, uint8_t v) {
  for (uint8_t i = 0; i < 5; i++) {                                  // 5 escritas, bit 0 primeiro
    if (addr >= 0xE000) nes_->reg_write_safe(addr, uint8_t(v >> i));   // acima de $E000 sem corromper a PRG-RAM (como write_mmc1_byte do OSCR)
    else nes_->prg_write(addr, uint8_t(v >> i));
  }
}

void CartBackend::mmc3_write(uint8_t reg, uint8_t v) {
  nes_->prg_write(0x8000, reg);   // seleção de registrador (PRG em modo 0, CHR sem inversão)
  nes_->prg_write(0x8001, v);
}

void CartBackend::nes_setup_mapper() {
  cur_prg_ = cur_chr_ = -1;
  if (mapper_ == 1) { nes_->prg_write(0x8000, 0x80); mmc1_write(0x8000, 0x1C); }   // reset; PRG modo 3, CHR 4 KB
  else if (mapper_ == 5) { nes_->prg_write(0x5100, 3); nes_->prg_write(0x5101, 0); }   // MMC5: PRG em bancos de 8 KB, CHR em 8 KB
  else if (mapper_ == 69) { nes_->prg_write(0x8000, 8); nes_->prg_write(0xA000, 0); }  // FME-7: $6000 = ROM banco 0 (RAM desligada)
}

uint8_t CartBackend::nes_prg_byte(uint32_t o) {
  uint32_t fixed = c_.prg > 16384UL ? c_.prg - 16384UL : 0;          // início do último banco de 16 KB
  switch (mapper_) {
    case 0: case 3: case 87: return nes_->prg(uint16_t(0x8000 + o));
    case 79: {                                                       // NINA-003/006: 32 KB por vez, registrador em $4100 (bit 3)
      int16_t bank = int16_t(o >> 15);
      if (bank != cur_prg_) { nes_->prg_write(0x4100, uint8_t(bank << 3)); cur_prg_ = bank; }
      return nes_->prg(uint16_t(0x8000 + (o & 0x7FFF)));
    }
    case 75: {                                                       // VRC1: 8 KB em $8000 pelo registrador $8000 (4 bits)
      int16_t bank = int16_t(o >> 13);
      if (bank != cur_prg_) { nes_->prg_write(0x8000, uint8_t(bank & 0x0F)); cur_prg_ = bank; }
      return nes_->prg(uint16_t(0x8000 + (o & 0x1FFF)));
    }
    case 7: case 11: case 66: {                                      // 32 KB por vez; 7 e 11 e 66 têm conflito de barramento
      int16_t bank = int16_t(o >> 15);
      if (bank != cur_prg_) {
        uint8_t v = mapper_ == 66 ? uint8_t(bank << 4) : uint8_t(bank);   // 66: bits 4-5; 7 e 11: bits 0-1/0-2
        nes_reg(v, 0x8000, 2048); cur_prg_ = bank;
      }
      return nes_->prg(uint16_t(0x8000 + (o & 0x7FFF)));
    }
    case 2: case 1: case 4: case 10: case 71: case 33: case 48: case 70: case 78: case 118: case 206: {
      if (o >= fixed) return nes_->prg(uint16_t(0xC000 + (o - fixed)));
      int16_t bank = int16_t(o >> 14);
      if (bank != cur_prg_) {
        if (mapper_ == 2) nes_reg(uint8_t(bank), 0xC000, 2048);
        else if (mapper_ == 1) mmc1_write(0xE000, uint8_t(bank));
        else if (mapper_ == 10) nes_->prg_write(0xA000, uint8_t(bank));
        else if (mapper_ == 71) nes_->prg_write(0xC000, uint8_t(bank));
        else if (mapper_ == 33 || mapper_ == 48) { nes_->prg_write(0x8000, uint8_t(bank * 2)); nes_->prg_write(0x8001, uint8_t(bank * 2 + 1)); }   // dois bancos de 8 KB
        else if (mapper_ == 70) nes_reg(uint8_t(bank << 4), 0xC000, 16384);   // PRG nos bits 4-7; conflito de barramento
        else if (mapper_ == 78) nes_reg(uint8_t(bank), 0xC000, 16384);        // PRG nos bits 0-2; conflito de barramento
        else { mmc3_write(6, uint8_t(bank * 2)); mmc3_write(7, uint8_t(bank * 2 + 1)); }
        cur_prg_ = bank;
      }
      return nes_->prg(uint16_t(0x8000 + (o & 0x3FFF)));
    }
    case 9: {                                                        // MMC2: 8 KB em $8000; os 3 últimos bancos ficam fixos em $A000
      uint32_t fixed9 = c_.prg > 24576UL ? c_.prg - 24576UL : 0;
      if (o >= fixed9) return nes_->prg(uint16_t(0xA000 + (o - fixed9)));
      int16_t bank = int16_t(o >> 13);
      if (bank != cur_prg_) { nes_->prg_write(0xA000, uint8_t(bank)); cur_prg_ = bank; }
      return nes_->prg(uint16_t(0x8000 + (o & 0x1FFF)));
    }
    case 69: {                                                       // FME-7: comando 9 = banco de 8 KB em $8000
      int16_t bank = int16_t(o >> 13);
      if (bank != cur_prg_) { nes_->prg_write(0x8000, 9); nes_->prg_write(0xA000, uint8_t(bank)); cur_prg_ = bank; }
      return nes_->prg(uint16_t(0x8000 + (o & 0x1FFF)));
    }
    case 5: {                                                        // MMC5, modo 3: dois bancos de 8 KB (bit 7 = ROM) em $8000-$BFFF
      int16_t bank = int16_t(o >> 14);
      if (bank != cur_prg_) {
        nes_->prg_write(0x5114, uint8_t((bank * 2) | 0x80)); nes_->prg_write(0x5115, uint8_t((bank * 2 + 1) | 0x80));
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
    case 3: case 66: case 11: case 70: case 78: {                    // 8 KB por vez; conflito de barramento
      int16_t bank = int16_t(o >> 13);
      if (bank != cur_chr_) {
        uint8_t v = (mapper_ == 11 || mapper_ == 78) ? uint8_t(bank << 4) : uint8_t(bank);   // 11 e 78: CHR nos bits 4-7
        nes_reg(v, (mapper_ == 70 || mapper_ == 78) ? 0xC000 : 0x8000, (mapper_ == 70 || mapper_ == 78) ? 16384 : 2048);               // 70 e 78: varre o banco fixo
        cur_chr_ = bank;
      }
      return nes_->chr(uint16_t(o & 0x1FFF));
    }
    case 79: {                                                       // NINA-003/006: 8 KB, bits 0-2 de $4100
      int16_t bank = int16_t(o >> 13);
      if (bank != cur_chr_) { nes_->prg_write(0x4100, uint8_t(bank)); cur_chr_ = bank; }
      return nes_->chr(uint16_t(o & 0x1FFF));
    }
    case 87: {                                                       // J87: 8 KB em $6000, bits 0 e 1 trocados
      int16_t bank = int16_t(o >> 13);
      if (bank != cur_chr_) { nes_->prg_write(0x6000, uint8_t(((bank & 1) << 1) | ((bank & 2) >> 1))); cur_chr_ = bank; }
      return nes_->chr(uint16_t(o & 0x1FFF));
    }
    case 75: {                                                       // VRC1: 4 KB, bits 0-3 em $E000 (escrita segura) e bit 4 em $9000
      int16_t k = int16_t(o >> 12);
      if (k != cur_chr_) { nes_->reg_write_safe(0xE000, uint8_t(k & 0x0F)); nes_->prg_write(0x9000, uint8_t((k & 0x10) >> 3)); cur_chr_ = k; }
      return nes_->chr(uint16_t(o & 0x0FFF));
    }
    case 33: case 48: {                                              // Taito TC0190: 2 KB em $0000 pelo registrador $8002
      int16_t k = int16_t(o >> 11);
      if (k != cur_chr_) { nes_->prg_write(0x8002, uint8_t(k)); cur_chr_ = k; }
      return nes_->chr(uint16_t(o & 0x07FF));
    }
    case 9: case 10: {                                               // MMC2/MMC4: 4 KB em $0000; os dois latches (FD/FE) recebem o mesmo banco
      int16_t k = int16_t(o >> 12);
      if (k != cur_chr_) { nes_->prg_write(0xB000, uint8_t(k)); nes_->prg_write(0xC000, uint8_t(k)); cur_chr_ = k; }
      return nes_->chr(uint16_t(o & 0x0FFF));
    }
    case 69: {                                                       // FME-7: comando 0 = banco de 1 KB em $0000
      int16_t k = int16_t(o >> 10);
      if (k != cur_chr_) { nes_->prg_write(0x8000, 0); nes_->prg_write(0xA000, uint8_t(k)); cur_chr_ = k; }
      return nes_->chr(uint16_t(o & 0x03FF));
    }
    case 5: {                                                        // MMC5, modo 0: 8 KB; $5130 = bits altos do banco (0)
      int16_t bank = int16_t(o >> 13);
      if (bank != cur_chr_) { nes_->prg_write(0x5130, 0); nes_->prg_write(0x5127, uint8_t(bank)); cur_chr_ = bank; }
      return nes_->chr(uint16_t(o & 0x1FFF));
    }
    case 1: {
      int16_t k = int16_t(o >> 12);                                  // 4 KB por vez
      if (k != cur_chr_) { mmc1_write(0xA000, uint8_t(k)); cur_chr_ = k; }
      return nes_->chr(uint16_t(o & 0x0FFF));
    }
    case 4: case 118: case 206: {
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
  if (!probe(sys, c, kind == KIND_SAVE)) { release(); err = (c.status == 2) ? E_SISTEMA : (c.status == 3 ? E_ARGUMENTO : E_SEM_CARTUCHO); return false; }
  if (kind == KIND_SAVE) {
    if ((sys != SYS_SNES && sys != SYS_GBA && sys != SYS_MD && sys != SYS_NES && sys != SYS_FAMICOM && sys != SYS_GB) || c_.save == 0) { release(); err = E_SEM_SAVE; return false; }
    if (sys == SYS_MD && c_.md_save != 4) md_sram(true);
    if (sys == SYS_NES || sys == SYS_FAMICOM) nes_ram(true);
    if (sys == SYS_GB) gb_ram_enable();
    if (sys == SYS_SNES && c_.hirom && !c_.spc7110) snes_->cs(true);
    if (sys == SYS_SNES && c_.spc7110) { snes_->write(0, 0x4830, 0x80); spc_sram_ = true; }   // SPC7110: libera a SRAM (sem CS alto)
    size = c_.save;
  } else {
    size = c_.rom;
  }
  return true;
}

void CartBackend::snes_save_addr(uint32_t i, uint8_t& bank, uint16_t& addr) const {
  if (c_.sfx) { bank = uint8_t(0x70 + (i >> 16)); addr = uint16_t(i & 0xFFFF); }   // SuperFX: bancos de 64 KB
  else if (c_.sa1) { bank = uint8_t(0x40 + (i >> 16)); addr = uint16_t(i & 0xFFFF); }   // BW-RAM: 64 KB por banco a partir de $40
  else if (c_.exhirom) { bank = uint8_t(0xB0 + (i >> 13)); addr = uint16_t(0x6000 + (i & 0x1FFF)); }
  else if (c_.hirom) { bank = uint8_t(0x30 + (i >> 13)); addr = uint16_t(0x6000 + (i & 0x1FFF)); }
  else { bank = uint8_t(0x70 + (i >> 15)); addr = uint16_t(i & 0x7FFF); }
}

bool CartBackend::read(uint8_t sys, uint8_t kind, uint32_t off, uint8_t* buf, uint16_t len) {
  if (active_ != sys) return false;
  for (uint16_t i = 0; i < len; i++) {
    if (kind == KIND_SAVE && (sys == SYS_NES || sys == SYS_FAMICOM)) {
      uint16_t a = nes_ram_addr(off + i);
      buf[i] = mapper_ == 5 ? nes_->ram(a) : nes_->prg(a);
    } else if (kind == KIND_SAVE && sys == SYS_MD && c_.md_save == 4) {
      if (!md_eep_read(uint16_t(off + i), buf[i])) return false;
    } else if (kind == KIND_SAVE && sys == SYS_MD) {
      buf[i] = md_save_byte(off + i);
    } else if (kind == KIND_SAVE && sys == SYS_GB) {
      buf[i] = gb_->sram_read(gb_ram_addr(off + i), c_.gb_type == 0xFC);
    } else if (kind == KIND_SAVE && sys == SYS_GBA) {
      buf[i] = gba_save_byte(off + i);
    } else if (kind == KIND_SAVE) {
      uint8_t bank; uint16_t addr;
      snes_save_addr(off + i, bank, addr);
      buf[i] = snes_->read(bank, addr);
    } else {
      buf[i] = byte_at(sys, off + i);
    }
  }
  return true;
}

bool CartBackend::md_eep_write(uint16_t address, uint8_t value) {   // writeEepromByte do OSCR
  uint8_t hi = uint8_t(address >> 8), lo = uint8_t(address & 0xFF);
  bool ok = true;
  if (c_.md_eep == 2) md_->eep_enable(true);
  eep_start();
  if (c_.md_eep_size > 0x80) {
    if (c_.md_eep_size > 0x800) ok = eep_device(0, true) && eep_set_address(hi);
    else ok = eep_device(hi, true);
    ok = ok && eep_set_address(lo);
  } else {                                                  // 24C01: endereço de 7 bits, depois o bit R/W = 0
    eep_set_address(lo);
    eep_set(0);
    ok = eep_status();
  }
  if (ok) {
    for (int i = 0; i < 8; i++) eep_set((value >> (7 - i)) & 1);
    ok = eep_status();
  }
  eep_stop();
  if (c_.md_eep == 2) md_->eep_enable(false);
  // O OSCR espera 50 ms por byte e não confere o ACK do próximo acesso: o ciclo de escrita (5 a 10 ms) precisa acabar antes.
  md_->wait_ms(c_.md_eep_size <= 0x100 ? 20 : 10);
  return ok;
}

// ---------------------------------------------------------------- GBA: gravação de SRAM, Flash e EEPROM
void CartBackend::gba_cmd(uint8_t c) {
  gba_->sram_write(0x5555, 0xAA); gba_->sram_write(0x2AAA, 0x55); gba_->sram_write(0x5555, c);
}

uint16_t CartBackend::gba_flash_id() {                     // idFlash_GBA + resetFLASH_GBA do OSCR
  gba_cmd(0x90);
  uint16_t id = uint16_t(gba_->sram_read(0) << 8);
  id |= gba_->sram_read(1);
  gba_->sram_write(0x5555, 0xAA); gba_->sram_write(0x2AAA, 0x55); gba_->sram_write(0x5555, 0xF0); gba_->sram_write(0x5555, 0xF0);
  gba_->wait_ms(100);
  return id;
}

bool CartBackend::gba_blank_check() {                      // blankcheckFLASH_GBA do OSCR (pula o que o e-Reader não deixa gravar)
  for (uint32_t i = 0; i < c_.save; i++) {
    if (c_.gba_skip && (i & 0xFFFF) >= 0xFF80) continue;
    if (gba_save_byte(i) != 0xFF) return false;
  }
  return true;
}

bool CartBackend::gba_flash_prepare() {
  uint16_t id = gba_flash_id();
  bool known = c_.gba_type == 4 ? (id == 0x1F3D || id == 0xBFD4 || id == 0xC21C || id == 0x321B)   // Atmel, SST, Macronix, Panasonic
                                : (id == 0xC209 || id == 0x6213);                                  // Macronix, Sanyo (128 KB)
  if (!known) return false;                                // chip desconhecido: não arrisca comandos de apagar
  gba_atmel_ = (id == 0x1F3D);
  if (gba_atmel_) return true;                             // a página Atmel se apaga sozinha
  gba_cmd(0x80); gba_cmd(0x10);                            // apaga o chip inteiro
  for (uint16_t n = 0; n < 500; n++) {                     // DQ7 = 1 quando termina (até 5 s)
    gba_->wait_ms(10);
    if (gba_->sram_read(0) == 0xFF) break;
  }
  if (c_.gba_type == 5 && gba_bank_ != 0) gba_flash_bank(0);
  return gba_blank_check();
}

bool CartBackend::gba_flash_program(uint32_t off, uint8_t v) {
  if (c_.gba_skip && (off & 0xFFFF) >= 0xFF80) return true;
  if (c_.gba_type == 5) { uint8_t bank = uint8_t(off >> 16); if (bank != gba_bank_) gba_flash_bank(bank); }
  uint16_t a = uint16_t(off & 0xFFFF);
  gba_cmd(0xA0);
  gba_->sram_write(a, v);
  for (uint16_t n = 0; n < 5000; n++) if (gba_->sram_read(a) == v) return true;   // o OSCR espera para sempre; aqui há limite
  return false;
}

bool CartBackend::gba_write(uint32_t off, const uint8_t* buf, uint16_t len) {
  uint8_t unit = (c_.gba_type == 1 || c_.gba_type == 2) ? 8 : (c_.gba_type == 4 && gba_atmel_ ? 128 : 0);
  for (uint16_t i = 0; i < len; i++) {
    uint32_t o = off + i;
    if (unit == 0) {
      if (c_.gba_type == 3) { gba_->sram_write(uint16_t(o), buf[i]); if (gba_->sram_read(uint16_t(o)) != buf[i]) return false; }
      else if (!gba_flash_program(o, buf[i])) return false;
      continue;
    }
    wbuf_[o % unit] = buf[i];
    if ((o + 1) % unit != 0) continue;                     // unidade ainda incompleta
    uint32_t base = o + 1 - unit;
    if (unit == 8) {                                       // EEPROM: bloco de 8 bytes, conferido na hora
      uint8_t back[8]; bool big = c_.gba_type == 2; uint16_t blk = uint16_t(base / 8);
      if (!gba_->eeprom_write_block(blk, big, wbuf_)) return false;
      gba_->eeprom_block(blk, big, back);
      if (memcmp(back, wbuf_, 8) != 0) return false;
    } else {                                               // Flash Atmel: página de 128 bytes
      gba_cmd(0xA0);
      for (uint8_t k = 0; k < 128; k++) gba_->sram_write(uint16_t(base + k), wbuf_[k]);
      gba_->wait_ms(15);
      for (uint8_t k = 0; k < 128; k++) if (gba_->sram_read(uint16_t(base + k)) != wbuf_[k]) return false;
    }
  }
  return true;
}

// ---------------------------------------------------------------- Mega Drive: EEPROM serial (I2C), leitura
// Linhas SDA/SCL e leitura do SDA por tipo de cartucho (EepromStart, EepromSet0... do OSCR). Endereços em palavras.
static const uint32_t EEP_ADDR = 0x100000UL, EEP_CM_WR = 0x180000UL, EEP_CM_RD = 0x1C0000UL;

void CartBackend::eep_state(uint8_t st) {
  bool sda = st & 1, scl = st & 2;
  switch (c_.md_eep) {
    case 4: md_->write_word(EEP_ADDR, uint16_t((sda ? 0x80 : 0) | (scl ? 0x40 : 0))); break;     // D7 = SDA, D6 = SCL
    case 5: md_->eep_cm(EEP_CM_WR, uint16_t(st & 3)); break;                                      // D0 = SDA, D1 = SCL
    default: md_->write_word(EEP_ADDR, uint16_t(st & 3)); break;                                  // tipos 1 e 3
  }
}

void CartBackend::eep_run(const char* gen, const char* t2) {
  bool slow = c_.md_eep_size <= 0x100;
  if (c_.md_eep != 2) { for (; *gen; gen++) eep_state(uint8_t(*gen - '0')); return; }
  for (; *t2; t2++) {                                      // a/b: SDA 0/1; c/d: SCL 0/1
    if (*t2 == 'a' || *t2 == 'b') md_->eep_sda(EEP_ADDR, *t2 == 'b', slow);
    else md_->eep_scl(EEP_ADDR, *t2 == 'd', slow);
  }
}

void CartBackend::eep_start() { eep_run(c_.md_eep == 5 ? "02320" : "0320", "acbdac"); }
void CartBackend::eep_finish() { eep_run("01310", "acbcbdbcac"); }
void CartBackend::eep_stop() { eep_run("02310", "adbdbcac"); }
void CartBackend::eep_set(bool one) { if (one) eep_run("1310", "bdbc"); else eep_run("020", "adac"); }

bool CartBackend::eep_sda_in() {
  switch (c_.md_eep) {
    case 1: return (md_->word(EEP_ADDR) >> 1) & 1;
    case 4: return (md_->word(EEP_ADDR) >> 7) & 1;
    case 5: return (md_->word(EEP_CM_RD) >> 7) & 1;
    default: return md_->word(EEP_ADDR) & 1;               // tipos 2 e 3
  }
}

bool CartBackend::eep_status() {                            // 9º pulso: espera o ACK (SDA baixo)
  eep_run("13", "bd");
  bool ack = false;
  for (uint16_t n = 0; n < 2000 && !ack; n++) ack = !eep_sda_in();   // o OSCR espera para sempre; aqui há limite
  eep_run("1", "c");
  return ack;
}

bool CartBackend::eep_device(uint16_t page, bool write_mode) {   // 1010 + A2..A0
  eep_set(1); eep_set(0); eep_set(1); eep_set(0);
  for (int i = 0; i < 3; i++) { eep_set((page >> 2) & 1); page <<= 1; }
  eep_set(!write_mode);
  return eep_status();
}

bool CartBackend::eep_set_address(uint16_t address) {
  if (c_.md_eep_size > 0x80) {                              // 24C02 ou maior: 8 bits + ACK
    for (int i = 0; i < 8; i++) { eep_set((address >> 7) & 1); address <<= 1; }
    return eep_status();
  }
  for (int i = 0; i < 7; i++) { eep_set((address >> 6) & 1); address <<= 1; }   // 24C01: 7 bits, sem ACK
  return true;
}

bool CartBackend::md_eep_read(uint16_t address, uint8_t& out) {   // readEepromByte do OSCR
  uint8_t hi = uint8_t(address >> 8), lo = uint8_t(address & 0xFF);
  bool ok = true;
  if (c_.md_eep == 2) md_->eep_enable(true);
  eep_start();
  if (c_.md_eep_size > 0x80) {
    if (c_.md_eep_size > 0x800) ok = eep_device(0, true) && eep_set_address(hi);      // 24C65: A2..A0 = 000, endereço de 16 bits
    else ok = eep_device(hi, true);                                                    // 24C02/08/16: bits altos no byte de dispositivo
  }
  ok = ok && eep_set_address(lo);
  if (ok && c_.md_eep_size > 0x80) {
    eep_start();
    ok = eep_device(c_.md_eep_size > 0x800 ? 0 : hi, false);
  } else if (ok) {                                            // 24C01: o bit R/W vem logo depois do endereço
    eep_set(1);
    ok = eep_status();
  }
  uint8_t v = 0;
  if (ok) {
    for (int i = 0; i < 8; i++) {
      eep_run("3", "bd");
      v = uint8_t((v << 1) | (eep_sda_in() ? 1 : 0));
      eep_run("1", "bc");
    }
    eep_finish();
  }
  eep_stop();
  if (c_.md_eep == 2) md_->eep_enable(false);
  out = v;
  return ok;
}

// ---------------------------------------------------------------- GBA: SRAM, Flash e EEPROM (só leitura)
void CartBackend::gba_flash_bank(uint8_t bank) {   // switchBank_GBA do OSCR (Macronix/Sanyo de 128 KB)
  gba_->sram_write(0x5555, 0xAA); gba_->sram_write(0x2AAA, 0x55); gba_->sram_write(0x5555, 0xB0); gba_->sram_write(0x0000, bank);
  gba_bank_ = bank;
}

uint8_t CartBackend::gba_save_byte(uint32_t i) {
  switch (c_.gba_type) {
    case 1: case 2: {                                    // EEPROM: blocos de 8 bytes
      int32_t blk = int32_t(i >> 3);
      if (blk != gba_eep_blk_) { gba_->eeprom_block(uint16_t(blk), c_.gba_type == 2, gba_eep_); gba_eep_blk_ = blk; }
      return gba_eep_[i & 7];
    }
    case 5: {                                            // Flash 128 KB: dois bancos de 64 KB
      uint8_t bank = uint8_t(i >> 16);
      if (bank != gba_bank_) gba_flash_bank(bank);
      return gba_->sram_read(uint16_t(i & 0xFFFF));
    }
    default: return gba_->sram_read(uint16_t(i));        // SRAM 32 KB e Flash 64 KB: leitura direta em /CS2
  }
}

// ---------------------------------------------------------------- Mega Drive: SRAM
void CartBackend::md_sram(bool on) {
  md_->map_write(0x509878UL, on ? 1 : 0);        // $A130F1 bit 0: liga a SRAM em $200000-$3FFFFF
  md_sram_on_ = on;
}

uint8_t CartBackend::md_save_byte(uint32_t i) {
  if (c_.md_save == 3) { uint16_t w = md_->word(c_.md_base + (i >> 1)); return (i & 1) ? uint8_t(w & 0xFF) : uint8_t(w >> 8); }
  uint16_t w = md_->word(c_.md_base + i);
  return c_.md_save == 1 ? uint8_t(w & 0xFF) : uint8_t(w >> 8);
}

void CartBackend::md_save_set(uint32_t i, uint8_t v) {
  if (c_.md_save == 1) md_->write_word(c_.md_base + i, v);
  else if (c_.md_save == 2) md_->write_word(c_.md_base + i, uint16_t(v) << 8);
  else {                                          // ambos os bytes: monta a palavra (alto, baixo)
    if ((i & 1) == 0) md_hi_ = v;
    else md_->write_word(c_.md_base + (i >> 1), uint16_t(md_hi_ << 8) | v);
  }
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

void CartBackend::snes_clocks_boot() {
  snes_->clocks_boot();
  clocks_on_ = true;
  for (uint16_t i = 0; i < 1024; i++) snes_->read(0xC0, i);          // "primeira leitura" do cartucho, como getCartInfo_SNES do OSCR
}

bool CartBackend::sa1_finish() {
  if (active_ != SYS_SNES || !c_.sa1 || sa1_blk_ < 0) return true;
  snes_->write(0, 0x2224, 0); snes_->write(0, 0x2226, 0x80);         // bloco 0 outra vez
  for (int8_t c = 15; c >= 0; c--) snes_->write(0, uint16_t(0x6000 + c), sa1_first_[c]);   // do último ao primeiro (corrige PGA Tour 96)
  bool ok = true;
  for (uint8_t c = 0; c < 16; c++) if (snes_->read(0, uint16_t(0x6000 + c)) != sa1_first_[c]) ok = false;
  sa1_blk_ = -1;
  return ok;
}

// ---------------------------------------------------------------- escrita de save (SNES SRAM)
bool CartBackend::write_begin(uint8_t sys, uint32_t size, uint16_t& err) {
  if (!supports(sys)) { err = E_SISTEMA; return false; }
  if (sys != SYS_SNES && sys != SYS_MD && sys != SYS_NES && sys != SYS_FAMICOM && sys != SYS_GBA && sys != SYS_GB) { err = E_SEM_SAVE; return false; }
  Cart c;
  if (!probe(sys, c, true)) { release(); err = (c.status == 2) ? E_SISTEMA : (c.status == 3 ? E_ARGUMENTO : E_SEM_CARTUCHO); return false; }
  if (c_.save == 0) { release(); err = E_SEM_SAVE; return false; }
  if (size != c_.save) { release(); err = E_ARGUMENTO; return false; }
  if (sys == SYS_MD && c_.md_save != 4) md_sram(true);
  if (sys == SYS_NES || sys == SYS_FAMICOM) nes_ram(true);
  if (sys == SYS_GB) gb_ram_enable();
  if (sys == SYS_SNES && c_.hirom && !c_.sa1 && !c_.spc7110) snes_->cs(true);
  if (sys == SYS_SNES && c_.spc7110) { snes_->write(0, 0x4830, 0x80); spc_sram_ = true; }
  if (sys == SYS_SNES && c_.sa1) {                                   // BW-RAM do SA-1: com o clock do CPU ligado, janela em $6000 pelo registrador $2224
    snes_->cpu_clock(true);
    snes_->write(0, 0x2224, 0);                                      // BMAPS: bloco 0
    snes_->write(0, 0x2226, 0x80);                                   // SBWE: gravação liberada
    snes_->write(0, 0x2228, 0);                                      // BWPA: sem área protegida
    snes_->wait_ms(1000);
    sa1_blk_ = 0;
  }
  if (sys == SYS_GBA && (c_.gba_type == 4 || c_.gba_type == 5) && !gba_flash_prepare()) { release(); err = E_CARTUCHO_IO; return false; }
  return true;
}

bool CartBackend::write_block(uint32_t off, const uint8_t* buf, uint16_t len) {
  if (active_ == SYS_GBA) return gba_write(off, buf, len);
  if (active_ == SYS_GB) {                                                     // grava e confere cada byte (MBC2 só guarda 4 bits)
    bool cam = c_.gb_type == 0xFC, mbc2 = c_.gb_type == 5 || c_.gb_type == 6;
    for (uint16_t i = 0; i < len; i++) {
      uint16_t a = gb_ram_addr(off + i);
      gb_->sram_write(a, buf[i], cam);
      uint8_t r = gb_->sram_read(a, cam);
      if (mbc2 ? ((r & 0x0F) != (buf[i] & 0x0F)) : (r != buf[i])) return false;
    }
    return true;
  }
  if (active_ == SYS_MD && c_.md_save == 4) {                                  // EEPROM serial: só grava o que mudou, e confere
    for (uint16_t i = 0; i < len; i++) {
      uint16_t a = uint16_t(off + i); uint8_t cur;
      if (!md_eep_read(a, cur)) return false;
      if (cur == buf[i]) continue;
      if (!md_eep_write(a, buf[i]) || !md_eep_read(a, cur) || cur != buf[i]) return false;
    }
    return true;
  }
  if (active_ == SYS_NES || active_ == SYS_FAMICOM) {
    for (uint16_t i = 0; i < len; i++) {
      uint16_t a = nes_ram_addr(off + i);
      if (mapper_ == 5) {                                        // MMC5: libera a proteção ($5102/$5103) e grava com a sequência wram; até 4 tentativas (o OSCR repete sem limite)
        bool ok = false;
        for (uint8_t t = 0; t < 4 && !ok; t++) {
          nes_->prg_write(0x5102, 2); nes_->prg_write(0x5103, 1);
          nes_->ram_write(a, buf[i]);
          ok = nes_->ram(a) == buf[i];
        }
        if (!ok) return false;
        continue;
      }
      nes_->prg_write(a, buf[i]);
      if (nes_->prg(a) != buf[i]) return false;                  // confere; sem RAM ou protegida = erro
    }
    if (mapper_ == 5) { nes_->prg_write(0x5102, 0); nes_->prg_write(0x5103, 0); }   // protege de novo
    return true;
  }
  if (active_ == SYS_MD) {
    for (uint16_t i = 0; i < len; i++) {
      md_save_set(off + i, buf[i]);
      if ((i & 1) || c_.md_save != 3) {                           // confere; no modo "ambos" a palavra só fecha no 2º byte
        if (md_save_byte(off + i) != buf[i]) return false;
        if (c_.md_save == 3 && md_save_byte(off + i - 1) != buf[i - 1]) return false;
      }
    }
    return true;
  }
  if (active_ != SYS_SNES) return false;
  if (active_ == SYS_SNES && c_.sa1) {                               // BW-RAM do SA-1 pela janela de $6000 (gravar direto em $40+ não funciona)
    for (uint16_t i = 0; i < len; i++) {
      uint32_t o = off + i;
      int16_t blk = int16_t(o >> 13);
      if (blk != sa1_blk_) { snes_->write(0, 0x2224, uint8_t(blk)); snes_->write(0, 0x2226, 0x80); sa1_blk_ = blk; }
      uint16_t a = uint16_t(0x6000 + (o & 0x1FFF));
      snes_->write(0, a, buf[i]);
      if (o < 16) sa1_first_[o] = buf[i];                            // os 16 primeiros saem errados com frequência: regravados e conferidos no fim
      else if (snes_->read(0, a) != buf[i]) return false;
    }
    return true;
  }
  for (uint16_t i = 0; i < len; i++) {
    uint8_t bank; uint16_t addr;
    snes_save_addr(off + i, bank, addr);
    snes_->write(bank, addr, buf[i]);
    if (snes_->read(bank, addr) != buf[i]) return false;       // confere o que gravou
  }
  return true;
}

}  // namespace oscr
