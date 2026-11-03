// SPDX-License-Identifier: GPL-3.0-or-later
// Testes do CartBackend com cartuchos simulados: cabeçalhos, tamanhos, mapeamento e SRAM.
#include <stdio.h>
#include <string.h>

#include <vector>

#include "../oscr_carts.h"

using namespace oscr;
static int g_fail = 0, g_n = 0;
#define CHECK(c) do { g_n++; if (!(c)) { g_fail++; printf("FALHOU %s:%d  %s\n", __FILE__, __LINE__, #c); } } while (0)

static uint8_t pat(uint32_t i) { return uint8_t((i * 2654435761u) >> 24) ^ uint8_t(i); }

// ---------------------------------------------------------------- SNES simulado
struct SimSnes : SnesBus {
  std::vector<uint8_t> rom, sram; bool hirom; bool absent = false, ex = false, cs_high = false;
  int special = 0;                                       // 1 SuperFX (BW-RAM em bancos de 64 KB), 2 S-DD1, 3 SPC7110, 4 Cx4
  uint8_t sdd1map = 5, r4830 = 0, r4833 = 2, r4834 = 0, cx4reg = 1, cx4want = 0; int cx4bad = 0;   // registradores dos chips
  void cs(bool high) override { cs_high = high; }
  SimSnes(bool hi, uint8_t rsz, uint8_t ssz, bool bad = false, bool exhi = false) : hirom(hi || exhi), ex(exhi) {
    rom.resize(1024UL << rsz); for (size_t i = 0; i < rom.size(); i++) rom[i] = pat(uint32_t(i));
    sram.assign(ssz ? 1024UL << ssz : 0, 0);
    size_t h = exhi ? 0x40FFC0 : (hi ? 0xFFC0 : 0x7FC0);   // posição do cabeçalho na ROM
    memset(&rom[h], ' ', 21); memcpy(&rom[h], "TESTE SNES", 10);
    rom[h + 0x15] = exhi ? 0x35 : (hi ? 0x21 : 0x20); rom[h + 0x16] = ssz ? 2 : 0; rom[h + 0x17] = rsz; rom[h + 0x18] = ssz;
    uint16_t sum = 0x1234, comp = bad ? 0x0000 : uint16_t(~sum);
    rom[h + 0x1C] = comp & 0xFF; rom[h + 0x1D] = comp >> 8; rom[h + 0x1E] = sum & 0xFF; rom[h + 0x1F] = sum >> 8;
  }
  void begin() override {} void end() override {}
  size_t sram_index(uint8_t b, uint16_t a, bool& ok) {
    ok = false;
    if (hirom && (special == 3 ? r4830 == 0x80 : cs_high) && !ex && b >= 0x30 && b <= 0x3F && a >= 0x6000 && a <= 0x7FFF) { ok = true; return size_t(b - 0x30) * 0x2000 + (a - 0x6000); }   // HiROM: só com CS alto
    if (ex && cs_high && b >= 0xB0 && b <= 0xBF && a >= 0x6000 && a <= 0x7FFF) { ok = true; return size_t(b - 0xB0) * 0x2000 + (a - 0x6000); }
    if (special == 1 && b >= 0x70 && b <= 0x7D) { ok = true; return (size_t(b - 0x70) << 16) | a; }               // SuperFX: 64 KB por banco
    if (!hirom && b >= 0x70 && b <= 0x7D && a < 0x8000) { ok = true; return size_t(b - 0x70) * 0x8000 + a; }
    return 0;
  }
  uint8_t read(uint8_t b, uint16_t a) override {
    if (absent) return 0xFF;
    bool ok; size_t si = sram_index(b, a, ok);
    if (ok) return si < sram.size() ? sram[si] : 0xFF;
    size_t off;
    if (special == 4 && b == 0 && a == 0x7F52) return cx4reg;
    if (special == 4 && b != 0 && cx4reg != cx4want) cx4bad++;
    if (special == 2 && b == 0 && a == 0x4807) return sdd1map;
    if (special == 2 && b >= 0xF0) return rom[(((size_t(sdd1map) << 20) | (size_t(b - 0xF0) << 16)) | a) % rom.size()];
    if (special == 3 && b >= 0xC0) {                       // SPC7110
      if (b < 0xE0) off = (size_t(b - 0xC0) << 16) | a;
      else if (b < 0xF0) off = (r4834 == 0xFF ? 0x200000 : 0) + ((size_t(b - 0xE0) << 16) | a);
      else off = (r4834 == 0xFF ? (r4833 == 3 ? 0x400000 : 0x300000) : 0) + ((size_t(b - 0xF0) << 16) | a);
      return rom[off % rom.size()];
    }
    if (!hirom && !ex && (b == 0x7E || b == 0x7F)) return 0xFF;   // WRAM do console
    if (ex) {                                              // ExHiROM: A22 invertido
      if (b >= 0xC0) off = (size_t(b - 0xC0) << 16) | a;
      else if (b >= 0x40 && b <= 0x7D) off = 0x400000 + ((size_t(b - 0x40) << 16) | a);
      else if (b <= 0x3F && a >= 0x8000) off = 0x400000 + ((size_t(b) << 16) | a);
      else if (b >= 0x80 && b <= 0xBF && a >= 0x8000) off = (size_t(b & 0x3F) << 16) | a;
      else return 0xFF;
    }
    else if (hirom) { if (b >= 0xC0 || (b <= 0x3F && a >= 0x8000)) off = (size_t(b & 0x3F) << 16) | a; else return 0xFF; }
    else { if (a < 0x8000) return 0xFF; off = (size_t(b & 0x7F) << 15) | (a & 0x7FFF); }
    return off < rom.size() ? rom[off] : rom[off % rom.size()];
  }
  void write(uint8_t b, uint16_t a, uint8_t v) override {
    if (b == 0) {
      if (special == 2 && a == 0x4807) sdd1map = v;
      if (special == 3 && a == 0x4830) r4830 = v;
      if (special == 3 && a == 0x4833) r4833 = v;
      if (special == 3 && a == 0x4834) r4834 = v;
      if (special == 4 && a == 0x7F52) cx4reg = v;
    }
    bool ok; size_t si = sram_index(b, a, ok); if (ok && si < sram.size()) sram[si] = v;
  }
};

// SA-1 simulado: o cabeçalho só aparece depois de clocks_boot (Si5351 + CIC); a ROM em $C0+ só com os clocks normais;
// a BW-RAM só grava pela janela de $6000 (BMAPS/SBWE) com o clock do CPU ligado; o primeiro byte gravado se perde (como na vida real, segundo o OSCR).
struct SimSa1 : SnesBus {
  std::vector<uint8_t> rom, bw; bool avail = true, booted = false, run = false, cpu = false, cs_high = false;
  uint8_t bmaps = 0, sbwe = 0; int boots = 0, stops = 0; bool first_lost = true; bool lose_first = true;
  SimSa1(uint8_t rsz, uint8_t ssz, bool bad = false) {
    rom.resize(1024UL << rsz); for (size_t i = 0; i < rom.size(); i++) rom[i] = pat(uint32_t(i) + 3);
    bw.assign(1024UL << ssz, 0);
    size_t h = 0x7FC0; memset(&rom[h], ' ', 21); memcpy(&rom[h], "SA1 TESTE", 9);
    rom[h + 0x15] = 0x23; rom[h + 0x16] = 0x35; rom[h + 0x17] = rsz; rom[h + 0x18] = ssz;
    uint16_t sum = 0x4321, comp = bad ? 0 : uint16_t(~sum);
    rom[h + 0x1C] = comp & 0xFF; rom[h + 0x1D] = comp >> 8; rom[h + 0x1E] = sum & 0xFF; rom[h + 0x1F] = sum >> 8;
  }
  void begin() override {} void end() override {}
  bool clocks_available() override { return avail; }
  void clocks_boot() override { booted = true; run = false; boots++; }
  void clocks_run() override { if (booted) run = true; }
  void cpu_clock(bool on) override { if (booted) cpu = on; }
  void clocks_stop() override { booted = run = cpu = false; stops++; }
  void cs(bool high) override { cs_high = high; }
  uint8_t read(uint8_t b, uint16_t a) override {
    if (!booted) return 0xFF;
    if (b >= 0x40 && b <= 0x4F) { size_t i = (size_t(b - 0x40) << 16) | a; return cs_high && i < bw.size() ? bw[i] : 0xFF; }
    if (b == 0 && a >= 0x6000 && a < 0x8000) { size_t i = size_t(bmaps) * 8192 + (a - 0x6000); return i < bw.size() ? bw[i] : 0xFF; }
    if (b >= 0xC0) return run ? rom[((size_t(b - 0xC0) << 16) | a) % rom.size()] : 0xFF;
    if (b <= 0x3F && a >= 0x8000) return rom[((size_t(b) << 15) | (a & 0x7FFF)) % rom.size()];
    return 0xFF;
  }
  void write(uint8_t b, uint16_t a, uint8_t v) override {
    if (b != 0) return;                                             // gravar direto em $40+ não faz nada
    if (a == 0x2224) bmaps = v; else if (a == 0x2226) sbwe = v;
    else if (a >= 0x6000 && a < 0x8000 && cpu && sbwe == 0x80) {
      if (lose_first && first_lost) { first_lost = false; return; }
      size_t i = size_t(bmaps) * 8192 + (a - 0x6000); if (i < bw.size()) bw[i] = v;
    }
  }
};

