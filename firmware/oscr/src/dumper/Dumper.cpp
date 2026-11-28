// SPDX-License-Identifier: GPL-3.0-or-later
// Fork oscr_minimal: laço de comandos do protocolo serial (docs/referencia/protocolo.md) ligado aos núcleos do OSCR.
// Estado: SNES, NES/Famicom, Mega Drive, GBA, GB/GBC, SMS/GG/SG-1000 e N64 (leitura de ROM e saves; D158) (DETECT, DUMP_ROM, READ_SAVE e WRITE_SAVE), nunca rodados em hardware (docs/referencia/fork-oscr.md).
#include "syslibinc.h"
#include "config.h"

#if OSCR_DUMPER

# include <setjmp.h>

# include "hardware.h"
# include "api.h"
# include "common.h"
# include "ui.h"
# include "cores/include.h"
# include "cores/MegaDrive.h"
# include "cores/GameBoyAdvance.h"
# include "cores/GameBoy.h"
# include "cores/SNES.h"
# include "cores/NES.h"
# include "cores/SMS.h"
# include "cores/N64.h"
# include "cores/Colecovision.h"
# include "cores/NeoGeoPocket.h"
# include "cores/Vectrex.h"
# include "cores/Arcadia2001.h"
# include "cores/RCAStudio2.h"
# include "cores/TomyPyuuta.h"
# include "cores/CasioPV1000.h"
# include "cores/BallyAstrocade.h"
# include "cores/ChannelF.h"
# include "cores/Odyssey2.h"
# include "cores/PokemonMini.h"
# include "cores/VSmile.h"
# include "cores/MSX.h"
# include "cores/Supervision.h"
# include "cores/Atari2600.h"
# include "cores/Atari5200.h"
# include "cores/Atari7800.h"
# include "cores/Atari8.h"
# include "cores/AtariLynx.h"
# include "cores/AtariJaguar.h"
# include "common/crdb/mapper.h"
# include "cores/SelfTest.h"
# include "dumper/Dumper.h"
# include "dumper/NesFlash.h"
# include "dumper/NesCore.h"
# include "dumper/Gba369.h"
# include "dumper/SnesAcc.h"
# include "dumper/SnesAccIo.h"
# include "cores/ST.h"
# include "cores/GPC.h"
# include "cores/Satellaview.h"
# include "cores/SFM.h"
# include "dumper/SnesFlash.h"
# include "dumper/SnesType.h"
# include "dumper/MdExtra.h"
# include "dumper/MdBank.h"
# include "dumper/GbAcc.h"
# include "dumper/GbRtc.h"
# include "cores/GameBoyMem.h"
# include "cores/GameBoySmart.h"
# include "dumper/MdFlash.h"
# include "dumper/GbaFlash.h"
# include "dumper/N64Flash.h"
# include "dumper/GbFlash.h"
# include "dumper/FlashProg.h"
# include "dumper/VoltCore.h"
# include "dumper/SmsCore.h"
# include "dumper/ColvCore.h"
# include "dumper/NgpCore.h"
# include "dumper/VecCore.h"
# include "dumper/ArcCore.h"
# include "dumper/RcaCore.h"
# include "dumper/PyuCore.h"
# include "dumper/PvCore.h"
# include "dumper/BallyCore.h"
# include "dumper/ChfCore.h"
# include "dumper/OdyCore.h"
# include "dumper/PkmCore.h"
# include "dumper/VsmCore.h"
# include "dumper/MsxCore.h"
# include "dumper/SvCore.h"
# include "dumper/AtariCore.h"
# include "dumper/N64Core.h"

// `mmc6` e `flashfound` ficam no .cpp do núcleo NES, sem declaração no cabeçalho; o MMC6 só é marcado, nunca desmarcado.
namespace OSCR::Cores::NES { extern bool mmc6; extern bool flashfound; }
// IDs do chip lidos pelo `getCartInfo` do Neo Geo Pocket; ficam no .cpp do núcleo, sem declaração no cabeçalho.
namespace OSCR::Cores::NeoGeoPocket { extern uint8_t manufacturerID; extern uint8_t deviceID; }

// O modo do adaptador do SMS fica no .cpp do núcleo, sem declaração no cabeçalho. O slot direto da placa megadrive_sms tem a fiação do
// `mastersystem_adapter` do OSCR (as mesmas portas do modo Raphnet/Retron do núcleo); o enum repete a ordem do SMS.cpp.
namespace OSCR::Cores::SMS
{
  enum class SMSMode : uint8_t { SMSRetrode, GGRetrode, SMSRetron, GGRetron, SMSRaphnet, SG1000Raphnet };
  extern SMSMode adapterMode;
  extern bool manRomSizeSelected;
}

// `eepPages` (páginas da EEPROM) e `crc1` (CRC1 do cabeçalho) ficam no .cpp do núcleo N64, sem declaração no cabeçalho.
namespace OSCR::Cores::N64 { extern uint16_t eepPages; extern OSCR::CRC32::crc32_t crc1; }

# ifndef OSCR_DUMPER_BAUD
#   define OSCR_DUMPER_BAUD 1000000UL     // fallbacks que o host tenta: compile com -DOSCR_DUMPER_BAUD=500000 ou 115200
# endif

// `romSize` (índice em `romSizes`) e `atari8right` ficam no .cpp do núcleo Atari8, sem declaração no cabeçalho (como `mmc6` do NES): o `readROM` do OSCR lê os dois.
namespace OSCR::Cores::Atari8 { extern uint8_t romSize; extern bool atari8right; }
// `romSize` (índice 0 a 2) e os dois últimos words lidos ficam no .cpp do núcleo Jaguar, sem declaração no cabeçalho.
// `ody2mapper` (0 = A10 sem ligação, 1 = A10 ligado) e `ody2size` (índice em `romSizes`) ficam no .cpp do núcleo Odyssey 2, sem declaração no cabeçalho: o `readROM` do OSCR lê os dois.
namespace OSCR::Cores::Odyssey2 { extern uint8_t ody2mapper; extern uint8_t ody2size; }
// `msxmapper` (0 a 14) fica no .cpp do núcleo MSX, sem declaração no cabeçalho: o `readROM`, o `readRAM` e o `writeRAM` do OSCR leem o campo (D230).
namespace OSCR::Cores::MSX { extern uint8_t msxmapper; }
namespace OSCR::Cores::AtariJaguar { extern uint8_t romSize; extern uint16_t tempDataLO; extern uint16_t tempDataHI; extern int eepSize; extern uint32_t flaSize; extern uint16_t flashID; }

namespace OSCR::Dumper
{
  namespace
  {
    oscr::StreamSink * activeSink = nullptr;
    oscr::StreamSource * activeSource = nullptr;
    bool errorFlag = false;
    jmp_buf escape;
    bool armed = false;
    bool clockTest = false;                     // saídas de teste do CLOCK ligadas (o fim de todo comando as desliga: runCore zera)

    uint8_t rxBuf[OSCR_MAX_PAYLOAD];
    uint8_t txBuf[OSCR_MAX_PAYLOAD + 10];

    int ioRead(void *, uint32_t timeoutMs)
    {
      if (ClockedSerial.available()) return ClockedSerial.read();   // D245: byte já na fila, sem ler o relógio
      uint32_t start = millis();
      for (;;)
      {
        if (ClockedSerial.available()) return ClockedSerial.read();
        if (millis() - start >= timeoutMs) return -1;
      }
    }

    void ioWrite(void *, uint8_t const * data, size_t len)
    {
      ClockedSerial.rawWrite(data, len);     // a UI de texto fica muda; só o protocolo usa a serial
    }

    uint32_t ioNow(void *) { return millis(); }

    /**
     * Slot do Mega Drive vazio? (D246) Sem cartucho o barramento de dados fica solto e o `dataIn` do OSCR liga os pull-ups: lê FFFF, como
     * uma flash apagada. Para separar os dois: pré-carrega as linhas de dados em 0 (cartucho desligado do barramento, /CE e /OE altos),
     * solta sem pull-up e lê com o `readWord` do OSCR; repete pré-carregando em 1. Linha solta guarda a carga (alguns pF, fuga de nA:
     * nada muda nos ~3 µs da leitura) e segue a pré-carga; linha que um chip dirige dá o mesmo valor nas duas. Vazio = a maioria dos 16
     * bits seguiu a pré-carga em todas as leituras. Chamado com o cartucho ligado (`cartOn`) e ANTES do `getCartInfo` do OSCR: depois dele o
     * cartucho KY (S29GL064N) não dirigia mais o barramento e a sonda o dava como vazio (bancada, 2026-11-27). Deixa o `dataIn` do OSCR.
     */
    bool mdBusFloating()
    {
      uint8_t followed = 0;
      static constexpr uint8_t kAddr[4] = { 0x80, 0x88, 0xC8, 0xD9 };    // palavras do cabeçalho em $100, $110, $190 e $1B2
      for (uint8_t i = 0; i < 4; i++)
      {
        uint16_t v[2];
        for (uint8_t pre = 0; pre < 2; pre++)
        {
          uint8_t lvl = pre ? 0xFF : 0x00;
          PORTC = lvl; PORTA = lvl; DDRC = 0xFF; DDRA = 0xFF;      // pré-carga
          NOP; NOP;
          DDRC = 0x00; DDRA = 0x00; PORTC = 0x00; PORTA = 0x00;    // entrada sem pull-up
          v[pre] = OSCR::Cores::MegaDrive::readWord(kAddr[i]);
        }
        uint16_t follow = uint16_t(~v[0] & v[1]);                  // bits que leram 0 com pré-carga 0 e 1 com pré-carga 1
        if (__builtin_popcount(follow) >= 8) followed++;
      }
      OSCR::Cores::MegaDrive::dataIn();
      return followed == 4;
    }

    /**
     * `/CART` do Mega Drive (B32 -> D50 = PB3, placa 16_bits v. 1.2; D87): o cartucho liga o pino ao GND, então baixo = há cartucho.
     * Alto não diz nada: placas anteriores deixam o pino solto e o pull-up interno lê alto, e com a v. 1.2 alto também é "slot vazio".
     * Por isso só o nível baixo é usado (como prova de que há cartucho). Nenhum núcleo do OSCR usa PB3 neste fork; o estado anterior do pino é restaurado.
     */
    bool mdCartPinLow()
    {
      uint8_t const bit = _BV(PB3);
      uint8_t const ddr = DDRB & bit, port = PORTB & bit;
      DDRB &= ~bit;
      PORTB |= bit;
      delayMicroseconds(50);                      // o pull-up interno (cerca de 35 kΩ) carrega o fio de 25 mm e os 5 pF do cartucho em poucos microssegundos
      bool low = (PINB & bit) == 0;
      PORTB = (PORTB & ~bit) | port;
      DDRB = (DDRB & ~bit) | ddr;
      return low;
    }

    /**
     * Executa uma função de núcleo com a saída ligada ao fluxo. Erros fatais dos núcleos (UI::fatalError) voltam aqui por longjmp.
     * Devolve false se o núcleo falhou.
     */
    bool fatalHit = false;
    bool abortHit = false;

    template <typename Fn>
    bool runCore(Fn fn, bool softErrors = false)
    {
      errorFlag = false;
      fatalHit = false;
      abortHit = false;
      armed = true;
      bool ok = true;

      if (setjmp(escape) == 0)
      {
        fn();
      }
      else
      {
        ok = false;
        fatalHit = true;
      }

      armed = false;
      OSCR::Power::disableCartridge();           // chama ClockGen::stop(): as saídas de teste do CLOCK também param
      clockTest = false;
      OSCR::Storage::Shared::sharedFile.close();
      return ok && (softErrors || !errorFlag);
    }

    /** Repassa ao fluxo do protocolo contando os bytes: erros "suaves" do OSCR depois de o dado sair não derrubam o comando. */
    struct CountingSink : oscr::StreamSink
    {
      oscr::StreamSink * inner = nullptr;
      uint32_t bytes = 0;
      bool write(uint8_t const * data, size_t len) override { if (!inner->write(data, len)) return false; bytes += len; return true; }   // conta só o que o PC aceitou
    };

    struct CountingSource : oscr::StreamSource
    {
      oscr::StreamSource * inner = nullptr;
      uint32_t bytes = 0;
      size_t read(uint8_t * data, size_t len) override { size_t n = inner->read(data, len); bytes += n; return n; }
      uint32_t size() const override { return inner->size(); }
      bool failed() const override { return inner->failed(); }
    };

    CountingSink countingSink;
    CountingSource countingSource;

    namespace MD = OSCR::Cores::MegaDrive;
    namespace GBA = OSCR::Cores::GameBoyAdvance;
    namespace GB = OSCR::Cores::GameBoy;
    namespace SN = OSCR::Cores::SNES;

    /**
     * GBA sem a base de dados do OSCR: lê o cabeçalho, confere o logo da Nintendo e o checksum e acha o tamanho da ROM pelo espelhamento
     * (o menor deslocamento em que a ROM se repete ou o barramento devolve o próprio endereço; sem nenhum dos dois até 16 MB, 32 MB). O tipo de save vem do usuário (campo `mapper`).
     * Devolve 0 = ok, 1 = sem cartucho, 4 = há dados mas o checksum do cabeçalho não confere.
     */
    uint8_t gbaProbe(uint8_t saveOption)
    {
      using namespace OSCR::Cores;
      uint8_t * buf = OSCR::Storage::Shared::buffer;

      GBA::cartOn();
      for (uint16_t w = 0; w < 192; w += 2)
      {
        uint16_t word = GBA::readWord(w);
        buf[w] = word & 0xFF;
        buf[w + 1] = word >> 8;
      }

      // Fim da ROM: ou ela se repete (espelho), ou o barramento devolve o endereço que ficou nas linhas AD (metade do endereço em bytes,
      // 16 bits baixos), como o GBATEK descreve para a área sem ROM (D241). 0xFFFF não conta: pode ser enchimento dentro da ROM.
      uint32_t size = 32UL << 20;
      for (uint32_t cand = 256UL << 10; cand <= (16UL << 20); cand <<= 1)
      {
        bool mirror = true, openBus = true;
        for (uint8_t i = 0; i < 64 && (mirror || openBus); i += 2)
        {
          uint16_t w = GBA::readWord(cand + i);
          mirror = mirror && w == GBA::readWord(i);
          openBus = openBus && w == uint16_t((cand + i) >> 1);
        }
        if (mirror || openBus) { size = cand; break; }
      }
      GBA::cartOff();

      uint16_t logo = 0;
      for (uint8_t i = 0x04; i < 0xA0; i++) logo += buf[i];
      if (logo != 0x4B1B) return 1;

      cartID[0] = char(buf[0xAC]); cartID[1] = char(buf[0xAD]); cartID[2] = char(buf[0xAE]); cartID[3] = char(buf[0xAF]); cartID[4] = 0;
      setOutName(reinterpret_cast<char const *>(&buf[0xA0]), 12);
      romVersion = buf[0xBC];
      checksum = GBA::checksumHeader(buf);
      cartSize = size;
      saveType = saveOption ? saveOption : 3;     // sem informação: SRAM/FRAM de 32 KB, como no firmware próprio

      return buf[0xBD] == checksum ? 0 : 4;
    }

    uint32_t gbaSaveBytes(uint8_t type)
    {
      static uint32_t const sizes[] = {0, 512, 8192, 32768, 65536, 131072, 65536};   // numeração do OSCR: 1 4K EEPROM, 2 64K EEPROM, 3 SRAM 32K, 4 Flash 64K, 5 Flash 128K, 6 SRAM 64K
      return type < sizeof sizes / sizeof sizes[0] ? sizes[type] : 0;
    }

    /**
     * Game Boy / Game Boy Color: o `checkCart` do OSCR lê o cabeçalho e preenche romType, romBanks, sramBanks e lastByteAddress.
     * Devolve 0 = ok, 1 = sem cartucho, 4 = há dados mas o checksum do cabeçalho não confere (o "continuar" do OSCR não existe aqui).
     */
    uint8_t gbProbe()
    {
      if (GB::checkCart()) return 0;
      uint8_t const * h = &OSCR::Storage::Shared::buffer[0x100];
      for (uint8_t i = 1; i < 0x50; i++) if (h[i] != h[0]) return 4;
      return 1;
    }

    /** Bytes do save lido por `GB::readSave()`, pela mesma conta das funções do OSCR (0 = sem save). */
    uint32_t gbSaveBytes()
    {
      using namespace OSCR::Cores;
      if (!GB::lastByteAddress) return 0;
      if (romType == 0x22) return GB::lastByteAddress;                      // MBC7: 256 ou 512 bytes (guardados como tamanho, não endereço)
      if (romType == 0x20) return 32768UL + 1048576UL;                      // MBC6: SRAM de 32 KB + Flash de 1 MB
      return uint32_t(GB::sramBanks) * (uint32_t(GB::lastByteAddress) - 0xA000UL + 1UL);
    }

    /**
     * Relógio do MBC3 (F-17, D192). Não vem do OSCR (ele não lê o RTC): liga o cartucho, confere pelo byte 0x0147 que é MBC3 com TIMER, habilita a RAM/RTC (0x0A em
     * 0x0000), trava os registradores (0 e depois 1 em 0x6000), seleciona 08h a 0Ch em 0x4000 e lê cada um em 0xA000 (com o CS, por `readByteSRAM`).
     * `gbRtcNone` fica true se o cartucho não tem RTC (nada é enviado).
     */
    bool gbRtcNone = false;
    void gbRtcRead()
    {
      using namespace OSCR::Dumper::GbRtc;
      GB::cartOn();
      uint8_t type = GB::readByte(0x0147);
      gbRtcNone = !hasRtc(type);
      if (!gbRtcNone)
      {
        OSCR::Cores::romType = type;
        uint8_t r[kRegs];
        GB::writeByte(0x0000, 0x0A);
        GB::writeByte(0x6000, 0);
        GB::writeByte(0x6000, 1);
        for (uint8_t i = 0; i < kRegs; i++) { GB::writeByte(0x4000, kFirstReg + i); r[i] = GB::readByteSRAM(0xA000); }
        GB::writeByte(0x0000, 0x00);
        OSCR::Storage::Shared::sharedFile.write(r, kRegs);
      }
      GB::cartOff();
    }

    /// Grava os 5 registradores do RTC: para o relógio (bit de parada), escreve segundos, minutos, horas e dias baixo, e por último os dias alto com o bit de parada pedido.
    void gbRtcWrite(const uint8_t * r)
    {
      using namespace OSCR::Dumper::GbRtc;
      GB::cartOn();
      uint8_t type = GB::readByte(0x0147);
      gbRtcNone = !hasRtc(type);
      if (!gbRtcNone)
      {
        OSCR::Cores::romType = type;
        GB::writeByte(0x0000, 0x0A);
        GB::writeByte(0x4000, kFirstReg + 4); GB::writeByteSRAM(0xA000, kHalt);
        for (uint8_t i = 0; i < 4; i++) { GB::writeByte(0x4000, kFirstReg + i); GB::writeByteSRAM(0xA000, r[i]); }
        GB::writeByte(0x4000, kFirstReg + 4); GB::writeByteSRAM(0xA000, r[4]);
        GB::writeByte(0x0000, 0x00);
      }
      GB::cartOff();
    }

