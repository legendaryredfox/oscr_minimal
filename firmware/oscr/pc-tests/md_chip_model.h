// SPDX-License-Identifier: GPL-3.0-or-later
// Modelo de chip de flash de 16 bits e do barramento do cartucho de Mega Drive, para rodar o MdFlashCore.h real no PC.
// Escrito a partir dos datasheets (AMD/JEDEC, Intel/Sharp 28F400, SST39VF); não é medição de um chip real. Origem: tests/host/host_hw.c
// do md_rewriter (firmware 1.1), reescrito sem as portas GPIO do STM32.
//
// O que modela: ciclos de comando com decodificação de 11 bits, de 15 bits (5555h) ou exata (555h) dos endereços de desbloqueio; autoselect;
// programar palavra com DQ7/DQ6/DQ5; apagar setor (30h) e bloco (50h) conforme o layout (bottom, top, uniforme); Intel com registrador de status;
// ROM de máscara (escritas ignoradas); chip travado (nunca termina). Tempo: cada ciclo de leitura e escrita avança o relógio.
#pragma once
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <vector>
#include <string>

namespace mdmodel
{
  enum Layout { BOTTOM, TOP, UNIFORM };
  enum Family { AMD11, AMD15, AMD_EXACT, INTEL };

  struct Cfg
  {
    char const * name;
    uint16_t id[4];             // palavras lidas em 00h, 01h, 0Eh, 0Fh no autoselect
    Layout layout;
    Family family;
    uint32_t words;             // tamanho do chip em palavras
    uint32_t erase30Words;      // 0 = o setor do layout; senão o tamanho que o 30h apaga (SST39VF320x: 2 KWord)
    uint64_t programNs;
    uint64_t sectorEraseNs;
  };

  // Chips usados nos testes. Os mesmos da tabela do núcleo, com o layout e o comportamento de apagar que o datasheet descreve.
  static const Cfg MX29LV640EB  = { "MX29LV640EB", { 0x00C2, 0x22CB, 0, 0 }, BOTTOM, AMD11, 0x400000, 0, 9000, 100000000ULL };
  static const Cfg MX29LV640ET  = { "MX29LV640ET", { 0x00C2, 0x22C9, 0, 0 }, TOP, AMD11, 0x400000, 0, 9000, 100000000ULL };
  static const Cfg M29W640DT    = { "M29W640DT",   { 0x0020, 0x22DE, 0, 0 }, TOP, AMD11, 0x400000, 0, 10000, 100000000ULL };
  static const Cfg M29W640DB    = { "M29W640DB",   { 0x0020, 0x22DF, 0, 0 }, BOTTOM, AMD11, 0x400000, 0, 10000, 100000000ULL };
  static const Cfg SST39VF6401B = { "SST39VF6401B", { 0x00BF, 0x236D, 0, 0 }, UNIFORM, AMD11, 0x400000, 0, 10000, 18000000ULL };
  static const Cfg SST39VF3201  = { "SST39VF3201", { 0x00BF, 0x235B, 0, 0 }, UNIFORM, AMD11, 0x200000, 0x800, 10000, 18000000ULL };
  static const Cfg M29W320ET    = { "M29W320ET",   { 0x0020, 0x2256, 0, 0 }, TOP, AMD11, 0x200000, 0, 10000, 100000000ULL };
  static const Cfg M29W320EB    = { "M29W320EB",   { 0x0020, 0x2257, 0, 0 }, BOTTOM, AMD11, 0x200000, 0, 10000, 100000000ULL };
  static const Cfg MX29LV320T   = { "MX29LV320T",  { 0x00C2, 0x22A7, 0, 0 }, TOP, AMD11, 0x200000, 0, 10000, 100000000ULL };
  static const Cfg MX29L3211    = { "MX29L3211",   { 0x00C2, 0x00F9, 0, 0 }, UNIFORM, AMD15, 0x200000, 0, 11000, 70000000ULL };
  static const Cfg MX29F1610    = { "MX29F1610",   { 0x00C2, 0x00F1, 0, 0 }, UNIFORM, AMD15, 0x100000, 0, 11000, 70000000ULL };
  static const Cfg S29GL064N    = { "S29GL064N",   { 0x0001, 0x227E, 0x220C, 0x2201 }, TOP, AMD11, 0x400000, 0, 15000, 100000000ULL };
  static const Cfg PA28F400B    = { "PA28F400B",   { 0x0089, 0x4471, 0, 0 }, BOTTOM, INTEL, 0x40000, 0, 8000, 100000000ULL };
  static const Cfg PA28F400T    = { "PA28F400T",   { 0x0089, 0x4470, 0, 0 }, TOP, INTEL, 0x40000, 0, 8000, 100000000ULL };
  // Um chip AMD que só reconhece 555h/2AAh exatos (sem ignorar os bits altos): a sondagem 5555h não o enxerga, a 555h sim.
  static const Cfg M29W320EB_EXACT = { "M29W320EB(exact)", { 0x0020, 0x2257, 0, 0 }, BOTTOM, AMD_EXACT, 0x200000, 0, 10000, 100000000ULL };
  // Um ID que não está na tabela.
  static const Cfg UNKNOWN_CHIP = { "unknown", { 0x00AB, 0x22CD, 0, 0 }, UNIFORM, AMD11, 0x200000, 0, 10000, 100000000ULL };

