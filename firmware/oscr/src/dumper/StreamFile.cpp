// SPDX-License-Identifier: GPL-3.0-or-later
// Ver include/dumper/StreamFile.h.
#include "config.h"

#if OSCR_DUMPER
# include "api/Storage.h"
# include "dumper/Dumper.h"

namespace OSCR::Storage
{
  StreamSd sd;

  bool StreamFile::open(char const *, oflag_t oflag)
  {
    opened = true;
    writing = (oflag & (O_WRITE | O_CREAT | O_TRUNC)) != 0;
    writeError = false;
    pos = 0;
    hasPeek = false;
    return true;
  }

  bool StreamFile::open(uint32_t, oflag_t oflag)
  {
    return open(static_cast<char const *>(nullptr), oflag);
  }

  bool StreamFile::close()
  {
    opened = false;
    return true;
  }

  size_t StreamFile::write(uint8_t const * buf, size_t count)
  {
    if (!writing) { writeError = true; return 0; }
    oscr::StreamSink * out = OSCR::Dumper::sink();
    if (out == nullptr)                       // sem comando em andamento (por exemplo um registro): descarta
    {
      pos += count;
      return count;
    }
    if (!out->write(buf, count)) { writeError = true; return 0; }
    pos += count;
    return count;
  }

  size_t StreamFile::write(uint8_t byte)
  {
    return write(&byte, 1);
  }

  int StreamFile::read(void * buf, size_t count)
  {
    if (writing) return 0;                     // reler o que acabou de gravar (soma de verificação): não existe, o PC confere o CRC32
    uint8_t * dst = static_cast<uint8_t *>(buf);
    size_t got = 0;
    if (hasPeek && count)
    {
      dst[got++] = peeked;
      hasPeek = false;
    }
    oscr::StreamSource * in = OSCR::Dumper::source();
    if (in != nullptr && got < count) got += in->read(dst + got, count - got);
    pos += got;
    return static_cast<int>(got);
  }

  int StreamFile::read()
  {
    uint8_t b;
    return read(&b, 1) == 1 ? b : -1;
  }

  int StreamFile::peek()
  {
    if (!hasPeek)
    {
      uint8_t b;
      oscr::StreamSource * in = OSCR::Dumper::source();
      if (writing || in == nullptr || in->read(&b, 1) != 1) return -1;
      peeked = b;
      hasPeek = true;
      pos++;                                   // o byte já saiu do fluxo
    }
    return peeked;
  }

  size_t StreamFile::readBytesUntil(char terminator, uint8_t * buf, size_t count)
  {
    size_t n = 0;
    while (n < count)
    {
      int c = read();
      if (c < 0 || c == static_cast<uint8_t>(terminator)) break;
      buf[n++] = static_cast<uint8_t>(c);
    }
    return n;
  }

  uint64_t StreamFile::fileSize() const
  {
    if (writing) return pos;
    oscr::StreamSource * in = OSCR::Dumper::source();
    return in ? in->size() : 0;
  }

  uint64_t StreamFile::available64() const
  {
    if (writing) return 0;
    uint64_t total = fileSize();
    return total > pos ? total - pos : 0;
  }

  bool StreamFile::seekSet(uint64_t p)
  {
    return p == pos;                           // fluxo sequencial: só "ficar onde está" é possível
  }

  bool StreamFile::seekEnd(int64_t offset)
  {
    return offset == 0 && pos == fileSize();
  }
}
#endif /* OSCR_DUMPER */