    /**
     * Acessórios do Game Boy (F-17, D186): chama a leitura do OSCR do acessório (GbAcc.h). Cada função do OSCR liga o cartucho sozinha, menos a do Mega Memory,
     * que o menu do OSCR chamava com o cartucho já ligado. Sem o acessório (ID desconhecido) o OSCR só avisa e volta sem gravar: o chamador vê zero bytes.
     */
    void gbAccRead(uint16_t acc)
    {
      using namespace OSCR::Dumper::GbAcc;
      switch (acc)
      {
      case kPelican: GB::readPelican(); GB::cartOff(); break;
      case kMegaMem: GB::cartOn(); GB::readMegaMem(); GB::cartOff(); break;
      case kGameShark: GB::readGameshark(); break;                       // liga e desliga sozinha
      case kGbMemory: OSCR::Cores::GameBoyMem::readROM(); break;
      case kGbMemoryMap: OSCR::Cores::GameBoyMem::readMapping(); break;
      case kGbSmart: OSCR::Cores::GameBoySmart::readFlash(); break;                   // o `runCore` desliga o cartucho
      case kRtc: gbRtcRead(); break;
      default: break;
      }
    }

    namespace SM = OSCR::Cores::SMS;
    namespace N6 = OSCR::Cores::N64;
    namespace CV = OSCR::Cores::Colecovision;
    namespace NG = OSCR::Cores::NeoGeoPocket;
    namespace VX = OSCR::Cores::Vectrex;
    namespace AC = OSCR::Cores::Arcadia2001;
    namespace RC = OSCR::Cores::RCAStudio2;
    namespace PY = OSCR::Cores::TomyPyuuta;
    namespace PV = OSCR::Cores::CasioPV1000;
    namespace BA = OSCR::Cores::BallyAstrocade;
    namespace CF = OSCR::Cores::ChannelF;
    namespace OD = OSCR::Cores::Odyssey2;
    namespace PK = OSCR::Cores::PokemonMini;
    namespace VS = OSCR::Cores::VSmile;
    namespace MX = OSCR::Cores::MSX;
    namespace SV = OSCR::Cores::Supervision;
    namespace A2 = OSCR::Cores::Atari2600;
    namespace A5 = OSCR::Cores::Atari5200;
    namespace A7 = OSCR::Cores::Atari7800;
    namespace A8 = OSCR::Cores::Atari8;
    namespace LX = OSCR::Cores::AtariLynx;
    namespace JG = OSCR::Cores::AtariJaguar;

    /**
     * Atari 2600 (F-20, D206): o `readROM` do OSCR escolhe o método de leitura por `mapperDetail->id`, um registro do banco `a2600-mappers` do SD
     * (que não existe aqui). A costura aponta `mapperDetail` para um registro estático só com o id que o PC mandou (`mapper` do protocolo) e **chama o
     * `readROM` do OSCR**; a única mudança no núcleo é o `matchCRC` no fim (banco do SD), desligado com `#if !OSCR_DUMPER`, como no ST.cpp.
     */
    OSCR::Databases::Basic::crdbMapperRecord a26Rec;
    uint8_t a26Probe()
    {
      uint8_t sample[32];
      A2::cartOn();
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = A2::readData(0x1000 + i);
      A2::cartOff();
      return oscr::a26::classify(sample, sizeof sample);
    }
    /**
     * Atari 5200 e 7800 (F-20, D209): como no 2600, o `readROM` do OSCR escolhe o método por `mapperDetail->id` e, nos mappers de tamanho variável,
     * por `romSize` (os dois globais que o menu do OSCR preenchia). A costura os preenche com o `mapper` e o `prg_kb` do PC e **chama o `readROM` do OSCR**
     * (único desvio nos núcleos: o `matchCRC` final sob `#if !OSCR_DUMPER`, como no 2600).
     */
    uint8_t a52Probe()
    {
      uint8_t sample[32];
      A5::cartOn();
      PORTH &= ~(1 << 6);                                               // /8000 (PH6) baixo: ROM em $8000-$BFFF, onde ficam o início e o fim de todo cartucho do 5200
      A5::cycleDelay(15);
      for (uint8_t i = 0; i < 16; i++) { sample[i] = A5::readData(0x8000 + i); sample[16 + i] = A5::readData(0xBFF0 + i); }
      PORTH |= (1 << 6);
      A5::cartOff();
      return oscr::a26::classify(sample, sizeof sample);
    }
    uint8_t a78Probe()
    {
      uint8_t sample[32];
      A7::cartOn();
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = A7::readData(0xFFE0 + i);   // vetores e cabeçalho: no último banco, fixos em $C000-$FFFF
      A7::cartOff();
      return oscr::a26::classify(sample, sizeof sample);
    }
    /**
     * Atari 8 bits e Lynx (F-20, D210). 8 bits: `readROM` do OSCR com o slot (`atari8right`) e o índice do tamanho (`romSize`) vindos do PC; o núcleo só mudou em
     * `checkStatus` (o `wait` esperava um botão) e no `matchCRC` final. Lynx: o próprio núcleo acha o tamanho do bloco (`detectCart`) e o `readROM` grava o cabeçalho
     * .lnx de 64 bytes e os 256 blocos; as únicas mudanças no núcleo são tirar o `static` de `detectCart`, `readROM` e `lynxBlockSize` e o `compareCRC` final.
     */
    uint8_t a8Probe(uint16_t slot)
    {
      uint8_t sample[32];
      A8::atari8right = slot == 1;
      A8::romSize = 0;                                                  // `cartOn` chama `checkStatus`, que lê `romSizes[romSize]`
      A8::cartOn();
      PORTH &= ~(1 << 3);                                               // /S5 (PH3) baixo: ROM em $A000-$BFFF (no slot direito, o /S4 dele é o /S5 do esquerdo)
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = A8::readData(0xBFE0 + i);
      PORTH |= (1 << 3);
      A8::cartOff();
      return oscr::a26::classify(sample, sizeof sample);
    }
    /**
     * PHI2 do Atari 8 bits (D213). O `bankSwitch` do núcleo pulsa PH1 para segurar o `PHI2`, mas PH1 não chega ao slot SNES; o `PHI2` vai ao pino 57 do slot (o CLK1 do
     * Si5351, o mesmo do 7800) e a costura programa o CLK1 em 1,7897725 MHz (o relógio NTSC do 6502 do Atari) enquanto o `readROM` do OSCR roda. Com o relógio correndo
     * solto, o pulso que o núcleo faz em PH1 vira irrelevante: a escrita em $D5xx fica de pé por mais de um período (cerca de 1 us contra 0,56 us).
     */
    bool a8ClockPresent()
    {
#if defined(ENABLE_CLOCKGEN)
      return OSCR::ClockGen::initialize();        // confere de novo se o módulo ainda responde (D241)
#else
      return false;
#endif
    }
    void a8Clock(bool on)
    {
#if defined(ENABLE_CLOCKGEN)
      if (!a8ClockPresent()) return;
      if (on) OSCR::ClockGen::clockgen.set_freq(178977250ULL, SI5351_CLK1);   // unidade da biblioteca: 0,01 Hz
      OSCR::ClockGen::clockgen.output_enable(SI5351_CLK1, on ? 1 : 0);
#else
      (void)on;
#endif
    }
    void a8Read(uint16_t slot, uint16_t kb)
    {
      A8::atari8right = slot == 1;
      A8::romSize = oscr::atari8::sizeIndex(kb) == oscr::atari8::kBad ? 0 : oscr::atari8::sizeIndex(kb);
      bool clk = oscr::atari8::usesClock(slot, kb);                     // 16 KB: liga se houver Si5351 (Necromancer); 32, 64 e 128 KB: `prepare` já exigiu
      if (clk) a8Clock(true);
      A8::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha
      if (clk) a8Clock(false);
    }
    /**
     * Atari Jaguar (F-20, D211): só ROM. O `readROM` do OSCR lê 32 bits por vez e usa `romSize` (0 a 2 = 1, 2 ou 4 MB) do próprio núcleo, que a costura
     * preenche com o `prg_kb` do PC; única mudança no núcleo: o `matchCRC` final sob `#if !OSCR_DUMPER`. A detecção lê os 32 bytes do cabeçalho "ATARI APPROVED DATA
     * HEADER ATRI!" em $400 (cartuchos oficiais; os caseiros podem não ter, mas um slot vazio dá um valor só).
     */
    uint8_t jagProbe()
    {
      uint8_t sample[32];
      JG::romSize = 0;
      JG::cartOn();
      for (uint8_t w = 0; w < 8; w++)
      {
        JG::readData(0x400UL + 4UL * w);                                  // o núcleo lê em passos de 4: o ROM não usa A0 e A1
        sample[4 * w] = JG::tempDataHI >> 8; sample[4 * w + 1] = JG::tempDataHI & 0xFF;
        sample[4 * w + 2] = JG::tempDataLO >> 8; sample[4 * w + 3] = JG::tempDataLO & 0xFF;
      }
      JG::cartOff();
      return oscr::a26::classify(sample, sizeof sample);
    }
    /**
     * Jaguar, saves (D212): `mapper` 0 a 4 = EEPROM 93C46/56/66/76/86 (128 a 2048 bytes, o `eepSize` do núcleo) e 5 = o flash AT29C010 de 128 KB do Memory Track
     * (`flaSize`); a costura só preenche essas duas variáveis do núcleo e chama `readEEP`, `writeEEP`, `readFLASH` e `writeFLASH` do OSCR. `readID` (o OSCR chama ao
     * entrar no menu) acha o Memory Track pelo ID 0x1FD5.
     */
    uint32_t jagSaveBytes(uint16_t m) { return oscr::jag::saveBytes(m); }
    bool jagMemoryTrack()
    {
      JG::readID();
      return JG::flashID == 0x1FD5;
    }
    void jagReadSave(uint16_t m)
    {
      if (m <= 4) { JG::eepSize = m; JG::readEEP(); }
      else { JG::flaSize = 0x20000UL; JG::readFLASH(); }
    }
    void jagWriteSave(uint16_t m)
    {
      if (m <= 4) { JG::eepSize = m; JG::writeEEP(); }              // a conferência é do PC: relê o save e compara
      else { JG::flaSize = 0x20000UL; JG::writeFLASH(); }           // idem: o `verifyFLASH` do OSCR relê o arquivo, que não existe no fluxo
    }
    void jagReadMem(uint16_t kb)
    {
      JG::romSize = oscr::jag::sizeIndex(kb) == oscr::jag::kBad ? 0 : oscr::jag::sizeIndex(kb);
      JG::readMEMORY();                                             // ROM U1 do Memory Track; `cartOn` do núcleo refaz `cartSize` em MB (ver D212)
    }
    void jagRead(uint16_t kb)
    {
      JG::romSize = oscr::jag::sizeIndex(kb) == oscr::jag::kBad ? 0 : oscr::jag::sizeIndex(kb);
      JG::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha
    }
    bool lynxProbe()
    {
      LX::setup();
      bool found = LX::detectCart();
      OSCR::Power::disableCartridge();
      return found;
    }
    void lynxRead()
    {
      LX::setup();
      LX::readROM();
      OSCR::Power::disableCartridge();
    }
    void a52Read(uint16_t id, uint16_t kb)
    {
      a26Rec.id = id;
      OSCR::Databases::Basic::mapperDetail = &a26Rec;
      OSCR::Cores::fromCRDB = false;
      OSCR::Cores::romSize = kb;
      A5::readROM();
      OSCR::Databases::Basic::mapperDetail = nullptr;
    }
    void a78Read(uint16_t id, uint16_t kb)
    {
      a26Rec.id = id;
      OSCR::Databases::Basic::mapperDetail = &a26Rec;
      OSCR::Cores::fromCRDB = false;
      OSCR::Cores::romSize = kb;
      A7::readROM();
      OSCR::Databases::Basic::mapperDetail = nullptr;
    }
    void a26Read(uint16_t id)
    {
      a26Rec.id = id;
      OSCR::Databases::Basic::mapperDetail = &a26Rec;
      OSCR::Cores::fromCRDB = false;
      A2::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha
      OSCR::Databases::Basic::mapperDetail = nullptr;
    }

    /**
     * Vectrex (F-20, D205; D215): a leitura chama o `readROM` do OSCR (índice em `romSize`, o PB6 dos 64 KB é trocado pelo próprio núcleo); única mudança no núcleo:
     * o `matchCRC` final sob `#if !OSCR_DUMPER`. A sondagem lê 32 bytes com `readData` do OSCR, com o PB6 baixo; a detecção não vem do OSCR (ver `VecCore.h`).
     */
    uint8_t vecProbe()
    {
      uint8_t sample[32];
      VX::cartOn();
      PORTH &= ~(1 << 5);                                               // PB6 baixo: banco 0
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = VX::readData(i);
      VX::cartOff();
      return oscr::vec::classify(sample, sizeof sample);
    }
    void vecRead(uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      OSCR::Cores::romSize = oscr::vec::sizeIndex(kb);                  // índice da tabela `romSizes` do núcleo
      VX::readROM();                                                    // trocas do PB6 (macros do núcleo), cartOn/cartOff e o "arquivo": tudo do OSCR (D215)
    }

    /**
     * Emerson Arcadia 2001 (F-20, D215): a leitura chama o `readROM` do OSCR (índice em `romSize`); única mudança no núcleo: o `matchCRC` final sob `#if !OSCR_DUMPER`.
     * A ROM do Arcadia não tem assinatura: a sondagem (`readData` do OSCR) só separa slot vazio de slot com dados, e o tamanho (2, 4, 6 ou 8 KB) vem sempre do PC.
     */
    uint8_t arcProbe()
    {
      uint8_t sample[32];
      AC::cartOn();
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = AC::readData(i);
      AC::cartOff();
      return oscr::arc::classify(sample, sizeof sample);
    }
    void arcRead(uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      OSCR::Cores::romSize = oscr::arc::sizeIndex(kb);                  // índice da tabela `romSizes` do núcleo
      AC::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha (D215)
    }

    /**
     * Neo Geo Pocket (F-20, D202): o `getCartInfo` do OSCR lê o ID do chip (autoselect) e o cabeçalho SNK; o menu de tamanho dele
     * (chip desconhecido) está desligado no fork e o tamanho vem do PC (`kb`). O `readROM` do OSCR não serve: ele abre um prompt de
     * erro e espera uma tecla em `printCartInfo`; a costura repete só o laço de leitura dele (blocos de 512 bytes), com as mesmas funções.
     */
    uint8_t ngpProbe(uint16_t kb)
    {
      NG::cartOn();
      bool ok = NG::getCartInfo();
      NG::cartOff();
      OSCR::Cores::cartSize = oscr::ngp::romBytes(OSCR::Cores::cartSize, kb);
      return oscr::ngp::classify(uint16_t(NG::manufacturerID) << 8 | NG::deviceID, ok);
    }
    void ngpRead(uint32_t bytes)
    {
      NG::cartOn();
      OSCR::Storage::Shared::sharedFile.open("rom", O_WRONLY | O_CREAT | O_TRUNC);
      NG::writeByte(0x0, 0xF0);                                         // modo de leitura (o OSCR faz o mesmo antes do laço)
      for (uint32_t addr = 0; addr < bytes; addr += 512)
      {
        for (uint16_t i = 0; i < 512; i++) OSCR::Storage::Shared::buffer[i] = NG::readByte(addr + i);
        OSCR::Storage::Shared::writeBuffer();
      }
      OSCR::Storage::Shared::sharedFile.close();
      NG::cartOff();
    }

    /**
     * RCA Studio II (F-20, D216): a leitura chama o `readROM` do OSCR (índice em `romSize`); única mudança no núcleo: o `matchCRC` final sob `#if !OSCR_DUMPER`.
     * A ROM do Studio II não tem assinatura: a sondagem (`readData` do OSCR, a partir de $0400) só separa slot vazio de slot com dados. O `readROM` do OSCR lê $0400-$07FF
     * (1 KB) no índice 1; o PC informa sempre 1 KB.
     */
    uint8_t rcaProbe()
    {
      uint8_t sample[32];
      RC::cartOn();
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = RC::readData(oscr::rca::kBase + i);
      RC::cartOff();
      return oscr::rca::classify(sample, sizeof sample);
    }
    void rcaRead(uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      OSCR::Cores::romSize = oscr::rca::sizeIndex(kb);                  // índice da tabela `romSizes` do núcleo
      RC::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha (D216)
    }

    /**
     * Tomy Pyuuta (F-20, D217): a leitura chama o `readROM` do OSCR (índice em `romSize`); única mudança no núcleo: o `matchCRC` final sob `#if !OSCR_DUMPER`.
     * A ROM do Pyuuta não tem assinatura: a sondagem lê 32 bytes de $8000 com `readData` do OSCR e só separa slot vazio de slot com dados. O `readData` não aciona
     * /DBIN nem /CS0 (quem faz isso é o `readROM`): a sondagem os baixa e sobe em volta da leitura, como o `readROM` faz para os primeiros 8 KB.
     */
    uint8_t pyuProbe()
    {
      uint8_t sample[32];
      PY::cartOn();
      PORTH &= ~(1 << 4);                                               // /DBIN(PH4) baixo
      PORTH &= ~(1 << 3);                                               // /CS0(PH3) baixo
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = PY::readData(oscr::pyu::kBase + i);
      PORTH |= (1 << 3);                                                // /CS0 alto
      PORTH |= (1 << 4);                                                // /DBIN alto
      PY::cartOff();
      return oscr::pyu::classify(sample, sizeof sample);
    }
    void pyuRead(uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      OSCR::Cores::romSize = oscr::pyu::sizeIndex(kb);                  // índice da tabela `romSizes` do núcleo: 8, 16 ou 32 KB
      PY::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha (D217)
    }

    /**
     * Watara Supervision (F-20, D218): a leitura chama o `readROM` do OSCR (índice em `romSize`); única mudança no núcleo: o `matchCRC` final sob `#if !OSCR_DUMPER`.
     * O núcleo pede 3,3 V (`setVoltage(k3V3)`); o slot SNES é 5 V fixo, então o adaptador precisa do próprio regulador (docs/planos/adaptadores.md#adaptador-supervision).
     * A ROM não tem assinatura: a sondagem liga o cartucho, lê 32 bytes de $8000 com o `readByte` do OSCR (RD já baixo no `cartOn`) e só separa slot vazio de slot com dados.
     */
    uint8_t svProbe()
    {
      uint8_t sample[32];
      SV::cartOn();
      SV::dataIn();
      SV::controlIn();
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = SV::readByte(oscr::sv::kBase + i);
      SV::cartOff();
      return oscr::sv::classify(sample, sizeof sample);
    }
    void svRead(uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      OSCR::Cores::romSize = oscr::sv::sizeIndex(kb);                   // índice da tabela `romSizes` do núcleo: 32, 64 ou 512 KB
      SV::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha (D218)
    }