// Game Boy simulado: MBC1 (modos de banco e de RAM), MBC1M, MBC2 (512 x 4 bits), MBC3, MBC5 e sem mapper. O cartucho só entrega a RAM habilitada.
struct SimGb : GbBus {
  int type; std::vector<uint8_t> rom, ram; bool absent = false;
  uint8_t r2000 = 1, r4000 = 0, r3000 = 0, mode = 0; bool ram_en = false; int cam_wrong = 0, cam_calls = 0;
  SimGb(int t, uint8_t rsz, uint8_t ssz, const char* title = "TESTE GB", uint8_t cs_override = 0, bool use_cs = false) : type(t) {
    rom.resize(16384UL << ((rsz > 8 ? 8 : rsz) + 1)); for (size_t i = 0; i < rom.size(); i++) rom[i] = pat(uint32_t(i) + 21);   // rsz inválido só no cabeçalho
    memset(&rom[0x134], 0, 16); memcpy(&rom[0x134], title, strlen(title));
    rom[0x147] = uint8_t(t); rom[0x148] = rsz; rom[0x149] = ssz;
    uint8_t sum = 0; for (int i = 0x134; i < 0x14D; i++) sum = uint8_t(sum - rom[i] - 1);
    rom[0x14D] = sum;
    if (use_cs) {                                                     // checksum válido E igual ao pedido: ajusta a versão ($14C), como nos cartuchos reais da tabela
      for (int v = 0; v < 256; v++) { rom[0x14C] = uint8_t(v); uint8_t x = 0; for (int i = 0x134; i < 0x14D; i++) x = uint8_t(x - rom[i] - 1); if (x == cs_override) { rom[0x14D] = x; break; } }
    }
    size_t n = t == 6 ? 512 : (t == 0x22 ? 256 : (ssz == 1 ? 2048 : (ssz == 2 ? 8192 : (ssz == 3 ? 32768 : (ssz == 4 ? 131072 : (ssz == 5 ? 65536 : 0))))));
    ram.assign(n, 0);
    if (is_mmm()) mm_hdr();
    if (t == 0x20) { ram.assign(32768, 0); flash.assign(1 << 20, 0xFF); }
  }
  // MMM01: ao ligar mostra os últimos 32 KB (menu); depois da sequência de trava ($3A e $7A em $0000-$1FFF) vê o jogo no deslocamento escolhido
  bool mm_map = false; uint8_t mm_base = 0, mm_bank = 0; int begins = 0;
  bool is_mmm() const { return type >= 0x0B && type <= 0x0D; }
  void mm_hdr() { memcpy(&rom[rom.size() - 0x8000 + 0x100], &rom[0x100], 0x50); }   // o cabeçalho do menu fica no fim da ROM
  // MBC6: bancos de ROM de 8 KB (A em $4000, B em $6000), seleção ROM/Flash em $2800/$3800, SRAM em bancos de 4 KB, Flash atrás da trava $1000/$0C00
  std::vector<uint8_t> flash; uint8_t sel_a = 0, sel_b = 0, sram_a = 0, sram_b = 0; bool flash_map = false, fw_en = false;
  uint8_t tama_reg = 0, tama_bank = 1;
  // MBC7: EEPROM 93LC56/66 em $A080 (bit 7 CS, bit 6 CLK, bit 1 DI, bit 0 DO), modelada pelo datasheet e não pelo código do firmware
  bool e_cs = false, e_clk = false, e_wen = false, e_prog = false, e_do = true, e_stuck = false; int e_st = 0, e_n = 0, e_busy = 0, e_op = 0, e_busy_polls = 3, e_cmd = 0; uint16_t e_sh = 0, e_addr = 0, e_rd = 0; int e_rdn = 0, e_words_written = 0;
  size_t e_words() const { return ram.size() / 2; }
  uint16_t e_get(size_t a) const { a %= e_words(); return uint16_t(ram[2 * a] | (ram[2 * a + 1] << 8)); }
  void e_put(size_t a, uint16_t v) { a %= e_words(); ram[2 * a] = uint8_t(v & 0xFF); ram[2 * a + 1] = uint8_t(v >> 8); e_words_written++; }
  void e_finish_data() {                                              // 16 bits de dados recebidos
    if (e_cmd == 1 && e_wen) { e_put(e_addr, e_sh); e_prog = true; }
    if (e_cmd == 2 && e_wen) { for (size_t a = 0; a < e_words(); a++) e_put(a, e_sh); e_prog = true; }
    e_st = 0;
  }
  void eep_write(uint8_t v) {
    bool ncs = v & 0x80, nclk = v & 0x40, di = (v >> 1) & 1;
    if (!ncs) { if (e_cs) { if (e_prog) { e_busy = e_stuck ? 1 << 30 : e_busy_polls; e_prog = false; } e_st = 0; } e_cs = false; e_clk = nclk; return; }
    if (!e_cs) { e_cs = true; e_do = e_busy == 0; e_st = 0; }         // CS sobe: DO mostra pronto (1) ou ocupado (0)
    bool rise = nclk && !e_clk; e_clk = nclk;
    if (!rise) return;
    if (e_st == 0) {
      if (e_busy > 0) { if (!e_stuck) e_busy--; e_do = e_busy == 0; return; }
      if (di) { e_st = 1; e_n = 0; e_op = 0; }
    } else if (e_st == 1) { e_op = (e_op << 1) | di; if (++e_n == 2) { e_st = 2; e_n = 0; e_addr = 0; }
    } else if (e_st == 2) {
      e_addr = uint16_t((e_addr << 1) | di);
      if (++e_n == 8) {
        e_n = 0;
        if (e_op == 2) { e_st = 4; e_do = false; e_rd = e_get(e_addr); e_rdn = 0; e_cmd = 0; }       // READ: bit zero falso, depois os 16 bits
        else if (e_op == 1) { e_st = 3; e_cmd = 1; e_sh = 0; }
        else if (e_op == 0) {
          int sub = e_addr & 0xC0; e_st = 0;
          if (sub == 0xC0) e_wen = true; else if (sub == 0x00) e_wen = false;
          else if (sub == 0x80) { if (e_wen) { for (size_t a = 0; a < e_words(); a++) e_put(a, 0xFFFF); e_prog = true; } }
          else { e_st = 3; e_cmd = 2; e_sh = 0; }
        } else e_st = 0;
      }
    } else if (e_st == 3) { e_sh = uint16_t((e_sh << 1) | di); if (++e_n == 16) { e_n = 0; e_finish_data(); }
    } else if (e_st == 4) {
      e_do = (e_rd >> 15) & 1; e_rd = uint16_t(e_rd << 1);
      if (++e_rdn == 16) { e_rdn = 0; e_addr++; e_rd = e_get(e_addr); }
    }
  }
  bool mbc1m() const { return type >= 0x101 && type <= 0x103; }
  bool is5() const { return type >= 0x19 && type <= 0x1E; }
  bool is2() const { return type == 5 || type == 6; }
  bool is1() const { return (type >= 1 && type <= 3) || mbc1m(); }
  size_t bank_hi() const {                                            // banco mapeado em $4000-$7FFF
    if (type == 0xFD) return tama_bank;
    if (is5()) return (size_t(r3000 & 1) << 8) | r2000;
    if (mbc1m()) return (size_t(r4000) << 4) | (r2000 & 0x0F);
    if (is1()) { size_t lo = r2000 & 0x1F; if (lo == 0) lo = 1; return (size_t(r4000 & 3) << 5) | lo; }
    if (is2()) { size_t b = r2000 & 0x0F; return b ? b : 1; }
    if (type == 0) return 1;
    size_t b = r2000 & 0x7F; return b ? b : 1;                         // MBC3, câmera, HuC
  }
  void begin() override { begins++; if (is_mmm()) { mm_map = false; mm_base = 0; mm_bank = 0; ram_en = false; } }
  void end() override {}
  uint8_t read(uint16_t a) override {
    if (absent) return 0xFF;
    if (is_mmm()) {
      if (a >= 0x8000) return 0xFF;
      if (!mm_map) return rom[rom.size() - 0x8000 + a];
      if (a < 0x4000) return rom[(size_t(mm_base) * 16384 + a) % rom.size()];
      return rom[((size_t(mm_base) + (mm_bank ? mm_bank : 1)) * 16384 + (a - 0x4000)) % rom.size()];
    }
    if (type == 0x20) {
      if (a < 0x4000) return rom[a];
      if (a >= 0x8000) return 0xFF;
      bool bwin = a >= 0x6000; uint8_t sel = bwin ? sel_b : sel_a, reg = bwin ? r3000 : r2000; size_t o = a & 0x1FFF;
      if (sel == 8 && flash_map) return flash[(size_t(reg) & 0x7F) * 8192 + o];
      return rom[(size_t(reg) * 8192 + o) % rom.size()];
    }
    if (a < 0x4000) { size_t b = (is1() && !mbc1m() && mode) ? (size_t(r4000 & 3) << 5) : 0; return rom[(b * 16384 + a) % rom.size()]; }
    if (a < 0x8000) return rom[(bank_hi() * 16384 + (a - 0x4000)) % rom.size()];
    if (type == 0x22 && a == 0xA080 && ram_en && r4000 == 0x40) return e_cs ? (e_do ? 1 : 0) : 1;
    return 0xFF;
  }
  void write(uint16_t a, uint8_t v) override {
    if (is_mmm()) {
      if (!mm_map) { if (a < 0x2000) { if (v & 0x40) mm_map = true; } else if (a < 0x4000) mm_base = v & 0x3F; return; }
      if (a < 0x2000) ram_en = (v & 0x0F) == 0x0A; else if (a < 0x4000) mm_bank = v & 0x1F; else if (a < 0x6000) r4000 = v; else if (a < 0x8000) mode = v & 1;
      return;
    }
    if (type == 0x20) {
      if (a < 0x0400) ram_en = (v & 0x0F) == 0x0A; else if (a < 0x0800) sram_a = v; else if (a < 0x0C00) sram_b = v;
      else if (a < 0x1000) { if (fw_en) flash_map = v & 1; }
      else if (a < 0x2000) fw_en = v & 1;
      else if (a < 0x2800) r2000 = v; else if (a < 0x3000) sel_a = v; else if (a < 0x3800) r3000 = v; else if (a < 0x4000) sel_b = v;
      return;
    }
    if (type == 0x22 && a == 0xA080) { if (ram_en && r4000 == 0x40) eep_write(v); return; }
    if (a < 0x2000) { if (!is2() || !(a & 0x100)) ram_en = (v & 0x0F) == 0x0A; }
    else if (a < 0x4000) {
      if (is5()) { if (a < 0x3000) r2000 = v; else r3000 = v; }
      else if (is2()) { if (a & 0x100) r2000 = v; }
      else r2000 = v;
    }
    else if (a < 0x6000) r4000 = v;
    else if (a < 0x8000) mode = v & 1;
  }
  size_t ram_index(uint16_t a) const {
    if (type == 0x20) return (size_t(sram_a & 7) * 4096 + ((a - 0xA000) & 0xFFF)) % ram.size();
    size_t bank = (type <= 4 ? (mode ? r4000 & 3 : 0) : r4000);
    if (is2()) return (a - 0xA000) & 0x1FF;
    return (bank * 8192 + (a - 0xA000)) % (ram.empty() ? 1 : ram.size());
  }
  uint8_t sram_read(uint16_t a, bool camera) override {
    if (type == 0xFC || type == 0xFD) { cam_calls++; if (!camera) cam_wrong++; } else if (camera) cam_wrong++;
    if (!ram_en || ram.empty() || a < 0xA000) return 0xFF;
    uint8_t v = ram[ram_index(a)]; return is2() ? uint8_t(0xF0 | (v & 0x0F)) : v;
  }
  void sram_write(uint16_t a, uint8_t v, bool camera) override {
    if (type == 0xFC || type == 0xFD) { cam_calls++; if (!camera) cam_wrong++; } else if (camera) cam_wrong++;
    if (type == 0xFD) {                                                // TAMA5: $A001 escolhe o registrador, $A000 grava o nibble do banco
      if (a == 0xA001) tama_reg = v & 1;
      else if (a == 0xA000) tama_bank = tama_reg == 0 ? uint8_t((tama_bank & 0xF0) | (v & 0x0F)) : uint8_t((tama_bank & 0x0F) | ((v & 0x0F) << 4));
      return;
    }
    if (!ram_en || ram.empty() || a < 0xA000) return;
    ram[ram_index(a)] = is2() ? uint8_t(v & 0x0F) : v;
  }
};

// ---------------------------------------------------------------- NES simulado
struct SimNes : NesBus {
  std::vector<uint8_t> prgrom, chrrom; bool absent = false;
  SimNes(uint32_t p, uint32_t c) { prgrom.resize(p); chrrom.resize(c); for (size_t i = 0; i < p; i++) prgrom[i] = pat(uint32_t(i) + 1); for (size_t i = 0; i < c; i++) chrrom[i] = pat(uint32_t(i) + 99); }
  void begin() override {} void end() override {}
  uint8_t prg(uint16_t a) override { if (absent || a < 0x8000) return 0xFF; return prgrom[(a - 0x8000) % prgrom.size()]; }
  uint8_t chr(uint16_t a) override { if (absent || chrrom.empty()) return 0xFF; return chrrom[a % chrrom.size()]; }
  void prg_write(uint16_t, uint8_t) override {}
};

