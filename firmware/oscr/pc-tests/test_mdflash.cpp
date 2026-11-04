// SPDX-License-Identifier: GPL-3.0-or-later
// Testa o MdFlashCore.h REAL (o mesmo código que vai para o Mega) contra o modelo de chip de md_chip_model.h: sondagem dos conjuntos de comandos,
// apagar por layout (bottom, top, uniforme, Intel), programar, e as falhas que o OSCR original não tratava (chip travado, 0 -> 1, ROM de máscara).
// O modelo vem dos datasheets; ele não prova que o chip real se comporta assim.
#include <stdio.h>
#include <stdlib.h>
#include <vector>
#include "../include/dumper/MdFlashCore.h"
#include "md_chip_model.h"

namespace C = OSCR::Dumper::MdFlashCore;
using namespace mdmodel;

static int checks = 0, failures = 0;
#define CHECK(cond) do { checks++; if (!(cond)) { failures++; printf("FALHOU %s:%d: %s\n", __FILE__, __LINE__, #cond); } } while (0)
#define CHECKM(cond, msg) do { checks++; if (!(cond)) { failures++; printf("FALHOU %s:%d: %s (%s)\n", __FILE__, __LINE__, #cond, msg); } } while (0)

// ROM de teste: palavras pseudo-aleatórias, com cerca de 1 em 8 igual a FFFF (preenchimento) e a primeira diferente de FFFF.
static std::vector<uint8_t> makeRom(size_t bytes, uint32_t seed)
{
  std::vector<uint8_t> r(bytes);
  uint32_t x = seed * 2654435761u + 1;
  for (size_t i = 0; i + 1 < bytes; i += 2)
  {
    x = x * 1664525u + 1013904223u;
    uint16_t w = uint16_t(x >> 8);
    if (((x >> 3) & 7) == 0) w = 0xFFFF;
    if (i == 0 && w == 0xFFFF) w = 0x1234;
    r[i] = uint8_t(w >> 8); r[i + 1] = uint8_t(w);
  }
  return r;
}

static void dirty(Chip & c, uint16_t pattern = 0x0000) { for (auto & w : c.mem) w = pattern; }

static bool matches(Chip const & c, std::vector<uint8_t> const & rom)
{
  for (size_t i = 0; i + 1 < rom.size(); i += 2)
    if (c.mem[i / 2] != uint16_t((rom[i] << 8) | rom[i + 1])) { printf("  diferente na palavra %zu: chip %04X, rom %02X%02X\n", i / 2, c.mem[i / 2], rom[i], rom[i + 1]); return false; }
  return true;
}

struct Outcome { C::Result prep, prog; bool known; C::Probe p; };

// Sondar, apagar e gravar, como o MdFlash::prepare e program. O chip começa "sujo" (todos os bits em 0): sem apagar, nada grava.
static Outcome flashRom(Chip & chip, std::vector<uint8_t> const & rom)
{
  Bus bus(chip);
  Outcome o;
  C::probe(bus, o.p);
  o.known = o.p.known;
  o.prep = C::prepare(bus, o.p, uint32_t(rom.size()));
  o.prog = C::kOk;
  if (o.prep == C::kOk)
  {
    Source src(rom);
    o.prog = C::program(bus, o.p, uint32_t(rom.size()), src);
  }
  return o;
}

