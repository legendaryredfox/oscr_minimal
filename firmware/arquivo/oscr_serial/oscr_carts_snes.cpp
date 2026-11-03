// SPDX-License-Identifier: GPL-3.0-or-later
// SNES: cabeçalho, ROM (LoROM, HiROM, ExHiROM, SA-1, SuperFX, S-DD1, SPC7110, Cx4), SRAM e clocks do SA-1.
#include "oscr_carts_internal.h"

namespace oscr {

bool CartBackend::probe_snes(uint8_t sys, Cart& o, bool for_save) {
  (void)sys; (void)for_save;
  uint8_t h[48]; (void)h;
    snes_->cs(false);                                                // volta ao padrão (ROM); a SRAM de HiROM/ExHiROM sobe o CS depois
    bool good = false;
    for (uint8_t pass = 0; pass < 2 && !good; pass++) {
      for (uint8_t i = 0; i < 32; i++) h[i] = snes_->read(0x00, uint16_t(0xFFC0 + i));
      uint16_t comp = h[0x1C] | (h[0x1D] << 8), sum = h[0x1E] | (h[0x1F] << 8);
      good = !all_same(h, 32) && uint16_t(comp ^ sum) == 0xFFFF;
      if (!good && pass == 0 && !clocks_on_ && snes_->clocks_available()) snes_clocks_boot();   // SA-1 e afins só respondem com clock e CIC
    }
    if (!good) { o.status = all_same(h, 32) ? 1 : 4; return false; }   // 1 sem cartucho; 4 há dados mas o checksum do cabeçalho não confere
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

uint8_t CartBackend::snes_byte(uint32_t off) {
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
}

void CartBackend::snes_save_addr(uint32_t i, uint8_t& bank, uint16_t& addr) const {
  if (c_.sfx) { bank = uint8_t(0x70 + (i >> 16)); addr = uint16_t(i & 0xFFFF); }   // SuperFX: bancos de 64 KB
  else if (c_.sa1) { bank = uint8_t(0x40 + (i >> 16)); addr = uint16_t(i & 0xFFFF); }   // BW-RAM: 64 KB por banco a partir de $40
  else if (c_.exhirom) { bank = uint8_t(0xB0 + (i >> 13)); addr = uint16_t(0x6000 + (i & 0x1FFF)); }
  else if (c_.hirom) { bank = uint8_t(0x30 + (i >> 13)); addr = uint16_t(0x6000 + (i & 0x1FFF)); }
  else { bank = uint8_t(0x70 + (i >> 15)); addr = uint16_t(i & 0x7FFF); }
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

}  // namespace oscr
