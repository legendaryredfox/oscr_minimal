#include "oscr_proto.h"

namespace oscr {

static const uint32_t kTab[16] = {
    0x00000000, 0x1DB71064, 0x3B6E20C8, 0x26D930AC, 0x76DC4190, 0x6B6B51F4, 0x4DB26158, 0x5005713C,
    0xEDB88320, 0xF00F9344, 0xD6D6A3E8, 0xCB61B38C, 0x9B64C2B0, 0x86D3D2D4, 0xA00AE278, 0xBDBDF21C};

uint32_t crc32_update(uint32_t start, const uint8_t* d, size_t n) {
  uint32_t c = ~start;
  while (n--) {
    uint8_t b = *d++;
    c = kTab[(c ^ b) & 0x0F] ^ (c >> 4);
    c = kTab[(c ^ (b >> 4)) & 0x0F] ^ (c >> 4);
  }
  return ~c;
}

size_t encode_frame(uint8_t* out, uint8_t type, uint8_t seq, const uint8_t* payload, uint16_t len) {
  out[0] = MAGIC0; out[1] = MAGIC1; out[2] = type; out[3] = seq;
  put_u16(out + 4, len);
  for (uint16_t i = 0; i < len; i++) out[6 + i] = payload ? payload[i] : 0;
  put_u32(out + 6 + len, crc32_update(0, out + 2, 4 + len));
  return size_t(10) + len;
}

bool Decoder::push(uint8_t b) {
  switch (st_) {
    case S_M0: if (b == MAGIC0) st_ = S_M1; break;
    case S_M1:
      if (b == MAGIC1) { st_ = S_TYPE; crc_ = 0; }
      else if (b != MAGIC0) st_ = S_M0;
      break;
    case S_TYPE: type = b; crc_ = crc32_update(crc_, &b, 1); st_ = S_SEQ; break;
    case S_SEQ:  seq = b;  crc_ = crc32_update(crc_, &b, 1); st_ = S_L0; break;
    case S_L0:   len = b;  crc_ = crc32_update(crc_, &b, 1); st_ = S_L1; break;
    case S_L1:
      len |= uint16_t(b) << 8; crc_ = crc32_update(crc_, &b, 1);
      if (len > OSCR_MAX_PAYLOAD || len > cap_) { fail(); break; }
      got_ = 0; st_ = len ? S_PAY : S_C0;
      break;
    case S_PAY:
      buf_[got_++] = b; crc_ = crc32_update(crc_, &b, 1);
      if (got_ == len) st_ = S_C0;
      break;
    case S_C0: rx_ = b; st_ = S_C1; break;
    case S_C1: rx_ |= uint32_t(b) << 8; st_ = S_C2; break;
    case S_C2: rx_ |= uint32_t(b) << 16; st_ = S_C3; break;
    case S_C3:
      rx_ |= uint32_t(b) << 24; st_ = S_M0;
      if (rx_ == crc_) return true;
      bad++;
      break;
  }
  return false;
}

}  // namespace oscr