static void testProbe()
{
  struct { Cfg const * cfg; char const * name; C::CmdSet cmd; C::Impl impl; } rows[] = {
    { &MX29LV640EB, "MX29LV640EB", C::kAmd555, C::kNative },
    { &MX29LV640ET, "MX29LV640ET", C::kAmd555, C::kNative },
    { &M29W640DT, "M29W640DT", C::kAmd555, C::kNative },
    { &M29W640DB, "M29W640DB", C::kAmd555, C::kNative },
    { &SST39VF6401B, "SST39VF6401B", C::kAmd555, C::kNative },
    { &SST39VF3201, "SST39VF3201", C::kAmd555, C::kNative },
    { &M29W320ET, "M29W320ET", C::kAmd555, C::kNative },
    { &M29W320EB, "M29W320EB", C::kAmd555, C::kNative },
    { &MX29LV320T, "MX29LV320T", C::kAmd555, C::kNative },
    { &MX29L3211, "MX29L3211", C::kAmd5555, C::kNative },
    { &MX29F1610, "MX29F1610", C::kAmd5555, C::kOscrF1610 },
    { &S29GL064N, "S29GL064N", C::kAmd555, C::kOscrGl },
    { &PA28F400B, "PA28F400B", C::kIntel, C::kNative },
    { &PA28F400T, "PA28F400T", C::kIntel, C::kNative },
    { &M29W320EB_EXACT, "M29W320EB", C::kAmd555, C::kNative },
  };
  for (auto & r : rows)
  {
    Chip chip(*r.cfg);
    Bus bus(chip);
    C::Probe p;
    C::probe(bus, p);
    CHECKM(p.known, r.cfg->name);
    CHECKM(strcmp(p.chip.name, r.name) == 0, r.cfg->name);
    CHECKM(p.chip.cmd == r.cmd, r.cfg->name);
    CHECKM(p.chip.impl == r.impl, r.cfg->name);
    CHECKM(p.chip.words == r.cfg->words, r.cfg->name);
    CHECKM(chip.errors == 0, chip.firstError.c_str());
    CHECKM(r.cmd != C::kAmd5555 || (p.u1 == 0x5555 && p.u2 == 0x2AAA), r.cfg->name);
    CHECKM(r.cmd == C::kAmd5555 || p.u1 == 0x555, r.cfg->name);
  }

  // ID fora da tabela: não é conhecido; o ID lido fica em p.id. Nada foi apagado nem gravado.
  {
    Chip chip(UNKNOWN_CHIP);
    Bus bus(chip);
    C::Probe p;
    C::probe(bus, p);
    CHECK(!p.known);
    CHECK(p.id[0] == 0xAB && p.id[1] == 0xCD);
    CHECK(chip.programs == 0 && chip.sectorErases == 0 && chip.blockErases == 0);
    CHECK(C::prepare(bus, p, 1024) == C::kNoChip);
  }

  // ROM de máscara: as escritas de sondagem são ignoradas e o conteúdo da ROM não é um ID da tabela.
  {
    Chip chip(M29W320EB);
    for (size_t i = 0; i < chip.mem.size(); i++) chip.mem[i] = uint16_t(0x4E71 + i);   // código qualquer
    chip.romOnly = true;
    auto before = chip.mem;
    Bus bus(chip);
    C::Probe p;
    C::probe(bus, p);
    CHECK(!p.known);
    CHECK(chip.mem == before);
    CHECK(C::prepare(bus, p, 4096) == C::kNoChip);
    CHECK(chip.mem == before);
  }

  // Os chips do OSCR são identificados, mas o núcleo se recusa a gravá-los (quem grava é o OSCR).
  {
    Chip chip(MX29F1610);
    dirty(chip, 0x5A5A);
    Bus bus(chip);
    C::Probe p;
    C::probe(bus, p);
    CHECK(p.known && p.chip.impl == C::kOscrF1610);
    CHECK(C::prepare(bus, p, 1024) == C::kNoChip);
    CHECK(chip.mem[0] == 0x5A5A && chip.sectorErases == 0);
  }
}

static void testRoundTrip(Cfg const & cfg, size_t bytes, char const * what)
{
  Chip chip(cfg);
  dirty(chip);
  auto rom = makeRom(bytes, uint32_t(bytes) + cfg.id[1]);
  Outcome o = flashRom(chip, rom);
  char msg[160];
  snprintf(msg, sizeof(msg), "%s, %zu bytes (%s)", cfg.name, bytes, what);
  CHECKM(o.known, msg);
  CHECKM(o.prep == C::kOk, msg);
  CHECKM(o.prog == C::kOk, msg);
  CHECKM(chip.errors == 0, chip.firstError.c_str());
  CHECKM(matches(chip, rom), msg);
  CHECKM(chip.programWhileBusy == 0, msg);
}

static void testRoundTrips()
{
  Cfg const * all[] = { &MX29LV640EB, &MX29LV640ET, &M29W640DT, &M29W640DB, &SST39VF6401B, &SST39VF3201, &M29W320ET, &M29W320EB, &MX29LV320T, &MX29L3211, &PA28F400B, &PA28F400T };
  for (Cfg const * c : all)
  {
    size_t full = size_t(c->words) * 2;
    testRoundTrip(*c, 4096, "so o primeiro setor pequeno");
    testRoundTrip(*c, 100000, "tamanho que nao fecha setor");
    testRoundTrip(*c, 524288, "512 KB");
    if (full >= 1048576) testRoundTrip(*c, 1048576, "1 MB");
    testRoundTrip(*c, full, "chip inteiro");
  }
}