    /**
     * Casio PV-1000 (F-20, D219): a leitura chama o `readROM` do OSCR (índice em `romSize`: 8 ou 16 KB); única mudança no núcleo: o `matchCRC` final sob `#if !OSCR_DUMPER`.
     * A ROM não tem assinatura: a sondagem lê 32 bytes de $0000 com o `readData` do OSCR e só separa slot vazio de slot com dados. O `readData` só aciona /RD (quem baixa
     * /CS1 ou /CS2 é o `readROM`): a sondagem tenta /CS1 (cartucho de 8 KB) e, se vier vazio, /CS2 (cartucho de 16 KB), como o `readROM` faz.
     */
    uint8_t pvProbe()
    {
      uint8_t sample[32];
      PV::cartOn();
      for (uint8_t cs = 4; cs >= 3; cs--)                               // /CS1 = PH4 (8 KB), depois /CS2 = PH3 (16 KB)
      {
        PORTH &= ~(1 << cs);
        for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = PV::readData(oscr::pv::kBase + i);
        PORTH |= (1 << cs);
        if (oscr::pv::classify(sample, sizeof sample) == oscr::pv::kOk) break;
      }
      PV::cartOff();
      return oscr::pv::classify(sample, sizeof sample);
    }
    void pvRead(uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      OSCR::Cores::romSize = oscr::pv::sizeIndex(kb);                   // índice da tabela `PV1000` do núcleo: 8 ou 16 KB
      PV::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha (D219)
    }

    /**
     * Bally Astrocade (F-20, D223): a leitura chama o `readROM` do OSCR (índice em `romSize`: 2, 4 ou 8 KB); única mudança no núcleo: o `matchCRC` final sob `#if !OSCR_DUMPER`.
     * O fork não confere assinatura: a sondagem lê 32 bytes de $0000 com o `readData` do OSCR (que baixa e sobe /ENABLE em PH3) e só separa slot vazio de slot com dados.
     */
    uint8_t ballyProbe()
    {
      uint8_t sample[32];
      BA::cartOn();
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = BA::readData(oscr::bally::kBase + i);
      BA::cartOff();
      return oscr::bally::classify(sample, sizeof sample);
    }
    void ballyRead(uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      OSCR::Cores::romSize = oscr::bally::sizeIndex(kb);                // índice da tabela `BALLY` do núcleo: 2, 4 ou 8 KB
      BA::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha (D223)
    }

    /**
     * Fairchild Channel F (F-20, D224): o cartucho não tem barramento de endereço; o F8 pede os bytes pelo protocolo ROMC (PF0-PF4), com PHI (PH3) e
     * WRITE (PH5). A sondagem repete o começo do `readROM` do OSCR com as funções do núcleo (`setROMC(8)` zera o PC0, `setREAD` e `readData` em
     * sequência) e procura o mesmo cabeçalho, com a mesma regra (`ChfCore.h`, `Scanner`).
     */
    uint8_t chfProbe()
    {
      oscr::chf::Scanner sc;
      CF::cartOn();
      CF::setROMC(0x8);
      CF::setREAD();
      while (!sc.feed(CF::readData())) {}
      CF::cartOff();
      return sc.result();
    }
    void chfRead(uint16_t mode, uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      OSCR::Cores::romSize = oscr::chf::sizeIndex(kb);                  // índice da tabela `romSizes` do núcleo: 2, 3, 4 ou 6 KB (o read16K usa para pular a BIOS nos de 4 KB)
      if (mode == oscr::chf::kModeRaw16K) { CF::read16K(); return; }    // liga e desliga o cartucho sozinha
      CF::cartOn();                                                     // o `readROM` do núcleo não liga o cartucho (o menu do OSCR também não): a costura liga e desliga
      CF::readROM();
      CF::cartOff();
    }

    /**
     * Magnavox Odyssey 2 / Videopac (F-20, D226): a leitura chama o `readROM` do OSCR com `ody2mapper` (0 = A10 sem ligação, 1 = A10 ligado) e `ody2size`
     * (índice de 2, 4, 8, 12 ou 16 KB; 12 e 16 KB trocam de banco pelo `bankSwitch` do núcleo); única mudança no núcleo: o `matchCRC` final sob `#if !OSCR_DUMPER`.
     * O fork não confere assinatura: a sondagem lê 32 bytes de $0400 com o `readData` do OSCR (que baixa e sobe /PSEN em PH6) e só separa slot vazio de slot com dados.
     */
    uint8_t odyProbe()
    {
      uint8_t sample[32];
      OD::cartOn();
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = OD::readData(oscr::ody::kBase + i);
      OD::cartOff();
      return oscr::ody::classify(sample, sizeof sample);
    }
    void odyRead(uint16_t mapper, uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      OD::ody2mapper = uint8_t(mapper);                                 // o mesmo campo que o `setCart` do OSCR copia da base (D226)
      OD::ody2size = oscr::ody::sizeIndex(kb);                          // índice da tabela `romSizes` do núcleo: 2, 4, 8, 12 ou 16 KB
      OD::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha
    }

    /**
     * Pokémon Mini (F-20, D227): a leitura chama o `readROM` do OSCR (sempre 512 KB); única mudança no núcleo: o `matchCRC` final sob `#if !OSCR_DUMPER`.
     * O núcleo pede 3,3 V (`setVoltage(k3V3)`); o slot SNES é 5 V fixo, então o adaptador precisa do próprio regulador (docs/planos/adaptadores.md#adaptador-pokemini).
     * O fork não confere assinatura: a sondagem lê 32 bytes de $2100 com o `readData` do OSCR (trava A10 a A20 com HALE e A0 a A9 com LALE) e só separa slot vazio de slot com dados.
     */
    uint8_t pkmProbe()
    {
      uint8_t sample[32];
      PK::cartOn();
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = PK::readData(oscr::pkm::kBase + i);
      PK::cartOff();
      return oscr::pkm::classify(sample, sizeof sample);
    }
    void pkmRead()
    {
      OSCR::Cores::fromCRDB = false;
      PK::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha (D227)
    }

    /**
     * V.Smile (F-20, D228): a leitura chama o `readROM` do OSCR com `romSize` = índice da tabela `romSizes` (4, 6, 8 ou 16 MB; 6 MB lê o segundo chip
     * com CSB2, 16 MB o segundo chip do V.Motion com CSB1 e CSB2); única mudança no núcleo: o `matchCRC` final sob `#if !OSCR_DUMPER`.
     * O núcleo pede 3,3 V (`setVoltage(k3V3)`); o slot SNES é 5 V fixo, então o adaptador precisa do próprio regulador (docs/planos/adaptadores.md#adaptador-vsmile).
     * O fork não confere assinatura: a sondagem lê 16 palavras do início do primeiro chip com o `read_rom_word` do OSCR e só separa slot vazio de slot com dados.
     */
    uint8_t vsmProbe()
    {
      uint8_t sample[32];
      VS::cartOn();
      for (uint8_t i = 0; i < 16; i++)
      {
        uint16_t w = VS::read_rom_word(oscr::vsm::kBase + i);
        sample[i * 2] = uint8_t(w >> 8); sample[i * 2 + 1] = uint8_t(w);   // a ordem em que o `readROM` grava
      }
      VS::cartOff();
      return oscr::vsm::classify(sample, sizeof sample);
    }
    void vsmRead(uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      OSCR::Cores::romSize = oscr::vsm::sizeIndex(kb);                  // índice da tabela `romSizes` do núcleo: 4, 6, 8 ou 16 MB
      VS::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha
    }

    /**
     * MSX (F-20, D230): a leitura da ROM chama o `readROM` do OSCR, a do save o `readRAM` e a gravação o `writeRAM`, com `msxmapper` (0 a 14),
     * `romSize` e `sramSize` = índices das tabelas do núcleo, que saem do que o PC informou (o menu "Set Mapper" do OSCR lê a faixa de cada mapper
     * de um arquivo do cartão SD; a mesma tabela está em `MsxCore.h`). Única mudança no núcleo: o `matchCRC` final sob `#if !OSCR_DUMPER`.
     * O `writeRAM` do OSCR não liga o cartucho (no menu, o `readROM` ou o `readRAM` já tinham configurado as portas): o fork chama `cartOn` antes.
     * A sondagem usa o `setCS` do OSCR (procura o cabeçalho "AB" em $4000 com cada chip select) e lê 32 bytes de $4000 com o `readData` do OSCR.
     * CLOCK (D230, como o PHI2 do Atari 8 bits na D213): o núcleo segura PH1 alto, mas PH1 não chega ao slot SNES; o CLOCK do cartucho vai ao pino 57 do slot
     * (CLK1 do Si5351, parte fixa das placas) e a costura programa o CLK1 em 3,579545 MHz (o relógio do Z80 do MSX) enquanto o núcleo roda.
     */
    void msxClock(bool on)
    {
#if defined(ENABLE_CLOCKGEN)
      if (!a8ClockPresent()) return;
      if (on) OSCR::ClockGen::clockgen.set_freq(357954500ULL, SI5351_CLK1);   // unidade da biblioteca: 0,01 Hz
      OSCR::ClockGen::clockgen.output_enable(SI5351_CLK1, on ? 1 : 0);
#else
      (void)on;
#endif
    }
    uint8_t msxProbe(bool & header)
    {
      uint8_t sample[32];
      msxClock(true);
      MX::cartOn();
      MX::setCS();
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = MX::readData(0x4000 + i);
      MX::disableCS();
      MX::cartOff();
      msxClock(false);
      header = oscr::msx::hasHeader(sample, sizeof sample);
      return oscr::msx::classify(sample, sizeof sample);
    }
    void msxRead(uint16_t mapper, uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      MX::msxmapper = uint8_t(mapper);
      OSCR::Cores::romSize = oscr::msx::romIndex(mapper, kb);           // índice da tabela `romSizes` do núcleo
      msxClock(true);
      MX::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha
      msxClock(false);
    }
    void msxReadSave(uint16_t mapper, uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      MX::msxmapper = uint8_t(mapper);
      OSCR::Cores::sramSize = oscr::msx::ramIndex(mapper, kb);          // índice da tabela `ramSizes` do núcleo
      msxClock(true);
      MX::readRAM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha
      msxClock(false);
    }
    void msxWriteSave(uint16_t mapper, uint16_t kb)
    {
      MX::msxmapper = uint8_t(mapper);
      OSCR::Cores::sramSize = oscr::msx::ramIndex(mapper, kb);
      msxClock(true);
      MX::cartOn();
      MX::writeRAM();                                                   // a conferência é do PC: relê o save e compara
      MX::cartOff();
      msxClock(false);
    }

    /**
     * ColecoVision (F-20, D201; D215): a leitura chama o `readROM` do OSCR (índice em `romSize`); única mudança no núcleo: o `matchCRC` final (base do cartão SD,
     * inexistente aqui) sob `#if !OSCR_DUMPER`. A sondagem lê 32 bytes de $8000 com `readData` do OSCR. O núcleo não detecta o cartucho: a classificação é de `ColvCore.h`.
     */
    uint8_t colvProbe()
    {
      uint8_t sample[32];
      CV::cartOn();
      for (uint8_t i = 0; i < sizeof sample; i++) sample[i] = CV::readData(oscr::colv::kBase + i);
      CV::cartOff();
      return oscr::colv::classify(sample, sizeof sample);
    }
    void colvRead(uint16_t kb)
    {
      OSCR::Cores::fromCRDB = false;
      OSCR::Cores::romSize = oscr::colv::sizeIndex(kb);                 // índice da tabela `COL` do núcleo
      CV::readROM();                                                    // liga e desliga o cartucho e abre/fecha o "arquivo" sozinha (D215: reuso do OSCR)
    }

    /**
     * Nintendo 64 (D158): lê os 64 primeiros bytes da ROM (`idCart` do OSCR: CRC1, código, versão e nome) e classifica o cabeçalho z64. O `getCartInfo` do OSCR
     * consulta a base de dados do cartão SD para achar tamanho e tipo de save; aqui o PC consulta a dele e manda os dois nos comandos (`prg_kb` = MB, `mapper` = tipo de save).
     */
    uint8_t n64Probe()
    {
      N6::cartOn();
      N6::idCart();
      N6::cartOff();
      return oscr::n64::classify(OSCR::Storage::Shared::buffer, 64);
    }

    bool isSega(uint8_t system) { return system == oscr::SYS_SMS || system == oscr::SYS_GG || system == oscr::SYS_SG1000; }
    // Cartucho de RAM de backup do Sega CD: `getCartInfo` (via `detect`, que `prepare` chama) deixou `bramSize` (F-16, D179).
    bool isMdBram(uint8_t system) { return system == oscr::SYS_MD && MD::bramSize > 0; }

    /// Lion King 3, Pokémon Stadium (32 KiB) e Star Odyssey (256 KiB; F-16, D181 e D183): troca de banco a cada pedaço (MdBank.h). Não vem do OSCR e não foi conferido em cartucho.
    void readBanked(uint16_t mapper, uint16_t kb)
    {
      namespace B = OSCR::Dumper::MdBank;
      MD::cartOn();
      OSCR::Storage::Shared::sharedFile.open("rom", O_WRONLY | O_CREAT | O_TRUNC);
      for (uint32_t bank = 0; bank < B::chunks(mapper, kb); bank++)
      {
        MD::dataOut();
        MD::writeWord(B::regWordAddr(mapper), B::regValue(mapper, bank));
        MD::dataIn();
        for (uint32_t w = 0; w < B::chunkBytes(mapper) / 2; w += 256)
        {
          for (uint16_t i = 0; i < 256; i++)
          {
            uint16_t word = MD::readWord(w + i);
            OSCR::Storage::Shared::buffer[2 * i] = word >> 8;
            OSCR::Storage::Shared::buffer[2 * i + 1] = word & 0xFF;
          }
          OSCR::Storage::Shared::writeBuffer();
        }
      }
      OSCR::Storage::Shared::close();
      MD::cartOff();
    }
    uint8_t segaConsole(uint8_t system) { return system == oscr::SYS_GG ? oscr::sms::kGg : system == oscr::SYS_SG1000 ? oscr::sms::kSg : oscr::sms::kSms; }
    bool segaOptionsOk(uint8_t system, uint16_t adapter, uint16_t kb) { return oscr::sms::mode(segaConsole(system), adapter) != oscr::sms::kBadMode && oscr::sms::sizeKbValid(segaConsole(system), kb); }

    /**
     * Família Sega de 8 bits (SMS, Game Gear, SG-1000; D137): o `getCartInfo` do OSCR lê o cabeçalho "TMR SEGA" em $7FF0, o tamanho (nibble de $7FFF e
     * espelhamento do cabeçalho) e preenche cartSize e fileName; sem cabeçalho ele abria um menu de tamanho, que aqui não existe (`SMS.cpp`, OSCR_DUMPER).
     * `console` (Sms, Gg, Sg) e `adapter` (campo `mapper`) escolhem o modo do núcleo; `sizeKb` (0 = automático) vem do PC e vale sempre. Devolve Sms::kOk, Sms::kNoCart ou Sms::kNoHeader.
     */
    uint8_t smsProbe(uint8_t console, uint16_t adapter, uint16_t sizeKb)
    {
      using namespace OSCR::Cores;
      SM::adapterMode = static_cast<SM::SMSMode>(oscr::sms::mode(console, adapter));
      SM::manRomSizeSelected = false;
      cartSize = 0;
      fileName[0] = 0;
      SM::getCartInfo();

      uint8_t name[8], sample[32];
      SM::cartOn();
      for (uint8_t i = 0; i < 8; i++) name[i] = SM::readByte(0x7FF0 + i);
      for (uint8_t i = 0; i < 32; i++) sample[i] = SM::readByte(i);
      SM::cartOff();

      bool tmr = strcmp_P(fileName, PSTR("TMR SEGA")) == 0;       // também liga o "Fantasy Zone (J)", que o núcleo ajusta
      uint8_t st = oscr::sms::classify(name, sample, sizeof sample, tmr);
      if (st == oscr::sms::kNoCart) return st;
      if (st == oscr::sms::kNoHeader) strlcpy_P(fileName, PSTR("SMS"), 8);
      cartSize = oscr::sms::romBytes(st, cartSize, sizeKb);
      return st;
    }

    /**
     * Seletor de tensão do cartucho (D138): D18 = PD3, nível baixo liga o P-MOSFET Q4 (5 V nos slots), nível alto ou solto deixa o LDO em 3,3 V.
     * O 5 V dos slots fica sempre ligado (não há mais chave para cortá-lo por software). Placa sem o seletor: o pino fica sem ligação e isto não tem efeito.
     *  OSCR_VOLT_SELECT  1 = placa com o seletor de tensão.
     */
#ifndef OSCR_VOLT_SELECT
# define OSCR_VOLT_SELECT 0
#endif
#ifndef OSCR_VOLT_SETTLE_MS
# define OSCR_VOLT_SETTLE_MS 200                                        // espera depois de mudar a tensão (o rail de 3,3 V cai pela carga do Q5 e do cartucho)
#endif
    /** Padrão da compilação; o perfil guardado na EEPROM (BOARD, D162) vale por cima, para uma imagem só servir as placas com e sem o seletor. */
    bool voltSelect = OSCR_VOLT_SELECT;
    bool boardStored = false;                                           // há perfil válido na EEPROM
    constexpr int kBoardEeprom = 4064;                                  // o OSCR só usa o endereço 0 (folderIncrement)
    constexpr uint8_t kBoardMagic = 0xB5, kBoardVer = 1;                // [magic, versão, flags, ~flags]

    /** Solta todos os pinos de sinal dos slots (entrada, sem pull-up). Mudar a tensão com o Mega ainda dirigindo os pinos alimentaria o cartucho por eles.
     *  Não toca na serial (PE0/PE1), no I²C (PD0/PD1), no seletor (D18 = PD3) nem nos LEDs (PB4 a PB7). */
    void releaseCartPins()
    {
      DDRA = 0; PORTA = 0;                      // D22 a D29
      DDRC = 0; PORTC = 0;                      // D30 a D37
      DDRF = 0; PORTF = 0;                      // A0 a A7
      DDRK = 0; PORTK = 0;                      // A8 a A15
      DDRL = 0; PORTL = 0;                      // D42 a D49
      DDRE &= ~(_BV(PE3) | _BV(PE4) | _BV(PE5)); PORTE &= ~(_BV(PE3) | _BV(PE4) | _BV(PE5));                 // D5, D2, D3
      DDRG &= ~(_BV(PG0) | _BV(PG1) | _BV(PG2) | _BV(PG5)); PORTG &= ~(_BV(PG0) | _BV(PG1) | _BV(PG2) | _BV(PG5));   // D41, D40, D39, D4
      DDRH &= ~(_BV(PH0) | _BV(PH1) | _BV(PH3) | _BV(PH4) | _BV(PH5) | _BV(PH6));
      PORTH &= ~(_BV(PH0) | _BV(PH1) | _BV(PH3) | _BV(PH4) | _BV(PH5) | _BV(PH6));                            // D17, D16, D6, D7, D8, D9
      DDRJ &= ~(_BV(PJ0) | _BV(PJ1)); PORTJ &= ~(_BV(PJ0) | _BV(PJ1));                                         // D15, D14
      DDRD &= ~_BV(PD7); PORTD &= ~_BV(PD7);                                                                    // D38
      DDRB &= ~_BV(PB3); PORTB &= ~_BV(PB3);                                                                    // D50 (/CART), sem pull-up
    }

