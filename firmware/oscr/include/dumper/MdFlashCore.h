// SPDX-License-Identifier: GPL-3.0-or-later
// Núcleo da gravação de flash de cartucho de Mega Drive: tabela de chips, escolha do conjunto de comandos, apagar por layout e programar,
// tudo com limite de tempo. Não inclui nada do Arduino: o barramento e a origem dos dados entram como parâmetros de template, para os
// testes do PC (pc-tests/test_mdflash.cpp) rodarem ESTE código contra um modelo de chip. No Mega, `MdFlash.cpp` liga o barramento às
// funções do OSCR (`MD::writeFlash`, `MD::readFlash`, `MD::dataOut`, `MD::dataIn`).
//
// Origem dos algoritmos: firmware 1.1 do md_rewriter (MD.c, flashid.c), já testado lá contra o mesmo tipo de modelo.
// Os dois chips que o OSCR já gravava (MX29F1610 e S29GL064N) continuam sendo gravados pelas funções do OSCR (`write29F1610`, `write29GL`);
// este núcleo só os identifica. Todos os outros chips usam o código daqui.
//
// Barramento (`B`), endereços em PALAVRAS de 16 bits:
//   void out();                       // dados como saída
//   void in();                        // dados como entrada
//   void w(uint32_t a, uint16_t d);   // um ciclo de escrita (dados já como saída)
//   uint16_t r(uint32_t a);           // um ciclo de leitura (dados já como entrada)
//   uint32_t ms();                    // relógio em ms
//   void wait_ms(uint32_t n);
// Origem dos dados (`S`):
//   uint8_t const * block(size_t & n);   // próximo trecho do arquivo (até 512 bytes); n = 0 no fim
#pragma once
#include <stdint.h>
#include <stddef.h>
#include <string.h>

#ifdef __AVR__
# include <avr/pgmspace.h>
# define MDF_PROGMEM PROGMEM
# define MDF_LOAD(dst, src) memcpy_P(&(dst), &(src), sizeof(dst))
#else
# define MDF_PROGMEM
# define MDF_LOAD(dst, src) memcpy(&(dst), &(src), sizeof(dst))
#endif