static void testLayouts()
{
  // Chip top boot de 32 Mbit com ROM de 4 MB: alcança os oito setores de 8 KB do fim; um 30h só apaga um deles.
  {
    Chip chip(M29W320ET);
    dirty(chip);
    auto rom = makeRom(4 * 1024 * 1024, 7);
    Outcome o = flashRom(chip, rom);
    CHECK(o.prep == C::kOk && o.prog == C::kOk);
    CHECK(matches(chip, rom));
    // 63 setores grandes + 8 pequenos
    CHECK(chip.sectorErases == 63 + 8);
  }
  // Bottom boot: oito setores de 8 KB no começo.
  {
    Chip chip(M29W320EB);
    dirty(chip);
    auto rom = makeRom(256 * 1024, 8);
    Outcome o = flashRom(chip, rom);
    CHECK(o.prep == C::kOk && o.prog == C::kOk);
    CHECK(chip.sectorErases == 8 + 3);         // 64 KB no começo em 8 KB + 3 de 64 KB (0x8000 palavras)
  }
  // Uniforme (SST39VF6401B, 30h = bloco de 32 KWord): um 30h por 64 KB, sem apagar o primeiro mais de uma vez.
  {
    Chip chip(SST39VF6401B);
    dirty(chip);
    auto rom = makeRom(256 * 1024, 9);
    Outcome o = flashRom(chip, rom);
    CHECK(o.prep == C::kOk && o.prog == C::kOk);
    CHECK(chip.sectorErases == 4);
  }
  // SST39VF3201: 30h apagaria só 2 KWord; o núcleo usa 50h (bloco).
  {
    Chip chip(SST39VF3201);
    dirty(chip);
    auto rom = makeRom(256 * 1024, 10);
    Outcome o = flashRom(chip, rom);
    CHECK(o.prep == C::kOk && o.prog == C::kOk);
    CHECK(chip.blockErases == 4 && chip.sectorErases == 0);
    CHECK(matches(chip, rom));
  }
  // Intel: apaga bloco a bloco pelo mapa. Bottom: 16K, 8K, 8K, 96K, 128K... (em palavras 2000h, 1000h, 1000h, C000h).
  {
    Chip chip(PA28F400B);
    dirty(chip);
    auto rom = makeRom(140 * 1024, 11);        // 140 KB = 71680 palavras = 0x11800: cobre os 4 primeiros blocos (até 0x10000) e começa o quinto
    Outcome o = flashRom(chip, rom);
    CHECK(o.prep == C::kOk && o.prog == C::kOk);
    CHECK(chip.blockErases == 5);
    CHECK(matches(chip, rom));
  }
  {
    Chip chip(PA28F400T);
    dirty(chip);
    auto rom = makeRom(512 * 1024, 12);
    Outcome o = flashRom(chip, rom);
    CHECK(o.prep == C::kOk && o.prog == C::kOk);
    CHECK(chip.blockErases == 7);
    CHECK(matches(chip, rom));
  }
}

static void testFfSkipped()
{
  Chip chip(M29W320EB);
  dirty(chip);
  auto rom = makeRom(64 * 1024, 5);
  size_t ff = 0;
  for (size_t i = 0; i < rom.size(); i += 2) if (rom[i] == 0xFF && rom[i + 1] == 0xFF) ff++;
  Outcome o = flashRom(chip, rom);
  CHECK(o.prog == C::kOk);
  CHECK(ff > 0);
  CHECK(chip.programs == int(rom.size() / 2 - ff));
}