    // Sobe em 3,3 V, o estado seguro do hardware (com o Mega em reset o pino solto e o pull-up do gate dão 3,3 V): a CLI e a GUI abrem a porta, o Mega reinicia
    // e um cartucho de 3,3 V no slot não pode receber 5 V antes de o host escolher. O host pede 5 V (padrão, D138) quando o usuário não escolheu 3,3 V.
    uint8_t cartVolt = voltSelect ? oscr::volt::kVolt3V3 : oscr::volt::kVoltNone;

    /** Lê o perfil da placa da EEPROM (quatro bytes: magic, versão, flags, flags invertidos). Sem perfil válido, fica o padrão da compilação. */
    void loadBoardProfile()
    {
      uint8_t b[4];
      for (uint8_t i = 0; i < 4; i++) b[i] = EEPROM.read(kBoardEeprom + i);
      boardStored = b[0] == kBoardMagic && b[1] == kBoardVer && uint8_t(~b[2]) == b[3] && !(b[2] & ~oscr::BOARD_VOLT_SELECT);
      if (boardStored) voltSelect = b[2] & oscr::BOARD_VOLT_SELECT;
      cartVolt = voltSelect ? oscr::volt::kVolt3V3 : oscr::volt::kVoltNone;
    }
    // Fator de correção do Si5351 (CLOCK, F-3), em ppb, guardado na EEPROM: [magic, versão, 4 bytes do fator (LE), soma de conferência]. Lê o do endereço 4056 a 4062.
    constexpr int kClockEeprom = 4056;
    constexpr uint8_t kClockMagic = 0xC7, kClockVer = 1;
    uint8_t clockCheck(const uint8_t * b) { return uint8_t(b[0] ^ b[1] ^ b[2] ^ b[3] ^ b[4] ^ b[5] ^ 0x5A); }
    bool loadClockPpb(int32_t & ppb)
    {
      uint8_t b[7];
      for (uint8_t i = 0; i < 7; i++) b[i] = EEPROM.read(kClockEeprom + i);
      if (b[0] != kClockMagic || b[1] != kClockVer || b[6] != clockCheck(b)) return false;
      uint32_t v = uint32_t(b[2]) | (uint32_t(b[3]) << 8) | (uint32_t(b[4]) << 16) | (uint32_t(b[5]) << 24);
      int32_t p = int32_t(v);
      if (p > oscr::CLOCK_MAX_PPB || p < -oscr::CLOCK_MAX_PPB) return false;     // EEPROM adulterada: ignora, vale 0
      ppb = p;
      return true;
    }
    void saveClockPpb(int32_t ppb)
    {
      uint8_t b[7] = {kClockMagic, kClockVer, uint8_t(ppb), uint8_t(uint32_t(ppb) >> 8), uint8_t(uint32_t(ppb) >> 16), uint8_t(uint32_t(ppb) >> 24), 0};
      b[6] = clockCheck(b);
      for (uint8_t i = 0; i < 7; i++) EEPROM.update(kClockEeprom + i, b[i]);
    }
    oscr::SelfTestReport * selfTestOut = nullptr;   // preenchido por noteSelfTest() durante o SELFTEST
    bool voltChosen = false;                    // o usuário escolheu 3,3 V (cartucho marcado como 3,3 V): o host pede confirmação antes de subir para 5 V

    /** Pino do seletor (D18 = PD3): alto = Q4 aberto = 3,3 V; baixo = Q4 conduz = 5 V. Com o Mega em reset o pino solto e o pull-up do gate dão 3,3 V. */
    void setVoltPin(uint8_t volt)
    {
      if (!voltSelect) return;
      DDRD |= _BV(PD3);
      if (volt == oscr::volt::kVolt5V) PORTD &= ~_BV(PD3);
      else PORTD |= _BV(PD3);
    }

    /**
     * SNES: o `getCartInfo` do OSCR lê o cabeçalho ($FFB0) e preenche romSize (Mbit), numBanks, sramSize (Kbit), romChips, romType e checksum
     * (sem a base de dados: tamanhos fora do padrão, como 6 MB, vêm do PC pela opção `prg_kb`). `sizeKb` > 0 troca o tamanho da ROM.
     * `forcedType` (F-2, D164; códigos de SnesType.h, 0 = pelo cabeçalho) impõe o tipo de ROM e recalcula os bancos. Com tipo e tamanho informados, um cabeçalho
     * ilegível não recusa o cartucho (repro multijogo, Sufami Turbo): o PC sabe o que está lendo.
     * Devolve 0 = ok, 1 = sem cartucho, 4 = há dados mas o cabeçalho não confere.
     */
    uint8_t snesProbe(uint16_t sizeKb, uint16_t forcedType = 0)
    {
      using namespace OSCR::Cores;
      abortHit = false;
      checksum = 0; romSize = 0; numBanks = 0; sramSize = 0;
      SN::getCartInfo();
      SN::cartOff();
      bool forced = forcedType != 0 && sizeKb != 0;                 // o PC disse tipo e tamanho: o cabeçalho não decide mais nada
      if (abortHit && !forced) return (checksum == 0 || checksum == 0xFFFF) ? 1 : 4;
      if ((romSize == 0 || numBanks < 1) && !forced) return 1;

      if (forcedType)                                             // tipo imposto pelo PC
      {
        romType = OSCR::Dumper::SnesType::romType(forcedType);
        numBanks = OSCR::Dumper::SnesType::numBanks(romType, romSize);
      }
      if (sizeKb)                                                 // tamanho informado pelo usuário/PC (Mbit = KB / 128)
      {
        romSize = sizeKb / 128;
        numBanks = OSCR::Dumper::SnesType::numBanks(romType, romSize);
      }
      return 0;
    }


    namespace NE = OSCR::Cores::NES;

    NE::crdbNESRecord nesRec;                       // no lugar do registro da base de dados: os macros NES_* do núcleo apontam para cá
    uint32_t nesPrgBytes = 0, nesChrBytes = 0, nesRamBytes = 0;
    char nesName[24];

    bool isNes(uint8_t system) { return system == oscr::SYS_NES || system == oscr::SYS_FAMICOM; }

    bool allSame(uint8_t const * p, uint8_t n) { for (uint8_t i = 1; i < n; i++) if (p[i] != p[0]) return false; return true; }

    uint8_t log2u(uint16_t v) { uint8_t n = 0; while (v > 1) { v >>= 1; n++; } return n; }

    bool isPow2(uint16_t v) { return v != 0 && (v & (v - 1)) == 0; }

    /** Mapper com PRG-RAM aceita em READ_SAVE/WRITE_SAVE (o mesmo conjunto do firmware próprio). */
    bool nesHasSave(uint16_t m) { return m == 1 || m == 4 || m == 5 || m == 69 || m == 118 || m == 16 || m == 159 || m == 19 || m == 80 || m == 82 || m == 155
                                      || m == 21 || m == 25 || m == 26 || m == 68 || m == 85 || m == 153; }    // 16 e 159: EEPROM serial; 19, 80, 82: RAM da Namco 163 e da Taito X1 (D184); 21, 25, 26, 68, 85, 153: ramo `default` do readRAM (8 KB, D185)

    /**
     * Confere mapper e tamanhos de ROM (KB) contra os limites do protocolo (docs/referencia/protocolo.md, NES/Famicom).
     * Devolve 0 = ok, E_SISTEMA = mapper ou tamanho além do registrador, E_ARGUMENTO = tamanhos inválidos.
     */
    uint16_t nesCheckRom(uint16_t m, uint16_t prg, uint16_t chr)
    {
      bool known = m == 0 || m == 1 || m == 2 || m == 3 || m == 4 || m == 5 || m == 7 || m == 9 || m == 10 || m == 11 || m == 33 || m == 48 || m == 66 || m == 69 || m == 70 || m == 71
                   || m == 75 || m == 78 || m == 79 || m == 87 || m == 118 || m == 206
                   || m == 13 || m == 30 || m == 34 || m == 67 || m == 68 || m == 72 || m == 73 || m == 86 || m == 92 || m == 93 || m == 94 || m == 140 || m == 152 || m == 180 || m == 184
                   || m == 16 || m == 18 || m == 19 || m == 32 || m == 65 || m == 80 || m == 82 || m == 85 || m == 153 || m == 154 || m == 155 || m == 159 || m == 207       // F-14, D184
                   || m == 21 || m == 22 || m == 23 || m == 24 || m == 25 || m == 26;      // VRC2, VRC4 e VRC6: o núcleo escolhe a variante pelo número e por leituras (D185)
      if (!known) return oscr::E_SISTEMA;
      // O núcleo do OSCR conta bancos em potências de 2 (NES_PRG e NES_CHR são expoentes).
      if (prg == 0 || prg % 16 != 0 || chr % 8 != 0 || !isPow2(prg / 16) || (chr && !isPow2(chr / 8))) return oscr::E_ARGUMENTO;
      if ((m == 2 || m == 7 || m == 71 || m == 13 || m == 30 || m == 73 || m == 93 || m == 94 || m == 180 || m == 153) && chr != 0) return oscr::E_ARGUMENTO;     // CHR-RAM
      if ((m == 79 || m == 87 || m == 78 || m == 75 || m == 70 || m == 33 || m == 48 || m == 118 || m == 206 || m == 67 || m == 68 || m == 72 || m == 92 || m == 86 || m == 140 || m == 152 || m == 184 || m == 16 || m == 159 || m == 18 || m == 32 || m == 65 || m == 80 || m == 82 || m == 154 || m == 207 || (m >= 21 && m <= 26)) && chr == 0) return oscr::E_ARGUMENTO;   // CHR-ROM
      if ((m == 7 || m == 11 || m == 66 || m == 79 || m == 34 || m == 86 || m == 140 || m == 13) && prg % 32 != 0) return oscr::E_ARGUMENTO;
      if (m == 21 && chr != 128 && chr != 256) return oscr::E_ARGUMENTO;     // o núcleo separa VRC4a (128 KB) de VRC4c (256 KB) pelo tamanho do CHR
      if (((m == 0 || m == 3) && prg > 32) || ((m == 1 || m == 155) && (prg > 256 || chr > 128)) || (m == 4 && (prg > 512 || chr > 256)) || ((m == 9 || m == 10) && chr > 128) || (m == 69 && chr > 256)) return oscr::E_SISTEMA;
      if ((m == 9 && prg > 128) || (m == 10 && prg > 256) || (m == 11 && (prg > 128 || chr > 128))
          || (m == 66 && (prg > 128 || chr > 32)) || (m == 69 && prg > 512) || (m == 5 && prg > 1024)
          || ((m == 33 || m == 48) && (prg > 256 || chr > 256)) || (m == 70 && (prg > 256 || chr > 128)) || (m == 75 && (prg > 128 || chr > 128))
          || (m == 78 && (prg > 128 || chr > 128)) || (m == 79 && (prg > 64 || chr > 64)) || (m == 87 && (prg > 32 || chr > 32))
          || (m == 118 && (prg > 512 || chr > 256)) || (m == 206 && (prg > 128 || chr > 64))
          || (m == 30 && prg > 512) || (m == 13 && prg > 32) || (m == 34 && (prg > 512 || chr > 64)) || (m == 67 && (prg > 128 || chr > 128)) || (m == 68 && (prg > 256 || chr > 256))
          || (m == 72 && (prg > 128 || chr > 128)) || (m == 92 && (prg > 256 || chr > 128)) || (m == 73 && prg > 128) || (m == 86 && (prg > 128 || chr > 64))
          || ((m == 93 || m == 94 || m == 180) && prg > 128) || (m == 140 && (prg > 128 || chr > 128)) || (m == 152 && (prg > 128 || chr > 128))
          || (m == 184 && (prg > 32 || chr > 32))
          || ((m == 16 || m == 159 || m == 18 || m == 19 || m == 65) && (prg > 256 || chr > 256)) || (m == 32 && (prg > 256 || chr > 128))
          || ((m == 80 || m == 82) && (prg > 128 || chr > 256)) || (m == 207 && (prg > 256 || chr > 128)) || (m == 85 && (prg > 512 || chr > 128))
          || (m == 153 && prg > 512) || (m == 154 && (prg > 128 || chr > 128))
          || ((m == 21 || m == 22 || m == 23 || m == 24 || m == 25 || m == 26) && prg > 256) || ((m == 22 || m == 24) && chr > 128) || ((m == 21 || m == 23 || m == 25 || m == 26) && chr > 256)) return oscr::E_SISTEMA;     // limites dos comentários do núcleo (readPRG/readCHR do NES.cpp)
      return 0;
    }

    /**
     * NES/Famicom: o cartucho não tem cabeçalho, então mapper e tamanhos vêm do PC (sem a base de dados do OSCR).
     * `mapper` 0 e `prgKb` 0 = automático (NROM: 16 ou 32 KB pelo espelhamento). Em modo save, `prgKb` é a RAM em KB (0 = 8).
     * Monta o registro do núcleo (`nesRec`, com o cabeçalho iNES sintético) e confere o MMC6. Deve rodar dentro de `runCore`.
     * Devolve 0 = ok, ou o código de erro do protocolo (E_SEM_CARTUCHO, E_SISTEMA, E_ARGUMENTO, E_SEM_SAVE).
     */
    uint16_t nesProbe(bool forSave, uint16_t m, uint16_t prgKb, uint16_t chrKb)
    {
      using namespace OSCR::Cores;
      uint8_t a[64], b[64], ch[64], mid[16], vec[16];

      NE::cartOn();
      for (uint8_t i = 0; i < 64; i++) { a[i] = NE::read_prg_byte(0x8000 + i); b[i] = NE::read_prg_byte(0xC000 + i); ch[i] = NE::read_chr_byte(i); }
      for (uint8_t i = 0; i < 16; i++) { mid[i] = NE::read_prg_byte(0xA000 + i); vec[i] = NE::read_prg_byte(0xFFC0 + i); }   // F-15 (D173): mais janelas, incluindo os vetores
      if (oscr::nes::cartAbsent(a, 64, mid, 16, b, 64, vec, 16)) return oscr::E_SEM_CARTUCHO;

      nesRec = NE::crdbNESRecord{};
      NE::romDetail = &nesRec;
      NE::mmc6 = false;
      NE::flashfound = false;
      fromCRDB = false;
      nesRec.mapper = m;
      nesPrgBytes = nesChrBytes = nesRamBytes = 0;

      if (forSave)
      {
        if (!nesHasSave(m)) return oscr::E_SEM_SAVE;
        uint16_t ram = prgKb ? prgKb : 8;
        bool internal128 = m == 19 && ram == 1;                       // Namco 163 sem SRAM: os 128 bytes de RAM interna do chip (o núcleo lê com NES_RAM == 2)
        if (!internal128 && ram != 8 && !((m == 1 || m == 5) && (ram == 16 || ram == 32))) return oscr::E_ARGUMENTO;     // 16/32 KB só no MMC1 (SOROM/SXROM) e no MMC5
        nesRec.ram = internal128 ? 2 : log2u(ram / 4);                // 8 KB = 1, 16 KB = 2, 32 KB = 3 (ramSizes do núcleo)
        nesRec.prg = 0;
        NE::checkStatus();                                            // preenche ramsize; no MMC6 acha a RAM de 1 KB; no mapper 82 são 5 KB
        nesRamBytes = uint32_t(nesRec.ramsize) * 1024UL;
        if (m == 16) nesRamBytes = 256;                               // EEPROM serial 24C02 (D184)
        else if (m == 159) nesRamBytes = 128;                         // 24C01
        else if (m == 80 || internal128) nesRamBytes = 128;           // Taito X1-005: 128 bytes espelhados em $7F00; RAM interna da Namco 163
        snprintf(nesName, sizeof nesName, "mapper %u", unsigned(m));
        return 0;
      }

      uint16_t prg, chr;
      if (m == 0 && prgKb == 0)                                       // automático: NROM
      {
        prg = memcmp(a, b, 64) == 0 ? 16 : 32;
        chr = (allSame(ch, 64) && (ch[0] == 0xFF || ch[0] == 0x00)) ? 0 : 8;
        strlcpy(nesName, "NROM (mapper 0)", sizeof nesName);
      }
      else
      {
        prg = prgKb; chr = chrKb;
        uint16_t rc = nesCheckRom(m, prg, chr);
        if (rc) return rc;
        snprintf(nesName, sizeof nesName, "mapper %u", unsigned(m));
      }

      nesRec.prg = log2u(prg / 16);
      nesRec.chr = chr ? log2u(chr / 4) : 0;
      nesRec.ram = 0;
      NE::checkStatus();
      nesPrgBytes = uint32_t(prg) * 1024UL;
      nesChrBytes = uint32_t(chr) * 1024UL;

      uint8_t * h = nesRec.iNES;                                      // cabeçalho iNES sintético: tamanhos e mapper; espelhamento e bateria ficam 0
      h[0] = 'N'; h[1] = 'E'; h[2] = 'S'; h[3] = 0x1A;
      h[4] = uint8_t(prg / 16); h[5] = uint8_t(chr / 8);
      h[6] = uint8_t((m & 0x0F) << 4); h[7] = uint8_t(m & 0xF0);
      return 0;
    }

    /** Backend dos núcleos do OSCR: SNES, NES/Famicom, Mega Drive, Game Boy Advance e Game Boy/Color. */
    class CoreBackend : public oscr::Backend
    {
    public:
      bool volt_select() override { return voltSelect; }

      // Perfil da placa (D162): guarda na EEPROM (update: só grava o que mudou) e vale já. Com o seletor: sobe em 3,3 V (estado seguro) e o host pede 5 V depois;
      // sem o seletor: o D18 volta a ser entrada, solta.
      bool board_supported() override { return true; }
      bool board_get(uint8_t & flags) override { flags = voltSelect ? oscr::BOARD_VOLT_SELECT : 0; return boardStored; }
      bool board_set(uint8_t flags, uint16_t & err) override
      {
        if (flags & ~oscr::BOARD_VOLT_SELECT) { err = oscr::E_ARGUMENTO; return false; }
        EEPROM.update(kBoardEeprom, kBoardMagic); EEPROM.update(kBoardEeprom + 1, kBoardVer);
        EEPROM.update(kBoardEeprom + 2, flags); EEPROM.update(kBoardEeprom + 3, uint8_t(~flags));
        boardStored = true;
        bool sel = flags & oscr::BOARD_VOLT_SELECT;
        if (sel != voltSelect)
        {
          releaseCartPins();
          voltSelect = sel;
          voltChosen = false;
          if (sel) { cartVolt = oscr::volt::kVolt3V3; setVoltPin(cartVolt); delay(OSCR_VOLT_SETTLE_MS); }
          else { cartVolt = oscr::volt::kVoltNone; DDRD &= ~_BV(PD3); PORTD &= ~_BV(PD3); }
        }
        return true;
      }

