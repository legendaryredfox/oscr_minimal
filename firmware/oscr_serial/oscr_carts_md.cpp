// SPDX-License-Identifier: GPL-3.0-or-later
// Mega Drive: cabeçalho, ROM (SSF2), SRAM e EEPROM serial.
#include "oscr_carts_internal.h"

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

bool CartBackend::probe_md(uint8_t sys, Cart& o, bool for_save) {
  (void)sys; (void)for_save;
  uint8_t h[48]; (void)h;
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

uint8_t CartBackend::md_byte(uint32_t off) {
  uint32_t a = off;
  if (c_.ssf && off >= 0x80000UL) {                                // SSF2: janela 1 ($080000-$0FFFFF) varre os bancos de 512 KB
    int16_t bank = int16_t(off >> 19);
    if (bank != md_bank_) { md_->map_write(0x509879UL, uint16_t(bank)); md_bank_ = bank; }
    a = 0x80000UL + (off & 0x7FFFFUL);
  }
  uint16_t w = md_->word(a >> 1);
  return (a & 1) ? uint8_t(w & 0xFF) : uint8_t(w >> 8);
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

}  // namespace oscr
