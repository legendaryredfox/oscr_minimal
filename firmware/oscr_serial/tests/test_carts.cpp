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
  std::vector<uint8_t> rom, sram; bool hirom; bool absent = false;
  SimSnes(bool hi, uint8_t rsz, uint8_t ssz, bool bad = false) : hirom(hi) {
    rom.resize(1024UL << rsz); for (size_t i = 0; i < rom.size(); i++) rom[i] = pat(uint32_t(i));
    sram.assign(ssz ? 1024UL << ssz : 0, 0);
    size_t h = hi ? 0xFFC0 : 0x7FC0;                       // posição do cabeçalho na ROM
    memset(&rom[h], ' ', 21); memcpy(&rom[h], "TESTE SNES", 10);
    rom[h + 0x15] = hi ? 0x21 : 0x20; rom[h + 0x16] = ssz ? 2 : 0; rom[h + 0x17] = rsz; rom[h + 0x18] = ssz;
    uint16_t sum = 0x1234, comp = bad ? 0x0000 : uint16_t(~sum);
    rom[h + 0x1C] = comp & 0xFF; rom[h + 0x1D] = comp >> 8; rom[h + 0x1E] = sum & 0xFF; rom[h + 0x1F] = sum >> 8;
  }
  void begin() override {} void end() override {}
  size_t sram_index(uint8_t b, uint16_t a, bool& ok) {
    ok = false;
    if (hirom && b >= 0x30 && b <= 0x3F && a >= 0x6000 && a <= 0x7FFF) { ok = true; return size_t(b - 0x30) * 0x2000 + (a - 0x6000); }
    if (!hirom && b >= 0x70 && b <= 0x7D && a < 0x8000) { ok = true; return size_t(b - 0x70) * 0x8000 + a; }
    return 0;
  }
  uint8_t read(uint8_t b, uint16_t a) override {
    if (absent) return 0xFF;
    bool ok; size_t si = sram_index(b, a, ok);
    if (ok) return si < sram.size() ? sram[si] : 0xFF;
    size_t off;
    if (hirom) { if (b >= 0xC0 || (b <= 0x3F && a >= 0x8000)) off = (size_t(b & 0x3F) << 16) | a; else return 0xFF; }
    else { if (a < 0x8000) return 0xFF; off = (size_t(b & 0x7F) << 15) | (a & 0x7FFF); }
    return off < rom.size() ? rom[off] : rom[off % rom.size()];
  }
  void write(uint8_t b, uint16_t a, uint8_t v) override { bool ok; size_t si = sram_index(b, a, ok); if (ok && si < sram.size()) sram[si] = v; }
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
  bool ram_enabled() const { return has_ram && (m == 1 ? !(mm1[3] & 0x10) : (m == 4 ? mmc3_ram_en : false)); }
  SimMapper(int mp, uint32_t p, uint32_t c) : m(mp) {
    prgrom.resize(p); chrrom.resize(c);
    for (size_t i = 0; i < p; i++) prgrom[i] = pat(uint32_t(i) + 11 * mp);
    for (size_t i = 0; i < c; i++) chrrom[i] = pat(uint32_t(i) + 77 * mp);
  }
  void begin() override {} void end() override {}
  size_t n16() const { return prgrom.size() / 16384; }
  uint8_t prg(uint16_t a) override {
    if (a >= 0x6000 && a < 0x8000) return ram_enabled() ? ram[a - 0x6000] : 0xFF;
    if (a < 0x8000) return 0xFF;
    size_t N = prgrom.size();
    switch (m) {
      case 0: case 3: return prgrom[(a - 0x8000) % N];
      case 2: return a < 0xC000 ? prgrom[(size_t(reg) % n16()) * 16384 + (a & 0x3FFF)] : prgrom[N - 16384 + (a & 0x3FFF)];
      case 7: return prgrom[(size_t(reg) * 32768 + (a & 0x7FFF)) % N];
      case 1: { int mode = (mm1[0] >> 2) & 3;
        if (mode >= 2) return a < 0xC000 ? prgrom[(size_t(mm1[3] & 0x0F) % n16()) * 16384 + (a & 0x3FFF)] : prgrom[N - 16384 + (a & 0x3FFF)];
        return prgrom[(size_t(mm1[3] & 0x0E) * 16384 + (a & 0x7FFF)) % N]; }
      case 4: { size_t n8 = N / 8192, bank;
        if (a < 0xA000) bank = r[6]; else if (a < 0xC000) bank = r[7]; else if (a < 0xE000) bank = n8 - 2; else bank = n8 - 1;
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
      case 4: { size_t b;
        if (a < 0x0800) b = (r[0] & ~1) + (a >> 10); else if (a < 0x1000) b = (r[1] & ~1) + ((a - 0x800) >> 10);
        else b = r[2 + ((a - 0x1000) >> 10)];
        return chrrom[((b * 1024) + (a & 0x3FF)) % C]; }
    }
    return 0xFF;
  }
  void prg_write(uint16_t a, uint8_t v) override {
    if (a >= 0x6000 && a < 0x8000) { if (ram_enabled()) ram[a - 0x6000] = v; return; }
    if (a < 0x8000) return;
    switch (m) {
      case 2: case 3: case 7: reg = v & prg(a); break;                       // conflito: valor E byte da ROM
      case 1:
        if (v & 0x80) { cnt = 0; sh = 0; mm1[0] |= 0x0C; break; }
        sh |= (v & 1) << cnt;
        if (++cnt == 5) { mm1[(a >> 13) & 3] = sh; cnt = 0; sh = 0; }
        break;
      case 4:
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
};

// ---------------------------------------------------------------- GBA simulado
struct SimGba : GbaBus {
  std::vector<uint8_t> rom; bool absent = false;
  explicit SimGba(uint32_t size) { rom.resize(size); for (size_t i = 0; i < size; i++) rom[i] = pat(uint32_t(i) + 3);
    const uint8_t logo[4] = {0x24, 0xFF, 0xAE, 0x51}; memcpy(&rom[4], logo, 4); memset(&rom[0xA0], ' ', 12); memcpy(&rom[0xA0], "GBA TESTE", 9); }
  void begin() override {} void end() override {}
  uint16_t word(uint32_t ba) override { if (absent) return 0xFFFF; uint32_t i = (ba & ~1UL) % rom.size(); return uint16_t(rom[i + 1] << 8) | rom[i]; }
  std::vector<uint8_t> sram = std::vector<uint8_t>(32768, 0);
  uint8_t sram_read(uint16_t a) override { return flash ? flash_data[(size_t(bank) << 16 | a) % flash_data.size()] : sram[a & 0x7FFF]; }
  void sram_write(uint16_t a, uint8_t v) override {
    // Flash de 128 KB: comando de troca de banco (AA, 55, B0 e o número do banco em $0000)
    if (flash) {
      if (st == 3 && a == 0) { bank = v & 1; st = 0; return; }
      if (st == 0 && a == 0x5555 && v == 0xAA) { st = 1; return; }
      if (st == 1 && a == 0x2AAA && v == 0x55) { st = 2; return; }
      if (st == 2 && a == 0x5555 && v == 0xB0) { st = 3; return; }
      st = 0; return;
    }
    sram[a & 0x7FFF] = v;
  }
  bool flash = false; int st = 0, bank = 0; int eep_reads = 0;
  std::vector<uint8_t> flash_data;     // Flash: 64 ou 128 KB
  std::vector<uint8_t> eep;
  void eeprom_block(uint16_t block, bool big, uint8_t out[8]) override {
    eep_reads++; size_t n = big ? 8192 : 512;
    for (int i = 0; i < 8; i++) out[i] = eep[(size_t(block) * 8 + i) % n];
  }
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
  DetectInfo d; be.detect(SYS_SNES, d); CHECK(d.status == 1);              // checksum não confere = sem cartucho
  std::vector<uint8_t> o; uint16_t err; dump(be, SYS_SNES, KIND_ROM, o, err); CHECK(err == E_SEM_CARTUCHO);
  SimSnes nosave(false, 9, 0); CartBackend b2(&nosave, nullptr, nullptr, nullptr);
  dump(b2, SYS_SNES, KIND_SAVE, o, err); CHECK(err == E_SEM_SAVE);
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
                      {4, 128 << 10, 128 << 10}, {4, 256 << 10, 256 << 10}, {7, 128 << 10, 0}, {0, 32 << 10, 8 << 10}};
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
    CHECK(out[0] == 'N' && out[4] == c.prg / 16384 && out[5] == c.chr / 8192 && out[6] == uint8_t((c.m & 0x0F) << 4));
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
  be.set_options(2, 128, 8);   CHECK(!be.open_read(SYS_NES, KIND_ROM, size, err) && err == E_ARGUMENTO);
}

static void test_nes_saves() {
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
  // DETECT ignora as opções; close_read as apaga
  be.set_options(0, 512, 0); be.detect(SYS_MD, d); CHECK(d.rom_size == 0x100000);
  CHECK(be.open_read(SYS_MD, KIND_ROM, size, err) && size == 0x80000); be.close_read();
  CHECK(be.open_read(SYS_MD, KIND_ROM, size, err) && size == 0x100000); be.close_read();
  // ROM real de 2 MB com cabeçalho correto não é reduzida
  SimMd real(0x200000); CartBackend b2(nullptr, nullptr, &real, nullptr); b2.detect(SYS_MD, d); CHECK(d.rom_size == 0x200000);
  // ROM de 1 MB sem espelho (metades diferentes) com cabeçalho de 1 MB também fica
  SimMd one(0x100000); CartBackend b3(nullptr, nullptr, &one, nullptr); b3.detect(SYS_MD, d); CHECK(d.rom_size == 0x100000);
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
  be.set_options(4, 0, 0); CHECK(!be.write_begin(SYS_GBA, 65536, err) && err == E_SEM_SAVE);  // gravação ainda não existe
}

static void test_gba() {
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
    uint16_t e2 = 0; CHECK(!be.write_begin(SYS_GBA, 32768, e2) && e2 == E_SEM_SAVE);   // gravação do GBA não suportada
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
  test_snes(); test_nes(); test_nes_mappers(); test_nes_saves(); test_md(); test_md_sram_ssf(); test_md_tamanho(); test_gba(); test_sistemas_sem_barramento();
  printf("%d verificações de cartuchos, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