  class Chip
  {
  public:
    explicit Chip(Cfg const & c) : cfg(c), mem(c.words, 0xFFFF) {}

    Cfg cfg;
    std::vector<uint16_t> mem;
    bool romOnly = false;       // ROM de máscara: leituras devolvem o conteúdo, escritas são ignoradas
    bool cfi = false;           // o chip responde à consulta CFI (98h no endereço 55h): "QRY" em 10h a 12h e o tamanho em 27h
    bool stuck = false;         // chip travado: apagar e programar nunca terminam
    uint32_t keepStart = 0, keepLen = 0;   // apagamento "termina sem erro" mas não limpa estas palavras (setores de boot de 8 KB; bancada do md_rewriter)
    uint64_t nowNs = 0;

    // contadores
    int errors = 0;             // contenção de barramento, escrita com o barramento como entrada
    std::string firstError;
    int sectorErases = 0, blockErases = 0, programs = 0, writeCycles = 0;
    int programWhileBusy = 0;
    uint64_t maxWriteGap = 0;

    void fail(char const * what)
    {
      if (errors == 0) firstError = what;
      errors++;
    }

    void write(uint32_t addr, uint16_t data)
    {
      writeCycles++;
      addr = (addr & 0xFFFFFF) % cfg.words;           // endereço acima do chip: espelha
      if (romOnly) return;
      if (cfg.family == INTEL) { intelWrite(addr, data); return; }
      amdWrite(addr, data);
    }

    uint16_t read(uint32_t addr)
    {
      addr &= 0xFFFFFF;
      addr %= cfg.words;
      if (romOnly) return mem[addr];
      return cfg.family == INTEL ? intelRead(addr) : amdRead(addr);
    }

  private:
    enum State { S_READ, S_C1, S_C2, S_AUTO, S_PROG_DATA, S_E1, S_E2, S_E3, S_PROG_BUSY, S_ERASE_BUSY, S_FAIL, S_CFI };
    State state = S_READ;
    uint64_t busyUntil = 0;
    uint32_t progAddr = 0;
    uint16_t progData = 0;
    uint16_t toggle = 0;

    bool isU1(uint32_t a) const
    {
      if (cfg.family == AMD15) return (a & 0x7FFF) == 0x5555;
      if (cfg.family == AMD_EXACT) return a == 0x555;
      return (a & 0x7FF) == 0x555;
    }
    bool isU2(uint32_t a) const
    {
      if (cfg.family == AMD15) return (a & 0x7FFF) == 0x2AAA;
      if (cfg.family == AMD_EXACT) return a == 0x2AA;
      return (a & 0x7FF) == 0x2AA;
    }

    // Setor de 30h: boot de 8 KB no começo (bottom) ou no fim (top); fora disso 32 KWord. SST39VF320x: 30h = 2 KWord.
    void sectorOf(uint32_t a, uint32_t & start, uint32_t & size) const
    {
      if (cfg.erase30Words) { size = cfg.erase30Words; start = a & ~(size - 1); return; }
      bool small = (cfg.layout == BOTTOM && a < 0x8000) || (cfg.layout == TOP && a >= cfg.words - 0x8000);
      size = small ? 0x1000 : 0x8000;
      start = a & ~(size - 1);
    }

    void eraseWords(uint32_t start, uint32_t n) { for (uint32_t i = 0; i < n; i++) if (!(keepLen && start + i >= keepStart && start + i < keepStart + keepLen)) mem[start + i] = 0xFFFF; }

