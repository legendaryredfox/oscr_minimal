// SPDX-License-Identifier: GPL-3.0-or-later
// GBA: cabeçalho, ROM, SRAM, Flash e EEPROM (leitura e gravação).
#include "oscr_carts_internal.h"

namespace oscr {

bool CartBackend::probe_gba(uint8_t sys, Cart& o, bool for_save) {
  (void)sys; (void)for_save;
  uint8_t h[48]; (void)h;
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

uint8_t CartBackend::gba_byte(uint32_t off) {
  uint16_t w = gba_->word(off & ~1UL);
  return (off & 1) ? uint8_t(w >> 8) : uint8_t(w & 0xFF);
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

}  // namespace oscr
