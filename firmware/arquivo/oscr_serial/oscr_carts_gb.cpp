// SPDX-License-Identifier: GPL-3.0-or-later
// Game Boy / Game Boy Color: cabeçalho, ROM por mapper e SRAM.
#include "oscr_carts_internal.h"

namespace oscr {

bool CartBackend::probe_gb(uint8_t sys, Cart& o, bool for_save) {
  (void)sys; (void)for_save;
  uint8_t h[48]; (void)h;
    uint8_t g[80];
    bool ok = false;
    if (mmm_mapped_) { gb_->begin(); mmm_mapped_ = false; }          // MMM01 já mapeado mostraria o jogo, não o menu: reinicia o cartucho
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
    {                                                                  // MMM01 de 4 coletâneas Mani/Taito cujo cabeçalho de menu não diz o mapper (tabela do OSCR)
      static const struct { const char* name; uint8_t len, sum; } mmm[] = {{"BOUKENJIMA2 SET", 15, 0x00}, {"BUBBLEBOBBLE SET", 16, 0xC6}, {"GANBARUGA SET", 13, 0x90}, {"RTYPE 2 SET", 11, 0x32}};
      for (uint8_t k = 0; k < 4; k++) if (strncmp(reinterpret_cast<const char*>(&g[0x34]), mmm[k].name, mmm[k].len) == 0 && g[0x4D] == mmm[k].sum) { type = 0x0B; t = 0x0B; }
    }
    if (type >= 1 && type <= 3) {                                      // MBC1M: não dá para saber pelo cabeçalho, tabela de títulos do OSCR
      static const struct { const char* name; uint8_t len, sum; } mm[] = {{"MOMOCOL", 7, 0x28}, {"BOMCOL", 6, 0x86}, {"GENCOL", 6, 0x8A}, {"SUPERCHINESE 123", 16, 0xE4}, {"MORTALKOMBATI&II", 16, 0xB9}, {"MORTALKOMBAT DUO", 16, 0xA7}};
      for (uint8_t k = 0; k < 6; k++) if (strncmp(reinterpret_cast<const char*>(&g[0x34]), mm[k].name, mm[k].len) == 0 && g[0x4D] == mm[k].sum) t = uint16_t(0x100 + type);
    }
    bool known = type == 0x00 || (type >= 1 && type <= 3) || type == 5 || type == 6 || (type >= 0x0B && type <= 0x0D) || type == 8 || type == 9 || (type >= 0x0F && type <= 0x13)
                 || (type >= 0x19 && type <= 0x1E) || type == 0x20 || type == 0x22 || type == 0xFC || type == 0xFD || type == 0xFE || type == 0xFF;
    if (!known || rsz > 8) { o.status = 2; copy_ascii(o.name, &g[0x34], 15); return false; }   // M161 e tamanhos fora da tabela
    if (type >= 0x0B && type <= 0x0D && rsz > 5) { o.status = 2; copy_ascii(o.name, &g[0x34], 15); return false; }   // MMM01: só até 1 MB (dois blocos de 512 KB; o OSCR repete o mesmo deslocamento acima disso)
    o.gb_type = t;
    o.rom = 16384UL << (rsz + 1);                                      // 2^(n+1) bancos de 16 KB
    uint16_t bank_bytes = 0; uint8_t banks = 0;
    if (type == 6) { bank_bytes = 512; banks = 1; o.gb_shift = 9; }    // MBC2: 512 x 4 bits
    else if (ssz == 1) { bank_bytes = 2048; banks = 1; o.gb_shift = 11; }
    else if (ssz >= 2 && ssz <= 5 && type != 5) { bank_bytes = 8192; banks = (ssz == 2) ? 1 : (ssz == 3 ? 4 : (ssz == 4 ? 16 : 8)); o.gb_shift = 13; }
    o.save = uint32_t(bank_bytes) * banks;
    if (type == 0x22) o.save = (g[0x4E] == 0xBE && g[0x4F] == 0xA5) ? 512 : 256;   // MBC7: EEPROM serial (o cabeçalho não diz o tamanho); só o Command Master tem 93LC66 (512 B), os outros 93LC56 (256 B)
    if (type == 0x20) o.save = 32768UL + 1048576UL;                    // MBC6: SRAM de 32 KB (8 bancos de 4 KB) + Flash de 1 MB (128 bancos de 8 KB)
    if (type == 0xFD) o.save = 0;                                      // TAMA5: tem 32 bytes de RAM interna, mas o OSCR não os lê
    o.save_type = o.save ? 1 : 0;
    uint8_t cgb = g[0x43], nlen = (cgb == 0x80 || cgb == 0xC0) ? 15 : 16;   // o título perde 1 byte quando $143 é a flag CGB
    copy_ascii(o.name, &g[0x34], nlen);
    o.status = 0;
    c_ = o;
    cur_prg_ = cur_chr_ = -1; mmm_chunk_ = -1; mbc6_flash_ = false; cur_flash_ = -1;
    return true;
}

void CartBackend::mmm01_map(uint8_t chunk) {                           // sequência do OSCR: reset, deslocamento do bloco de 512 KB e trava do mapper
  gb_->begin(); mmm_mapped_ = true;
  gb_->write(0x3FFF, uint8_t(chunk * 0x20)); gb_->write(0x5FFF, 0x40); gb_->write(0x7FFF, 0x01);
  gb_->write(0x1FFF, 0x3A); gb_->write(0x1FFF, 0x7A);
  mmm_chunk_ = int8_t(chunk); cur_prg_ = -1; cur_chr_ = -1;
}

uint8_t CartBackend::gb_byte(uint32_t off) {
  if (c_.gb_type == 0x20) {                                            // MBC6: banco A de 8 KB em $4000-$5FFF (ROM = $2800/$3800 em 0); $0000-$3FFF fixo
    if (off < 0x4000UL) return gb_->read(uint16_t(off));
    int16_t b8 = int16_t(off >> 13);
    if (b8 != cur_prg_) { gb_->write(0x2800, 0); gb_->write(0x3800, 0); gb_->write(0x2000, uint8_t(b8)); gb_->write(0x3000, uint8_t(b8)); cur_prg_ = b8; }
    return gb_->read(uint16_t(0x4000 + (off & 0x1FFF)));
  }
  if (c_.gb_type >= 0x0B && c_.gb_type <= 0x0D) {                      // MMM01: blocos de 512 KB (32 bancos) com reset e novo deslocamento
    uint8_t chunk = uint8_t(off >> 19);
    if (chunk != mmm_chunk_) mmm01_map(chunk);
    int16_t lb = int16_t((off >> 14) & 31);
    if (lb == 0) return gb_->read(uint16_t(off & 0x3FFF));
    if (lb != cur_prg_) { gb_->write(0x6000, 0); gb_->write(0x2000, uint8_t(lb)); cur_prg_ = lb; }
    return gb_->read(uint16_t(0x4000 + (off & 0x3FFF)));
  }
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
  if (t == 0xFD) {                                                     // TAMA5: o banco entra por dois nibbles nos registradores $A001 (índice) e $A000 (valor), com a sequência de CS/CLK da câmera
    gb_->sram_write(0xA001, 0, true); gb_->sram_write(0xA000, uint8_t(bank & 0x0F), true);
    gb_->sram_write(0xA001, 1, true); gb_->sram_write(0xA000, uint8_t((bank >> 4) & 0x0F), true);
  } else if (t >= 0x101 && t <= 0x103) {                                      // MBC1M
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
  bool mmm = c_.gb_type >= 0x0B && c_.gb_type <= 0x0D;
  if (mmm && mmm_chunk_ != 0) mmm01_map(0);                            // MMM01: precisa estar mapeado (sai do menu) para ver a RAM
  if (c_.gb_type <= 4 || mmm) gb_->write(0x6000, 1);                   // MBC1 e MMM01: modo de RAM
  gb_->write(0x0000, 0x0A);                                            // habilita a RAM
  if (c_.gb_type == 0x22) gb_->write(0x4000, 0x40);                    // MBC7: a EEPROM fica em $A080 com o banco $40
  gb_ram_on_ = true; cur_chr_ = -1; mbc7_wa_ = -1; mbc6_flash_ = false; cur_flash_ = -1;
}

// MBC6: $0000-$FFFF do save = SRAM (32 KB, bancos de 4 KB em $0400/$0800); depois a Flash de 1 MB, mapeada sobre a ROM ($0C00 liga, atrás da trava $1000)
void CartBackend::mbc6_mode(bool flash) {
  if (flash == mbc6_flash_) return;
  if (flash) {
    gb_->write(0x0000, 0x00);                                          // desliga a SRAM
    gb_->write(0x1000, 0x01); gb_->write(0x0C00, 0x01); gb_->write(0x1000, 0x00);   // libera, liga e trava de novo
    gb_->write(0x2800, 0x08); gb_->write(0x3800, 0x08);                // bancos A e B passam a mostrar a Flash
    cur_flash_ = -1;
  } else {
    gb_->write(0x1000, 0x01); gb_->write(0x0C00, 0x00); gb_->write(0x1000, 0x00);   // disableFlashSaveMemory do OSCR
    gb_->write(0x2800, 0x00); gb_->write(0x3800, 0x00);
    gb_->write(0x0000, 0x0A); cur_chr_ = -1;
  }
  mbc6_flash_ = flash;
}

uint8_t CartBackend::mbc6_save_byte(uint32_t off) {
  if (off < 0x8000UL) {
    mbc6_mode(false);
    int16_t b = int16_t(off >> 12);
    if (b != cur_chr_) { gb_->write(0x0400, uint8_t(b)); gb_->write(0x0800, uint8_t(b)); cur_chr_ = b; }
    return gb_->sram_read(uint16_t(0xA000 + (off & 0xFFF)), false);
  }
  mbc6_mode(true);
  uint32_t f = off - 0x8000UL;
  int16_t fb = int16_t(f >> 13);
  if (fb != cur_flash_) { gb_->write(0x2000, uint8_t(fb)); gb_->write(0x3000, uint8_t(fb)); cur_flash_ = fb; }
  return gb_->read(uint16_t(0x4000 + (f & 0x1FFF)));
}

// MBC7: EEPROM serial 93LC56/66 por bit-bang em $A080 (bit 7 = CS, bit 6 = CLK, bit 1 = DI, bit 0 = DO); sequências do OSCR (GB.ino, sendMBC7EEPROM_Inst_GB)
void CartBackend::mbc7_inst(uint8_t op, uint8_t addr, uint16_t data) {
  bool send_data = false;
  op &= 3;
  if (op == 0) { addr &= 0xC0; if (addr == 0x40) send_data = true; } else if (op == 1) send_data = true;
  gb_->write(0xA080, 0x82); gb_->write(0xA080, 0xC2);                  // bit de início
  for (uint8_t i = 0; i < 2; i++, op = uint8_t(op << 1)) { uint8_t b = op & 0x02; gb_->write(0xA080, uint8_t(b | 0x80)); gb_->write(0xA080, uint8_t(b | 0xC0)); }
  for (uint8_t i = 0; i < 8; i++, addr = uint8_t(addr << 1)) { uint8_t b = uint8_t((addr & 0x80) >> 6); gb_->write(0xA080, uint8_t(b | 0x80)); gb_->write(0xA080, uint8_t(b | 0xC0)); }
  if (send_data) for (uint8_t i = 0; i < 16; i++, data = uint16_t(data << 1)) { uint8_t b = uint8_t((data & 0x8000) >> 14); gb_->write(0xA080, uint8_t(b | 0x80)); gb_->write(0xA080, uint8_t(b | 0xC0)); }
}

bool CartBackend::mbc7_read_word(uint8_t a, uint16_t& w) {
  if (mbc7_wa_ == a) { w = mbc7_w_; return true; }
  gb_->write(0xA080, 0x00); gb_->write(0xA080, 0x80);                  // CS alto
  mbc7_inst(2, a, 0);                                                  // READ
  uint16_t v = 0;
  for (uint8_t j = 0; j < 16; j++) { gb_->write(0xA080, 0x80); gb_->write(0xA080, 0xC0); v = uint16_t((v << 1) | (gb_->read(0xA080) & 1)); }
  gb_->write(0xA080, 0x00);
  mbc7_wa_ = a; mbc7_w_ = w = v;
  return true;
}

bool CartBackend::mbc7_wait_ready() {
  for (uint32_t n = 0; n < 100000UL; n++) {                            // o OSCR espera sem limite; aqui há um teto
    gb_->write(0xA080, 0x80); gb_->write(0xA080, 0xC0);
    if (gb_->read(0xA080) & 1) return true;
  }
  return false;
}

bool CartBackend::mbc7_write_word(uint8_t a, uint16_t w) {
  mbc7_wa_ = -1;
  gb_->write(0xA080, 0x00); gb_->write(0xA080, 0x80); mbc7_inst(0, 0xC0, 0); gb_->write(0xA080, 0x00);   // EWEN: libera a escrita
  gb_->write(0xA080, 0x80); mbc7_inst(1, a, w);                        // WRITE
  gb_->write(0xA080, 0x00); gb_->write(0xA080, 0x80);                  // CS baixo e alto: começa a gravar
  bool ok = mbc7_wait_ready();
  gb_->write(0xA080, 0x00); gb_->write(0xA080, 0x80); mbc7_inst(0, 0x00, 0); gb_->write(0xA080, 0x00);   // EWDS: protege de novo
  return ok;
}

bool CartBackend::mbc7_write_range(uint32_t off, const uint8_t* buf, uint16_t len) {
  uint16_t i = 0; uint32_t o = off;
  while (i < len) {
    uint8_t a = uint8_t(o >> 1); uint16_t w, nw;
    if (!mbc7_read_word(a, w)) return false;
    nw = w;
    if (!(o & 1)) { nw = uint16_t((nw & 0xFF00) | buf[i]); i++; o++; }
    if (i < len && (o & 1)) { nw = uint16_t((nw & 0x00FF) | (uint16_t(buf[i]) << 8)); i++; o++; }
    if (nw == w) continue;                                             // só grava o que mudou
    uint16_t chk;
    if (!mbc7_write_word(a, nw) || !mbc7_read_word(a, chk) || chk != nw) return false;
  }
  return true;
}

uint16_t CartBackend::gb_ram_addr(uint32_t off) {
  int16_t b = int16_t(off >> c_.gb_shift);
  if (b != cur_chr_) { gb_->write(0x4000, uint8_t(b)); cur_chr_ = b; }
  return uint16_t(0xA000 + (off & ((1UL << c_.gb_shift) - 1)));
}

}  // namespace oscr
