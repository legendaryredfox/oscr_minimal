// SPDX-License-Identifier: GPL-3.0-or-later
// Backend dos cartuchos: dispatch, leitura e gravação de save comuns a todos os sistemas.
#include "oscr_carts_internal.h"

namespace oscr {

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
    case SYS_SNES: return snes_byte(off);
    case SYS_NES: case SYS_FAMICOM: return nes_byte(off);
    case SYS_MD: return md_byte(off);
    case SYS_GB: return gb_byte(off);
    case SYS_GBA: return gba_byte(off);
  }
  return 0xFF;
}

// ---------------------------------------------------------------- detecção (o cabeçalho de cada sistema fica em oscr_carts_<sistema>.cpp)
bool CartBackend::probe(uint8_t sys, Cart& o, bool for_save) {
  o = Cart();
  c_ = o;
  acquire(sys);
  if (sys == SYS_SNES) return probe_snes(sys, o, for_save);
  if (sys == SYS_NES || sys == SYS_FAMICOM) return probe_nes(sys, o, for_save);
  if (sys == SYS_GB) return probe_gb(sys, o, for_save);
  if (sys == SYS_MD) return probe_md(sys, o, for_save);
  if (sys == SYS_GBA) return probe_gba(sys, o, for_save);
  return false;
}

void CartBackend::detect(uint8_t sys, DetectInfo& out) {
  if (!supports(sys)) { out.status = 2; return; }
  Cart c;
  opt_mapper_ = opt_prg_ = opt_chr_ = 0;   // DETECT nunca usa opções
  probe(sys, c);
  release();
  out.status = c.status; out.rom_size = c.rom; out.save_size = c.save; out.save_type = c.save_type;
  strncpy(out.name, c.name, 32); out.name[32] = 0;
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

bool CartBackend::read(uint8_t sys, uint8_t kind, uint32_t off, uint8_t* buf, uint16_t len) {
  if (active_ != sys) return false;
  if (sys == SYS_GBA && kind == KIND_ROM) {                          // uma leitura de 16 bits por duas posições (em vez de uma por byte)
    uint16_t i = 0;
    if ((off & 1) && len) { buf[0] = gba_byte(off); i = 1; }
    for (; i + 1 < len; i += 2) { uint16_t w = gba_->word((off + i) & ~1UL); buf[i] = uint8_t(w & 0xFF); buf[i + 1] = uint8_t(w >> 8); }
    if (i < len) buf[i] = gba_byte(off + i);
    return true;
  }
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