// NES com mapper: modelo do hardware (com conflito de barramento nos mappers 2, 3 e 7)
struct SimMapper : NesBus {
  int m; std::vector<uint8_t> prgrom, chrrom;
  int reg = 0;                                  // 2, 3, 7
  uint8_t sh = 0, cnt = 0, mm1[4] = {0x0C, 0, 0, 0};   // MMC1
  uint8_t sel = 0, r[8] = {0, 2, 0, 0, 0, 0, 0, 1};   // MMC3
  std::vector<uint8_t> ram = std::vector<uint8_t>(8192, 0xFF); bool has_ram = true, mmc3_ram_en = false;
  uint8_t xp = 0, xfd = 0, xfe = 0; bool xlatch = false;                // 9 e 10 (MMC2/MMC4): PRG, bancos CHR dos latches FD e FE, latch
  uint8_t r79 = 0, r87 = 0, r78 = 0, r75[4] = {0, 0, 0, 0}, r33[4] = {0, 1, 0, 0};   // 79, 87, 78/70, 75 ($8000/$A000/$C000/$E000 + $9000 em r9000), 33/48
  uint8_t r9000 = 0;
  uint8_t fcmd = 0, f[16] = {0};                                         // 69 (FME-7): comando e registradores 0-15
  uint8_t m5[0x40] = {0}; bool m5_prg_set = false;                       // 5 (MMC5): registradores $5100-$513F
  size_t ram_off() const {                                              // MMC1 SOROM/SXROM: banco de RAM pelo registrador CHR 0 (mm1[1])
    if (m == 5) {                                                       // MMC5: $5113; 16 KB = dois chips de 8 KB (bit 2 escolhe o chip)
      if (ram.size() == 16384) return (m5[0x13] & 4) ? 8192 : 0;
      return size_t(m5[0x13] & 3) * 8192 % ram.size();
    }
    if (m != 1) return 0;
    if (ram.size() == 32768) return size_t((mm1[1] >> 2) & 3) * 8192;
    if (ram.size() == 16384) return size_t((mm1[1] >> 3) & 1) * 8192;
    return 0;
  }
  bool ram_enabled() const { return has_ram && (m == 1 ? !(mm1[3] & 0x10) : ((m == 4 || m == 118) ? mmc3_ram_en : (m == 5 ? true : (m == 69 ? (f[8] & 0xC0) == 0xC0 : false)))); }
  SimMapper(int mp, uint32_t p, uint32_t c) : m(mp) {
    prgrom.resize(p); chrrom.resize(c);
    for (size_t i = 0; i < p; i++) prgrom[i] = pat(uint32_t(i) + 11 * mp);
    for (size_t i = 0; i < c; i++) chrrom[i] = pat(uint32_t(i) + 77 * mp);
    if (mp == 5) { m5[0] = 3; m5[0x14] = m5[0x15] = 0xFF; m5[1] = 3; }   // MMC5 liga em PRG modo 3 (últimos bancos) e CHR modo 3 (1 KB)
  }
  void begin() override {} void end() override {}
  size_t n16() const { return prgrom.size() / 16384; }
  uint8_t prg(uint16_t a) override {
    if (a >= 0x6000 && a < 0x8000) return ram_enabled() ? ram[ram_off() + a - 0x6000] : 0xFF;
    if (a < 0x8000) return 0xFF;
    size_t N = prgrom.size();
    switch (m) {
      case 0: case 3: return prgrom[(a - 0x8000) % N];
      case 2: return a < 0xC000 ? prgrom[(size_t(reg) % n16()) * 16384 + (a & 0x3FFF)] : prgrom[N - 16384 + (a & 0x3FFF)];
      case 7: return prgrom[(size_t(reg) * 32768 + (a & 0x7FFF)) % N];
      case 1: { int mode = (mm1[0] >> 2) & 3;
        if (mode >= 2) return a < 0xC000 ? prgrom[(size_t(mm1[3] & 0x0F) % n16()) * 16384 + (a & 0x3FFF)] : prgrom[N - 16384 + (a & 0x3FFF)];
        return prgrom[(size_t(mm1[3] & 0x0E) * 16384 + (a & 0x7FFF)) % N]; }
      case 4: case 118: case 206: { size_t n8 = N / 8192, bank;
        if (a < 0xA000) bank = r[6]; else if (a < 0xC000) bank = r[7]; else if (a < 0xE000) bank = n8 - 2; else bank = n8 - 1;
        return prgrom[(bank % n8) * 8192 + (a & 0x1FFF)]; }
      case 87: return prgrom[(a - 0x8000) % N];
      case 79: return prgrom[(size_t((r79 >> 3) & 1) * 32768 + (a & 0x7FFF)) % N];
      case 78: return a < 0xC000 ? prgrom[(size_t(r78 & 7) % n16()) * 16384 + (a & 0x3FFF)] : prgrom[N - 16384 + (a & 0x3FFF)];
      case 70: return a < 0xC000 ? prgrom[(size_t(r78 >> 4) % n16()) * 16384 + (a & 0x3FFF)] : prgrom[N - 16384 + (a & 0x3FFF)];
      case 75: { size_t n8 = N / 8192, bank;
        if (a < 0xA000) bank = r75[0] & 0x0F; else if (a < 0xC000) bank = r75[1] & 0x0F; else if (a < 0xE000) bank = r75[2] & 0x0F; else bank = n8 - 1;
        return prgrom[(bank % n8) * 8192 + (a & 0x1FFF)]; }
      case 33: case 48: { size_t n8 = N / 8192, bank;
        if (a < 0xA000) bank = r33[0] & 0x3F; else if (a < 0xC000) bank = r33[1] & 0x3F; else if (a < 0xE000) bank = n8 - 2; else bank = n8 - 1;
        return prgrom[(bank % n8) * 8192 + (a & 0x1FFF)]; }
      case 66: return prgrom[(size_t((reg >> 4) & 3) * 32768 + (a & 0x7FFF)) % N];
      case 11: return prgrom[(size_t(reg & 3) * 32768 + (a & 0x7FFF)) % N];
      case 71: return a < 0xC000 ? prgrom[(size_t(reg) % n16()) * 16384 + (a & 0x3FFF)] : prgrom[N - 16384 + (a & 0x3FFF)];
      case 10: return a < 0xC000 ? prgrom[(size_t(xp & 0x0F) % n16()) * 16384 + (a & 0x3FFF)] : prgrom[N - 16384 + (a & 0x3FFF)];
      case 9: { size_t n8 = N / 8192;
        if (a < 0xA000) return prgrom[(size_t(xp & 0x0F) % n8) * 8192 + (a & 0x1FFF)];
        return prgrom[(n8 - 3 + ((a - 0xA000) >> 13)) * 8192 + (a & 0x1FFF)]; }
      case 69: { size_t n8 = N / 8192, bank;
        if (a < 0xA000) bank = f[9] & 0x3F; else if (a < 0xC000) bank = f[10] & 0x3F; else if (a < 0xE000) bank = f[11] & 0x3F; else bank = n8 - 1;
        return prgrom[(bank % n8) * 8192 + (a & 0x1FFF)]; }
      case 5: { size_t n8 = N / 8192, bank;
        if (m5[0] != 3) return 0xFF;                                    // sem $5100 = 3 o modelo não troca bancos de 8 KB
        if (a < 0xA000) bank = m5[0x14] & 0x7F; else if (a < 0xC000) bank = m5[0x15] & 0x7F; else if (a < 0xE000) bank = n8 - 2; else bank = n8 - 1;
        return prgrom[(bank % n8) * 8192 + (a & 0x1FFF)]; }
    }
    return 0xFF;
  }
  uint8_t chr(uint16_t a) override {
    if (chrrom.empty()) return 0xFF;
    size_t C = chrrom.size();
    switch (m) {
      case 0: return chrrom[a % C];
      case 3: return chrrom[(size_t(reg) * 8192 + a) % C];
      case 1: { if (!(mm1[0] & 0x10)) return chrrom[((size_t(mm1[1] & 0x1E)) * 4096 + a) % C];
        return chrrom[((a < 0x1000 ? size_t(mm1[1]) : size_t(mm1[2])) * 4096 + (a & 0xFFF)) % C]; }
      case 4: case 118: case 206: { size_t b;
        if (a < 0x0800) b = (r[0] & ~1) + (a >> 10); else if (a < 0x1000) b = (r[1] & ~1) + ((a - 0x800) >> 10);
        else b = r[2 + ((a - 0x1000) >> 10)];
        return chrrom[((b * 1024) + (a & 0x3FF)) % C]; }
      case 87: return chrrom[(size_t(((r87 & 1) << 1) | ((r87 >> 1) & 1)) * 8192 + a) % C];
      case 79: return chrrom[(size_t(r79 & 7) * 8192 + a) % C];
      case 78: return chrrom[(size_t(r78 >> 4) * 8192 + a) % C];
      case 70: return chrrom[(size_t(r78 & 0x0F) * 8192 + a) % C];
      case 75: { size_t b = a < 0x1000 ? (size_t(r75[3] & 0x0F) | (size_t(r9000 & 2) << 3)) : 0; return chrrom[(b * 4096 + (a & 0xFFF)) % C]; }
      case 33: case 48: { size_t b = a < 0x800 ? r33[2] : (a < 0x1000 ? r33[3] : 0); return chrrom[(b * 2048 + (a & 0x7FF)) % C]; }
      case 66: return chrrom[(size_t(reg & 3) * 8192 + a) % C];
      case 11: return chrrom[(size_t(reg >> 4) * 8192 + a) % C];
      case 9: case 10: {
        uint8_t v;
        if (a < 0x1000) { v = xlatch ? xfe : xfd; } else v = 0;
        uint8_t out = chrrom[((size_t(v & 0x1F) * 4096) + (a & 0xFFF)) % C];
        if (a >= 0x0FD8 && a <= 0x0FDF) xlatch = false;                  // latch troca depois da leitura
        if (a >= 0x0FE8 && a <= 0x0FEF) xlatch = true;
        return out; }
      case 69: return chrrom[((size_t(f[a >> 10]) * 1024) + (a & 0x3FF)) % C];
      case 5: { if (m5[1] != 0) return 0xFF;                            // $5101 = 0: modo de 8 KB, banco em $5127 (unidades de 8 KB)
        return chrrom[((size_t(m5[0x30] & 3) << 8 | m5[0x27]) * 8192 + a) % C]; }
    }
    return 0xFF;
  }
  void reg_write_safe(uint16_t a, uint8_t v) override { safe_write = true; prg_write(a, v); safe_write = false; }
  bool safe_write = false; int corrupted = 0;
  void prg_write(uint16_t a, uint8_t v) override {
    if (m == 1 && a >= 0xE000 && !safe_write && has_ram && !(mm1[3] & 0x10)) { ram[0] ^= 0xFF; corrupted++; }   // escrita em $E000+ sem a sequência segura estraga a RAM
    if (m == 5 && a >= 0x5100 && a < 0x5140) { m5[a - 0x5100] = v; return; }
    if (m == 79 && a >= 0x4100 && a < 0x6000 && (a & 0x100)) { r79 = v; return; }
    if (m == 87 && a >= 0x6000 && a < 0x8000) { r87 = v; return; }
    if (a >= 0x6000 && a < 0x8000) { if (ram_enabled() && (m != 5 || (m5[2] == 2 && m5[3] == 1))) ram[ram_off() + a - 0x6000] = v; return; }   // MMC5: só com $5102=2 e $5103=1
    if (a < 0x8000) return;
    switch (m) {
      case 2: case 3: case 7: case 11: case 66: reg = v & prg(a); break;     // conflito: valor E byte da ROM
      case 71: if (a >= 0xC000) reg = v; break;
      case 78: case 70: r78 = v & prg(a); break;                              // conflito de barramento
      case 75:
        if (a >= 0xE000) r75[3] = v; else if (a >= 0xC000 && a < 0xD000) r75[2] = v; else if (a >= 0xA000 && a < 0xB000) r75[1] = v;
        else if (a >= 0x9000 && a < 0xA000) r9000 = v; else if (a < 0x9000) r75[0] = v;
        break;
      case 33: case 48: if (a < 0xA000) r33[a & 3] = v; break;                              // sem conflito
      case 9: case 10:
        if (a >= 0xA000 && a < 0xB000) xp = v; else if (a >= 0xB000 && a < 0xC000) xfd = v; else if (a >= 0xC000 && a < 0xD000) xfe = v;
        break;
      case 69: if (a < 0xA000) fcmd = v & 0x0F; else if (a < 0xC000) f[fcmd] = v; break;
      case 1:
        if (v & 0x80) { cnt = 0; sh = 0; mm1[0] |= 0x0C; break; }
        sh |= (v & 1) << cnt;
        if (++cnt == 5) { mm1[(a >> 13) & 3] = sh; cnt = 0; sh = 0; }
        break;
      case 4: case 118: case 206:
        if (a < 0xA000) { if ((a & 1) == 0) sel = v; else r[sel & 7] = v; }
        else if (a < 0xC000 && (a & 1)) mmc3_ram_en = (v & 0x80) != 0;
        break;
    }
  }
};

// ---------------------------------------------------------------- Mega Drive simulado
struct SimMd : MdBus {
  std::vector<uint8_t> rom; bool absent = false, ssf = false, sram_on = false;
  int save_kind = 0;                                // 0 nenhum, 1 ímpares, 2 pares, 3 ambos
  std::vector<uint16_t> sram = std::vector<uint16_t>(0x10000, 0xFFFF);
  uint8_t bank[8] = {0, 1, 2, 3, 4, 5, 6, 7};
  explicit SimMd(uint32_t size, int kind = 0, bool is_ssf = false, uint32_t ssram = 8192, uint32_t claimed = 0) : ssf(is_ssf), save_kind(kind) {
    rom.resize(size); for (size_t i = 0; i < size; i++) rom[i] = pat(uint32_t(i) + 7);
    memcpy(&rom[0x100], is_ssf ? "SEGA SSF        " : "SEGA MEGA DRIVE ", 16); memset(&rom[0x150], ' ', 48); memcpy(&rom[0x150], "JOGO DE TESTE", 13);
    uint32_t end = (claimed ? claimed : size) - 1; rom[0x1A4] = end >> 24; rom[0x1A5] = end >> 16; rom[0x1A6] = end >> 8; rom[0x1A7] = end;
    if (kind) {
      uint32_t base = kind == 2 ? 0x200000 : 0x200001, last = kind == 1 ? base + ssram * 2 - 2 : (kind == 2 ? base + ssram * 2 - 1 : base + ssram - 2 + (0));
      if (kind == 3) { base = 0x200001; last = base + ssram - 2 + 1 - 1 + 0; last = base + ssram - 2; }
      rom[0x1B0] = 'R'; rom[0x1B1] = 'A'; rom[0x1B2] = kind == 3 ? 0xE0 : 0xF8; rom[0x1B3] = 0x20;
      for (int i = 0; i < 4; i++) { rom[0x1B4 + i] = base >> (24 - 8 * i); rom[0x1B8 + i] = last >> (24 - 8 * i); }
    }
  }
  void begin() override {} void end() override {}
  uint16_t word(uint32_t wa) override {
    if (absent) return 0xFFFF;
    uint32_t b = wa * 2;
    if (sram_on && b >= 0x200000 && b < 0x400000) {
      uint16_t w = sram[(b - 0x200000) / 2];
      if (save_kind == 1) return 0xFF00 | (w & 0xFF);
      if (save_kind == 2) return (w & 0xFF00) | 0xFF;
      return w;
    }
    uint32_t o = b;
    if (ssf && b >= 0x80000 && b < 0x400000) o = uint32_t(bank[b >> 19]) * 0x80000 + (b & 0x7FFFF);
    o %= rom.size();
    return uint16_t(rom[o] << 8) | rom[o + 1];
  }
  void write_word(uint32_t wa, uint16_t w) override {
    uint32_t b = wa * 2;
    if (sram_on && b >= 0x200000 && b < 0x400000) {
      uint16_t& cell = sram[(b - 0x200000) / 2];
      if (save_kind == 1) cell = (cell & 0xFF00) | (w & 0xFF); else if (save_kind == 2) cell = (cell & 0x00FF) | (w & 0xFF00); else cell = w;
    }
  }
  void map_write(uint32_t wa, uint16_t w) override {
    uint32_t b = wa * 2;
    if (b == 0xA130F0) sram_on = w & 1;
    else if (b >= 0xA130F2 && b <= 0xA130FE) bank[(b - 0xA130F0) / 2] = w & 0xFF;
  }
  void eep_enable(bool) override {}
  void eep_sda(uint32_t, uint8_t, bool) override {}
  void eep_scl(uint32_t, uint8_t, bool) override {}
  void eep_cm(uint32_t, uint16_t) override {}
  void wait_ms(uint16_t) override {}
};

