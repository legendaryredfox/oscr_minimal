/********************************************************************
*        Open Source Cartridge Reader for Arduino Mega 2560        */
/*H******************************************************************
* FILENAME :        ClockedSerial.cpp
*
* DESCRIPTION :
*       Modified HardwareSerial class for using with a dynamic clock speed.
*
* PUBLIC FUNCTIONS :
*       void    DynamicClockSerial::begin(baud, config, sclock)
*
* LICENSE :
*       This program is free software: you can redistribute it and/or modify
*       it under the terms of the GNU General Public License as published by
*       the Free Software Foundation, either version 3 of the License, or
*       (at your option) any later version.
*
*       This program is distributed in the hope that it will be useful,
*       but WITHOUT ANY WARRANTY; without even the implied warranty of
*       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*       GNU General Public License for more details.
*
*       You should have received a copy of the GNU General Public License
*       along with this program.  If not, see <https://www.gnu.org/licenses/>.
*
* CHANGES :
*
* REF NO    VERSION  DATE        WHO            DETAIL
*           12.5     2023-03-29  Ancyker        Initial version
*
*H*/

#include "arch/avr/generic/interfaces/ClockedSerial.h"

#if defined(OSCR_ARCH_AVR)

# include <util/atomic.h>
# include "common/Power.h"

# define F_CPU_FULL (F_CPU)
# define F_CPU_HALF (F_CPU / 2)

# if defined(ENABLE_STATIC_BAUD)
#   define MIN_BAUD_HIGH (((F_CPU_FULL / 4) / 8191) + 1)
#   define MIN_BAUD_LOW (((F_CPU_HALF / 4) / 8191) + 1)

#   if ((OSCR_BAUD < MIN_BAUD_HIGH) || (OSCR_BAUD == 57600))
#     define U2X_NEVER
#     define BAUD_SETTING_HIGH ((((F_CPU_FULL / 8) / OSCR_BAUD) - 1) / 2)
#     define BAUD_SETTING_LOW  ((((F_CPU_HALF / 8) / OSCR_BAUD) - 1) / 2)
#   elif (OSCR_BAUD > MIN_BAUD_LOW)
#     define U2X_ALWAYS
#     define BAUD_SETTING_HIGH ((((F_CPU_FULL / 4) / OSCR_BAUD) - 1) / 2)
#     define BAUD_SETTING_LOW  ((((F_CPU_HALF / 4) / OSCR_BAUD) - 1) / 2)
#   else
#     define U2X_WHEN_HIGH
#     define BAUD_SETTING_HIGH ((((F_CPU_FULL / 4) / OSCR_BAUD) - 1) / 2)
#     define BAUD_SETTING_LOW  ((((F_CPU_HALF / 8) / OSCR_BAUD) - 1) / 2)
#   endif


constexpr uint32_t const kBaudSettingHigh = BAUD_SETTING_HIGH;
constexpr uint32_t const kBaudSettingLow = BAUD_SETTING_LOW;

# else
#   define F_CPU_FULL_DIV_4 (F_CPU_FULL / 4)
#   define F_CPU_FULL_DIV_8 (F_CPU_FULL / 8)

#   define F_CPU_HALF_DIV_4 (F_CPU_HALF / 4)
#   define F_CPU_HALF_DIV_8 (F_CPU_HALF / 8)

#   define MIN_BAUD_HIGH ((F_CPU_FULL_DIV_4 / 8191) + 1)
#   define MIN_BAUD_LOW ((F_CPU_HALF_DIV_4 / 8191) + 1)

constexpr uint32_t const kCPUHigh = F_CPU_FULL;
constexpr uint32_t const kCPULow = F_CPU_HALF;

constexpr uint32_t const kDivHighFCPU4 = F_CPU_FULL_DIV_4;
constexpr uint32_t const kDivHighFCPU8 = F_CPU_FULL_DIV_8;

constexpr uint32_t const kDivLowFCPU4 = F_CPU_HALF_DIV_4;
constexpr uint32_t const kDivLowFCPU8 = F_CPU_HALF_DIV_8;

constexpr uint32_t const kBaudMinimumHigh = MIN_BAUD_HIGH;
constexpr uint32_t const kBaudMinimumLow = MIN_BAUD_LOW;
# endif


/**
 * @brief Serial interface that supports a dynamic clock speed
 *
 * This function is unchanged, including comments, from HardwareSerial. Comments not from
 * the original function are denoted with a prefix of "(ClockedSerial)".
 *
 * The parameter `sclock` is used to let it know the clockspeed. It replaces the usage of
 * the F_CPU preprocessor variable. Unlike `clock_prescale_set` this parameter is the
 * speed in MHz, i.e. 16000000 (16MHz).
 *
 * @sa https://docs.arduino.cc/language-reference/en/functions/communication/serial/
 */
void DynamicClockSerial::begin(uint32_t baud, uint8_t config, uint32_t sclock)
{
  baudRate = baud;

  clockSkew(sclock);

  _written = false;

  //set the data bits, parity, and stop bits
# if defined(__AVR_ATmega8__)
  config |= 0x80; // select UCSRC register (shared with UBRRH)
# endif

  *_ucsrc = config;

  sbi(*_ucsrb, RXEN0);
  sbi(*_ucsrb, TXEN0);
  sbi(*_ucsrb, RXCIE0);
  cbi(*_ucsrb, UDRIE0);
}

