// SPDX-License-Identifier: GPL-3.0-or-later
// NES/Famicom: mappers, PRG-RAM e iNES sintético.
#include "oscr_carts_internal.h"

namespace oscr {

bool CartBackend::probe_nes(uint8_t sys, Cart& o, bool for_save) {
  (void)sys; (void)for_save;
  uint8_t h[48]; (void)h;
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
      if (m == 1 && (opt_prg_ > 256 || opt_chr_ > 128)) { o.status = 2; return false; }      // SUROM etc.; registrador de CHR de 5 bits
      if (m == 4 && (opt_prg_ > 512 || opt_chr_ > 256)) { o.status = 2; return false; }     // registradores de banco do MMC3 de 8 bits (CHR de 1 KB)
      if ((m == 9 || m == 10) && opt_chr_ > 128) { o.status = 2; return false; }            // registrador de CHR de 5 bits (4 KB)
      if (m == 69 && opt_chr_ > 256) { o.status = 2; return false; }                        // registrador de CHR de 8 bits (1 KB)
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

uint8_t CartBackend::nes_byte(uint32_t off) {
  if (off < 16) {                                  // cabeçalho iNES sintético
    uint8_t m = uint8_t(mapper_);
    uint8_t h[16] = {'N', 'E', 'S', 0x1A, uint8_t(c_.prg >> 14), uint8_t(c_.chr >> 13), uint8_t((m & 0x0F) << 4), uint8_t(m & 0xF0), 0, 0, 0, 0, 0, 0, 0, 0};
    return h[off];
  }
  uint32_t o = off - 16;
  return o < c_.prg ? nes_prg_byte(o) : nes_chr_byte(o - c_.prg);
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

}  // namespace oscr