// EEPROM serial 24Cxx (I2C) simulada, escrita a partir do datasheet e independente do código do firmware.
struct I2cEeprom {
  std::vector<uint8_t> mem; bool sda_m = true, scl = true, slave_low = false;
  enum Ph { IDLE, BITS_IN, ACK_OUT, TX, MACK } ph = IDLE;
  enum Next { N_DEV, N_HI, N_LO, N_DATA } next = N_DEV;
  int bits = 0, txbit = 0; uint8_t shift = 0; uint32_t addr = 0, hi = 0, lo = 0; int page = 0; bool rw = false, tx_next = false, nack = false;
  int ack_count = 0, writes = 0; bool busy = false, wrote = false;   // busy: ciclo de escrita em andamento, não dá ACK
  explicit I2cEeprom(size_t n) : mem(n) {}
  bool line() const { return sda_m && !slave_low; }
  uint8_t cur() const { return mem[addr % mem.size()]; }
  void update(bool nsda, bool nscl) {
    bool osda = sda_m, oscl = scl;
    sda_m = nsda; scl = nscl;
    if (oscl && nscl && osda != nsda) {                        // START / STOP com SCL alto
      if (!nsda) { ph = BITS_IN; next = N_DEV; bits = 0; slave_low = false; }
      else { ph = IDLE; slave_low = false; if (wrote) { busy = true; wrote = false; } }
      return;
    }
    if (nscl && !oscl) {                                       // subida do SCL
      if (ph == BITS_IN) { shift = uint8_t(shift << 1 | (line() ? 1 : 0)); bits++; }
      else if (ph == MACK) nack = line();
    } else if (!nscl && oscl) {                                // descida do SCL
      if (ph == BITS_IN && bits == 8) {
        bits = 0; bool ack = true; tx_next = false;
        if (mem.size() <= 128 && next == N_DEV) { ack = !busy; addr = shift >> 1; rw = shift & 1; next = N_DATA; tx_next = rw; }
        else if (next == N_DEV) {
          ack = (shift >> 4) == 0xA && !busy; page = (shift >> 1) & 7; rw = shift & 1;
          if (rw) { addr = mem.size() > 0x800 ? (hi << 8 | lo) : (((uint32_t)page << 8) | lo) & (mem.size() - 1); tx_next = true; }
          else next = mem.size() > 0x800 ? N_HI : N_LO;
        } else if (next == N_HI) { hi = shift; next = N_LO; }
        else if (next == N_LO) { lo = shift; addr = mem.size() > 0x800 ? (hi << 8 | lo) : (((uint32_t)page << 8) | lo) & (mem.size() - 1); next = N_DATA; }
        else if (next == N_DATA) { mem[addr % mem.size()] = shift; addr++; writes++; wrote = true; }
        if (ack) { slave_low = true; ack_count++; }
        ph = ack ? ACK_OUT : IDLE;
      } else if (ph == ACK_OUT) {
        slave_low = false;
        if (tx_next) { ph = TX; txbit = 0; slave_low = !((cur() >> 7) & 1); }
        else { ph = BITS_IN; bits = 0; }
      } else if (ph == TX) {
        txbit++;
        if (txbit == 8) { slave_low = false; ph = MACK; }
        else slave_low = !((cur() >> (7 - txbit)) & 1);
      } else if (ph == MACK) {
        if (nack) ph = IDLE; else { addr++; ph = TX; txbit = 0; slave_low = !((cur() >> 7) & 1); }
      }
    }
  }
};

// Cartucho Mega Drive com EEPROM e a "cola" elétrica de cada tipo (bits de SDA e SCL), como descrito no OSCR.
struct SimMdEep : SimMd {
  int type; I2cEeprom e; bool on2 = false, dead = false; int violations = 0;
  SimMdEep(int t, size_t size, uint16_t chk) : SimMd(0x100000), type(t), e(size) {
    rom[0x18E] = chk >> 8; rom[0x18F] = chk & 0xFF;
    for (size_t i = 0; i < size; i++) e.mem[i] = pat(uint32_t(i) * 5 + 9);
  }
  void write_word(uint32_t wa, uint16_t w) override {
    if (wa == 0x100000 && (type == 1 || type == 3)) e.update(w & 1, (w >> 1) & 1);
    else if (wa == 0x100000 && type == 4) e.update(w & 0x80, w & 0x40);
    else SimMd::write_word(wa, w);
  }
  void eep_cm(uint32_t wa, uint16_t w) override { if (type == 5 && wa == 0x180000) e.update(w & 1, (w >> 1) & 1); }
  void eep_enable(bool on) override { on2 = on; }
  void wait_ms(uint16_t) override { e.busy = false; }       // o ciclo de escrita acaba
  void eep_sda(uint32_t wa, uint8_t d, bool) override { if (type == 2 && wa == 0x100000 && on2) e.update(d & 1, e.scl); else violations++; }
  void eep_scl(uint32_t wa, uint8_t d, bool) override { if (type == 2 && wa == 0x100000 && on2) e.update(e.sda_m, d & 1); else violations++; }
  uint16_t word(uint32_t wa) override {
    if (dead && (wa == 0x100000 || wa == 0x1C0000)) return 0xFFFF;            // barramento aberto: SDA fica alto, sem ACK
    if (wa == 0x100000 && type == 1) return uint16_t(e.line() << 1);
    if (wa == 0x100000 && (type == 2 || type == 3)) return e.line() ? 1 : 0;
    if (wa == 0x100000 && type == 4) return uint16_t(e.line() << 7);
    if (wa == 0x1C0000 && type == 5) return uint16_t(e.line() << 7);
    return SimMd::word(wa);
  }
};

// ---------------------------------------------------------------- GBA simulado
struct SimGba : GbaBus {
  std::vector<uint8_t> rom; bool absent = false;
  explicit SimGba(uint32_t size) { rom.resize(size); for (size_t i = 0; i < size; i++) rom[i] = pat(uint32_t(i) + 3);
    const uint8_t logo[4] = {0x24, 0xFF, 0xAE, 0x51}; memcpy(&rom[4], logo, 4); memset(&rom[0xA0], ' ', 12); memcpy(&rom[0xA0], "GBA TESTE", 9); }
  void begin() override {} void end() override {}
  uint16_t word(uint32_t ba) override { if (absent) return 0xFFFF; uint32_t i = (ba & ~1UL) % rom.size(); return uint16_t(rom[i + 1] << 8) | rom[i]; }
  std::vector<uint8_t> sram = std::vector<uint8_t>(32768, 0);
  uint8_t sram_read(uint16_t a) override {
    if (!flash) return sram[a & 0x7FFF];
    if (id_mode && a == 0) return uint8_t(flash_id >> 8);
    if (id_mode && a == 1) return uint8_t(flash_id & 0xFF);
    return flash_data[(size_t(bank) << 16 | a) % flash_data.size()];
  }
  // Flash (JEDEC): comandos AA/55 + {90 ID, F0 reset, 80 apagar, A0 gravar, B0 trocar de banco}. Gravar só zera bits (AND),
  // por isso o chip precisa ser apagado antes; o Atmel grava páginas de 128 bytes que se apagam sozinhas.
  void sram_write(uint16_t a, uint8_t v) override {
    if (!flash) { if (!sram_ro) sram[a & 0x7FFF] = v; return; }
    size_t full = (size_t(bank) << 16 | a) % flash_data.size();
    if (st == 3) { if (a == 0) bank = v & 1; st = 0; return; }
    if (st == 4) { if (!stuck) flash_data[full] &= v; st = 0; programmed++; return; }
    if (st == 8) {
      page.push_back({a, v});
      if (page.size() == 128) {
        if (!stuck) { size_t base = (size_t(bank) << 16 | (page[0].first & ~127u)) % flash_data.size(); for (int j = 0; j < 128; j++) flash_data[base + j] = page[j].second; }
        page.clear(); st = 0;
      }
      return;
    }
    if (v == 0xF0) { id_mode = false; st = 0; return; }
    switch (st) {
      case 0: if (a == 0x5555 && v == 0xAA) st = 1; break;
      case 1: st = (a == 0x2AAA && v == 0x55) ? 2 : 0; break;
      case 2:
        if (a != 0x5555) { st = 0; break; }
        if (v == 0x90) { id_mode = true; st = 0; }
        else if (v == 0xA0) st = atmel ? 8 : 4;
        else if (v == 0xB0) st = 3;
        else if (v == 0x80) st = 5;
        else st = 0;
        break;
      case 5: st = (a == 0x5555 && v == 0xAA) ? 6 : 0; break;
      case 6: st = (a == 0x2AAA && v == 0x55) ? 7 : 0; break;
      case 7: if (a == 0x5555 && v == 0x10 && !stuck) { std::fill(flash_data.begin(), flash_data.end(), 0xFF); erases++; } st = 0; break;
    }
  }
  bool flash = false, id_mode = false, atmel = false, stuck = false, sram_ro = false, eep_stuck = false;
  int st = 0, bank = 0, eep_reads = 0, erases = 0, programmed = 0; uint16_t flash_id = 0xBFD4;
  std::vector<std::pair<uint16_t, uint8_t>> page;
  std::vector<uint8_t> flash_data;     // Flash: 64 ou 128 KB
  std::vector<uint8_t> eep;
  void eeprom_block(uint16_t block, bool big, uint8_t out[8]) override {
    eep_reads++; size_t n = big ? 8192 : 512;
    for (int i = 0; i < 8; i++) out[i] = eep[(size_t(block) * 8 + i) % n];
  }
  bool eeprom_write_block(uint16_t block, bool big, const uint8_t in[8]) override {
    size_t n = big ? 8192 : 512;
    if (!eep_stuck) for (int i = 0; i < 8; i++) eep[(size_t(block) * 8 + i) % n] = in[i];
    return true;
  }
  void wait_ms(uint16_t) override {}
};

static void dump(CartBackend& be, uint8_t sys, uint8_t kind, std::vector<uint8_t>& out, uint16_t& err) {
  uint32_t size = 0; out.clear();
  if (!be.open_read(sys, kind, size, err)) return;
  out.resize(size);
  for (uint32_t off = 0; off < size; off += 512) { uint16_t n = size - off < 512 ? uint16_t(size - off) : 512; be.read(sys, kind, off, &out[off], n); }
  be.close_read();
}

static void test_snes() {
  for (int hi = 0; hi < 2; hi++) {
    SimSnes s(hi, 9, 3);   // 512 KB, SRAM de 8 KB
    CartBackend be(&s, nullptr, nullptr, nullptr);
    DetectInfo d; be.detect(SYS_SNES, d);
    CHECK(d.status == 0 && d.rom_size == 512 * 1024 && d.save_size == 8192 && strcmp(d.name, "TESTE SNES") == 0);
    std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_SNES, KIND_ROM, out, err);
    CHECK(out.size() == s.rom.size() && memcmp(out.data(), s.rom.data(), out.size()) == 0);
    // SRAM: grava um padrão e lê de volta
    uint16_t e2 = 0; std::vector<uint8_t> save(8192); for (size_t i = 0; i < save.size(); i++) save[i] = pat(uint32_t(i) + 500);
    CHECK(be.write_begin(SYS_SNES, 8192, e2));
    bool ok = true; for (uint32_t off = 0; off < 8192; off += 512) ok = ok && be.write_block(off, &save[off], 512);
    CHECK(ok && be.write_commit());
    CHECK(s.sram == save);
    dump(be, SYS_SNES, KIND_SAVE, out, err);
    CHECK(out == save);
    CHECK(!be.write_begin(SYS_SNES, 4096, e2) && e2 == E_ARGUMENTO);
  }
  SimSnes bad(false, 9, 0, true); CartBackend be(&bad, nullptr, nullptr, nullptr);
  DetectInfo d; be.detect(SYS_SNES, d); CHECK(d.status == 4);              // há dados mas o checksum não confere = cabeçalho inválido
  std::vector<uint8_t> o; uint16_t err; dump(be, SYS_SNES, KIND_ROM, o, err); CHECK(err == E_SEM_CARTUCHO);
  SimSnes nosave(false, 9, 0); CartBackend b2(&nosave, nullptr, nullptr, nullptr);
  dump(b2, SYS_SNES, KIND_SAVE, o, err); CHECK(err == E_SEM_SAVE);
}

static void test_snes_exhirom() {
  for (uint8_t ssz : {3, 5}) {                                         // SRAM de 8 KB e de 32 KB (4 bancos de 8 KB em $B0-$B3)
    SimSnes s(false, 13, ssz, false, true);                            // 8 MB, cabeçalho em $40FFC0
    CartBackend be(&s, nullptr, nullptr, nullptr);
    DetectInfo d; be.detect(SYS_SNES, d);
    CHECK(d.status == 0 && d.rom_size == 6144UL * 1024 && d.save_size == (1024u << ssz));   // cabeçalho 8 MB = 6 MB
    std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_SNES, KIND_ROM, out, err);
    CHECK(out.size() == 6144UL * 1024 && memcmp(out.data(), s.rom.data(), out.size()) == 0);
    uint32_t n = 1024u << ssz;
    std::vector<uint8_t> save(n); for (size_t i = 0; i < n; i++) save[i] = pat(uint32_t(i) + 640);
    uint16_t e2 = 0; CHECK(be.write_begin(SYS_SNES, n, e2));
    bool ok = true; for (uint32_t off = 0; off < n; off += 512) ok = ok && be.write_block(off, &save[off], 512);
    CHECK(ok && be.write_commit() && s.sram == save);
    dump(be, SYS_SNES, KIND_SAVE, out, err); CHECK(out == save);
    dump(be, SYS_SNES, KIND_ROM, out, err); CHECK(out.size() == 6144UL * 1024);   // a ROM volta a ler com CS baixo
  }
  SimSnes s(false, 13, 0, false, true); CartBackend be(&s, nullptr, nullptr, nullptr);          // 6 MB informados (cabeçalho diz 8 MB)
  std::vector<uint8_t> out; uint16_t err = 0;
  be.set_options(0, 6144, 0); dump(be, SYS_SNES, KIND_ROM, out, err);
  CHECK(out.size() == 6144UL * 1024 && memcmp(out.data(), s.rom.data(), out.size()) == 0);
  uint32_t size = 0;
  be.set_options(0, 8064, 0); dump(be, SYS_SNES, KIND_ROM, out, err);                          // máximo: até $7DFFFF
  CHECK(out.size() == 8064UL * 1024 && memcmp(out.data(), s.rom.data(), out.size()) == 0);
  be.set_options(0, 100, 0);   CHECK(!be.open_read(SYS_SNES, KIND_ROM, size, err) && err == E_ARGUMENTO);   // múltiplo de 64 KB
  be.set_options(0, 8128, 0);  CHECK(!be.open_read(SYS_SNES, KIND_ROM, size, err) && err == E_ARGUMENTO);   // acima de $7DFFFF
  SimSnes hi(true, 9, 5); CartBackend bh(&hi, nullptr, nullptr, nullptr);                      // HiROM com SRAM de 32 KB (CS alto)
  std::vector<uint8_t> sv(32768); for (size_t i = 0; i < sv.size(); i++) sv[i] = pat(uint32_t(i) + 9);
  uint16_t e2 = 0; CHECK(bh.write_begin(SYS_SNES, 32768, e2));
  bool ok = true; for (uint32_t off = 0; off < 32768; off += 512) ok = ok && bh.write_block(off, &sv[off], 512);
  CHECK(ok && bh.write_commit() && hi.sram == sv);
}