      // Seletor 3,3 V/5 V (D138): solta os pinos de sinal, muda o D18 e espera o rail assentar. O 5 V não é cortado: o cartucho continua alimentado,
      // por isso o host só pede 5 V depois do alerta e da confirmação, e o usuário troca o cartucho com o USB desligado.
      bool cart_voltage(uint8_t volt, uint16_t & err) override
      {
        if (!voltSelect || (volt != oscr::volt::kVolt3V3 && volt != oscr::volt::kVolt5V)) { err = oscr::E_COMANDO; return false; }
        voltChosen = volt == oscr::volt::kVolt3V3;
        if (cartVolt == volt) return true;
        releaseCartPins();
        cartVolt = volt;
        setVoltPin(volt);
        delay(OSCR_VOLT_SETTLE_MS);
        return true;
      }
      // Relógio do Si5351 (F-3). As chamadas à biblioteca são as do `clkcal` do OSCR (ClockGen.cpp): `set_correction` e, para o teste, PLL fixo e as três saídas
      // (CLK0 4 MHz = EXT, CLK1 1 MHz = CPU, CLK2 3,072 MHz = CIC do SNES). O fator em vigor no boot vem de `clockOffset()`.
#if defined(ENABLE_CLOCKGEN)
      bool clock_supported() override { return true; }
      bool clock(uint8_t action, int32_t ppb, oscr::ClockInfo & out, uint16_t & err) override
      {
        bool present = OSCR::ClockGen::initialize();   // módulo ligado depois do boot, ou que parou de responder: confere de novo (D241)
        int32_t cur = 0;
        bool stored = loadClockPpb(cur);
        if (action != oscr::CLOCK_STATUS && !present) { err = oscr::E_CARTUCHO_IO; return false; }
        if (action == oscr::CLOCK_SET)
        {
          saveClockPpb(ppb); stored = true; cur = ppb;
          OSCR::ClockGen::clockgen.set_correction(ppb, SI5351_PLL_INPUT_XO);
          OSCR::ClockGen::clockgen.set_correction(ppb, SI5351_PLL_INPUT_CLKIN);
        }
        if (action == oscr::CLOCK_TEST_ON || (action == oscr::CLOCK_SET && clockTest))     // com o teste ligado, o fator novo vale nas saídas já
        {
          OSCR::ClockGen::clockgen.set_pll(SI5351_PLL_FIXED, SI5351_PLLA);
          OSCR::ClockGen::clockgen.set_pll(SI5351_PLL_FIXED, SI5351_PLLB);
          OSCR::ClockGen::clockgen.pll_reset(SI5351_PLLA);
          OSCR::ClockGen::clockgen.pll_reset(SI5351_PLLB);
          OSCR::ClockGen::clockgen.set_freq(400000000ULL, SI5351_CLK0);
          OSCR::ClockGen::clockgen.set_freq(100000000ULL, SI5351_CLK1);
          OSCR::ClockGen::clockgen.set_freq(307200000ULL, SI5351_CLK2);
          OSCR::ClockGen::clockgen.output_enable(SI5351_CLK1, 1);
          OSCR::ClockGen::clockgen.output_enable(SI5351_CLK2, 1);
          OSCR::ClockGen::clockgen.output_enable(SI5351_CLK0, 1);
          clockTest = true;
        }
        if (action == oscr::CLOCK_TEST_OFF) { OSCR::ClockGen::stop(); clockTest = false; }
        out.present = present; out.stored = stored; out.ppb = present ? OSCR::ClockGen::clockgen.get_correction(SI5351_PLL_INPUT_XO) : cur; out.test = clockTest;
        return true;
      }
#endif
      // Autoteste do OSCR (cores/SelfTest.cpp, chamado direto): precisa do slot vazio. Os achados chegam por noteSelfTest().
      bool selftest_supported() override { return true; }
      bool selftest(oscr::SelfTestReport & r, uint16_t & err) override
      {
        releaseCartPins();
        selfTestOut = &r;
        bool ok = runCore([] { OSCR::Cores::SelfTest::run(); }, true);   // erros suaves: cada achado só marca o erro e o teste segue
        selfTestOut = nullptr;
        releaseCartPins();
        if (!ok) { err = oscr::E_CARTUCHO_IO; return false; }
        return true;
      }

      void volt_info(oscr::VoltInfo & p) override
      {
        p.select = voltSelect;
        p.volt = cartVolt;
        p.chosen = voltChosen;
      }

      // bit1: Si5351 achado no boot ou no último `ClockGen::initialize()` (D247; `exists()`, sem I²C: o `initialize()` pararia as saídas de teste do CLOCK);
      // bit3: o firmware aceita WRITE_ROM (flash repro); bit4: programador de flash genérico (sistema 7, ERASE)
      uint8_t flags() override { return (OSCR::ClockGen::exists() ? 2 : 0) | 8 | 16; }
      uint64_t systems() override { return (1ULL << oscr::SYS_SNES) | (1ULL << oscr::SYS_NES) | (1ULL << oscr::SYS_FAMICOM) | (1ULL << oscr::SYS_MD) | (1ULL << oscr::SYS_GBA) | (1ULL << oscr::SYS_GB) | (1ULL << oscr::SYS_SMS) | (1ULL << oscr::SYS_GG) | (1ULL << oscr::SYS_SG1000) | (1ULL << oscr::SYS_N64) | (1ULL << oscr::SYS_COLV) | (1ULL << oscr::SYS_NGP) | (1ULL << oscr::SYS_VEC) | (1ULL << oscr::SYS_A26) | (1ULL << oscr::SYS_A52) | (1ULL << oscr::SYS_A78) | (1ULL << oscr::SYS_A8) | (1ULL << oscr::SYS_LYNX) | (1ULL << oscr::SYS_JAG) | (1ULL << oscr::SYS_ARC) | (1ULL << oscr::SYS_RCA2) | (1ULL << oscr::SYS_PYU) | (1ULL << oscr::SYS_SV) | (1ULL << oscr::SYS_PV) | (1ULL << oscr::SYS_BALLY) | (1ULL << oscr::SYS_CHF) | (1ULL << oscr::SYS_ODY2) | (1ULL << oscr::SYS_POKE) | (1ULL << oscr::SYS_VSMILE) | (1ULL << oscr::SYS_MSX) | (1ULL << oscr::SYS_FLASH); }
      bool supports(uint8_t system) override { return system == oscr::SYS_SNES || isNes(system) || system == oscr::SYS_MD || system == oscr::SYS_GBA || system == oscr::SYS_GB || isSega(system) || system == oscr::SYS_N64 || system == oscr::SYS_COLV || system == oscr::SYS_NGP || system == oscr::SYS_VEC || system == oscr::SYS_A26 || system == oscr::SYS_A52 || system == oscr::SYS_A78 || system == oscr::SYS_A8 || system == oscr::SYS_LYNX || system == oscr::SYS_JAG || system == oscr::SYS_ARC || system == oscr::SYS_RCA2 || system == oscr::SYS_PYU || system == oscr::SYS_SV || system == oscr::SYS_PV || system == oscr::SYS_BALLY || system == oscr::SYS_CHF || system == oscr::SYS_ODY2 || system == oscr::SYS_POKE || system == oscr::SYS_VSMILE || system == oscr::SYS_MSX || system == oscr::SYS_FLASH; }
      bool streams() override { return true; }

      // GBA: o campo `mapper` do protocolo é o tipo de save (numeração do OSCR); valores acima de 6 são recusados.
      // SNES: `prg_kb` é o tamanho da ROM em KB (0 = pelo cabeçalho).
      // NES/Famicom: mapper, PRG e CHR em KB (0 = NROM automático); nos saves, `prg_kb` é a RAM em KB (0 = 8).
      void set_options(uint16_t mapper, uint16_t prg, uint16_t chr) override { optMapper = mapper; optPrgKb = prg; optChrKb = chr; }