    void amdWrite(uint32_t addr, uint16_t data)
    {
      uint8_t cmd = uint8_t(data & 0xFF);
      if (state == S_PROG_BUSY || state == S_ERASE_BUSY)
      {
        if (nowNs < busyUntil) { programWhileBusy++; return; }
        state = S_READ;
      }
      if (state == S_FAIL) { if (cmd == 0xF0) state = S_READ; return; }
      if (cmd == 0xF0 && state != S_PROG_DATA) { state = S_READ; return; }
      if (cmd == 0x98 && cfi && addr == 0x55 && (state == S_READ || state == S_AUTO)) { state = S_CFI; return; }
      switch (state)
      {
      case S_READ:
      case S_AUTO:
        if (isU1(addr) && cmd == 0xAA) state = S_C1;
        break;
      case S_CFI:
        break;                                              // só o reset (F0) sai do modo CFI
      case S_C1:
        state = (isU2(addr) && cmd == 0x55) ? S_C2 : S_READ;
        break;
      case S_C2:
        if (isU1(addr) && cmd == 0x90) state = S_AUTO;
        else if (isU1(addr) && cmd == 0xA0) state = S_PROG_DATA;
        else if (isU1(addr) && cmd == 0x80) state = S_E1;
        else state = S_READ;
        break;
      case S_PROG_DATA:
        {
          uint16_t old = mem[addr];
          programs++;
          progAddr = addr; progData = data;
          if (data & uint16_t(~old)) state = S_FAIL;          // 0 -> 1 não programa: o chip desiste (DQ5)
          else
          {
            mem[addr] = uint16_t(old & data);
            busyUntil = stuck ? ~0ULL : nowNs + cfg.programNs;
            state = S_PROG_BUSY;
          }
        }
        break;
      case S_E1:
        state = (isU1(addr) && cmd == 0xAA) ? S_E2 : S_READ;
        break;
      case S_E2:
        state = (isU2(addr) && cmd == 0x55) ? S_E3 : S_READ;
        break;
      case S_E3:
        if (cmd == 0x30)
        {
          uint32_t st, sz;
          sectorOf(addr, st, sz);
          eraseWords(st, sz);
          sectorErases++;
          busyUntil = stuck ? ~0ULL : nowNs + cfg.sectorEraseNs;
          state = S_ERASE_BUSY;
        }
        else if (cmd == 0x50 && cfg.layout == UNIFORM)       // bloco de 32 KWord (SST)
        {
          eraseWords(addr & ~0x7FFFU, 0x8000);
          blockErases++;
          busyUntil = stuck ? ~0ULL : nowNs + cfg.sectorEraseNs;
          state = S_ERASE_BUSY;
        }
        else state = S_READ;
        break;
      default:
        state = S_READ;
        break;
      }
    }

    uint16_t statusWord(uint16_t dq7, uint16_t dq5)
    {
      toggle ^= 1;
      return uint16_t((dq7 ? 0x80 : 0) | (toggle ? 0x40 : 0) | (dq5 ? 0x20 : 0));
    }

    uint16_t amdRead(uint32_t addr)
    {
      switch (state)
      {
      case S_CFI:
        switch (addr)
        {
        case 0x10: return 0x0051;
        case 0x11: return 0x0052;
        case 0x12: return 0x0059;
        case 0x27: { uint32_t bytes = cfg.words * 2, e = 0; while ((1UL << e) < bytes) e++; return uint16_t(e); }
        default: return 0;
        }
      case S_AUTO:
        switch (addr & 0xFF)
        {
        case 0x00: return cfg.id[0];
        case 0x01: return cfg.id[1];
        case 0x0E: return cfg.id[2];
        case 0x0F: return cfg.id[3];
        default: return 0;
        }
      case S_PROG_BUSY:
        if (nowNs >= busyUntil) { state = S_READ; return mem[addr]; }
        return statusWord(uint16_t((~progData) & 0x80), 0);
      case S_ERASE_BUSY:
        if (nowNs >= busyUntil) { state = S_READ; return mem[addr]; }
        return statusWord(0, 0);
      case S_FAIL:
        return statusWord(uint16_t((~progData) & 0x80), 1);
      default:
        return mem[addr];
      }
    }