static void test_snes_chips() {
  uint16_t err = 0; std::vector<uint8_t> out;
  // LoROM de 4 MB: os bancos $7E-$7F são a WRAM, a ROM tem que sair de $80+
  { SimSnes s(false, 12, 0); CartBackend be(&s, nullptr, nullptr, nullptr);
    dump(be, SYS_SNES, KIND_ROM, out, err);
    CHECK(out.size() == s.rom.size() && memcmp(out.data(), s.rom.data(), out.size()) == 0); }
  // SuperFX: RAM de 32 KB por padrão, 64 KB no Star Fox 2, e pelo byte $FFBD quando o mapa é $33; bancos de 64 KB em $70
  for (int v = 0; v < 3; v++) {
    SimSnes s(false, 10, 0); s.special = 1; size_t h = 0x7FC0;
    s.rom[h + 0x16] = 0x15; if (v == 1) memcpy(&s.rom[h], "STARFOX2  ", 10);
    if (v == 2) { s.rom[h + 0x1A] = 0x33; s.rom[0x7FBD] = 7; }
    uint32_t want = v == 1 ? 65536 : (v == 2 ? 131072 : 32768);
    s.sram.assign(want, 0);
    CartBackend be(&s, nullptr, nullptr, nullptr);
    DetectInfo d; be.detect(SYS_SNES, d);
    CHECK(d.status == 0 && d.save_size == want && d.rom_size == 1024UL * 1024);
    for (size_t i = 0; i < s.sram.size(); i++) s.sram[i] = pat(uint32_t(i) + 17);
    dump(be, SYS_SNES, KIND_SAVE, out, err); CHECK(out == s.sram);
    std::vector<uint8_t> sv(want); for (size_t i = 0; i < want; i++) sv[i] = pat(uint32_t(i) + 99);
    uint16_t e2 = 0; CHECK(be.write_begin(SYS_SNES, want, e2));
    bool ok = true; for (uint32_t off = 0; off < want; off += 512) ok = ok && be.write_block(off, &sv[off], 512);
    CHECK(ok && be.write_commit() && s.sram == sv);
  }
  // S-DD1: 4 MB (chips $43) e 6 MB (chips $45), janelas de 1 MB em $F0-$FF; o registrador $4807 volta ao valor original
  for (uint8_t chips : {0x43, 0x45}) {
    SimSnes s(false, 13, 0); s.special = 2; s.sdd1map = 5; s.rom[0x7FC0 + 0x16] = chips; s.rom[0x7FC0 + 0x15] = 0x32;
    CartBackend be(&s, nullptr, nullptr, nullptr);
    DetectInfo d; be.detect(SYS_SNES, d);
    uint32_t want = chips == 0x45 ? 6144UL * 1024 : 4096UL * 1024;
    CHECK(d.status == 0 && d.rom_size == want);
    dump(be, SYS_SNES, KIND_ROM, out, err);
    bool same = out.size() == want;
    for (uint32_t i = 0; same && i < want; i++) if (out[i] != s.rom[i]) same = false;
    CHECK(same); CHECK(s.sdd1map == 5);
  }
  // SPC7110: 3 MB ($F5) e 5 MB ($F9); $4833/$4834 voltam a 2 e 0; a SRAM pede $4830 = $80 (e não sobe o CS)
  for (uint8_t chips : {0xF5, 0xF9}) {
    SimSnes s(true, 13, 3); s.special = 3; size_t h = 0xFFC0; s.rom[h + 0x15] = 0x3A; s.rom[h + 0x16] = chips;
    CartBackend be(&s, nullptr, nullptr, nullptr);
    uint32_t want = chips == 0xF5 ? 3072UL * 1024 : 5120UL * 1024;
    DetectInfo d; be.detect(SYS_SNES, d); CHECK(d.status == 0 && d.rom_size == want && d.save_size == 8192);
    dump(be, SYS_SNES, KIND_ROM, out, err);
    bool ok = out.size() == want;
    for (uint32_t i = 0; ok && i < want; i++) {                      // regiões: 0-2 MB, 2-3 MB, 3-4 MB, 4-5 MB do arquivo
      uint32_t expect = i;                                           // o simulador mapeia cada região para o mesmo deslocamento do arquivo
      if (out[i] != s.rom[expect]) ok = false;
    }
    CHECK(ok); CHECK(s.r4833 == 2 && s.r4834 == 0);
    for (size_t i = 0; i < s.sram.size(); i++) s.sram[i] = pat(uint32_t(i) + 3);
    dump(be, SYS_SNES, KIND_SAVE, out, err); CHECK(out == s.sram && s.r4830 == 0 && !s.cs_high);
  }
  // Cx4: X2 pede $7F52 = 0 e X3 pede 1 durante a leitura; o valor original volta
  for (int type : {2, 3}) {
    SimSnes s(false, 11, 0); s.special = 4; s.rom[0x7FC0 + 0x16] = 0xF3; s.rom[0x7FC0 + 9] = uint8_t(type);
    s.cx4reg = type == 2 ? 1 : 0; s.cx4want = type == 2 ? 0 : 1;
    CartBackend be(&s, nullptr, nullptr, nullptr);
    uint8_t orig = s.cx4reg;
    dump(be, SYS_SNES, KIND_ROM, out, err);
    CHECK(out.size() == (type == 2 ? 1536UL : 2048UL) * 1024 && s.cx4bad == 0 && s.cx4reg == orig);
  }
}

static void test_snes_sa1() {
  {
    SimSa1 s(10, 5);                                                   // 1 MB, BW-RAM de 32 KB
    CartBackend be(&s, nullptr, nullptr, nullptr);
    CHECK((be.flags() & 2) != 0);
    DetectInfo d; be.detect(SYS_SNES, d);
    CHECK(d.status == 0 && d.rom_size == 1024UL * 1024 && d.save_size == 32768 && strcmp(d.name, "SA1 TESTE") == 0);
    CHECK(s.boots == 1 && !s.booted && s.stops >= 1);                   // ligou os clocks uma vez e desligou ao terminar
    std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_SNES, KIND_ROM, out, err);
    CHECK(out.size() == s.rom.size() && memcmp(out.data(), s.rom.data(), out.size()) == 0);
    for (size_t i = 0; i < s.bw.size(); i++) s.bw[i] = pat(uint32_t(i) + 71);
    dump(be, SYS_SNES, KIND_SAVE, out, err);                            // leitura pelos bancos $40+ (com CS alto)
    CHECK(out == s.bw);
    std::vector<uint8_t> save(32768); for (size_t i = 0; i < save.size(); i++) save[i] = pat(uint32_t(i) + 5000);
    uint16_t e2 = 0; CHECK(be.write_begin(SYS_SNES, 32768, e2));
    CHECK(s.cpu);                                                       // clock do CPU ligado para gravar
    bool ok = true; for (uint32_t off = 0; off < 32768; off += 512) ok = ok && be.write_block(off, &save[off], 512);
    CHECK(ok && be.write_commit());                                     // o primeiro byte se perdeu; os 16 primeiros foram regravados
    CHECK(s.bw == save && !s.cpu && !s.booted);
  }
  { SimSa1 s(10, 5); s.avail = false; CartBackend be(&s, nullptr, nullptr, nullptr);     // sem Si5351: o cabeçalho nunca aparece
    DetectInfo d; be.detect(SYS_SNES, d); CHECK(d.status == 1 && s.boots == 0); CHECK((be.flags() & 2) == 0); }
  { SimSa1 s(10, 5, true); CartBackend be(&s, nullptr, nullptr, nullptr);                // cabeçalho inválido mesmo com clocks
    DetectInfo d; be.detect(SYS_SNES, d); CHECK(d.status == 4 && s.boots == 1 && !s.booted); }
  { SimSa1 s(10, 5); s.lose_first = false; CartBackend be(&s, nullptr, nullptr, nullptr);   // gravação que não confere: falha
    std::vector<uint8_t> save(32768, 0x55); uint16_t e2 = 0; CHECK(be.write_begin(SYS_SNES, 32768, e2));
    s.sbwe = 0; s.cpu = false;                                         // simula a BW-RAM protegida
    bool ok = true; for (uint32_t off = 0; off < 512; off += 512) ok = ok && be.write_block(off, &save[off], 512);
    CHECK(!ok); be.write_abort(); }
  // cartuchos comuns não ligam clock nenhum, mesmo com o Si5351 presente
  { struct Counting : SimSnes { int boots = 0; using SimSnes::SimSnes; bool clocks_available() override { return true; } void clocks_boot() override { boots++; } };
    Counting plain(false, 9, 3); CartBackend be(&plain, nullptr, nullptr, nullptr); DetectInfo d; be.detect(SYS_SNES, d);
    CHECK(d.status == 0 && plain.boots == 0);
    Counting none(false, 9, 3, true); CartBackend b2(&none, nullptr, nullptr, nullptr); b2.detect(SYS_SNES, d);   // sem cartucho: tenta os clocks uma vez
    CHECK(d.status == 4 && none.boots == 1); }
}