namespace OSCR { namespace Dumper { namespace MdFlashCore {

enum CmdSet : uint8_t { kAmd555 = 0, kAmd5555 = 1, kIntel = 2 };
enum Layout : uint8_t { kLayoutUnknown = 0, kBottomBoot, kTopBoot, kUniform };
/// Quem grava o chip: `kNative` = este núcleo; os outros dois = funções do OSCR em MegaDrive.cpp.
enum Impl : uint8_t { kNative = 0, kOscrF1610, kOscrGl };

enum Result : uint8_t { kOk = 0, kNoChip, kTooBig, kEraseFail, kProgramFail, kShortFile, kNotBlank };

constexpr uint32_t kPollMax = 2000;             ///< leituras de DQ7 por palavra antes de desistir (cada uma leva alguns µs)
constexpr uint32_t kEraseTimeoutMs = 15000;     ///< por setor ou bloco; o pior caso dos datasheets é bem menor
constexpr uint32_t kW64 = 0x400000UL, kW32 = 0x200000UL;     ///< tamanho do chip em palavras

struct Chip
{
  uint8_t mfr;
  uint8_t dev;
  char name[14];
  uint8_t layout;
  uint8_t cmd;
  uint8_t impl;
  uint8_t eraseCode;      ///< comando de apagar setor: 30h, ou 50h (bloco de 32 KWord das SST39VF320x)
  uint32_t words;         ///< tamanho do chip em palavras
};

/// IDs: fabricante e dispositivo (byte baixo do ciclo 1 do autoselect), de datasheets e do flashlist.csv do MD_Dumper.
/// Só o MX29LV640EB foi confirmado em chip real (firmware 1.0 do md_rewriter). O resto: não confirmado.
static const Chip kChips[] MDF_PROGMEM = {
  { 0xC2, 0xF1, "MX29F1610",   kUniform,    kAmd5555, kOscrF1610, 0x30, 0x100000UL },       // o que o OSCR já gravava: 2 MB
  { 0xC2, 0xCB, "MX29LV640EB", kBottomBoot, kAmd555,  kNative,    0x30, kW64 },
  { 0xC2, 0xC9, "MX29LV640ET", kTopBoot,    kAmd555,  kNative,    0x30, kW64 },
  { 0x20, 0xDF, "M29W640DB",   kBottomBoot, kAmd555,  kNative,    0x30, kW64 },
  { 0x20, 0xDE, "M29W640DT",   kTopBoot,    kAmd555,  kNative,    0x30, kW64 },
  { 0x20, 0x7E, "M29W640G",    kLayoutUnknown, kAmd555, kNative,  0x30, kW64 },
  { 0xBF, 0x6D, "SST39VF6401B", kUniform,   kAmd555,  kNative,    0x30, kW64 },           // 30h = bloco de 32 KWord (datasheet)
  { 0xBF, 0x6C, "SST39VF6402B", kUniform,   kAmd555,  kNative,    0x30, kW64 },
  { 0xBF, 0x5B, "SST39VF3201", kUniform,    kAmd555,  kNative,    0x50, kW32 },           // 30h apaga só 2 KWord: bloco = 50h
  { 0xBF, 0x5A, "SST39VF3202", kUniform,    kAmd555,  kNative,    0x50, kW32 },
  { 0x20, 0xCA, "M29W320DT",   kTopBoot,    kAmd555,  kNative,    0x30, kW32 },
  { 0x20, 0xCB, "M29W320DB",   kBottomBoot, kAmd555,  kNative,    0x30, kW32 },
  { 0x20, 0x56, "M29W320ET",   kTopBoot,    kAmd555,  kNative,    0x30, kW32 },
  { 0x20, 0x57, "M29W320EB",   kBottomBoot, kAmd555,  kNative,    0x30, kW32 },
  { 0xC2, 0xA7, "MX29LV320T",  kTopBoot,    kAmd555,  kNative,    0x30, kW32 },
  { 0xC2, 0xA8, "MX29LV320B",  kBottomBoot, kAmd555,  kNative,    0x30, kW32 },
  { 0xC2, 0xF9, "MX29L3211",   kLayoutUnknown, kAmd5555, kNative, 0x30, kW32 },           // desbloqueio 5555h/2AAAh
  { 0x89, 0x70, "PA28F400T",   kTopBoot,    kIntel,   kNative,    0x20, 0x40000UL },      // Intel: apagar bloco 20h+D0h
  { 0x89, 0x71, "PA28F400B",   kBottomBoot, kIntel,   kNative,    0x20, 0x40000UL },
};
constexpr size_t kChipCount = sizeof(kChips) / sizeof(kChips[0]);

/// S29GL: o OSCR trata todo 017Eh como o chip de 4 MB. O ciclo 2 (0Ch ou 10h) é do S29GL064N, de 8 MB.
inline void glChip(uint8_t const id[4], Chip & out)
{
  memset(&out, 0, sizeof(out));
  out.mfr = 0x01; out.dev = 0x7E;
  out.cmd = kAmd555; out.impl = kOscrGl; out.eraseCode = 0x30;
  bool gl064 = id[2] == 0x0C || id[2] == 0x10;
  strcpy(out.name, gl064 ? "S29GL064N" : "S29GL-7E");
  out.words = gl064 ? kW64 : kW32;
  out.layout = id[2] == 0x10 ? kUniform : (id[2] == 0x0C ? (id[3] == 0x01 ? kTopBoot : (id[3] == 0x00 ? kBottomBoot : kLayoutUnknown)) : kLayoutUnknown);
}

/// Procura o chip pelo ID (fabricante, dispositivo, ciclos 2 e 3).
inline bool identify(uint8_t const id[4], Chip & out)
{
  if (id[0] == 0x01 && id[1] == 0x7E) { glChip(id, out); return true; }
  for (size_t i = 0; i < kChipCount; i++)
  {
    MDF_LOAD(out, kChips[i]);
    if (out.mfr == id[0] && out.dev == id[1]) return true;
  }
  return false;
}

struct Probe
{
  bool known = false;
  Chip chip;
  uint8_t id[4] = { 0, 0, 0, 0 };
  uint16_t u1 = 0x555, u2 = 0x2AA;       ///< endereços de desbloqueio AMD
  bool cfi = false;                      ///< chip fora da tabela que respondeu à consulta CFI ("QRY"): só informação, não grava
  uint32_t cfiWords = 0;                 ///< capacidade dita pelo CFI, em palavras
  Probe() { memset(&chip, 0, sizeof(chip)); }
};

// ---------- conjunto de comandos AMD ----------
template <class B> void resetAmd(B & b, uint32_t u1, uint32_t u2)
{
  b.out();
  b.w(u1, 0xAA); b.w(u2, 0x55); b.w(u1, 0xF0);
}

/// Reset, autoselect (ciclos 1 a 3, bytes baixos) e reset; como `resetFlash(); idFlash(); resetFlash();` do OSCR.
template <class B> void autoselectAmd(B & b, uint32_t u1, uint32_t u2, uint8_t id[4])
{
  resetAmd(b, u1, u2);
  b.out();
  b.w(u1, 0xAA); b.w(u2, 0x55); b.w(u1, 0x90);
  b.in();
  id[0] = uint8_t(b.r(0x00));
  id[1] = uint8_t(b.r(0x01));
  id[2] = uint8_t(b.r(0x0E));
  id[3] = uint8_t(b.r(0x0F));
  resetAmd(b, u1, u2);
}

/// Intel/Sharp: FFh (ler matriz), 90h (ler ID), fabricante na palavra 0 e dispositivo na 1, FFh de novo.
template <class B> void autoselectIntel(B & b, uint8_t id[4])
{
  b.out();
  b.w(0, 0xFF); b.w(0, 0x90);
  b.in();
  id[0] = uint8_t(b.r(0)); id[1] = uint8_t(b.r(1)); id[2] = 0; id[3] = 0;
  b.out();
  b.w(0, 0xFF);
}

/// Consulta CFI (menu "Flash CFI" do `MD.ino` do OSCR legado, `identifyFlashCFIChip_MD`): reset duplo, 98h no endereço 55h, "QRY" nas palavras 10h a 12h
/// e o tamanho 2^n bytes na palavra 27h. Só informa o tamanho de um chip que não está na tabela; o OSCR legado gravava por aí, aqui não se grava
/// um chip que nenhum ID confirmou. `p.cfi` e `p.cfiWords` ficam zerados se não houver resposta ou se o tamanho for absurdo (fora de 128 KB a 128 MB).
template <class B> void queryCfi(B & b, Probe & p)
{
  p.cfi = false; p.cfiWords = 0;
  b.out();
  b.w(0x555, 0xF0); b.wait_ms(2);
  b.w(0x555, 0xF0); b.wait_ms(2);
  b.w(0x55, 0x98);
  b.in();
  bool qry = (b.r(0x10) & 0xFF) == 0x51 && (b.r(0x11) & 0xFF) == 0x52 && (b.r(0x12) & 0xFF) == 0x59;
  uint8_t exp = uint8_t(b.r(0x27) & 0xFF);
  b.out();
  b.w(0x555, 0xF0);
  if (qry && exp >= 17 && exp <= 27) { p.cfi = true; p.cfiWords = (1UL << exp) / 2; }
}

/// Descobre o conjunto de comandos. Ordem: o desbloqueio 5555h/2AAAh que o OSCR já usa (os chips de 11 bits de decodificação respondem
/// igual), depois 555h/2AAh exato, depois Intel. O ID do primeiro acerto vale. Chip fora da tabela: `known` = false e `id` = a primeira leitura.
template <class B> void probe(B & b, Probe & p)
{
  uint8_t first[4], alt[4];
  Chip c;
  p = Probe();
  autoselectAmd(b, 0x5555, 0x2AAA, first);
  memcpy(p.id, first, 4);
  if (identify(first, c) && c.cmd != kIntel) { p.known = true; p.chip = c; }
  else
  {
    autoselectAmd(b, 0x555, 0x2AA, alt);
    if (identify(alt, c) && c.cmd != kIntel) { p.known = true; p.chip = c; memcpy(p.id, alt, 4); }
    else
    {
      autoselectIntel(b, alt);
      if (identify(alt, c) && c.cmd == kIntel) { p.known = true; p.chip = c; memcpy(p.id, alt, 4); }
    }
  }
  if (p.known && p.chip.cmd == kAmd5555) { p.u1 = 0x5555; p.u2 = 0x2AAA; }
  if (!p.known) queryCfi(b, p);
}

// ---------- apagar ----------

/// Bloco do Intel 28F400 que contém a palavra `a`: 16 KB, 8, 8, 96 e três de 128 KB (em palavras: 2000h, 1000h, 1000h, C000h, 3 x 10000h).
/// Boot embaixo no -B; no -T o mapa é espelhado. Mapa de memória do datasheet: conferir em chip real.
inline void intelBlock(bool top, uint32_t a, uint32_t & start, uint32_t & size)
{
  static const uint32_t bs[7] = { 0x0000, 0x2000, 0x3000, 0x4000, 0x10000, 0x20000, 0x30000 };
  static const uint32_t bn[7] = { 0x2000, 0x1000, 0x1000, 0xC000, 0x10000, 0x10000, 0x10000 };
  if (a >= 0x40000UL) { start = a & ~0xFFFFUL; size = 0x10000; return; }
  uint32_t m = top ? (0x3FFFFUL - a) : a;
  int i = 6;
  while (i > 0 && bs[i] > m) i--;
  if (top) { start = 0x40000UL - (bs[i] + bn[i]); size = bn[i]; }
  else { start = bs[i]; size = bn[i]; }
}

/// Apaga o setor (ou bloco) que contém `sa`. DQ7 e DQ6 (AMD) com limite de tempo; falha se DQ5 ficou preso ou estourou o tempo (e dá reset).
template <class B> bool eraseSectorAmd(B & b, Probe const & p, uint32_t sa)
{
  b.out();
  b.w(p.u1, 0xAA); b.w(p.u2, 0x55); b.w(p.u1, 0x80); b.w(p.u1, 0xAA); b.w(p.u2, 0x55); b.w(sa, p.chip.eraseCode);
  b.in();
  uint32_t t0 = b.ms();
  for (;;)
  {
    uint8_t s1 = uint8_t(b.r(sa)), s2 = uint8_t(b.r(sa));
    if ((s1 & 0x40) == (s2 & 0x40) && (s2 & 0x80)) return true;
    if (s2 & 0x20)
    {
      // DQ5 também é dado (FFh) quando o apagamento acabou de terminar: olhar de novo antes de desistir
      uint8_t s3 = uint8_t(b.r(sa)), s4 = uint8_t(b.r(sa));
      if ((s3 & 0x40) == (s4 & 0x40) && (s4 & 0x80)) return true;
      resetAmd(b, p.u1, p.u2);
      return false;
    }
    if (b.ms() - t0 > kEraseTimeoutMs) { resetAmd(b, p.u1, p.u2); return false; }
  }
}

/// 20h, D0h no bloco e espera o bit 7 do registrador de status. Erros: bits 5, 4, 3 e 1. Termina sempre com FFh.
template <class B> bool eraseBlockIntel(B & b, uint32_t a)
{
  b.out();
  b.w(a, 0x20); b.w(a, 0xD0);
  b.in();
  uint32_t t0 = b.ms();
  uint8_t sr = 0;
  bool ready = false;
  while (b.ms() - t0 <= kEraseTimeoutMs)
  {
    sr = uint8_t(b.r(a));
    if (sr & 0x80) { ready = true; break; }
  }
  b.out();
  if (!ready || (sr & 0x3A)) { b.w(a, 0x50); b.w(a, 0xFF); return false; }
  b.w(a, 0xFF);
  return true;
}

/// Apaga o que uma ROM de `words` palavras ocupa, por layout. AMD: o início de chip *bottom boot* e o fim de chip *top boot* são oito setores de 8 KB
/// (um 30h apaga um só); o resto, setores de 32 KWord. Chip de layout desconhecido: passos de 8 KB no começo (comportamento do md_rewriter 1.0).
/// Intel: bloco a bloco, conforme o mapa.
template <class B> bool eraseRange(B & b, Probe const & p, uint32_t words)
{
  Chip const & c = p.chip;
  if (c.cmd == kIntel)
  {
    bool top = c.layout != kBottomBoot;
    for (uint32_t a = 0; a < words;)
    {
      uint32_t bs, bn;
      intelBlock(top, a, bs, bn);
      if (!eraseBlockIntel(b, a)) return false;
      a = bs + bn;
    }
    return true;
  }

  bool smallStart = c.layout == kBottomBoot || c.layout == kLayoutUnknown;
  for (uint32_t a = 0; a < words;)
  {
    if (c.layout == kTopBoot && c.words && a >= c.words - 0x8000UL)
    {
      for (uint8_t k = 0; k < 8; k++)
        if (!eraseSectorAmd(b, p, a + uint32_t(k) * 0x1000UL)) return false;
      a += 0x8000UL;
      continue;
    }
    if (!eraseSectorAmd(b, p, a)) return false;
    a += (a < 0x8000UL && smallStart) ? 0x1000UL : 0x8000UL;
  }
  return true;
}

// ---------- programar ----------

/// A0h, o dado, e DQ7 (polling): ocupado lê o complemento do bit 7 do dado. DQ5 = o chip desistiu (ex.: 0 -> 1 numa célula não apagada).
template <class B> bool programWordAmd(B & b, Probe const & p, uint32_t a, uint16_t d)
{
  b.out();
  b.w(p.u1, 0xAA); b.w(p.u2, 0x55); b.w(p.u1, 0xA0); b.w(a, d);
  b.in();
  for (uint32_t n = 0; n < kPollMax; n++)
  {
    uint8_t v = uint8_t(b.r(a));
    if ((v & 0x80) == (d & 0x80)) return true;
    if (v & 0x20)
    {
      v = uint8_t(b.r(a));
      if ((v & 0x80) == (d & 0x80)) return true;
      break;
    }
  }
  resetAmd(b, p.u1, p.u2);
  return false;
}

/// 40h, o dado, e status (bit 7 = pronto). Erros: bits 4, 3 e 1. Termina com FFh.
template <class B> bool programWordIntel(B & b, uint32_t a, uint16_t d)
{
  b.out();
  b.w(a, 0x40); b.w(a, d);
  b.in();
  uint8_t sr = 0;
  bool ready = false;
  for (uint32_t n = 0; n < kPollMax; n++)
  {
    sr = uint8_t(b.r(a));
    if (sr & 0x80) { ready = true; break; }
  }
  b.out();
  if (!ready || (sr & 0x1A)) { b.w(a, 0x50); b.w(a, 0xFF); return false; }
  b.w(a, 0xFF);
  return true;
}

/// Apaga a área da ROM. Só para `kNative`; os dois chips do OSCR são apagados por `MD::eraseFlash`.
/// Confere que as `words` primeiras palavras leem FFFFh. Lição da bancada do md_rewriter: um apagamento pode "terminar" sem erro e deixar setores
/// gravados (setores de boot de 8 KB tratados como um de 64 KB); gravar por cima falha no primeiro bit 0 -> 1.
template <class B> bool blankRange(B & b, uint32_t words)
{
  b.in();
  for (uint32_t a = 0; a < words; a++)
    if (b.r(a) != 0xFFFF) return false;
  return true;
}

template <class B> Result prepare(B & b, Probe const & p, uint32_t sizeBytes)
{
  if (!p.known || p.chip.impl != kNative) return kNoChip;
  uint32_t words = (sizeBytes + 1) / 2;
  if (words == 0 || words > p.chip.words) return kTooBig;
  if (!eraseRange(b, p, words))
  {
    if (p.chip.cmd == kIntel) { b.out(); b.w(0, 0xFF); } else resetAmd(b, p.u1, p.u2);
    return kEraseFail;
  }
  if (p.chip.cmd == kIntel) { b.out(); b.w(0, 0xFF); } else resetAmd(b, p.u1, p.u2);
  if (!blankRange(b, words)) return kNotBlank;          // apagou "sem erro" mas sobrou dado: não grava por cima
  return kOk;
}

/// Programa `sizeBytes` bytes (par) vindos de `src`, palavra a palavra, depois do `prepare`. Palavras FFFFh não são gravadas: o chip
/// já está apagado ali. Para na primeira palavra que não gravou.
template <class B, class S> Result program(B & b, Probe const & p, uint32_t sizeBytes, S & src)
{
  if (!p.known || p.chip.impl != kNative) return kNoChip;
  uint32_t aw = 0, done = 0;
  while (done < sizeBytes)
  {
    size_t n = 0;
    uint8_t const * blk = src.block(n);
    if (!blk || n == 0) return kShortFile;
    if (n > sizeBytes - done) n = sizeBytes - done;
    for (size_t i = 0; i + 1 < n; i += 2, aw++)
    {
      uint16_t w = uint16_t((uint16_t(blk[i]) << 8) | blk[i + 1]);
      if (w == 0xFFFF) continue;
      bool ok = p.chip.cmd == kIntel ? programWordIntel(b, aw, w) : programWordAmd(b, p, aw, w);
      if (!ok) return kProgramFail;
    }
    done += uint32_t(n);
  }
  if (p.chip.cmd == kIntel) { b.out(); b.w(0, 0xFF); } else resetAmd(b, p.u1, p.u2);
  return kOk;
}

}}}   // namespace OSCR::Dumper::MdFlashCore