void DynamicClockSerial::begin()
{
  begin(OSCR_BAUD, SERIAL_8N1, OSCR::Clock::getClock());
}

void DynamicClockSerial::begin(uint32_t baud)
{
# if defined(ENABLE_STATIC_BAUD)
  begin();
# else
  begin(baud, SERIAL_8N1, OSCR::Clock::getClock());
# endif
}

void DynamicClockSerial::begin(uint32_t baud, uint8_t config)
{
# if defined(ENABLE_STATIC_BAUD)
  begin(OSCR_BAUD, config, OSCR::Clock::getClock());
# else
  begin(baud, config, OSCR::Clock::getClock());
# endif
}

void DynamicClockSerial::begin(uint32_t baud, uint32_t sclock)
{
# if defined(ENABLE_STATIC_BAUD)
  begin(OSCR_BAUD, SERIAL_8N1, sclock);
# else
  begin(baud, SERIAL_8N1, sclock);
# endif
}

void DynamicClockSerial::clockSkew(uint32_t sclock)
{
  if (clockSpeed == sclock) return; // unchanged

# if defined(ENABLE_STATIC_BAUD)
  uint16_t baud_setting = (F_CPU_FULL == sclock) ? kBaudSettingHigh : kBaudSettingLow;

#   if defined(U2X_NEVER)
  uint16_t const ucsra_setting = 0;
#   elif defined(U2X_ALWAYS)
  uint16_t const ucsra_setting = 1 << U2X0;
#   else
  uint16_t const ucsra_setting = (F_CPU_FULL == sclock) ? (1 << U2X0) : 0;
#   endif

# else
  uint16_t baud_setting, ucsra_setting;
  uint16_t const minimumBaud = ((F_CPU == sclock) ? kBaudMinimumHigh : kBaudMinimumLow);
  uint16_t const clockDiv4 = (F_CPU == sclock) ? kDivHighFCPU4 : kDivLowFCPU4;
  uint16_t const clockDiv8 = (F_CPU == sclock) ? kDivHighFCPU8 : kDivLowFCPU8;

#   if defined(__ATMEGA8U2_USB_TO_UART__)
  if (((sclock == F_CPU) && (baud == 57600)) || (baudRate < minimumBaud))
#   else
  if (baudRate < minimumBaud)
#   endif
  {
    baud_setting = (clockDiv8 / baudRate - 1) / 2;
    ucsra_setting = 0;
  }
  else
  {
    baud_setting = (clockDiv4 / baudRate - 1) / 2;
    ucsra_setting = 1 << U2X0;
  }
# endif

  /**
   * Flush buffer first or the data will corrupt.
   */
  if (clockSpeed > 0) flush();

  // Save clock speed
  clockSpeed = sclock;

  // Update UART registers
  *_ucsra = ucsra_setting;
  *_ubrrh = baud_setting >> 8;
  *_ubrrl = baud_setting;
}

void DynamicClockSerial::clockSkewAtomic(uint32_t sclock)
{
  if (clockSpeed == sclock) return; // unchanged

  ATOMIC_BLOCK(ATOMIC_FORCEON)
  {
    clockSkew(sclock);
  }
}

// ClockedSerial setup
# if !defined(NO_GLOBAL_INSTANCES) && !defined(NO_GLOBAL_SERIAL) && !defined(ENABLE_SERIAL) && defined(ENABLE_UPDATER)
#   if defined(UBRRH) && defined(UBRRL)
    DynamicClockSerial ClockedSerial(&UBRRH, &UBRRL, &UCSRA, &UCSRB, &UCSRC, &UDR);
#   else
    DynamicClockSerial ClockedSerial(&UBRR0H, &UBRR0L, &UCSR0A, &UCSR0B, &UCSR0C, &UDR0);
#   endif

#   if defined(USART_RX_vect)
    ISR(USART_RX_vect)
#   elif defined(USART0_RX_vect)
    ISR(USART0_RX_vect)
#   elif defined(USART_RXC_vect)
    ISR(USART_RXC_vect) // ATmega8
#   else
#     error "Don't know what the Data Received vector is called for Serial"
#   endif
    {
      ClockedSerial._rx_complete_irq();
    }

#   if defined(UART0_UDRE_vect)
  ISR(UART0_UDRE_vect)
#   elif defined(UART_UDRE_vect)
  ISR(UART_UDRE_vect)
#   elif defined(USART0_UDRE_vect)
  ISR(USART0_UDRE_vect)
#   elif defined(USART_UDRE_vect)
  ISR(USART_UDRE_vect)
#   else
#     error "Don't know what the Data Register Empty vector is called for Serial"
#   endif
  {
    ClockedSerial._tx_udr_empty_irq();
  }

  bool Serial0_available()
  {
    return ClockedSerial.available();
  }
# endif

#endif /* OSCR_ARCH_AVR */