static void test_gb() {
  struct Cfg { int type; uint8_t rsz, ssz; const char* title; };
  const Cfg cfgs[] = {
    {0x00, 0, 0, "ROM SO"}, {0x01, 4, 0, "MBC1"}, {0x03, 5, 3, "MBC1 32K"}, {0x03, 6, 2, "MBC1 8K"}, {0x02, 6, 1, "MBC1 2K"},
    {0x06, 3, 0, "MBC2"}, {0x13, 6, 3, "MBC3"}, {0x10, 5, 2, "MBC3 RTC"}, {0x1B, 8, 4, "MBC5 128K"}, {0x1E, 7, 5, "MBC5 64K"},
    {0x19, 8, 0, "MBC5 4MB"}, {0xFC, 5, 4, "CAMERA"}, {0x103, 5, 2, "MOMOCOL"}, {0x22, 3, 0, "KIRBY TNT"}, {0x0D, 5, 3, "MMM01 SAVE"}, {0x0B, 5, 0, "MMM01"}, {0xFD, 4, 0, "TAMA5"},
  };
  for (const Cfg& c : cfgs) {
    int hdr_type = c.type & 0xFF;
    SimGb s(hdr_type, c.rsz, c.ssz, c.title, c.type == 0x103 ? 0x28 : 0, c.type == 0x103);
    if (c.type == 0x103) s.type = 0x103;
    CartBackend be(nullptr, nullptr, nullptr, nullptr, &s);
    DetectInfo d; be.detect(SYS_GB, d);
    CHECK(d.status == 0 && d.rom_size == s.rom.size() && d.save_size == s.ram.size());
    std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_GB, KIND_ROM, out, err);
    bool same = out.size() == s.rom.size() && memcmp(out.data(), s.rom.data(), out.size()) == 0;
    CHECK(same);
    if (!same) printf("  GB tipo %02X (%s): ROM difere\n", c.type, c.title);
    if (s.ram.empty()) { dump(be, SYS_GB, KIND_SAVE, out, err); CHECK(err == E_SEM_SAVE); continue; }
    for (size_t i = 0; i < s.ram.size(); i++) s.ram[i] = (hdr_type == 6) ? uint8_t(pat(uint32_t(i) + 3) & 0x0F) : pat(uint32_t(i) + 3);
    dump(be, SYS_GB, KIND_SAVE, out, err);
    bool eq = out.size() == s.ram.size();
    for (size_t i = 0; eq && i < out.size(); i++) if ((hdr_type == 6 ? (out[i] & 0x0F) : out[i]) != s.ram[i]) eq = false;
    CHECK(eq); CHECK(!s.ram_en);                                       // lê e desabilita a RAM
    if (!eq) printf("  GB tipo %02X (%s): save difere\n", c.type, c.title);
    uint32_t n = uint32_t(s.ram.size());
    std::vector<uint8_t> sv(n); for (size_t i = 0; i < n; i++) sv[i] = (hdr_type == 6) ? uint8_t(pat(uint32_t(i) + 800) & 0x0F) : pat(uint32_t(i) + 800);
    uint16_t e2 = 0; bool wb = be.write_begin(SYS_GB, n, e2); CHECK(wb); if (!wb) printf("  GB tipo %02X (%s): write_begin err=%u n=%u\n", c.type, c.title, e2, n);
    bool ok = true; for (uint32_t off = 0; off < n; off += 512) ok = ok && be.write_block(off, &sv[off], uint16_t(n - off < 512 ? n - off : 512));
    CHECK(ok && be.write_commit() && s.ram == sv && !s.ram_en);
    CHECK(s.cam_wrong == 0);
    CHECK(hdr_type != 0xFC || s.cam_calls > 0);
  }
  // MBC7: EEPROM serial por bit-bang
  { SimGb s(0x22, 3, 0, "COMMAND MASTER"); s.rom[0x14E] = 0xBE; s.rom[0x14F] = 0xA5; s.ram.assign(512, 0);   // só o Command Master tem 93LC66 (512 B)
    CartBackend be(nullptr, nullptr, nullptr, nullptr, &s); DetectInfo d; be.detect(SYS_GB, d); CHECK(d.status == 0 && d.save_size == 512);
    for (size_t i = 0; i < 512; i++) s.ram[i] = pat(uint32_t(i) + 40);
    std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_GB, KIND_SAVE, out, err); CHECK(out == s.ram);
    std::vector<uint8_t> sv(512); for (size_t i = 0; i < 512; i++) sv[i] = pat(uint32_t(i) + 900);
    uint16_t e2 = 0; CHECK(be.write_begin(SYS_GB, 512, e2));
    bool ok = true; for (uint32_t off = 0; off < 512; off += 7) ok = ok && be.write_block(off, &sv[off], uint16_t(512 - off < 7 ? 512 - off : 7));   // blocos de 7 bytes: começam e terminam no meio de palavras
    CHECK(ok && be.write_commit() && s.ram == sv && !s.e_wen && !s.ram_en && !s.e_cs); }
  { SimGb s(0x22, 3, 0, "KIRBY TNT"); CartBackend be(nullptr, nullptr, nullptr, nullptr, &s);
    for (size_t i = 0; i < 256; i++) s.ram[i] = pat(uint32_t(i) + 5);
    std::vector<uint8_t> same = s.ram; uint16_t e2 = 0; CHECK(be.write_begin(SYS_GB, 256, e2));
    int before = s.e_words_written; bool ok = be.write_block(0, same.data(), 256); CHECK(ok && be.write_commit() && s.e_words_written == before && s.ram == same);   // não regrava o que não mudou
    CHECK(be.write_begin(SYS_GB, 256, e2)); std::vector<uint8_t> one = same; one[101] ^= 0x40;
    ok = be.write_block(0, one.data(), 256); CHECK(ok && be.write_commit() && s.ram == one && s.e_words_written == before + 1); }       // muda 1 byte: grava 1 palavra
  { SimGb s(0x22, 3, 0, "KIRBY TNT"); s.e_busy_polls = 50; CartBackend be(nullptr, nullptr, nullptr, nullptr, &s);                         // gravação lenta: espera o pronto
    std::vector<uint8_t> sv(256, 0x5A); uint16_t e2 = 0; CHECK(be.write_begin(SYS_GB, 256, e2)); bool ok = be.write_block(0, sv.data(), 256); CHECK(ok && be.write_commit() && s.ram == sv); }
  { SimGb s(0x22, 3, 0, "KIRBY TNT"); s.e_stuck = true; CartBackend be(nullptr, nullptr, nullptr, nullptr, &s);                           // EEPROM que nunca fica pronta: erro, sem travar
    std::vector<uint8_t> sv(256, 0x5A); uint16_t e2 = 0; CHECK(be.write_begin(SYS_GB, 256, e2)); CHECK(!be.write_block(0, sv.data(), 256)); be.write_abort(); CHECK(!s.ram_en && !s.e_cs); }
  // MMM01 reconhecido só pela tabela de títulos (o cabeçalho do menu diz MBC1)
  { SimGb s(0x01, 5, 0, "RTYPE 2 SET", 0x32, true); s.type = 0x0B; s.mm_hdr();
    CartBackend be(nullptr, nullptr, nullptr, nullptr, &s); DetectInfo d; be.detect(SYS_GB, d); CHECK(d.status == 0 && d.rom_size == s.rom.size());
    std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_GB, KIND_ROM, out, err); CHECK(out == s.rom); CHECK(s.begins >= 3); }          // um reset por bloco de 512 KB, mais o de ligar
  { SimGb s(0x0B, 6, 0, "GRANDE"); CartBackend be(nullptr, nullptr, nullptr, nullptr, &s); DetectInfo d; be.detect(SYS_GB, d); CHECK(d.status == 2); }   // MMM01 de 2 MB: recusado
  // MMM01 já mapeado por uma operação anterior: a próxima operação tem que ler o cabeçalho do menu (o acquire e o probe reiniciam o cartucho)
  { SimGb s(0x0B, 5, 0, "MMM01"); CartBackend be(nullptr, nullptr, nullptr, nullptr, &s); std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_GB, KIND_ROM, out, err);
    DetectInfo d; be.detect(SYS_GB, d); CHECK(d.status == 0 && strcmp(d.name, "MMM01") == 0); }
  // MBC6: ROM em bancos de 8 KB; save = SRAM de 32 KB + Flash de 1 MB (só leitura)
  { SimGb s(0x20, 5, 3, "NETDEGET"); for (size_t i = 0; i < s.ram.size(); i++) s.ram[i] = pat(uint32_t(i) + 31); for (size_t i = 0; i < s.flash.size(); i++) s.flash[i] = pat(uint32_t(i) + 977);
    CartBackend be(nullptr, nullptr, nullptr, nullptr, &s); DetectInfo d; be.detect(SYS_GB, d); CHECK(d.status == 0 && d.rom_size == s.rom.size() && d.save_size == 32768 + (1 << 20));
    s.sel_a = s.sel_b = 8; s.flash_map = true;                           // estado velho de uma operação anterior: a ROM tem que voltar a aparecer
    std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_GB, KIND_ROM, out, err); CHECK(out == s.rom);
    s.flash_map = false; s.sel_a = s.sel_b = 0;
    dump(be, SYS_GB, KIND_SAVE, out, err); std::vector<uint8_t> exp = s.ram; exp.insert(exp.end(), s.flash.begin(), s.flash.end());
    CHECK(out == exp); CHECK(!s.flash_map && !s.ram_en && !s.fw_en && s.sel_a == 0 && s.sel_b == 0);                  // volta tudo ao normal
    uint16_t e2 = 0; CHECK(!be.write_begin(SYS_GB, 32768 + (1 << 20), e2) && e2 == E_SISTEMA); CHECK(!s.flash_map && !s.ram_en); }  // gravar a Flash não foi portado
  // sem cartucho, checksum errado, mappers sem suporte
  { SimGb none(0x01, 4, 0); none.absent = true; CartBackend be(nullptr, nullptr, nullptr, nullptr, &none); DetectInfo d; be.detect(SYS_GB, d); CHECK(d.status == 1); }
  { SimGb bad(0x01, 4, 0, "RUIM"); bad.rom[0x14D] ^= 0x55; CartBackend be(nullptr, nullptr, nullptr, nullptr, &bad); DetectInfo d; be.detect(SYS_GB, d); CHECK(d.status == 4); }
  for (int t : {0x15, 0x1F}) { SimGb s(t, 4, 0); CartBackend be(nullptr, nullptr, nullptr, nullptr, &s); DetectInfo d; be.detect(SYS_GB, d); CHECK(d.status == 2); }
  { SimGb s(0x01, 0x52, 0); CartBackend be(nullptr, nullptr, nullptr, nullptr, &s); DetectInfo d; be.detect(SYS_GB, d); CHECK(d.status == 2); }   // tamanho fora da tabela
  { SimGb s(0x01, 4, 0); CartBackend be(nullptr, nullptr, nullptr, nullptr, &s); CHECK((be.systems() >> SYS_GB) & 1); }
  { SimSnes s(false, 9, 3); CartBackend be(&s, nullptr, nullptr, nullptr); CHECK(!be.supports(SYS_GB)); }
}

static void test_nes() {
  for (uint32_t prg : {16384u, 32768u}) for (uint32_t chr : {0u, 8192u}) {
    SimNes s(prg, chr); CartBackend be(nullptr, &s, nullptr, nullptr);
    for (uint8_t sys : {SYS_NES, SYS_FAMICOM}) {
      DetectInfo d; be.detect(sys, d);
      CHECK(d.status == 0 && d.rom_size == 16 + prg + chr);
      std::vector<uint8_t> out; uint16_t err; dump(be, sys, KIND_ROM, out, err);
      CHECK(out.size() == 16 + prg + chr && out[0] == 'N' && out[3] == 0x1A && out[4] == prg / 16384 && out[5] == chr / 8192);
      CHECK(memcmp(&out[16], s.prgrom.data(), prg) == 0 && (chr == 0 || memcmp(&out[16 + prg], s.chrrom.data(), chr) == 0));
    }
  }
  SimNes none(16384, 8192); none.absent = true; CartBackend be(nullptr, &none, nullptr, nullptr);
  DetectInfo d; be.detect(SYS_NES, d); CHECK(d.status == 1);
}

static void test_nes_mappers() {
  struct Cfg { int m; uint32_t prg, chr; };
  const Cfg cfgs[] = {{1, 128 << 10, 64 << 10}, {1, 256 << 10, 0}, {2, 128 << 10, 0}, {3, 32 << 10, 32 << 10},
                      {4, 128 << 10, 128 << 10}, {4, 256 << 10, 256 << 10}, {7, 128 << 10, 0}, {0, 32 << 10, 8 << 10},
                      {66, 128 << 10, 32 << 10}, {66, 64 << 10, 16 << 10}, {11, 128 << 10, 128 << 10}, {11, 32 << 10, 16 << 10},
                      {71, 128 << 10, 0}, {71, 256 << 10, 0}, {9, 128 << 10, 128 << 10}, {9, 64 << 10, 32 << 10},
                      {10, 128 << 10, 64 << 10}, {10, 256 << 10, 128 << 10}, {69, 128 << 10, 128 << 10}, {69, 256 << 10, 256 << 10},
                      {5, 128 << 10, 128 << 10}, {5, 512 << 10, 256 << 10},
                      {118, 128 << 10, 128 << 10}, {206, 32 << 10, 32 << 10}, {206, 64 << 10, 64 << 10}, {79, 64 << 10, 32 << 10}, {79, 32 << 10, 16 << 10},
                      {87, 32 << 10, 32 << 10}, {87, 16 << 10, 8 << 10}, {78, 128 << 10, 128 << 10}, {70, 128 << 10, 128 << 10}, {70, 256 << 10, 64 << 10},
                      {75, 128 << 10, 128 << 10}, {75, 64 << 10, 64 << 10}, {33, 128 << 10, 128 << 10}, {48, 256 << 10, 256 << 10}};
  for (const Cfg& c : cfgs) {
    SimMapper s(c.m, c.prg, c.chr); CartBackend be(nullptr, &s, nullptr, nullptr);
    be.set_options(uint16_t(c.m), uint16_t(c.prg >> 10), uint16_t(c.chr >> 10));
    uint32_t size = 0; uint16_t err = 0;
    bool ok = be.open_read(SYS_NES, KIND_ROM, size, err);
    CHECK(ok && size == 16 + c.prg + c.chr);
    if (!ok) { printf("  mapper %d: erro %u\n", c.m, err); continue; }
    std::vector<uint8_t> out(size);
    for (uint32_t off = 0; off < size; off += 512) { uint16_t n = size - off < 512 ? uint16_t(size - off) : 512; be.read(SYS_NES, KIND_ROM, off, &out[off], n); }
    be.close_read();
    CHECK(out[0] == 'N' && out[4] == c.prg / 16384 && out[5] == c.chr / 8192 && out[6] == uint8_t((c.m & 0x0F) << 4) && out[7] == uint8_t(c.m & 0xF0));
    bool prg_ok = memcmp(&out[16], s.prgrom.data(), c.prg) == 0;
    bool chr_ok = c.chr == 0 || memcmp(&out[16 + c.prg], s.chrrom.data(), c.chr) == 0;
    CHECK(prg_ok); CHECK(chr_ok);
    if (!prg_ok || !chr_ok) printf("  mapper %d prg %uK chr %uK: prg_ok=%d chr_ok=%d\n", c.m, c.prg >> 10, c.chr >> 10, prg_ok, chr_ok);
  }
  // opções inválidas
  SimMapper s(4, 128 << 10, 128 << 10); CartBackend be(nullptr, &s, nullptr, nullptr);
  uint32_t size; uint16_t err;
  be.set_options(99, 128, 128); CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_SISTEMA);
  be.set_options(4, 0, 128);   CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_ARGUMENTO);
  be.set_options(71, 128, 8);  CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_ARGUMENTO);   // Camerica: CHR-RAM
  be.set_options(66, 48, 8);   CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_ARGUMENTO);   // GxROM: PRG múltiplo de 32
  be.set_options(66, 256, 8);  CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_SISTEMA);     // além dos 2 bits
  be.set_options(9, 256, 8);   CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_SISTEMA);     // MMC2: até 128 KB
  be.set_options(1, 128, 256); CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_SISTEMA);     // MMC1: CHR até 128 KB (5 bits)
  be.set_options(4, 128, 512); CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_SISTEMA);     // MMC3: CHR até 256 KB (8 bits)
  be.set_options(4, 1024, 128); CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_SISTEMA);    // MMC3: PRG até 512 KB
  be.set_options(10, 128, 256); CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_SISTEMA);    // MMC4: CHR até 128 KB
  be.set_options(69, 128, 512); CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_SISTEMA);    // FME-7: CHR até 256 KB
  be.set_options(2, 128, 8);   CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_ARGUMENTO);
}