      void detect(uint8_t system, oscr::DetectInfo & out) override
      {
        if (!supports(system)) { out.status = 2; return; }

        if (system == oscr::SYS_FLASH)
        {
          // Programador genérico: as opções (chip, tamanho, tipo) vêm no próprio DETECT; o "nome" é o ID lido do chip.
          uint16_t chip = optMapper, prg = optPrgKb, chr = optChrKb;
          if (FlashProg::checkDetect(chip, prg, chr)) { out.status = 2; return; }
          uint8_t st = 1; uint32_t size = 0;
          out.name[0] = 0;
          if (chip == FlashProg::kMdCart)
          {
            // Flash do cartucho de Mega Drive: o nome é "CHIP FFDD" (fabricante e dispositivo). Status 0 = chip da tabela; 1 = ID desconhecido
            // (o nome traz "?" e o ID lido, para o PC mostrar). A sondagem escreve comandos de ID no cartucho (ROM de máscara os ignora).
            uint16_t rc = oscr::E_FLASH;
            bool ranMd = runCore([&] { rc = MdFlash::identify(out.name, size); MD::cartOff(); });
            out.status = (ranMd && rc == 0) ? 0 : 1;
            out.rom_size = size;
            out.save_size = 0; out.save_type = 0;
            return;
          }
          bool ran = runCore([&] { st = FlashProg::detect(chip, prg, chr, out.name, size); OSCR::Cores::SNES::cartOff(); });
          out.status = ran ? st : 1;
          out.rom_size = size;
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_GBA)
        {
          uint8_t st = 1;
          bool ran = runCore([&st] { st = gbaProbe(0); });
          if (!ran && st == 1) { out.status = 1; return; }
          out.status = st;
          if (st == 1) return;
          out.rom_size = OSCR::Cores::cartSize;
          out.save_size = 32768;                  // o tipo real (SRAM, Flash ou EEPROM) o usuário informa; o cabeçalho não diz
          out.save_type = 255;
          strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
          return;
        }

        if (isNes(system))
        {
          uint16_t rc = oscr::E_SEM_CARTUCHO;
          bool ran = runCore([&rc] { rc = nesProbe(false, 0, 0, 0); NE::cartOff(); });   // o DETECT ignora as opções: NROM automático
          if (!ran || rc != 0) { out.status = rc == oscr::E_SEM_CARTUCHO || !ran ? 1 : 2; return; }
          out.status = 0;
          out.rom_size = 16UL + nesPrgBytes + nesChrBytes;
          out.save_size = 0;                                     // o PC informa mapper e RAM; o cartucho não diz
          out.save_type = 0;
          strlcpy(out.name, nesName, sizeof(out.name));
          return;
        }

        if (system == oscr::SYS_SNES && oscr::snesacc::isAcc(optChrKb))
        {
          // Acessório do SNES (F-10, D178): o Sufami Turbo tem cabeçalho; o GPC não (sem DETECT)
          if (!oscr::snesacc::isSufami(optChrKb)) { out.status = 2; return; }
          uint16_t rc = oscr::E_SEM_CARTUCHO; uint32_t bytes = 0; bool slotB = oscr::snesacc::sufamiSlotB(optChrKb);
          bool ran = runCore([&rc, &bytes, slotB] { rc = SnesAcc::probeSufami(slotB, bytes); OSCR::Cores::ST::cartOff(); });
          out.status = (ran && rc == 0) ? 0 : 1;
          if (out.status != 0) return;
          out.rom_size = bytes;
          out.save_size = 0; out.save_type = 0;
          strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
          return;
        }

        if (system == oscr::SYS_SNES)
        {
          uint8_t st = 1;
          uint16_t kb = optPrgKb, ty = optChrKb;                 // tamanho e tipo forçados (F-2); sem eles, pelo cabeçalho
          if (!OSCR::Dumper::SnesType::valid(ty)) { out.status = 2; return; }
          runCore([&st, kb, ty] { st = snesProbe(kb, ty); });
          out.status = st;
          if (st == 1) return;
          out.rom_size = uint32_t(OSCR::Cores::romSize) * 131072UL;
          out.save_size = uint32_t(OSCR::Cores::sramSize) * 128UL;
          out.save_type = out.save_size ? 1 : 0;
          strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
          return;
        }

        if (system == oscr::SYS_N64)
        {
          uint8_t st = oscr::n64::kNoCart;
          bool ran = runCore([&st] { st = n64Probe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st != oscr::n64::kOk) return;                         // 1 slot vazio; 4 há dados mas o cabeçalho não é de N64
          oscr::n64::formatName(out.name, sizeof(out.name), uint32_t(N6::crc1), OSCR::Cores::cartID, OSCR::Cores::fileName);
          out.rom_size = 0;                                         // o cabeçalho não diz o tamanho: o PC acha pelo CRC1 (base de dados) ou o usuário informa
          out.save_size = 0; out.save_type = 0;                     // nem o tipo de save
          return;
        }

        if (system == oscr::SYS_A8)
        {
          uint8_t st = oscr::a26::kNoCart;
          uint16_t slot = optMapper;
          bool ran = runCore([&st, slot] { st = a8Probe(slot); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::a26::kNoCart) return;
          strlcpy_P(out.name, PSTR("ATARI8"), sizeof(out.name));
          out.rom_size = uint32_t(oscr::atari8::totalKb(slot, optPrgKb)) * 1024UL;     // 0 se slot ou tamanho inválidos
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_JAG)
        {
          uint8_t st = oscr::a26::kNoCart;
          bool ran = runCore([&st] { st = jagProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::a26::kNoCart) return;
          bool mt = false;
          runCore([&mt] { mt = jagMemoryTrack(); }, true);                              // o OSCR faz o mesmo ao entrar no menu (escreve a sequência de ID no cartucho)
          strlcpy_P(out.name, mt ? PSTR("JAGMEMTRACK") : PSTR("JAGUAR"), sizeof(out.name));
          out.rom_size = oscr::jag::sizeIndex(optPrgKb) == oscr::jag::kBad ? 0 : uint32_t(optPrgKb) * 1024UL;   // o cartucho não informa o tamanho: vem do `prg_kb`
          out.save_size = mt ? 0x20000UL : 0; out.save_type = mt ? 5 : 0;                // 5 = o `mapper` do save do Memory Track; a EEPROM não tem como ser detectada
          return;
        }

        if (system == oscr::SYS_LYNX)
        {
          bool found = false;
          bool ran = runCore([&found] { found = lynxProbe(); }, true);                  // sem cartucho o `detectCart` do OSCR dá "erro" (suave): o DETECT só quer saber se achou
          if (!ran) { out.status = 1; return; }
          if (!found) { out.status = oscr::a26::kNoCart; return; }
          out.status = oscr::a26::kOk;
          strlcpy_P(out.name, PSTR("LYNX"), sizeof(out.name));
          out.rom_size = oscr::lynx::totalBytes(LX::lynxBlockSize);
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_A52 || system == oscr::SYS_A78)
        {
          uint8_t st = oscr::a26::kNoCart;
          bool is52 = system == oscr::SYS_A52;
          bool ran = runCore([&st, is52] { st = is52 ? a52Probe() : a78Probe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::a26::kNoCart) return;
          strlcpy_P(out.name, is52 ? PSTR("ATARI5200") : PSTR("ATARI7800"), sizeof(out.name));
          uint16_t kb = is52 ? oscr::atari::a52Kb(optMapper, optPrgKb) : oscr::atari::a78Kb(optMapper, optPrgKb);   // o DETECT leva mapper e prg_kb; combinação inválida deixa o tamanho em 0
          out.rom_size = uint32_t(kb) * 1024UL;
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_A26)
        {
          uint8_t st = oscr::a26::kNoCart;
          bool ran = runCore([&st] { st = a26Probe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::a26::kNoCart) return;
          strlcpy_P(out.name, PSTR("ATARI2600"), sizeof(out.name));
          uint16_t kb = oscr::a26::mapperKb(optMapper);             // o DETECT leva o mapper no quadro; sem mapper válido o tamanho fica 0 (E7 também: 8, 12 ou 16 KB)
          out.rom_size = (kb != oscr::a26::kUnknown) ? uint32_t(kb) * 1024UL : 0;
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_VEC)
        {
          uint8_t st = oscr::vec::kNoCart;
          bool ran = runCore([&st] { st = vecProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::vec::kNoCart) return;
          strlcpy_P(out.name, PSTR("VECTREX"), sizeof(out.name));
          out.rom_size = 0;                                         // o console não diz o tamanho (4 a 64 KB): o PC informa
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_ARC)
        {
          uint8_t st = oscr::arc::kNoCart;
          bool ran = runCore([&st] { st = arcProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::arc::kNoCart) return;
          strlcpy_P(out.name, PSTR("ARCADIA2001"), sizeof(out.name));
          out.rom_size = 0;                                         // o console não diz o tamanho (2 a 8 KB): o PC informa
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_ODY2)
        {
          uint8_t st = oscr::ody::kNoCart;
          bool ran = runCore([&st] { st = odyProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::ody::kNoCart) return;
          strlcpy_P(out.name, PSTR("ODYSSEY2"), sizeof(out.name));
          out.rom_size = oscr::ody::fileBytes(optMapper, optPrgKb);    // o cartucho não diz o tamanho: sai do que o PC informou (0 sem combinação válida)
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_POKE)
        {
          uint8_t st = oscr::pkm::kNoCart;
          bool ran = runCore([&st] { st = pkmProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::pkm::kNoCart) return;
          strlcpy_P(out.name, PSTR("POKEMINI"), sizeof(out.name));
          out.rom_size = oscr::pkm::kRomBytes;                          // o `readROM` do OSCR lê sempre 512 KB
          out.save_size = 0; out.save_type = 0;                         // o save fica no console, não no cartucho
          return;
        }

        if (system == oscr::SYS_MSX)
        {
          uint8_t st = oscr::msx::kNoCart; bool header = false;
          bool ran = runCore([&st, &header] { st = msxProbe(header); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::msx::kNoCart) return;
          strlcpy_P(out.name, header ? PSTR("MSX") : PSTR("MSX (SEM AB)"), sizeof(out.name));
          out.rom_size = oscr::msx::romBytes(optMapper, optPrgKb);      // o cartucho não diz mapper nem tamanho: o DETECT leva os dois (0 sem combinação válida)
          out.save_size = oscr::msx::ramBytes(optMapper, optPrgKb);     // o mesmo campo é o KB do save quando o PC estima a leitura do save
          out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_VSMILE)
        {
          uint8_t st = oscr::vsm::kNoCart;
          bool ran = runCore([&st] { st = vsmProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::vsm::kNoCart) return;
          strlcpy_P(out.name, PSTR("VSMILE"), sizeof(out.name));
          out.rom_size = oscr::vsm::fileBytes(optPrgKb);                // o cartucho não diz o tamanho: sai do que o PC informou (0 sem tamanho válido)
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_CHF)
        {
          uint8_t st = oscr::chf::kNoCart;
          bool ran = runCore([&st] { st = chfProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::chf::kNoCart) return;
          strlcpy_P(out.name, PSTR("CHANNELF"), sizeof(out.name));
          out.rom_size = oscr::chf::fileBytes(optMapper, optPrgKb);    // o cartucho não diz o tamanho: sai do que o PC informou (0 sem tamanho válido)
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_BALLY)
        {
          uint8_t st = oscr::bally::kNoCart;
          bool ran = runCore([&st] { st = ballyProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::bally::kNoCart) return;
          strlcpy_P(out.name, PSTR("BALLY"), sizeof(out.name));
          out.rom_size = 0;                                         // o cartucho não diz o tamanho: o PC informa (2, 4 ou 8 KB)
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_PV)
        {
          uint8_t st = oscr::pv::kNoCart;
          bool ran = runCore([&st] { st = pvProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::pv::kNoCart) return;
          strlcpy_P(out.name, PSTR("CASIOPV1000"), sizeof(out.name));
          out.rom_size = 0;                                         // o console não diz o tamanho: o PC informa (8 ou 16 KB)
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_SV)
        {
          uint8_t st = oscr::sv::kNoCart;
          bool ran = runCore([&st] { st = svProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::sv::kNoCart) return;
          strlcpy_P(out.name, PSTR("SUPERVISION"), sizeof(out.name));
          out.rom_size = 0;                                         // o console não diz o tamanho: o PC informa (32, 64 ou 512 KB)
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_PYU)
        {
          uint8_t st = oscr::pyu::kNoCart;
          bool ran = runCore([&st] { st = pyuProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::pyu::kNoCart) return;
          strlcpy_P(out.name, PSTR("TOMYPYUUTA"), sizeof(out.name));
          out.rom_size = 0;                                         // o console não diz o tamanho: o PC informa (8, 16 ou 32 KB)
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_RCA2)
        {
          uint8_t st = oscr::rca::kNoCart;
          bool ran = runCore([&st] { st = rcaProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::rca::kNoCart) return;
          strlcpy_P(out.name, PSTR("RCASTUDIO2"), sizeof(out.name));
          out.rom_size = 0;                                         // o console não diz o tamanho: o PC informa (1 KB)
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (system == oscr::SYS_NGP)
        {
          uint8_t st = oscr::ngp::kNoCart;
          bool ran = runCore([&st] { st = ngpProbe(0); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::ngp::kNoCart) return;
          out.rom_size = OSCR::Cores::cartSize;                     // 0 se o chip não é conhecido: o PC informa o tamanho
          out.save_size = 0; out.save_type = 0;
          strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
          return;
        }

        if (system == oscr::SYS_COLV)
        {
          uint8_t st = oscr::colv::kNoCart;
          bool ran = runCore([&st] { st = colvProbe(); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::colv::kNoCart) return;
          strlcpy_P(out.name, PSTR("COLECOVISION"), sizeof(out.name));
          out.rom_size = 0;                                         // o console não diz o tamanho (8 a 32 KB): o PC informa
          out.save_size = 0; out.save_type = 0;
          return;
        }

        if (isSega(system))
        {
          if (!segaOptionsOk(system, optMapper, 0)) { out.status = 2; return; }      // o DETECT usa só o adaptador (campo mapper); o tamanho vem no dump
          uint8_t st = oscr::sms::kNoCart, con = segaConsole(system); uint16_t ad = optMapper;
          bool ran = runCore([&st, con, ad] { st = smsProbe(con, ad, 0); });
          if (!ran) { out.status = 1; return; }
          out.status = st;
          if (st == oscr::sms::kNoCart) return;
          out.rom_size = OSCR::Cores::cartSize;                     // com status 4 é a estimativa do núcleo (nibble de $7FFF); o PC informa o tamanho
          out.save_size = oscr::sms::kSramBytes;                    // o cabeçalho não diz se há SRAM: o usuário decide
          out.save_type = 255;
          strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
          return;
        }

        if (system == oscr::SYS_GB)
        {
          uint8_t st = 1;
          runCore([&st] { st = gbProbe(); GB::cartOff(); });
          out.status = st;
          if (st == 1) return;
          out.rom_size = uint32_t(GB::romBanks) * 16384UL;
          out.save_size = gbSaveBytes();
          out.save_type = out.save_size ? 1 : 0;
          strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
          return;
        }

        MD::bramSize = 0; MD::realtec = false;                 // o OSCR só liga; cartucho trocado sem reiniciar deixaria o estado do anterior (D179)
        bool floating = false;
        bool ok = runCore([&floating] { MD::cartOn(); MD::dataIn(); floating = mdBusFloating(); MD::getCartInfo(); MD::cartOff(); });   // a sonda vem antes: depois do `getCartInfo` o cartucho KY deixa de dirigir o barramento
        if (ok && floating) { out.status = mdCartPinLow() ? 4 : 1; return; }   // D246: barramento solto = slot vazio (sem o /CART a v1.0 dava 128 KB "detectados")

        if (ok && OSCR::Dumper::MdExtra::bramSizeValid(MD::bramSize))      // RAM de backup do Sega CD (F-16, D179): não tem ROM de jogo, o save é a RAM
        {
          out.status = 0;
          out.rom_size = 0;
          out.save_size = MD::bramSize;
          out.save_type = OSCR::Dumper::MdExtra::kSaveBram;
          strlcpy(out.name, OSCR::Dumper::MdExtra::kBramName, sizeof(out.name));
          return;
        }

        // O OSCR considera "sem cartucho" um tamanho zero ou absurdo (o maior jogo conhecido tem 10 MB).
        // Sem cabeçalho legível: se o /CART está baixo há cartucho (contato sujo ou mal encaixado): status 4 em vez de 1. Alto: como antes.
        if (!ok || OSCR::Cores::cartSize == 0 || OSCR::Cores::cartSize > 16777216UL) { out.status = mdCartPinLow() ? 4 : 1; return; }

        out.status = 0;
        out.rom_size = OSCR::Cores::cartSize + MD::lockonBytes();     // Sonic & Knuckles com jogo encaixado: o `readROM` do OSCR lê os dois (D180)
        out.save_size = OSCR::Cores::saveType == 4 ? MD::eepSize : OSCR::Cores::sramSize;
        out.save_type = OSCR::Cores::saveType;
        strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
      }

      bool stream_read(uint8_t system, uint8_t kind, oscr::StreamSink & sink, uint16_t & err) override
      {
        if (!supports(system)) { err = oscr::E_SISTEMA; return false; }
        if (system == oscr::SYS_SNES && oscr::snesacc::isAcc(optChrKb)) return accRead(kind, sink, err);

        if (system == oscr::SYS_FLASH)                            // programador genérico: ler o chip inteiro (o conteúdo vai ao PC; "em branco" é conferido lá)
        {
          uint16_t chip = optMapper, prg = optPrgKb;
          if (kind != oscr::KIND_ROM) { err = oscr::E_COMANDO; return false; }
          if (FlashProg::check(chip, prg, optChrKb, 0)) { err = oscr::E_ARGUMENTO; return false; }
          countingSink.inner = &sink; countingSink.bytes = 0;
          activeSink = &countingSink;
          bool ok = runCore([chip, prg] { FlashProg::read(chip, prg); OSCR::Cores::SNES::cartOff(); });
          activeSink = nullptr;
          err = oscr::E_CARTUCHO_IO;
          return ok && countingSink.bytes > 0;
        }

        if (system == oscr::SYS_GB && kind == oscr::KIND_ROM && optMapper != 0)       // acessórios do Game Boy (F-17, D186): sem cabeçalho de jogo, só leitura
        {
          uint16_t acc = optMapper;
          if (!OSCR::Dumper::GbAcc::valid(acc)) { err = oscr::E_ARGUMENTO; return false; }
          countingSink.inner = &sink; countingSink.bytes = 0;
          activeSink = &countingSink;
          gbRtcNone = false;
          bool ok = runCore([acc] { gbAccRead(acc); }, true);
          activeSink = nullptr;
          err = acc == OSCR::Dumper::GbAcc::kRtc && gbRtcNone ? oscr::E_SEM_SAVE : oscr::E_CARTUCHO_IO;   // sem MBC3 com TIMER: nada a ler
          return ok && countingSink.bytes > 0;
        }
        if (system == oscr::SYS_MD && kind == oscr::KIND_ROM && optMapper != 0 && !OSCR::Dumper::MdBank::sizeValid(optMapper, optPrgKb)) { err = oscr::E_ARGUMENTO; return false; }   // mapper 1, 2 ou 3 e tamanho em KB (D181, D183)
        if ((system == oscr::SYS_COLV || system == oscr::SYS_NGP || system == oscr::SYS_VEC || system == oscr::SYS_A26 || system == oscr::SYS_A52 || system == oscr::SYS_A78 || system == oscr::SYS_A8 || system == oscr::SYS_LYNX || system == oscr::SYS_ARC || system == oscr::SYS_RCA2 || system == oscr::SYS_PYU || system == oscr::SYS_SV || system == oscr::SYS_PV || system == oscr::SYS_BALLY || system == oscr::SYS_CHF || system == oscr::SYS_ODY2 || system == oscr::SYS_POKE || system == oscr::SYS_VSMILE) && kind == oscr::KIND_SAVE) { err = oscr::E_SEM_SAVE; return false; }   // cartucho de ColecoVision não tem save
        if (!prepare(system, kind == oscr::KIND_SAVE, err)) return false;

        uint8_t saveType = OSCR::Cores::saveType;
        if (isNes(system)) { if (kind == oscr::KIND_SAVE && nesRamBytes == 0) { err = oscr::E_SEM_SAVE; return false; } }
        else if (system == oscr::SYS_SNES) { if (kind == oscr::KIND_SAVE && OSCR::Cores::sramSize < 1) { err = oscr::E_SEM_SAVE; return false; } }
        else if (system == oscr::SYS_GB) { if (kind == oscr::KIND_SAVE && gbSaveBytes() == 0) { err = oscr::E_SEM_SAVE; return false; } }
        else if (isSega(system)) { }                                      // SRAM de 32 KB sempre (o usuário sabe se o cartucho tem)
        else if (system == oscr::SYS_JAG) { }                             // EEPROM ou Memory Track: o `mapper` já foi validado em `prepare`
        else if (system == oscr::SYS_MSX) { }                             // mapper e tamanho do save já validados em `prepare`
        else if (kind == oscr::KIND_SAVE && saveType == 0 && !isMdBram(system)) { err = oscr::E_SEM_SAVE; return false; }
        if (kind == oscr::KIND_ROM && isMdBram(system)) { err = oscr::E_ARGUMENTO; return false; }   // a RAM de backup do Sega CD não tem ROM

        countingSink.inner = &sink; countingSink.bytes = 0;
        activeSink = &countingSink;
        bool r369 = system == oscr::SYS_GBA && kind == oscr::KIND_ROM && oscr::gba369::isRead(optMapper);
        uint16_t m369 = optMapper, mb369 = optPrgKb;
        uint16_t m64 = optMapper;
        uint16_t colvKb = optPrgKb, a26Id = optMapper;
        uint32_t ngpBytes = OSCR::Cores::cartSize;                    // `prepare` já leu o chip e aplicou o tamanho do PC
        uint16_t a5romsize = optPrgKb;
        bool ok = runCore([system, kind, saveType, r369, m369, mb369, m64, colvKb, a26Id, a5romsize, ngpBytes]
        {
          if (system == oscr::SYS_COLV) { colvRead(colvKb); return; }
          if (system == oscr::SYS_VEC) { vecRead(colvKb); return; }
          if (system == oscr::SYS_ARC) { arcRead(colvKb); return; }
          if (system == oscr::SYS_RCA2) { rcaRead(colvKb); return; }
          if (system == oscr::SYS_PYU) { pyuRead(colvKb); return; }
          if (system == oscr::SYS_SV) { svRead(colvKb); return; }
          if (system == oscr::SYS_PV) { pvRead(colvKb); return; }
          if (system == oscr::SYS_BALLY) { ballyRead(colvKb); return; }
          if (system == oscr::SYS_CHF) { chfRead(a26Id, colvKb); return; }
          if (system == oscr::SYS_ODY2) { odyRead(a26Id, colvKb); return; }
          if (system == oscr::SYS_POKE) { pkmRead(); return; }
          if (system == oscr::SYS_VSMILE) { vsmRead(colvKb); return; }
          if (system == oscr::SYS_MSX) { if (kind == oscr::KIND_SAVE) msxReadSave(a26Id, colvKb); else msxRead(a26Id, colvKb); return; }
          if (system == oscr::SYS_A26) { a26Read(a26Id); return; }
          if (system == oscr::SYS_A52) { a52Read(a26Id, a5romsize); return; }
          if (system == oscr::SYS_A78) { a78Read(a26Id, a5romsize); return; }
          if (system == oscr::SYS_A8) { a8Read(a26Id, a5romsize); return; }
          if (system == oscr::SYS_LYNX) { lynxRead(); return; }
          if (system == oscr::SYS_JAG)
          {
            if (kind == oscr::KIND_SAVE) jagReadSave(a26Id);
            else if (a26Id == 1) jagReadMem(a5romsize);
            else jagRead(a5romsize);
            return;
          }
          if (system == oscr::SYS_NGP) { ngpRead(ngpBytes); return; }
          if (isNes(system))
          {
            NE::cartOn();
            if (kind == oscr::KIND_ROM)
            {
              OSCR::Storage::Shared::sharedFile.open("rom", O_WRONLY | O_CREAT | O_TRUNC);
              OSCR::Storage::Shared::sharedFile.write(nesRec.iNES, 16);       // o CRC32 do arquivo (no END) inclui o cabeçalho, como no firmware próprio
              NE::readPRG(true);
              NE::readCHR(true);
            }
            else
            {
              NE::readRAM();
            }
            NE::cartOff();
            return;
          }
          if (system == oscr::SYS_GBA)
          {
            if (kind == oscr::KIND_ROM && r369) GBA::read369in1(oscr::gba369::block(m369), uint8_t(mb369));   // liga e desliga o cartucho sozinha; 0 MB = 256 MB (bloco 0)
            else if (kind == oscr::KIND_ROM) GBA::readROM(); else GBA::readSave();
            return;
          }
          if (system == oscr::SYS_SNES)
          {
            if (kind == oscr::KIND_ROM) SN::readROM(); else SN::readSRAM();
            SN::cartOff();
            return;
          }
          if (system == oscr::SYS_GB)
          {
            if (kind == oscr::KIND_ROM) GB::readROM(); else GB::readSave();
            GB::cartOff();
            return;
          }
          if (isSega(system))
          {
            if (kind == oscr::KIND_ROM) SM::readROM(); else SM::readSRAM();     // as duas ligam e desligam o cartucho sozinhas
            return;
          }
          if (system == oscr::SYS_N64)
          {
            if (kind == oscr::KIND_ROM && oscr::n64::isBackup(m64)) { N64Flash::backup(m64 & 0xFF); N6::cartOff(); return; }   // flash do Gameshark ou do Xplorer 64
            if (kind == oscr::KIND_ROM) N6::readRom();                          // liga e desliga o cartucho sozinha
            else
            {
              if (!oscr::n64::isEeprom(saveType)) N6::cartOn();                // SRAM e FlashRAM: o menu do OSCR chamava `cartOn` antes; a EEPROM liga sozinha
              N6::readSave();
            }
            N6::cartOff();
            return;
          }
          if (kind == oscr::KIND_ROM)
          {
            if (OSCR::Dumper::MdBank::valid(m64)) readBanked(m64, mb369);       // `mapper` 1 (Lion King 3), 2 (Pokémon Stadium) ou 3 (Star Odyssey), `prg_kb` = tamanho (D181, D183)
            else if (MD::realtec) MD::readRealtec(); else MD::readROM();      // Realtec: o OSCR lê com `readRealtec` (F-16, D179); liga e desliga o cartucho sozinha
          }
          else if (MD::bramSize > 0)
          {
            MD::readBram(); MD::cartOff();                               // RAM de backup do Sega CD
          }
          else if (saveType == 4)
          {
            MD::readEEP();
          }
          else
          {
            MD::cartOn(); MD::enableSram(1); MD::readSram(); MD::enableSram(0); MD::cartOff();
          }
        }, true);
        activeSink = nullptr;

        // Avisos do OSCR depois que o dado já saiu (checksum, base de dados) não anulam a leitura; sem nenhum byte, é falha.
        err = oscr::E_CARTUCHO_IO;
        return ok || (!fatalHit && countingSink.bytes > 0);
      }

      bool stream_write(uint8_t system, oscr::StreamSource & in, uint16_t & err) override
      {
        if (!supports(system)) { err = oscr::E_SISTEMA; return false; }
        if (system == oscr::SYS_SNES && oscr::snesacc::isAcc(optChrKb)) return accWrite(in, err);
        if (system == oscr::SYS_GB && optMapper == OSCR::Dumper::GbAcc::kRtc)           // relógio do MBC3 (D192): 5 bytes, sem cabeçalho de jogo
        {
          uint8_t r[OSCR::Dumper::GbRtc::kRegs];
          size_t got = 0;
          if (in.size() == sizeof(r)) { while (got < sizeof(r)) { size_t k = in.read(r + got, sizeof(r) - got); if (k == 0) break; got += k; } }
          if (got != sizeof(r) || !OSCR::Dumper::GbRtc::valid(r)) { err = oscr::E_ARGUMENTO; return false; }
          gbRtcNone = false;
          bool ok = runCore([&r] { gbRtcWrite(r); });
          err = gbRtcNone ? oscr::E_SEM_SAVE : oscr::E_CARTUCHO_IO;
          return ok && !gbRtcNone;
        }
        if (system == oscr::SYS_COLV || system == oscr::SYS_NGP || system == oscr::SYS_VEC || system == oscr::SYS_A26 || system == oscr::SYS_A52 || system == oscr::SYS_A78 || system == oscr::SYS_A8 || system == oscr::SYS_LYNX || system == oscr::SYS_ARC || system == oscr::SYS_RCA2 || system == oscr::SYS_PYU || system == oscr::SYS_SV || system == oscr::SYS_PV || system == oscr::SYS_BALLY || system == oscr::SYS_CHF || system == oscr::SYS_ODY2 || system == oscr::SYS_POKE || system == oscr::SYS_VSMILE) { err = oscr::E_SEM_SAVE; return false; }
        if (!prepare(system, true, err)) return false;

        uint8_t saveType = OSCR::Cores::saveType;
        uint32_t expected = isNes(system) ? nesRamBytes
                          : system == oscr::SYS_GBA ? gbaSaveBytes(saveType)
                          : (system == oscr::SYS_GB ? gbSaveBytes()
                          : (system == oscr::SYS_JAG ? jagSaveBytes(optMapper)
                          : (system == oscr::SYS_MSX ? oscr::msx::ramBytes(optMapper, optPrgKb)
                          : (system == oscr::SYS_N64 ? oscr::n64::saveBytes(saveType)
                          : (isSega(system) ? oscr::sms::kSramBytes
                          : (isMdBram(system) ? MD::bramSize
                          : (system == oscr::SYS_SNES ? uint32_t(OSCR::Cores::sramSize) * 128UL : (saveType == 4 ? MD::eepSize : OSCR::Cores::sramSize))))))));

        if ((system != oscr::SYS_GB && system != oscr::SYS_JAG && system != oscr::SYS_MSX && system != oscr::SYS_SNES && !isSega(system) && !isNes(system) && saveType == 0 && !isMdBram(system)) || expected == 0) { err = oscr::E_SEM_SAVE; return false; }
        if (in.size() != expected) { err = oscr::E_ARGUMENTO; return false; }

        countingSource.inner = &in; countingSource.bytes = 0;
        activeSource = &countingSource;
        OSCR::Storage::Shared::sharedFile.open("save", O_RDONLY);    // o "arquivo" é o que o PC manda
        uint16_t jagMap = optMapper, msxKb = optPrgKb;
        bool ok = runCore([system, saveType, jagMap, msxKb]
        {
          if (system == oscr::SYS_JAG) { jagWriteSave(jagMap); return; }
          if (system == oscr::SYS_MSX) { msxWriteSave(jagMap, msxKb); return; }
          if (isNes(system))
          {
            NE::cartOn();
            NE::writeRAM();               // a conferência do OSCR relê o arquivo (não existe no fluxo): o PC relê o save e compara
            NE::cartOff();
            return;
          }
          if (system == oscr::SYS_GBA)
          {
            GBA::writeSave();
            return;
          }
          if (system == oscr::SYS_SNES)
          {
            SN::writeSRAM(true);          // a verificação do OSCR relê o arquivo (não existe no fluxo): o PC relê o save e compara
            SN::cartOff();
            return;
          }
          if (system == oscr::SYS_GB)
          {
            GB::writeSave();
            GB::cartOff();
            return;
          }
          if (isSega(system))
          {
            SM::writeSRAM();              // a conferência é do PC: relê o save e compara
            return;
          }
          if (system == oscr::SYS_N64)
          {
            if (!oscr::n64::isEeprom(saveType)) N6::cartOn();
            if (!N6::writeSave()) errorFlag = true;     // a conferência do OSCR relê o arquivo (sem rewind no fluxo): o PC lê o save de volta e compara
            N6::cartOff();
            return;
          }
          if (MD::bramSize > 0)
          {
            MD::writeBram();                                             // RAM de backup do Sega CD (liga e desliga o cartucho sozinha); a conferência é do PC
          }
          else if (saveType == 4)
          {
            MD::writeEEP();
          }
          else
          {
            MD::cartOn(); MD::enableSram(1); MD::writeSram(); MD::enableSram(0); MD::cartOff();
          }
        }, true);
        activeSource = nullptr;

        // A verificação do OSCR relê o arquivo, que não existe no fluxo; vale ter consumido o arquivo inteiro sem erro fatal.
        err = oscr::E_CARTUCHO_IO;
        return ok || (!fatalHit && countingSource.bytes == expected);
      }

      // WRITE_ROM. Opções: `mapper` = chip (NES: NesFlash::kNesMaker, kA29040B; SNES: SnesFlash::kCfiLoRom, kCfiHiRom);
      // NES: `prg_kb` e `chr_kb` = tamanhos que o PC tirou do arquivo; SNES: `prg_kb` = capacidade do flash em KB.
      bool rom_prepare(uint8_t system, uint32_t size, uint16_t & err) override
      {
        uint8_t chip = uint8_t(optMapper); uint16_t prg = optPrgKb, chr = optChrKb;
        uint16_t rc;
        bool ran;
        romWriteSize = size;
        if (isNes(system))
        {
          rc = NesFlash::check(chip, prg, chr, size);
          if (rc) { err = rc; return false; }
          rc = oscr::E_CARTUCHO_IO;
          ran = runCore([&rc, chip, prg, chr] { NE::cartOn(); rc = NesFlash::prepare(chip, prg, chr); NE::cartOff(); });
        }
        else if (system == oscr::SYS_SNES)
        {
          uint16_t code = optMapper;                                    // SNES: o campo inteiro (disposição << 8 | fiação)
          if (oscr::snesacc::isWriteChip(code))                         // Memory Pack do BS-X, flash e mapeamento do SFM (D190): tamanho exato, sem prg_kb nem chr_kb
          {
            if (chr != 0 || size != oscr::snesacc::writeChipBytes(code)) { err = oscr::E_ARGUMENTO; return false; }
            rc = oscr::E_FLASH;
            ran = runCore([&rc, code] { rc = SnesAcc::prepareWrite(code); });
          }
          else
          {
            rc = SnesFlash::check(code, prg, chr, size);
            if (rc) { err = rc; return false; }
            rc = oscr::E_CARTUCHO_IO;
            ran = runCore([&rc, code, prg, chr, size] { rc = SnesFlash::prepare(code, prg, chr, size); SN::cartOff(); });
          }
        }
        else if (system == oscr::SYS_MD)
        {
          rc = MdFlash::check(chip, size);
          if (rc) { err = rc; return false; }
          rc = oscr::E_CARTUCHO_IO;
          ran = runCore([&rc, size] { rc = MdFlash::prepare(size); MD::cartOff(); });
        }
        else if (system == oscr::SYS_GBA)
        {
          uint16_t code = optMapper;                                    // GBA: (bloco << 8) | 1; o bloco só vale no 369-in-1
          rc = GbaFlash::check(code, size);
          if (rc) { err = rc; return false; }
          rc = oscr::E_FLASH;                                           // o `idFlashrom` do OSCR faz fatalError se não reconhece o chip
          ran = runCore([&rc, code, size] { rc = GbaFlash::prepare(code, size); GBA::cartOff(); });
        }
        else if (system == oscr::SYS_N64)
        {
          uint16_t kind64 = chip;                                       // N64: 1 = flash repro (o firmware identifica o chip pelo ID), 2 = Gameshark, 3 = Xplorer 64
          rc = N64Flash::check(kind64, size);
          if (rc) { err = rc; return false; }
          rc = oscr::E_FLASH;                                           // chip desconhecido, ROM de máscara ou apagamento que não fica em branco
          ran = runCore([&rc, kind64, size] { rc = N64Flash::prepare(kind64, size); N6::cartOff(); });
        }
        else if (system == oscr::SYS_GB)
        {
          rc = GbFlash::check(chip, size);
          if (rc) { err = rc; return false; }
          rc = oscr::E_FLASH;
          ran = runCore([&rc, chip, size] { rc = GbFlash::prepare(chip, size); GB::cartOff(); });
          GB::audioWE = 0;                                              // o pino de áudio como WE só vale durante a gravação
        }
        else if (system == oscr::SYS_FLASH)
        {
          uint16_t code = optMapper;
          rc = size ? FlashProg::check(code, prg, chr, size) : oscr::E_ARGUMENTO;
          if (rc) { err = rc; return false; }
          rc = oscr::E_FLASH;
          ran = runCore([&rc, code, prg, chr, size] { rc = FlashProg::prepare(code, prg, chr, size); OSCR::Cores::SNES::cartOff(); });
        }
        else { err = oscr::E_COMANDO; return false; }
        if (rc != 0 || !ran) { err = rc ? rc : oscr::E_CARTUCHO_IO; return false; }
        return true;
      }

      bool stream_write_rom(uint8_t system, oscr::StreamSource & in, uint16_t & err) override
      {
        uint8_t chip = uint8_t(optMapper); uint16_t prg = optPrgKb, chr = optChrKb;
        uint16_t rc = oscr::E_CARTUCHO_IO;
        bool ran;
        if (isNes(system)) ran = runCore([&rc, &in, chip, prg, chr] { NE::cartOn(); rc = NesFlash::program(chip, prg, chr, in); NE::cartOff(); });
        else if (system == oscr::SYS_SNES)
        {
          uint16_t code = optMapper; uint32_t n = romWriteSize;
          bool generic = SnesFlash::isGeneric(code);
          if (oscr::snesacc::isWriteChip(code)) ran = runCore([&rc, &in, code] { rc = SnesAcc::programWrite(code, in); });       // D190: lê direto do fluxo
          else
          {
            if (generic)                                                  // P0/P1: as funções do OSCR leem o "arquivo" (sharedFile); ligá-lo ao fluxo, como no WRITE_SAVE
            {
              countingSource.inner = &in; countingSource.bytes = 0;
              activeSource = &countingSource;
              OSCR::Storage::Shared::sharedFile.open("rom", O_RDONLY);
            }
            ran = runCore([&rc, &in, code, prg, chr, n] { rc = SnesFlash::program(code, prg, chr, n, in); SN::cartOff(); });
            if (generic)
            {
              activeSource = nullptr;
              if (rc == 0 && countingSource.bytes != n) rc = oscr::E_CARTUCHO_IO;     // o OSCR não avisa se o arquivo acabou antes
            }
          }
        }
        else if (system == oscr::SYS_MD)
        {
          // As funções do OSCR leem o "arquivo" (sharedFile): ligá-lo ao fluxo, como no WRITE_SAVE.
          countingSource.inner = &in; countingSource.bytes = 0;
          activeSource = &countingSource;
          OSCR::Storage::Shared::sharedFile.open("rom", O_RDONLY);
          ran = runCore([&rc] { rc = MdFlash::program(); MD::cartOff(); });
          activeSource = nullptr;
          if (rc == 0 && countingSource.bytes != romWriteSize) rc = oscr::E_CARTUCHO_IO;       // o OSCR não avisa se o arquivo acabou antes
        }
        else if (system == oscr::SYS_GBA)
        {
          // As funções do OSCR leem o "arquivo" (sharedFile): ligá-lo ao fluxo, como no WRITE_SAVE.
          uint16_t code = optMapper; uint32_t n = romWriteSize;
          countingSource.inner = &in; countingSource.bytes = 0;
          activeSource = &countingSource;
          OSCR::Storage::Shared::sharedFile.open("rom", O_RDONLY);
          ran = runCore([&rc, code, n] { rc = GbaFlash::program(code, n); GBA::cartOff(); });
          activeSource = nullptr;
          if (rc == 0 && countingSource.bytes != n) rc = oscr::E_CARTUCHO_IO;
        }
        else if (system == oscr::SYS_GB)
        {
          uint32_t n = romWriteSize;
          ran = runCore([&rc, &in, chip, n] { rc = GbFlash::program(chip, n, in); GB::cartOff(); });
          GB::audioWE = 0;
        }
        else if (system == oscr::SYS_N64)
        {
          // As funções do OSCR leem o "arquivo" (sharedFile): ligá-lo ao fluxo, como no WRITE_SAVE.
          uint32_t n = romWriteSize;
          countingSource.inner = &in; countingSource.bytes = 0;
          activeSource = &countingSource;
          OSCR::Storage::Shared::sharedFile.open("rom", O_RDONLY);
          uint16_t kind64 = chip;
          ran = runCore([&rc, kind64, n] { rc = N64Flash::program(kind64, n); N6::cartOff(); });
          activeSource = nullptr;
          if (rc == 0 && countingSource.bytes != n) rc = oscr::E_CARTUCHO_IO;
        }
        else if (system == oscr::SYS_FLASH)
        {
          uint16_t code = optMapper; uint32_t n = romWriteSize;
          countingSource.inner = &in; countingSource.bytes = 0;
          activeSource = &countingSource;
          OSCR::Storage::Shared::sharedFile.open("rom", O_RDONLY);
          ran = runCore([&rc, &in, code, prg, chr, n] { rc = FlashProg::program(code, prg, chr, n, in); OSCR::Cores::SNES::cartOff(); });
          activeSource = nullptr;
          if (rc == 0 && countingSource.bytes != n) rc = oscr::E_CARTUCHO_IO;       // todas as rotinas do OSCR leem o "arquivo"; sem consumir tudo, a gravação ficou incompleta
        }
        else { err = oscr::E_COMANDO; return false; }
        if (rc != 0 || !ran) { err = rc ? rc : oscr::E_CARTUCHO_IO; return false; }
        return true;
      }

      // ERASE (programador genérico): apaga o chip inteiro. 8 bits: o tipo é obrigatório (identifica o chip antes e escolhe a rotina de apagar).
      bool erase(uint8_t system, uint16_t & err) override
      {
        if (system == oscr::SYS_SNES)
        {
          // Test RAM do SNES (F-10, D178): o `eraseSRAM` do OSCR sobrescreve a SRAM inteira com o byte dado (`chip`). O OSCR lê o save antes, escreve 0x0F e 0xF0 e o grava de volta;
          // aqui o PC faz o backup e a restauração (a SRAM não cabe na RAM do Arduino) e este comando só preenche.
          if (optMapper > 0xFF) { err = oscr::E_ARGUMENTO; return false; }
          if (!prepare(system, true, err)) return false;                // lê o cabeçalho: tipo de ROM e tamanho da SRAM
          if (OSCR::Cores::sramSize < 1) { err = oscr::E_SEM_SAVE; return false; }
          uint8_t pattern = uint8_t(optMapper);
          bool ran = runCore([pattern] { OSCR::Cores::SNES::eraseSRAM(pattern); OSCR::Cores::SNES::cartOff(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          return true;
        }
        if (system != oscr::SYS_FLASH) { err = oscr::E_COMANDO; return false; }
        uint16_t code = optMapper, prg = optPrgKb, chr = optChrKb;
        uint16_t rc = FlashProg::check(code, prg, chr, 0);
        bool needsType = (code & 0xFF) == FlashProg::k8Adapter || (code & 0xFF) == FlashProg::k8Plcc32;
        if (rc || (needsType && ((chr & 0xF) < 1 || (chr & 0xF) > 8)) || (code & 0xFF) == FlashProg::kEprom) { err = oscr::E_ARGUMENTO; return false; }
        rc = oscr::E_FLASH;
        bool ran = runCore([&rc, code, prg, chr] { rc = FlashProg::prepare(code, prg, chr, 0); OSCR::Cores::SNES::cartOff(); });
        if (rc != 0 || !ran) { err = rc ? rc : oscr::E_CARTUCHO_IO; return false; }
        return true;
      }

      // Caminhos que o modo fluxo não usa.
      bool open_read(uint8_t, uint8_t, uint32_t &, uint16_t & err) override { err = oscr::E_COMANDO; return false; }
      bool read(uint8_t, uint8_t, uint32_t, uint8_t *, uint16_t) override { return false; }
      bool write_begin(uint8_t, uint32_t, uint16_t & err) override { err = oscr::E_COMANDO; return false; }
      bool write_block(uint32_t, uint8_t const *, uint16_t) override { return false; }
      bool write_commit() override { return false; }

    private:
      uint16_t optMapper = 0, optPrgKb = 0, optChrKb = 0;

      /** Leitura de acessório do SNES (F-10, D178): Sufami Turbo (ROM do slot A ou B) e GPC (os 512 KB da RAM, como "save"). */
      bool accRead(uint8_t kind, oscr::StreamSink & sink, uint16_t & err)
      {
        uint16_t f = optChrKb;
        if (!oscr::snesacc::valid(f)) { err = oscr::E_ARGUMENTO; return false; }
        bool sufami = oscr::snesacc::isSufami(f);
        if (oscr::snesacc::isRomAcc(f) != (kind == oscr::KIND_ROM)) { err = oscr::E_ARGUMENTO; return false; }   // ROM: Sufami, Memory Pack, SFM; save: GPC e SRAM do BS-X

        bool slotB = oscr::snesacc::sufamiSlotB(f);
        if (sufami)
        {
          uint16_t rc = oscr::E_SEM_CARTUCHO; uint32_t bytes = 0;
          bool ran = runCore([&rc, &bytes, slotB] { rc = SnesAcc::probeSufami(slotB, bytes); OSCR::Cores::ST::cartOff(); });
          if (!ran || rc) { err = rc ? rc : oscr::E_CARTUCHO_IO; return false; }
        }

        if (f == oscr::snesacc::kBsxPack || f == oscr::snesacc::kBsxSram)         // F-11 (D187): precisa do cartucho base do BS-X
        {
          uint16_t rc = oscr::E_SEM_CARTUCHO;
          bool ran = runCore([&rc] { rc = SnesAcc::probeBsx(); });
          if (!ran || rc) { err = rc ? rc : oscr::E_CARTUCHO_IO; return false; }
        }

        countingSink.inner = &sink; countingSink.bytes = 0;
        activeSink = &countingSink;
        bool ok = runCore([f, sufami, slotB]
        {
          namespace A = oscr::snesacc;
          if (sufami) OSCR::Cores::ST::readSlot(slotB);
          else if (f == A::kGpc) OSCR::Cores::GPC::readRAM();
          else if (f == A::kBsxPack) OSCR::Cores::Satellaview::readROM();                          // liga e desliga sozinha
          else if (f == A::kBsxSram) { OSCR::Cores::Satellaview::readSRAM(); OSCR::Cores::Satellaview::cartOff(); }
          else if (f == A::kSfmFlash) OSCR::Cores::SFM::readFlash();                               // destrava, lê os 4 MB e desliga
          else if (f == A::kSfmMap) SnesAcc::readSfmMap();
          else SnesAcc::readSfmGame(A::sfmGameIndex(f));
        }, true);
        activeSink = nullptr;
        err = oscr::E_CARTUCHO_IO;
        return ok || (!fatalHit && countingSink.bytes > 0);
      }

      /** Gravação dos 512 KB do GPC (WRITE_SAVE com o acessório). */
      bool accWrite(oscr::StreamSource & in, uint16_t & err)
      {
        uint16_t f = optChrKb;
        if (!oscr::snesacc::hasWrite(f)) { err = oscr::E_ARGUMENTO; return false; }         // só o GPC e a SRAM do BS-X gravam; o resto é só leitura
        uint32_t want = oscr::snesacc::writeBytes(f);
        if (in.size() != want) { err = oscr::E_ARGUMENTO; return false; }
        if (f == oscr::snesacc::kBsxSram)
        {
          uint16_t rc = oscr::E_SEM_CARTUCHO;
          bool ran = runCore([&rc] { rc = SnesAcc::probeBsx(); });
          if (!ran || rc) { err = rc ? rc : oscr::E_CARTUCHO_IO; return false; }
        }
        countingSource.inner = &in; countingSource.bytes = 0;
        activeSource = &countingSource;
        OSCR::Storage::Shared::sharedFile.open("save", O_RDONLY);
        bool ok = runCore([f] { if (f == oscr::snesacc::kGpc) SnesAcc::writeGpc(); else SnesAcc::writeBsxSram(); });
        activeSource = nullptr;
        err = oscr::E_CARTUCHO_IO;
        return ok || (!fatalHit && countingSource.bytes == want);
      }
      uint32_t romWriteSize = 0;      // tamanho do arquivo do último WRITE_ROM (rom_prepare -> stream_write_rom)

      /** Lê o cabeçalho do cartucho (preenche cartSize, saveType, sramSize...) antes de ler ou gravar. */
      bool prepare(uint8_t system, bool forSave, uint16_t & err)
      {
        if (system == oscr::SYS_GBA)
        {
          bool r369 = !forSave && oscr::gba369::isRead(optMapper);        // F-18 (D174): leitura do 369-in-1; o `mapper` não é tipo de save
          if (r369 && !oscr::gba369::valid(optMapper, optPrgKb)) { err = oscr::E_ARGUMENTO; return false; }
          if (forSave && optMapper > 6) { err = oscr::E_ARGUMENTO; return false; }
          uint8_t st = 1;
          runCore([&st, this, r369] { st = gbaProbe(r369 ? uint8_t(0) : uint8_t(optMapper)); });
          if (st == 1) { err = oscr::E_SEM_CARTUCHO; return false; }     // 4 (checksum do cabeçalho errado) segue: o PC decide
          if (!forSave && !r369 && optPrgKb) OSCR::Cores::cartSize = uint32_t(optPrgKb) * 1024UL;   // tamanho informado (conferência depois de gravar o flash: a detecção por espelho vê o flash inteiro)
          return true;
        }
        if (system == oscr::SYS_SNES)
        {
          uint8_t st = 1;
          uint16_t kb = forSave ? uint16_t(0) : optPrgKb, ty = optChrKb;
          if (!OSCR::Dumper::SnesType::valid(ty)) { err = oscr::E_ARGUMENTO; return false; }
          runCore([&st, kb, ty] { st = snesProbe(kb, ty); });
          if (st == 1) { err = oscr::E_SEM_CARTUCHO; return false; }
          if (st != 0) { err = oscr::E_CARTUCHO_IO; return false; }
          return true;
        }
        if (isNes(system))
        {
          uint16_t rc = oscr::E_SEM_CARTUCHO;
          uint16_t m = optMapper, p = optPrgKb, c = optChrKb;
          bool ran = runCore([&rc, forSave, m, p, c] { rc = nesProbe(forSave, m, p, c); NE::cartOff(); });
          if (!ran && rc == oscr::E_SEM_CARTUCHO) { err = oscr::E_CARTUCHO_IO; return false; }
          if (rc != 0) { err = rc; return false; }
          return true;
        }
        if (system == oscr::SYS_N64 && !forSave && oscr::n64::isBackup(optMapper))
        {
          // Backup da flash do Gameshark ou do Xplorer 64 (F-19, D177): não é um cartucho de jogo, então não tem cabeçalho de N64; só confere o ID do acessório.
          if (!oscr::n64::backupValid(optMapper)) { err = oscr::E_ARGUMENTO; return false; }
          uint16_t rc = oscr::E_FLASH, kind64 = optMapper & 0xFF;
          bool ran = runCore([&rc, kind64] { rc = N64Flash::probe(kind64); N6::cartOff(); });
          if (!ran && rc == 0) rc = oscr::E_CARTUCHO_IO;
          if (rc) { err = rc; return false; }
          return true;
        }
        if (system == oscr::SYS_N64)
        {
          uint8_t st = oscr::n64::kNoCart;
          bool ran = runCore([&st] { st = n64Probe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::n64::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          if (st != oscr::n64::kOk) { err = oscr::E_CARTUCHO_IO; return false; }        // 4: cabeçalho que não é de N64 (limpar os contatos e tentar de novo)
          if (forSave)
          {
            if (!oscr::n64::saveTypeValid(optMapper)) { err = oscr::E_ARGUMENTO; return false; }
            OSCR::Cores::saveType = uint8_t(optMapper);
            N6::eepPages = oscr::n64::eepromPages(uint8_t(optMapper));
          }
          else
          {
            if (!oscr::n64::romMbValid(optPrgKb)) { err = oscr::E_ARGUMENTO; return false; }
            OSCR::Cores::cartSize = optPrgKb;                                           // o `readRom` do OSCR conta em MB
          }
          return true;
        }
        if (system == oscr::SYS_A8)
        {
          if (oscr::atari8::totalKb(optMapper, optPrgKb) == 0) { err = oscr::E_ARGUMENTO; return false; }   // slot 0 ou 1 e tamanho do OSCR (AtariCore.h); no slot direito o tamanho é ignorado
          if (!forSave && oscr::atari8::needsClock(optMapper, optPrgKb) && !a8ClockPresent()) { err = oscr::E_CARTUCHO_IO; return false; }   // XE de 32/64/128 KB troca de banco pelo PHI2 do Si5351 (D213)
          uint8_t st = oscr::a26::kNoCart;
          uint16_t slot = optMapper;
          bool ran = runCore([&st, slot] { st = a8Probe(slot); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::a26::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_JAG)
        {
          if (forSave) { if (jagSaveBytes(optMapper) == 0) { err = oscr::E_ARGUMENTO; return false; } }          // `mapper` 0 a 4 (EEPROM) ou 5 (Memory Track)
          else if (optMapper > 1 || oscr::jag::sizeIndex(optPrgKb) == oscr::jag::kBad) { err = oscr::E_ARGUMENTO; return false; }   // `mapper` 0 (ROM) ou 1 (ROM U1 do Memory Track) e 1024, 2048 ou 4096 KB, sempre informado pelo PC
          uint8_t st = oscr::a26::kNoCart;
          bool ran = runCore([&st] { st = jagProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::a26::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_LYNX)
        {
          bool found = false;
          bool ran = runCore([&found] { found = lynxProbe(); }, true);
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (!found || oscr::lynx::totalBytes(LX::lynxBlockSize) == 0) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_A52 || system == oscr::SYS_A78)
        {
          bool is52 = system == oscr::SYS_A52;
          uint16_t kb = is52 ? oscr::atari::a52Kb(optMapper, optPrgKb) : oscr::atari::a78Kb(optMapper, optPrgKb);
          if (kb == 0) { err = oscr::E_ARGUMENTO; return false; }                                   // mapper e prg_kb do OSCR (AtariCore.h)
          uint8_t st = oscr::a26::kNoCart;
          bool ran = runCore([&st, is52] { st = is52 ? a52Probe() : a78Probe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::a26::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_A26)
        {
          if (!oscr::a26::mapperValid(optMapper)) { err = oscr::E_ARGUMENTO; return false; }        // id do `a2600-mappers` do OSCR (campo mapper); `prg_kb` é ignorado
          uint8_t st = oscr::a26::kNoCart;
          bool ran = runCore([&st] { st = a26Probe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::a26::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_VEC)
        {
          if (oscr::vec::sizeIndex(optPrgKb) == oscr::vec::kBadIndex) { err = oscr::E_ARGUMENTO; return false; }     // 4, 8, 12, 16, 32 ou 64 KB, sempre informado pelo PC
          uint8_t st = oscr::vec::kNoCart;
          bool ran = runCore([&st] { st = vecProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::vec::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_ARC)
        {
          if (oscr::arc::sizeIndex(optPrgKb) == oscr::arc::kBadIndex) { err = oscr::E_ARGUMENTO; return false; }     // 2, 4, 6 ou 8 KB, sempre informado pelo PC
          uint8_t st = oscr::arc::kNoCart;
          bool ran = runCore([&st] { st = arcProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::arc::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_ODY2)
        {
          if (!oscr::ody::argsValid(optMapper, optPrgKb)) { err = oscr::E_ARGUMENTO; return false; }   // mapper 0 com 2, 4, 8, 12 ou 16 KB; mapper 1 só com 4 KB
          uint8_t st = oscr::ody::kNoCart;
          bool ran = runCore([&st] { st = odyProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::ody::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_POKE)
        {
          if (!oscr::pkm::sizeValid(optPrgKb)) { err = oscr::E_ARGUMENTO; return false; }   // 0 ou 512: o arquivo tem sempre 512 KB
          uint8_t st = oscr::pkm::kNoCart;
          bool ran = runCore([&st] { st = pkmProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::pkm::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_MSX)
        {
          if (!oscr::msx::validMapper(optMapper)) { err = oscr::E_ARGUMENTO; return false; }                         // mapper 0 a 14, sempre informado pelo PC
          if (forSave && !oscr::msx::hasSave(optMapper)) { err = oscr::E_SEM_SAVE; return false; }                  // só ASCII8, ASCII16, Game Master 2, HAL Note, Koei e PAC/FM-PAC têm SRAM
          if (forSave ? oscr::msx::ramIndex(optMapper, optPrgKb) == oscr::msx::kBadIndex
                      : oscr::msx::romIndex(optMapper, optPrgKb) == oscr::msx::kBadIndex) { err = oscr::E_ARGUMENTO; return false; }   // KB de ROM (ou de SRAM) dentro da faixa do mapper
          uint8_t st = oscr::msx::kNoCart; bool header = false;
          bool ran = runCore([&st, &header] { st = msxProbe(header); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::msx::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_VSMILE)
        {
          if (oscr::vsm::sizeIndex(optPrgKb) == oscr::vsm::kBadIndex) { err = oscr::E_ARGUMENTO; return false; }   // 4096, 6144, 8192 ou 16384 KB, sempre informado pelo PC
          uint8_t st = oscr::vsm::kNoCart;
          bool ran = runCore([&st] { st = vsmProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::vsm::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_CHF)
        {
          if (!oscr::chf::modeValid(optMapper) || oscr::chf::sizeIndex(optPrgKb) == oscr::chf::kBadIndex) { err = oscr::E_ARGUMENTO; return false; }   // modo 0 ou 1; 2, 3, 4 ou 6 KB, sempre informado pelo PC
          uint8_t st = oscr::chf::kNoCart;
          bool ran = runCore([&st] { st = chfProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::chf::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          if (st == oscr::chf::kNoHeader && optMapper == oscr::chf::kModeRom) { err = oscr::E_CARTUCHO_IO; return false; }   // sem cabeçalho o readROM não grava nada; o read16K ainda lê
          return true;
        }
        if (system == oscr::SYS_BALLY)
        {
          if (oscr::bally::sizeIndex(optPrgKb) == oscr::bally::kBadIndex) { err = oscr::E_ARGUMENTO; return false; }     // 2, 4 ou 8 KB, sempre informado pelo PC
          uint8_t st = oscr::bally::kNoCart;
          bool ran = runCore([&st] { st = ballyProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::bally::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_PV)
        {
          if (oscr::pv::sizeIndex(optPrgKb) == oscr::pv::kBadIndex) { err = oscr::E_ARGUMENTO; return false; }     // 8 ou 16 KB, sempre informado pelo PC
          uint8_t st = oscr::pv::kNoCart;
          bool ran = runCore([&st] { st = pvProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::pv::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_SV)
        {
          if (oscr::sv::sizeIndex(optPrgKb) == oscr::sv::kBadIndex) { err = oscr::E_ARGUMENTO; return false; }     // 32, 64 ou 512 KB, sempre informado pelo PC
          uint8_t st = oscr::sv::kNoCart;
          bool ran = runCore([&st] { st = svProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::sv::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_PYU)
        {
          if (oscr::pyu::sizeIndex(optPrgKb) == oscr::pyu::kBadIndex) { err = oscr::E_ARGUMENTO; return false; }     // 8, 16 ou 32 KB, sempre informado pelo PC
          uint8_t st = oscr::pyu::kNoCart;
          bool ran = runCore([&st] { st = pyuProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::pyu::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_RCA2)
        {
          if (oscr::rca::sizeIndex(optPrgKb) == oscr::rca::kBadIndex) { err = oscr::E_ARGUMENTO; return false; }     // 1 KB, sempre informado pelo PC
          uint8_t st = oscr::rca::kNoCart;
          bool ran = runCore([&st] { st = rcaProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::rca::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (system == oscr::SYS_NGP)
        {
          uint16_t kb = optPrgKb;
          if (kb != 0 && !oscr::ngp::sizeKbValid(kb)) { err = oscr::E_ARGUMENTO; return false; }     // 512, 1024, 2048 ou 4096 KB; 0 = pelo ID do chip
          uint8_t st = oscr::ngp::kNoCart;
          bool ran = runCore([&st, kb] { st = ngpProbe(kb); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::ngp::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          if (st == oscr::ngp::kNoHeader && kb == 0) { err = oscr::E_CARTUCHO_IO; return false; }    // sem cabeçalho SNK só com o tamanho informado (o "Continuar" do OSCR)
          if (OSCR::Cores::cartSize == 0) { err = oscr::E_ARGUMENTO; return false; }               // chip desconhecido: o PC precisa informar o tamanho
          return true;
        }
        if (system == oscr::SYS_COLV)
        {
          if (oscr::colv::sizeIndex(optPrgKb) == oscr::colv::kBadIndex) { err = oscr::E_ARGUMENTO; return false; }     // 8, 12, 16, 20, 24 ou 32 KB, sempre informado pelo PC
          uint8_t st = oscr::colv::kNoCart;
          bool ran = runCore([&st] { st = colvProbe(); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::colv::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          return true;
        }
        if (isSega(system))
        {
          if (!segaOptionsOk(system, optMapper, forSave ? uint16_t(0) : optPrgKb)) { err = oscr::E_ARGUMENTO; return false; }
          uint8_t st = oscr::sms::kNoCart, con = segaConsole(system); uint16_t ad = optMapper;
          uint16_t kb = forSave ? uint16_t(0) : optPrgKb;
          bool ran = runCore([&st, con, ad, kb] { st = smsProbe(con, ad, kb); });
          if (!ran) { err = oscr::E_CARTUCHO_IO; return false; }
          if (st == oscr::sms::kNoCart) { err = oscr::E_SEM_CARTUCHO; return false; }
          if (!forSave && OSCR::Cores::cartSize == 0) { err = oscr::E_ARGUMENTO; return false; }     // sem cabeçalho e sem tamanho informado
          return true;
        }
        if (system == oscr::SYS_GB)
        {
          uint8_t st = 1;
          runCore([&st] { st = gbProbe(); GB::cartOff(); });
          if (st == 1) { err = oscr::E_SEM_CARTUCHO; return false; }
          if (st != 0) { err = oscr::E_CARTUCHO_IO; return false; }      // 4: checksum do cabeçalho errado (limpar os contatos e tentar de novo)
          return true;
        }
        oscr::DetectInfo d;
        detect(system, d);
        if (d.status != 0) { err = oscr::E_SEM_CARTUCHO; return false; }
        return true;
      }
    };

    CoreBackend backend;
    oscr::Session * session = nullptr;
  }

  oscr::StreamSink * sink() { return activeSink; }
  oscr::StreamSource * source() { return activeSource; }

  void noteError() { errorFlag = true; }

  void noteAbort() { abortHit = true; }

  int32_t clockOffset()
  {
    int32_t ppb = 0;
    loadClockPpb(ppb);
    return ppb;
  }

  // D240: a Wire do Arduino não tem limite de tempo por padrão e o `init` da biblioteca do Si5351 espera o SYS_INIT sem limite.
  // Um módulo sem 5V ou mal encaixado prende SDA/SCL em nível baixo e o firmware parava ainda no boot, antes de abrir a serial.
  // D241: antes de começar, solta o barramento se um escravo ficou segurando o SDA no meio de um byte (Mega reiniciado pelo DTR no meio de
  // uma leitura, com o módulo ainda ligado): até 9 pulsos no SCL e um STOP. A espera do SYS_INIT tem limite de tempo total, não por tentativa.
  bool clockgenProbe()
  {
#if defined(ENABLE_CLOCKGEN)
    Wire.end();                                     // o TWI solta os pinos para o resgate abaixo
    pinMode(SDA, INPUT_PULLUP);
    pinMode(SCL, INPUT_PULLUP);
    delayMicroseconds(10);
    for (uint8_t i = 0; i < 9 && !digitalRead(SDA); i++)
    {
      digitalWrite(SCL, LOW); pinMode(SCL, OUTPUT); delayMicroseconds(5);   // dreno aberto: só puxa para baixo, nunca força o nível alto
      pinMode(SCL, INPUT_PULLUP); delayMicroseconds(5);
    }
    digitalWrite(SDA, LOW); pinMode(SDA, OUTPUT); delayMicroseconds(5);     // START + STOP com o SCL alto: o escravo volta ao estado ocioso
    pinMode(SDA, INPUT_PULLUP); delayMicroseconds(5);

    Wire.setWireTimeout(25000, true);   // 25 ms por operação, com reset do TWI; vale para todo uso do I²C daqui em diante
    Wire.begin();
    Wire.beginTransmission(SI5351_BUS_BASE_ADDR);
    if (Wire.endTransmission() != 0) return false;   // 2: ninguém respondeu no endereço; 5: barramento preso
    uint32_t t0 = millis();
    do                                               // até 100 ms no total pelo SYS_INIT (bit 7 do registro de estado)
    {
      Wire.beginTransmission(SI5351_BUS_BASE_ADDR);
      Wire.write(uint8_t(SI5351_DEVICE_STATUS));
      uint8_t e = Wire.endTransmission();
      if (e == 5) return false;                      // barramento preso de novo: não insiste
      if (e == 0 && Wire.requestFrom(uint8_t(SI5351_BUS_BASE_ADDR), uint8_t(1)) == 1 && !(Wire.read() & 0x80)) return true;
      delay(1);
    } while (millis() - t0 < 100);
#endif
    return false;
  }

  // noipa (D235): com LTO, o avr-gcc 15.2 gravava 0 fixo em `b` (o segundo pino de cada par chegava ao PC como "D0").
  __attribute__((noipa)) void noteSelfTest(uint8_t kind, uint8_t a, uint8_t b)
  {
    if (selfTestOut != nullptr) selfTestOut->add(kind, a, b);
  }

  // O fluxo do PC morreu no meio de uma gravação (ABORT ou PC parado): para o núcleo antes que ele grave dados velhos no cartucho.
  void streamDead()
  {
    errorFlag = true;
    if (armed) longjmp(escape, 1);
  }

  [[ noreturn ]] void fatal()
  {
    errorFlag = true;
    if (armed) longjmp(escape, 1);

    // Erro fora de um comando (por exemplo no setup): nada a fazer além de parar com a serial muda.
    for (;;) {}
  }

  void setup()
  {
    loadBoardProfile();                       // perfil guardado pelo PC (BOARD); sem ele vale a compilação
    setVoltPin(cartVolt);                     // o seletor começa em 3,3 V (estado seguro, D138); sem seletor não faz nada
    delay(50);                                // o 5V dos slots, o Si5351 e o PIC sobem antes do primeiro comando
    ClockedSerial.begin(OSCR_DUMPER_BAUD);
    ClockedSerial.mute = true;                // a UI de texto do OSCR não pode escrever no meio dos quadros

    static oscr::Session s(oscr::Io{nullptr, ioRead, ioWrite, ioNow}, backend, rxBuf, sizeof rxBuf, txBuf, sizeof txBuf);
    session = &s;
  }

  void loop()
  {
    if (session != nullptr) session->poll();
  }
}

#endif /* OSCR_DUMPER */