    // ---- Intel/Sharp 28F400 ----
    enum IState { I_ARRAY, I_ID, I_PROG_DATA, I_ERASE_CONFIRM, I_STATUS };
    IState istate = I_ARRAY;
    uint16_t isr = 0;

    void intelBlockOf(uint32_t a, uint32_t & start, uint32_t & size) const
    {
      static const uint32_t bs[7] = { 0x0000, 0x2000, 0x3000, 0x4000, 0x10000, 0x20000, 0x30000 };
      static const uint32_t bn[7] = { 0x2000, 0x1000, 0x1000, 0xC000, 0x10000, 0x10000, 0x10000 };
      bool top = cfg.layout == TOP;
      uint32_t m = top ? (0x3FFFFU - (a & 0x3FFFFU)) : (a & 0x3FFFFU);
      int i = 6;
      while (i > 0 && bs[i] > m) i--;
      if (top) { start = 0x40000U - (bs[i] + bn[i]); size = bn[i]; }
      else { start = bs[i]; size = bn[i]; }
    }

    void intelWrite(uint32_t addr, uint16_t data)
    {
      uint8_t cmd = uint8_t(data & 0xFF);
      if (nowNs < busyUntil && istate == I_STATUS && !(isr & 0x80)) { programWhileBusy++; return; }
      switch (istate)
      {
      case I_PROG_DATA:
        {
          uint16_t old = mem[addr];
          programs++;
          isr = 0;
          if (data & uint16_t(~old)) isr = 0x10;
          else mem[addr] = uint16_t(old & data);
          busyUntil = stuck ? ~0ULL : nowNs + cfg.programNs;
          istate = I_STATUS;
          return;
        }
      case I_ERASE_CONFIRM:
        if (cmd == 0xD0)
        {
          uint32_t st, sz;
          intelBlockOf(addr, st, sz);
          eraseWords(st, sz);
          blockErases++;
          isr = 0;
          busyUntil = stuck ? ~0ULL : nowNs + cfg.sectorEraseNs;
        }
        else { isr = 0x30; busyUntil = 0; }
        istate = I_STATUS;
        return;
      default:
        break;
      }
      switch (cmd)
      {
      case 0xFF: istate = I_ARRAY; break;
      case 0x90: istate = I_ID; break;
      case 0x70: istate = I_STATUS; break;
      case 0x50: isr = 0; break;
      case 0x40: istate = I_PROG_DATA; break;
      case 0x20: istate = I_ERASE_CONFIRM; break;
      default: break;              // AAh, 55h, F0h, A0h: não são comandos Intel
      }
    }

    uint16_t intelRead(uint32_t addr)
    {
      switch (istate)
      {
      case I_ID: return (addr & 0xFF) == 0 ? cfg.id[0] : ((addr & 0xFF) == 1 ? cfg.id[1] : 0);
      case I_STATUS: return nowNs >= busyUntil ? uint16_t(isr | 0x80) : isr;
      default: return mem[addr];
      }
    }
  };

  /// Barramento para o MdFlashCore: o tempo avança a cada ciclo; confere a direção dos dados.
  class Bus
  {
  public:
    explicit Bus(Chip & c) : chip(c) {}
    Chip & chip;
    bool dataOutput = false;
    uint64_t readNs = 2000, writeNs = 500;

    void out() { dataOutput = true; }
    void in() { dataOutput = false; }
    void w(uint32_t a, uint16_t d)
    {
      if (!dataOutput) chip.fail("escrita com o barramento de dados como entrada");
      chip.write(a, d);
      chip.nowNs += writeNs;
    }
    uint16_t r(uint32_t a)
    {
      if (dataOutput) chip.fail("leitura com o barramento de dados como saída");
      uint16_t v = chip.read(a);
      chip.nowNs += readNs;
      return v;
    }
    uint32_t ms() { return uint32_t(chip.nowNs / 1000000ULL); }
    void wait_ms(uint32_t n) { chip.nowNs += uint64_t(n) * 1000000ULL; }
  };

  /// Origem dos dados: um vetor de bytes, em blocos de 512.
  class Source
  {
  public:
    Source(std::vector<uint8_t> const & d) : data(d) {}
    std::vector<uint8_t> const & data;
    size_t pos = 0;
    uint8_t const * block(size_t & n)
    {
      size_t left = data.size() - pos;
      n = left > 512 ? 512 : left;
      uint8_t const * p = data.data() + pos;
      pos += n;
      return n ? p : nullptr;
    }
  };
}