static void test_nes_saves() {
  // dumpar a ROM de um MMC1 com bateria não pode estragar a SRAM (escritas em $E000+ pela sequência segura)
  { SimMapper s(1, 256 << 10, 0); CartBackend be(nullptr, &s, nullptr, nullptr);
    for (size_t i = 0; i < s.ram.size(); i++) s.ram[i] = pat(uint32_t(i) + 4);
    std::vector<uint8_t> before = s.ram, out; uint16_t err = 0;
    be.set_options(1, 256, 0); dump(be, SYS_NES, KIND_ROM, out, err);
    CHECK(out.size() == 16 + (256u << 10) && s.ram == before && s.corrupted == 0);
    be.set_options(1, 0, 0); dump(be, SYS_NES, KIND_SAVE, out, err);
    CHECK(out == before && s.corrupted == 0);
  }
  for (int m : {1, 4}) {
    SimMapper s(m, 128 << 10, 64 << 10); CartBackend be(nullptr, &s, nullptr, nullptr);
    for (size_t i = 0; i < s.ram.size(); i++) s.ram[i] = pat(uint32_t(i) + 321);
    be.set_options(uint16_t(m), 0, 0);                                  // para save só o mapper importa
    std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_NES, KIND_SAVE, out, err);
    CHECK(out.size() == 8192 && out == s.ram && !s.ram_enabled());      // lê e desliga a RAM
    std::vector<uint8_t> save(8192); for (size_t i = 0; i < save.size(); i++) save[i] = pat(uint32_t(i) + 777);
    be.set_options(uint16_t(m), 0, 0);
    uint16_t e2 = 0; CHECK(be.write_begin(SYS_FAMICOM, 8192, e2));
    bool ok = true; for (uint32_t off = 0; off < 8192; off += 512) ok = ok && be.write_block(off, &save[off], 512);
    CHECK(ok && be.write_commit() && s.ram == save && !s.ram_enabled());
    be.set_options(uint16_t(m), 0, 0); CHECK(!be.write_begin(SYS_NES, 4096, e2) && e2 == E_ARGUMENTO);
    // cartucho sem RAM: a gravação falha na conferência
    SimMapper nr(m, 128 << 10, 64 << 10); nr.has_ram = false; CartBackend b2(nullptr, &nr, nullptr, nullptr);
    b2.set_options(uint16_t(m), 0, 0); CHECK(b2.write_begin(SYS_NES, 8192, e2)); CHECK(!b2.write_block(0, &save[0], 512)); b2.write_abort();
  }
  // MMC1 com RAM de 16 KB (SOROM) e 32 KB (SXROM): bancos de 8 KB pelo registrador CHR 0
  for (uint32_t kb : {16u, 32u}) {
    uint32_t n = kb * 1024;
    SimMapper s(1, 256 << 10, 0); s.ram.assign(n, 0); CartBackend be(nullptr, &s, nullptr, nullptr);
    for (size_t i = 0; i < n; i++) s.ram[i] = pat(uint32_t(i) + 55);
    be.set_options(1, uint16_t(kb), 0);
    std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_NES, KIND_SAVE, out, err);
    CHECK(out.size() == n && out == s.ram && !s.ram_enabled());
    std::vector<uint8_t> save(n); for (size_t i = 0; i < n; i++) save[i] = pat(uint32_t(i) + 901);
    uint16_t e2 = 0; be.set_options(1, uint16_t(kb), 0); CHECK(be.write_begin(SYS_NES, n, e2));
    bool ok = true; for (uint32_t off = 0; off < n; off += 512) ok = ok && be.write_block(off, &save[off], 512);
    CHECK(ok && be.write_commit() && s.ram == save && !s.ram_enabled());
    be.set_options(1, 8, 0); CHECK(!be.write_begin(SYS_NES, n, e2) && e2 == E_ARGUMENTO);     // tamanho do arquivo != RAM informada
    uint32_t size = 0; be.set_options(1, 24, 0); CHECK(!be.open_read(SYS_NES, KIND_SAVE, size, err) && err == E_ARGUMENTO);
    be.set_options(4, uint16_t(kb), 0); CHECK(!be.open_read(SYS_NES, KIND_SAVE, size, err) && err == E_ARGUMENTO);   // MMC3: só 8 KB
  }
  // MMC5 (8, 16 e 32 KB) e FME-7 (8 KB): RAM com habilitação/proteção
  for (int m : {5, 69}) for (uint32_t kb : {8u, 16u, 32u}) {
    if (m == 69 && kb != 8) continue;
    uint32_t n = kb * 1024;
    SimMapper s(m, 128 << 10, 64 << 10); s.ram.assign(n, 0); CartBackend be(nullptr, &s, nullptr, nullptr);
    for (size_t i = 0; i < n; i++) s.ram[i] = pat(uint32_t(i) + 31 * m);
    be.set_options(uint16_t(m), uint16_t(kb == 8 ? 0 : kb), 0);
    std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_NES, KIND_SAVE, out, err);
    CHECK(out.size() == n && out == s.ram);
    CHECK(m == 5 || !s.ram_enabled());                                  // FME-7: RAM desligada ao terminar
    std::vector<uint8_t> save(n); for (size_t i = 0; i < n; i++) save[i] = pat(uint32_t(i) + 4242 + m);
    uint16_t e2 = 0; be.set_options(uint16_t(m), uint16_t(kb == 8 ? 0 : kb), 0); CHECK(be.write_begin(SYS_NES, n, e2));
    bool ok = true; for (uint32_t off = 0; off < n; off += 512) ok = ok && be.write_block(off, &save[off], 512);
    CHECK(ok && be.write_commit() && s.ram == save);
    CHECK(m != 5 || (s.m5[2] == 0 && s.m5[3] == 0));                    // MMC5: protegida de novo
    CHECK(m != 69 || !s.ram_enabled());
    // cartucho sem RAM: a conferência falha
    SimMapper nr(m, 128 << 10, 64 << 10); nr.has_ram = false; CartBackend b2(nullptr, &nr, nullptr, nullptr);
    b2.set_options(uint16_t(m), uint16_t(kb == 8 ? 0 : kb), 0); CHECK(b2.write_begin(SYS_NES, n, e2)); CHECK(!b2.write_block(0, &save[0], 512)); b2.write_abort();
  }
  { uint32_t size = 0; uint16_t err = 0;
    SimMapper s(69, 128 << 10, 64 << 10); CartBackend be(nullptr, &s, nullptr, nullptr);
    be.set_options(69, 16, 0); CHECK(!be.open_read(SYS_NES, KIND_SAVE, size, err) && err == E_ARGUMENTO);   // FME-7: só 8 KB
  }
  SimMapper s2(2, 128 << 10, 0); CartBackend be2(nullptr, &s2, nullptr, nullptr);
  std::vector<uint8_t> o; uint16_t err;
  be2.set_options(2, 0, 0); dump(be2, SYS_NES, KIND_SAVE, o, err); CHECK(err == E_SEM_SAVE);       // UxROM não tem bateria
  be2.set_options(0, 0, 0); dump(be2, SYS_NES, KIND_SAVE, o, err); CHECK(err == E_SEM_SAVE);       // sem mapper informado
}

static void test_md() {
  SimMd s(0x100000); CartBackend be(nullptr, nullptr, &s, nullptr);
  DetectInfo d; be.detect(SYS_MD, d);
  CHECK(d.status == 0 && d.rom_size == 0x100000 && strcmp(d.name, "JOGO DE TESTE") == 0);
  std::vector<uint8_t> out; uint16_t err; dump(be, SYS_MD, KIND_ROM, out, err);
  CHECK(out.size() == s.rom.size() && memcmp(out.data(), s.rom.data(), out.size()) == 0);
  s.absent = true; be.detect(SYS_MD, d); CHECK(d.status == 1);
}

static void test_md_sram_ssf() {
  for (int kind = 1; kind <= 3; kind++) {
    SimMd s(0x100000, kind); CartBackend be(nullptr, nullptr, &s, nullptr);
    DetectInfo d; be.detect(SYS_MD, d);
    CHECK(d.status == 0 && d.save_size == 8192 && d.save_type == 1);
    for (size_t i = 0; i < s.sram.size(); i++) s.sram[i] = uint16_t(pat(uint32_t(i) + 31) << 8 | pat(uint32_t(i) + 32));
    // SRAM só aparece com o registrador ligado; a leitura liga e desliga
    std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_MD, KIND_SAVE, out, err);
    CHECK(out.size() == 8192 && !s.sram_on);
    bool same = true;
    for (uint32_t i = 0; i < 8192 && same; i++) {
      uint16_t w = s.sram[kind == 3 ? i / 2 : i];
      uint8_t want = kind == 1 ? uint8_t(w) : (kind == 2 ? uint8_t(w >> 8) : ((i & 1) ? uint8_t(w) : uint8_t(w >> 8)));
      same = out[i] == want;
    }
    CHECK(same);
    // gravação: padrão novo, lido de volta pelo próprio caminho de leitura
    std::vector<uint8_t> save(8192); for (size_t i = 0; i < save.size(); i++) save[i] = pat(uint32_t(i) + 900);
    uint16_t e2 = 0; CHECK(be.write_begin(SYS_MD, 8192, e2));
    bool ok = true; for (uint32_t off = 0; off < 8192; off += 512) ok = ok && be.write_block(off, &save[off], 512);
    CHECK(ok && be.write_commit() && !s.sram_on);
    dump(be, SYS_MD, KIND_SAVE, out, err); CHECK(out == save);
    CHECK(!be.write_begin(SYS_MD, 4096, e2) && e2 == E_ARGUMENTO);
    // a ROM continua igual (a SRAM não pode vazar para a leitura da ROM)
    dump(be, SYS_MD, KIND_ROM, out, err); CHECK(out.size() == s.rom.size() && memcmp(out.data(), s.rom.data(), out.size()) == 0);
  }
  SimMd nosave(0x100000, 0); CartBackend b2(nullptr, nullptr, &nosave, nullptr);
  std::vector<uint8_t> o; uint16_t err; dump(b2, SYS_MD, KIND_SAVE, o, err); CHECK(err == E_SEM_SAVE);
  // SSF2: 5 MB com bancos de 512 KB
  SimMd ssf(0x500000, 0, true); CartBackend b3(nullptr, nullptr, &ssf, nullptr);
  DetectInfo d; b3.detect(SYS_MD, d); CHECK(d.status == 0 && d.rom_size == 0x500000);
  dump(b3, SYS_MD, KIND_ROM, o, err);
  CHECK(o.size() == ssf.rom.size() && memcmp(o.data(), ssf.rom.data(), o.size()) == 0);
  // sem o mapper, uma ROM de 5 MB no cabeçalho é limitada a 4 MB
  SimMd big(0x500000, 0, false); CartBackend b4(nullptr, nullptr, &big, nullptr); b4.detect(SYS_MD, d); CHECK(d.rom_size == 0x400000);
}

static void test_md_tamanho() {
  uint32_t size; uint16_t err; DetectInfo d;
  // cabeçalho diz 4 MB, mas a ROM de 1 MB aparece espelhada: o firmware reduz sozinho
  SimMd m(0x100000, 0, false, 8192, 0x400000); CartBackend be(nullptr, nullptr, &m, nullptr);
  be.detect(SYS_MD, d); CHECK(d.status == 0 && d.rom_size == 0x100000);
  // tamanho informado vence o cabeçalho
  be.set_options(0, 8192, 0); CHECK(!be.open_read(SYS_MD, KIND_ROM, size, err) && err == E_ARGUMENTO);   // acima do limite de 4 MB
  be.set_options(0, 16, 0);   CHECK(!be.open_read(SYS_MD, KIND_ROM, size, err) && err == E_ARGUMENTO);   // abaixo de 32 KB
  // DETECT ignora e apaga as opções (nada herdado entre comandos); close_read também as apaga
  be.set_options(0, 512, 0); be.detect(SYS_MD, d); CHECK(d.rom_size == 0x100000);
  CHECK(be.open_read(SYS_MD, KIND_ROM, size, err) && size == 0x100000); be.close_read();
  be.set_options(0, 512, 0); CHECK(be.open_read(SYS_MD, KIND_ROM, size, err) && size == 0x80000); be.close_read();
  CHECK(be.open_read(SYS_MD, KIND_ROM, size, err) && size == 0x100000); be.close_read();
  // ROM real de 2 MB com cabeçalho correto não é reduzida
  SimMd real(0x200000); CartBackend b2(nullptr, nullptr, &real, nullptr); b2.detect(SYS_MD, d); CHECK(d.rom_size == 0x200000);
  // ROM de 1 MB sem espelho (metades diferentes) com cabeçalho de 1 MB também fica
  SimMd one(0x100000); CartBackend b3(nullptr, nullptr, &one, nullptr); b3.detect(SYS_MD, d); CHECK(d.rom_size == 0x100000);
}

