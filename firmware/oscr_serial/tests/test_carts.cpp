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
};

// ---------------------------------------------------------------- Mega Drive simulado
struct SimMd : MdBus {
  std::vector<uint8_t> rom; bool absent = false;
  explicit SimMd(uint32_t size) { rom.resize(size); for (size_t i = 0; i < size; i++) rom[i] = pat(uint32_t(i) + 7);
    memcpy(&rom[0x100], "SEGA MEGA DRIVE ", 16); memset(&rom[0x150], ' ', 48); memcpy(&rom[0x150], "JOGO DE TESTE", 13);
    uint32_t end = size - 1; rom[0x1A4] = end >> 24; rom[0x1A5] = end >> 16; rom[0x1A6] = end >> 8; rom[0x1A7] = end; }
  void begin() override {} void end() override {}
  uint16_t word(uint32_t wa) override { if (absent) return 0xFFFF; uint32_t b = (wa * 2) % rom.size(); return uint16_t(rom[b] << 8) | rom[b + 1]; }
};

// ---------------------------------------------------------------- GBA simulado
struct SimGba : GbaBus {
  std::vector<uint8_t> rom; bool absent = false;
  explicit SimGba(uint32_t size) { rom.resize(size); for (size_t i = 0; i < size; i++) rom[i] = pat(uint32_t(i) + 3);
    const uint8_t logo[4] = {0x24, 0xFF, 0xAE, 0x51}; memcpy(&rom[4], logo, 4); memset(&rom[0xA0], ' ', 12); memcpy(&rom[0xA0], "GBA TESTE", 9); }
  void begin() override {} void end() override {}
  uint16_t word(uint32_t ba) override { if (absent) return 0xFFFF; uint32_t i = (ba & ~1UL) % rom.size(); return uint16_t(rom[i + 1] << 8) | rom[i]; }
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

static void test_md() {
  SimMd s(0x100000); CartBackend be(nullptr, nullptr, &s, nullptr);
  DetectInfo d; be.detect(SYS_MD, d);
  CHECK(d.status == 0 && d.rom_size == 0x100000 && strcmp(d.name, "JOGO DE TESTE") == 0);
  std::vector<uint8_t> out; uint16_t err; dump(be, SYS_MD, KIND_ROM, out, err);
  CHECK(out.size() == s.rom.size() && memcmp(out.data(), s.rom.data(), out.size()) == 0);
  s.absent = true; be.detect(SYS_MD, d); CHECK(d.status == 1);
}

static void test_gba() {
  for (uint32_t mb : {1u, 4u, 16u}) {
    SimGba s(mb << 20); CartBackend be(nullptr, nullptr, nullptr, &s);
    DetectInfo d; be.detect(SYS_GBA, d);
    CHECK(d.status == 0 && d.rom_size == (mb << 20) && strcmp(d.name, "GBA TESTE") == 0);
    std::vector<uint8_t> out; uint16_t err; dump(be, SYS_GBA, KIND_ROM, out, err);
    CHECK(out.size() == s.rom.size() && memcmp(out.data(), s.rom.data(), out.size()) == 0);
  }
  SimGba s(1 << 20); s.absent = true; CartBackend be(nullptr, nullptr, nullptr, &s); DetectInfo d; be.detect(SYS_GBA, d); CHECK(d.status == 1);
}

static void test_sistemas_sem_barramento() {
  SimNes n(16384, 8192); CartBackend be(nullptr, &n, nullptr, nullptr);
  CHECK(be.systems() == ((1 << SYS_NES) | (1 << SYS_FAMICOM)) && !be.supports(SYS_SNES) && !be.supports(SYS_MOCK));
  uint32_t size; uint16_t err; CHECK(!be.open_read(SYS_SNES, KIND_ROM, size, err) && err == E_SISTEMA);
}

int main() {
  test_snes(); test_nes(); test_md(); test_gba(); test_sistemas_sem_barramento();
  printf("%d verificações de cartuchos, %d falhas\n", g_n, g_fail);
  return g_fail ? 1 : 0;
}