static void testFailures()
{
  // Chip travado: apagar nunca termina. Tem que devolver erro, com o tempo limitado.
  {
    Chip chip(M29W320EB);
    dirty(chip);
    chip.stuck = true;
    Bus bus(chip);
    C::Probe p;
    C::probe(bus, p);
    uint64_t t0 = chip.nowNs;
    auto r = C::prepare(bus, p, 65536);
    CHECK(r == C::kEraseFail);
    CHECK((chip.nowNs - t0) / 1000000ULL < C::kEraseTimeoutMs + 1000);
  }
  // Chip travado ao programar: erro dentro de kPollMax leituras por palavra.
  {
    Chip chip(M29W320EB);
    Bus bus(chip);
    C::Probe p;
    C::probe(bus, p);
    CHECK(C::prepare(bus, p, 65536) == C::kOk);
    chip.stuck = true;
    auto rom = makeRom(65536, 3);
    Source src(rom);
    uint64_t t0 = chip.nowNs;
    CHECK(C::program(bus, p, uint32_t(rom.size()), src) == C::kProgramFail);
    CHECK((chip.nowNs - t0) < 100000000ULL);      // menos de 100 ms
  }
  // Gravar sem apagar: 0 -> 1 não programa; o chip desiste (DQ5) e o núcleo para na primeira palavra.
  {
    Chip chip(M29W320EB);
    dirty(chip);
    Bus bus(chip);
    C::Probe p;
    C::probe(bus, p);
    auto rom = makeRom(4096, 4);
    Source src(rom);
    CHECK(C::program(bus, p, uint32_t(rom.size()), src) == C::kProgramFail);
    CHECK(chip.programs == 1);
    // o chip voltou ao modo leitura (reset): lê a matriz
    CHECK(chip.read(0) == 0x0000);
  }
  // Intel: gravar sem apagar também falha (status bit 4).
  {
    Chip chip(PA28F400B);
    dirty(chip);
    Bus bus(chip);
    C::Probe p;
    C::probe(bus, p);
    auto rom = makeRom(4096, 4);
    Source src(rom);
    CHECK(C::program(bus, p, uint32_t(rom.size()), src) == C::kProgramFail);
  }
  // Intel travado.
  {
    Chip chip(PA28F400B);
    chip.stuck = true;
    Bus bus(chip);
    C::Probe p;
    C::probe(bus, p);
    uint64_t t0 = chip.nowNs;
    CHECK(C::prepare(bus, p, 65536) == C::kEraseFail);
    CHECK((chip.nowNs - t0) / 1000000ULL < C::kEraseTimeoutMs + 1000);
  }
  // ROM maior que o chip.
  {
    Chip chip(M29W320EB);
    dirty(chip, 0x1111);
    Bus bus(chip);
    C::Probe p;
    C::probe(bus, p);
    CHECK(C::prepare(bus, p, 4 * 1024 * 1024 + 2) == C::kTooBig);
    CHECK(chip.mem[0] == 0x1111);                  // nada foi apagado
  }
  // Arquivo que acaba antes do tamanho anunciado.
  {
    Chip chip(M29W320EB);
    Bus bus(chip);
    C::Probe p;
    C::probe(bus, p);
    CHECK(C::prepare(bus, p, 8192) == C::kOk);
    auto rom = makeRom(4096, 6);
    Source src(rom);
    CHECK(C::program(bus, p, 8192, src) == C::kShortFile);
  }
}

static void testIdentifyTable()
{
  // Nenhum ID repetido na tabela; nomes cabem; tamanhos são potências de dois; os chips Intel têm 0x40000 palavras.
  for (size_t i = 0; i < C::kChipCount; i++)
  {
    C::Chip a;
    MDF_LOAD(a, C::kChips[i]);
    CHECK(strlen(a.name) < sizeof(a.name));
    CHECK(a.words && (a.words & (a.words - 1)) == 0);
    for (size_t j = i + 1; j < C::kChipCount; j++)
    {
      C::Chip b;
      MDF_LOAD(b, C::kChips[j]);
      CHECK(!(a.mfr == b.mfr && a.dev == b.dev));
    }
  }
  // S29GL: ciclo 2 decide o tamanho; o OSCR tratava qualquer 017E como 4 MB.
  uint8_t gl064[4] = { 0x01, 0x7E, 0x10, 0x01 };
  uint8_t glOther[4] = { 0x01, 0x7E, 0x1A, 0x00 };
  C::Chip c;
  CHECK(C::identify(gl064, c) && c.words == C::kW64 && strcmp(c.name, "S29GL064N") == 0 && c.layout == C::kUniform);
  CHECK(C::identify(glOther, c) && c.words == C::kW32 && c.impl == C::kOscrGl);
  uint8_t none[4] = { 0xFF, 0xFF, 0xFF, 0xFF };
  CHECK(!C::identify(none, c));
}

int main()
{
  testIdentifyTable();
  testProbe();
  testRoundTrips();
  testLayouts();
  testFfSkipped();
  testFailures();
  printf("%d verificacoes, %d falhas\n", checks, failures);
  return failures ? 1 : 0;
}