static void test_md_eeprom() {
  struct Case { int type; size_t size; uint16_t chk; };
  const Case cases[] = {
    {1, 256, 0x694F}, {2, 256, 0xCC3F}, {2, 2048, 0x3DE6}, {2, 8192, 0xCB78}, {3, 128, 0xAD23}, {3, 128, 0x7270},
    {4, 128, 0xA107}, {5, 1024, 0x7E65}, {5, 2048, 0x7E50}, {5, 8192, 0x12C1},
  };
  for (const Case& k : cases) {
    SimMdEep s(k.type, k.size, k.chk); CartBackend be(nullptr, nullptr, &s, nullptr);
    DetectInfo d; be.detect(SYS_MD, d);
    CHECK(d.status == 0 && d.save_size == k.size && d.save_type == 3);
    std::vector<uint8_t> out; uint16_t err = 0; dump(be, SYS_MD, KIND_SAVE, out, err);
    CHECK(out == s.e.mem);
    CHECK(s.violations == 0 && !s.on2);                    // tipo 2 liga a EEPROM só durante o acesso
    // gravação: só o que mudou é gravado; conferido; o ciclo de escrita é esperado
    std::vector<uint8_t> nd(k.size); for (size_t i = 0; i < k.size; i++) nd[i] = pat(uint32_t(i) * 17 + 3);
    uint16_t e2 = 0; be.set_options(0, 0, 0);
    CHECK(be.write_begin(SYS_MD, uint32_t(k.size), e2));
    for (size_t off = 0; off < k.size; off += 100) { size_t n = k.size - off < 100 ? k.size - off : 100; CHECK(be.write_block(uint32_t(off), &nd[off], uint16_t(n))); }
    CHECK(be.write_commit() && s.e.mem == nd);
    int w1 = s.e.writes;
    CHECK(be.write_begin(SYS_MD, uint32_t(k.size), e2) && be.write_block(0, nd.data(), uint16_t(k.size < 512 ? k.size : 512)) && be.write_commit());
    CHECK(s.e.writes == w1);                              // mesmos dados: nada é regravado
    CHECK(!be.write_begin(SYS_MD, uint32_t(k.size) + 1, e2) && e2 == E_ARGUMENTO);
  }
  {  // checksum em branco só vale com E840 no cabeçalho; Codemasters 165E só com 'DN' no início
    SimMdEep a(3, 128, 0x0000); CartBackend ba(nullptr, nullptr, &a, nullptr); DetectInfo d; ba.detect(SYS_MD, d); CHECK(d.save_size == 0);
    a.rom[0x1B2] = 0xE8; a.rom[0x1B3] = 0x40; ba.detect(SYS_MD, d); CHECK(d.save_size == 128 && d.save_type == 3);
    SimMdEep c(5, 2048, 0x165E); CartBackend bc(nullptr, nullptr, &c, nullptr); bc.detect(SYS_MD, d); CHECK(d.save_size == 0);
    c.rom[0] = 0x44; c.rom[1] = 0x4E; bc.detect(SYS_MD, d); CHECK(d.save_size == 2048);
  }
  {  // sem ACK na gravação: erro, e a EEPROM não é alterada
    SimMdEep s(4, 128, 0xA107); s.dead = true; std::vector<uint8_t> before = s.e.mem;
    CartBackend be(nullptr, nullptr, &s, nullptr); uint16_t e2 = 0; uint8_t b = 0x5A;
    CHECK(be.write_begin(SYS_MD, 128, e2) && !be.write_block(0, &b, 1)); be.write_abort();
    CHECK(s.e.mem == before);
  }
  {  // EEPROM que não responde (sem ACK): erro de leitura, sem travar
    SimMdEep s(4, 128, 0xA107); s.dead = true;
    CartBackend be(nullptr, nullptr, &s, nullptr); uint32_t size = 0; uint16_t err = 0; uint8_t buf[16];
    CHECK(be.open_read(SYS_MD, KIND_SAVE, size, err) && size == 128);
    CHECK(!be.read(SYS_MD, KIND_SAVE, 0, buf, 16));
    be.close_read();
  }
  {  // cartucho com SRAM continua como antes
    SimMd s(0x100000, 1, false, 8192); CartBackend be(nullptr, nullptr, &s, nullptr); DetectInfo d; be.detect(SYS_MD, d); CHECK(d.save_type == 1 && d.save_size == 8192);
  }
}

static void test_gba_saves() {
  struct Case { uint16_t type; uint32_t size; uint8_t stype; };
  const Case cases[] = {{1, 512, 3}, {2, 8192, 3}, {3, 32768, 1}, {4, 65536, 2}, {5, 131072, 2}};
  for (const Case& k : cases) {
    SimGba s(1 << 20); CartBackend be(nullptr, nullptr, nullptr, &s);
    for (size_t i = 0; i < s.sram.size(); i++) s.sram[i] = pat(uint32_t(i) + 77);
    s.eep.resize(k.size); s.flash_data.resize(k.size);
    for (uint32_t i = 0; i < k.size; i++) s.eep[i] = s.flash_data[i] = pat(i * 3 + 11);
    s.flash = (k.type >= 4);
    be.set_options(k.type, 0, 0);
    uint32_t size = 0; uint16_t err = 0;
    CHECK(be.open_read(SYS_GBA, KIND_SAVE, size, err) && size == k.size);
    std::vector<uint8_t> out(size);
    for (uint32_t off = 0; off < size; off += 512) be.read(SYS_GBA, KIND_SAVE, off, &out[off], 512 < size - off ? 512 : uint16_t(size - off));
    be.close_read();
    const std::vector<uint8_t>& want = (k.type == 3) ? s.sram : (k.type >= 4 ? s.flash_data : s.eep);
    CHECK(out.size() == want.size() && memcmp(out.data(), want.data(), out.size()) == 0);
    CHECK(s.bank == 0);                                    // Flash volta ao banco 0
    if (k.type <= 2) CHECK(s.eep_reads == int(k.size / 8)); // um acesso por bloco de 8 bytes
  }
  SimGba s(1 << 20); CartBackend be(nullptr, nullptr, nullptr, &s);
  uint32_t size; uint16_t err = 0;
  be.set_options(9, 0, 0); CHECK(!be.open_read(SYS_GBA, KIND_SAVE, size, err) && err == E_ARGUMENTO);
  be.set_options(9, 0, 0); CHECK(!be.write_begin(SYS_GBA, 65536, err) && err == E_ARGUMENTO);
}

// Grava `data` pelo backend em blocos de `blk` bytes. Devolve false se algo falhar (err recebe o código).
static bool gba_write(CartBackend& be, uint16_t type, const std::vector<uint8_t>& data, size_t blk, uint16_t& err) {
  be.set_options(type, 0, 0);
  if (!be.write_begin(SYS_GBA, uint32_t(data.size()), err)) return false;
  for (size_t off = 0; off < data.size(); off += blk) {
    size_t n = data.size() - off < blk ? data.size() - off : blk;
    if (!be.write_block(uint32_t(off), &data[off], uint16_t(n))) { be.write_abort(); err = E_CARTUCHO_IO; return false; }
  }
  return be.write_commit();
}

static void test_gba_write() {
  uint16_t err = 0;
  {  // SRAM 32 KB
    SimGba s(1 << 20); CartBackend be(nullptr, nullptr, nullptr, &s);
    std::vector<uint8_t> d(32768); for (size_t i = 0; i < d.size(); i++) d[i] = pat(uint32_t(i) * 11 + 5);
    CHECK(gba_write(be, 3, d, 512, err) && s.sram == d);
    SimGba ro(1 << 20); ro.sram_ro = true; CartBackend b2(nullptr, nullptr, nullptr, &ro);
    CHECK(!gba_write(b2, 3, d, 512, err) && err == E_CARTUCHO_IO);          // não gravou: a conferência pega
    CHECK(!gba_write(be, 3, std::vector<uint8_t>(100), 100, err) && err == E_ARGUMENTO);   // tamanho errado
  }
  for (uint16_t type : {1, 2}) {   // EEPROM 512 B e 8 KB, com blocos que não são múltiplos de 8
    uint32_t n = type == 1 ? 512 : 8192;
    for (size_t blk : {512u, 100u, 7u}) {
      SimGba s(1 << 20); CartBackend be(nullptr, nullptr, nullptr, &s); s.eep.assign(n, 0xAA);
      std::vector<uint8_t> d(n); for (size_t i = 0; i < n; i++) d[i] = pat(uint32_t(i) * 13 + 1);
      CHECK(gba_write(be, type, d, blk, err) && s.eep == d);
    }
    SimGba s(1 << 20); CartBackend be(nullptr, nullptr, nullptr, &s); s.eep.assign(n, 0xAA); s.eep_stuck = true;
    CHECK(!gba_write(be, type, std::vector<uint8_t>(n, 1), 512, err) && err == E_CARTUCHO_IO);
  }
  struct F { uint16_t type; uint16_t id; bool atmel; uint32_t size; };
  const F flashes[] = {{4, 0xBFD4, false, 65536}, {4, 0xC21C, false, 65536}, {4, 0x321B, false, 65536}, {4, 0x1F3D, true, 65536},
                       {5, 0xC209, false, 131072}, {5, 0x6213, false, 131072}};
  for (const F& f : flashes) {
    for (size_t blk : {512u, 200u}) {
      SimGba s(1 << 20); CartBackend be(nullptr, nullptr, nullptr, &s);
      s.flash = true; s.flash_id = f.id; s.atmel = f.atmel; s.flash_data.resize(f.size);
      for (size_t i = 0; i < f.size; i++) s.flash_data[i] = pat(uint32_t(i) + 99);          // conteúdo velho, não apagado
      std::vector<uint8_t> d(f.size); for (size_t i = 0; i < f.size; i++) d[i] = pat(uint32_t(i) * 3 + 17);
      bool ok = gba_write(be, f.type, d, blk, err);
      CHECK(ok && s.flash_data == d);
      CHECK(s.bank == 0);                                                                     // volta ao banco 0
      CHECK(f.atmel ? s.erases == 0 : s.erases == 1);                                         // Atmel não apaga o chip
    }
  }
  {  // chip desconhecido: nada é apagado nem gravado
    SimGba s(1 << 20); CartBackend be(nullptr, nullptr, nullptr, &s);
    s.flash = true; s.flash_id = 0x1234; s.flash_data.assign(65536, 0x55);
    CHECK(!gba_write(be, 4, std::vector<uint8_t>(65536, 0), 512, err) && err == E_CARTUCHO_IO);
    CHECK(s.erases == 0 && s.programmed == 0 && s.flash_data == std::vector<uint8_t>(65536, 0x55));
    // ID de 128 KB com tipo 4 (e o contrário) também é recusado
    SimGba s2(1 << 20); CartBackend b2(nullptr, nullptr, nullptr, &s2);
    s2.flash = true; s2.flash_id = 0xC209; s2.flash_data.assign(131072, 0x55);
    CHECK(!gba_write(b2, 4, std::vector<uint8_t>(65536, 0), 512, err) && s2.erases == 0);
  }
  {  // não apagou (comando ignorado): a conferência de apagado impede de gravar
    SimGba s(1 << 20); CartBackend be(nullptr, nullptr, nullptr, &s);
    s.flash = true; s.flash_id = 0xBFD4; s.stuck = true; s.flash_data.assign(65536, 0x55);
    CHECK(!gba_write(be, 4, std::vector<uint8_t>(65536, 0), 512, err) && err == E_CARTUCHO_IO && s.programmed == 0);
  }
  {  // e-Reader (PSAE, 128 KB): os últimos 128 bytes de cada banco ficam como estão (0xFF depois de apagar)
    SimGba s(1 << 20); CartBackend be(nullptr, nullptr, nullptr, &s);
    memcpy(&s.rom[0xAC], "PSAE", 4);
    s.flash = true; s.flash_id = 0xC209; s.flash_data.resize(131072);
    for (size_t i = 0; i < 131072; i++) s.flash_data[i] = pat(uint32_t(i));
    std::vector<uint8_t> d(131072); for (size_t i = 0; i < d.size(); i++) d[i] = pat(uint32_t(i) * 7 + 2);
    CHECK(gba_write(be, 5, d, 512, err));
    std::vector<uint8_t> want = d; for (int b = 0; b < 2; b++) for (int i = 0; i < 128; i++) want[b * 65536 + 65408 + i] = 0xFF;
    CHECK(s.flash_data == want);
  }
}

static void test_gba() {
  { SimGba g(1 << 20); CartBackend be(nullptr, nullptr, nullptr, &g);       // leitura por palavras: deslocamento e tamanho ímpares
    uint32_t size = 0; uint16_t err = 0; CHECK(be.open_read(SYS_GBA, KIND_ROM, size, err));
    std::vector<uint8_t> a(301), b(1024), one(1);
    CHECK(be.read(SYS_GBA, KIND_ROM, 0, b.data(), 1024));
    CHECK(be.read(SYS_GBA, KIND_ROM, 77, a.data(), 301));                    // começa e termina no meio de uma palavra
    CHECK(memcmp(a.data(), &b[77], 301) == 0);
    CHECK(be.read(SYS_GBA, KIND_ROM, 1, one.data(), 1) && one[0] == b[1]);
    be.close_read(); }
  for (uint32_t mb : {1u, 4u, 16u}) {
    SimGba s(mb << 20); CartBackend be(nullptr, nullptr, nullptr, &s);
    DetectInfo d; be.detect(SYS_GBA, d);
    CHECK(d.status == 0 && d.rom_size == (mb << 20) && strcmp(d.name, "GBA TESTE") == 0);
    std::vector<uint8_t> out; uint16_t err; dump(be, SYS_GBA, KIND_ROM, out, err);
    CHECK(out.size() == s.rom.size() && memcmp(out.data(), s.rom.data(), out.size()) == 0);
    // SRAM de 32 KB (somente leitura)
    for (size_t i = 0; i < s.sram.size(); i++) s.sram[i] = pat(uint32_t(i) + 4242);
    CHECK(d.save_size == 32768 && d.save_type == 255);
    dump(be, SYS_GBA, KIND_SAVE, out, err);
    CHECK(out == s.sram);
  }
  test_gba_saves();
  SimGba s(1 << 20); s.absent = true; CartBackend be(nullptr, nullptr, nullptr, &s); DetectInfo d; be.detect(SYS_GBA, d); CHECK(d.status == 1);
}

static void test_sistemas_sem_barramento() {
  SimNes n(16384, 8192); CartBackend be(nullptr, &n, nullptr, nullptr);
  CHECK(be.systems() == ((1 << SYS_NES) | (1 << SYS_FAMICOM)) && !be.supports(SYS_SNES) && !be.supports(SYS_MOCK));
  uint32_t size; uint16_t err; CHECK(!be.open_read(SYS_SNES, KIND_ROM, size, err) && err == E_SISTEMA);
}

int main() {
  test_snes(); test_snes_exhirom(); test_snes_sa1(); test_snes_chips(); test_gb(); test_nes(); test_nes_mappers(); test_nes_saves(); test_md(); test_md_sram_ssf(); test_md_tamanho(); test_md_eeprom(); test_gba_write(); test_gba(); test_sistemas_sem_barramento();
  printf("%d verificações de cartuchos, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
