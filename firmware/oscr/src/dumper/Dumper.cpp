// SPDX-License-Identifier: GPL-3.0-or-later
// Fork oscr_minimal: laço de comandos do protocolo serial (docs/protocolo.md) ligado aos núcleos do OSCR.
// Estado: Mega Drive (DETECT, DUMP_ROM, READ_SAVE e WRITE_SAVE). Os demais consoles ainda não estão ligados (docs/fork-oscr.md).
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
# include "dumper/Dumper.h"

# ifndef OSCR_DUMPER_BAUD
#   define OSCR_DUMPER_BAUD 1000000UL     // 115200 como fallback: compile com -DOSCR_DUMPER_BAUD=115200
# endif

namespace OSCR::Dumper
{
  namespace
  {
    oscr::StreamSink * activeSink = nullptr;
    oscr::StreamSource * activeSource = nullptr;
    bool errorFlag = false;
    jmp_buf escape;
    bool armed = false;

    uint8_t rxBuf[OSCR_MAX_PAYLOAD];
    uint8_t txBuf[OSCR_MAX_PAYLOAD + 10];

    int ioRead(void *, uint32_t timeoutMs)
    {
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
     * Executa uma função de núcleo com a saída ligada ao fluxo. Erros fatais dos núcleos (UI::fatalError) voltam aqui por longjmp.
     * Devolve false se o núcleo falhou.
     */
    template <typename Fn>
    bool runCore(Fn fn)
    {
      errorFlag = false;
      armed = true;
      bool ok = true;

      if (setjmp(escape) == 0)
      {
        fn();
      }
      else
      {
        ok = false;
      }

      armed = false;
      OSCR::Power::disableCartridge();
      OSCR::Storage::Shared::sharedFile.close();
      return ok && !errorFlag;
    }

    /** Backend dos núcleos do OSCR. Só o Mega Drive está ligado até agora. */
    class CoreBackend : public oscr::Backend
    {
    public:
      uint8_t flags() override { return 0; }
      uint16_t systems() override { return 1U << oscr::SYS_MD; }
      bool supports(uint8_t system) override { return system == oscr::SYS_MD; }
      bool streams() override { return true; }

      void detect(uint8_t system, oscr::DetectInfo & out) override
      {
        if (!supports(system)) { out.status = 2; return; }

        bool ok = runCore([] { OSCR::Cores::MegaDrive::getCartInfo(); OSCR::Cores::MegaDrive::cartOff(); });

        // O OSCR considera "sem cartucho" um tamanho zero ou absurdo (o maior jogo conhecido tem 10 MB).
        if (!ok || OSCR::Cores::cartSize == 0 || OSCR::Cores::cartSize > 16777216UL) { out.status = 1; return; }

        out.status = 0;
        out.rom_size = OSCR::Cores::cartSize;
        out.save_size = OSCR::Cores::saveType == 4 ? OSCR::Cores::MegaDrive::eepSize : OSCR::Cores::sramSize;
        out.save_type = OSCR::Cores::saveType;
        strlcpy(out.name, OSCR::Cores::fileName, sizeof(out.name));
      }

      bool stream_read(uint8_t system, uint8_t kind, oscr::StreamSink & sink, uint16_t & err) override
      {
        if (!supports(system)) { err = oscr::E_SISTEMA; return false; }
        if (!prepare(err)) return false;

        uint8_t saveType = OSCR::Cores::saveType;

        if (kind == oscr::KIND_SAVE && saveType == 0) { err = oscr::E_SEM_SAVE; return false; }

        activeSink = &sink;
        bool ok = runCore([kind, saveType]
        {
          using namespace OSCR::Cores::MegaDrive;
          if (kind == oscr::KIND_ROM)
          {
            readROM();
          }
          else if (saveType == 4)
          {
            readEEP();
          }
          else
          {
            cartOn(); enableSram(1); readSram(); enableSram(0); cartOff();
          }
        });
        activeSink = nullptr;

        err = oscr::E_CARTUCHO_IO;
        return ok;
      }

      bool stream_write(uint8_t system, oscr::StreamSource & in, uint16_t & err) override
      {
        if (!supports(system)) { err = oscr::E_SISTEMA; return false; }
        if (!prepare(err)) return false;

        uint8_t saveType = OSCR::Cores::saveType;
        uint32_t expected = saveType == 4 ? OSCR::Cores::MegaDrive::eepSize : OSCR::Cores::sramSize;

        if (saveType == 0) { err = oscr::E_SEM_SAVE; return false; }
        if (in.size() != expected) { err = oscr::E_ARGUMENTO; return false; }

        activeSource = &in;
        OSCR::Storage::Shared::sharedFile.open("save", O_RDONLY);    // o "arquivo" é o que o PC manda
        bool ok = runCore([saveType]
        {
          using namespace OSCR::Cores::MegaDrive;
          if (saveType == 4)
          {
            writeEEP();
          }
          else
          {
            cartOn(); enableSram(1); writeSram(); enableSram(0); cartOff();
          }
        });
        activeSource = nullptr;

        err = oscr::E_CARTUCHO_IO;
        return ok;
      }

      // Caminhos que o modo fluxo não usa.
      bool open_read(uint8_t, uint8_t, uint32_t &, uint16_t & err) override { err = oscr::E_COMANDO; return false; }
      bool read(uint8_t, uint8_t, uint32_t, uint8_t *, uint16_t) override { return false; }
      bool write_begin(uint8_t, uint32_t, uint16_t & err) override { err = oscr::E_COMANDO; return false; }
      bool write_block(uint32_t, uint8_t const *, uint16_t) override { return false; }
      bool write_commit() override { return false; }

    private:
      /** Lê o cabeçalho do cartucho (preenche cartSize, saveType, sramSize...) antes de ler ou gravar. */
      bool prepare(uint16_t & err)
      {
        oscr::DetectInfo d;
        detect(oscr::SYS_MD, d);
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

  [[ noreturn ]] void fatal()
  {
    errorFlag = true;
    if (armed) longjmp(escape, 1);

    // Erro fora de um comando (por exemplo no setup): nada a fazer além de parar com a serial muda.
    for (;;) {}
  }

  void setup()
  {
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
