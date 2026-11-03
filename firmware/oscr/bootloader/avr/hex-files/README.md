# OSCR ATmega2560 Bootloaders
This directory contains several bootloaders for the ATmega2560. Some are intended for a module and others are intended for an ATmega2560 integrated directly onto the OSCR main board.

## Burning a Bootloader
Burning a bootloader to an ATmega2560 is relatively straightforward, but requires having a few things most people will not have. As such, it is only recommended for advanced users or users with a new ATmega2560 that has no bootloader.

### Requirements
Burning a bootloader requires a few tools:
* **ICSP/ISP**: This can be a specialty programmer or you can use another ATmega2560, Arduino Uno, Arduino Nano, etc. Anything using the ATmega328P (typical with Nano clones) will suffice.
* **Cable/Jumpers**: Depending on if you are programming a module or an integrated ATmega2560, you will either need jumper wires for a module or a specialty cable for the integrated ATmega2560. If you are installing the pin headers for the top PCB onto the main board, then you can also use jumpers to burn a bootloader to the integrated ATmega2560 the same way as a module.

### Steps
Before you begin, assuming you are using another microcontroller to do this, you will need to upload the "ArduinoISP" sketch found in the "Examples" menu of any Arduino IDE to the device you want to use to burn a bootloader to your ATmega2560. Then, in the "Tools" menu under "Programmer", you must choose "Arduino as ISP" (***NOT*** "ArduinoISP" -- this is confusingly the name of an obsolete product) before burning the bootloader. If using a specialty device, you will have to follow the instructions for that device. There are too many devices out there with the capability to reasonably create a guide for all of them.

After that, you will need to connect the ATmega2560 to the programmer. How you do this varies based on your hardware version and whether or not you have a module, and if you have a module, how easy it is to remove it from the main PCB. Many modules are hardwired into (soldered to) the main PCB by the power wire that comes off of the USB port. In some cases, this wire can be very short, so removing the module without damaging it might be difficult. Take care when removing and handling the module, as you may rip off the pad on the PCB that the wire is connected to. If you do that, you may need to buy a new module as it is generally difficult to fix.

With that said, if you have HW4 or HW5 with a top PCB connected via the pin headers, you can burn a bootloader without removing the module. You will only need to remove the top PCB and unplug the LCD, after which you can easily access the pin headers which are labeled fairly clearly. The SPI pins are part of the furthest away/longer header on the right-most side. You will also need to connect to the reset pin, which can be found on the closer/shorter top PCB header also on the right-most side. Finally, you need to connect power and ground as well. If you are powering the devices with separate power supplies for some reason, do *not* connect power but ***do*** still connect ground.

For which pins go where, you can follow the guide provided by Arduino located here: https://docs.arduino.cc/built-in-examples/arduino-isp/ArduinoISP/

You will need to use PlatformIO to upload a bootloader from this directory. Simply choose it by adding this under your hardware configuration (replacing the file name with your flavor of bootloader, and changing the upload speed to match):
```
board = atmega2560-urboot
board_bootloader.file = bootloader/avr/hex-files/urboot-<...>.hex
board_upload.speed = 250000
```
*or*
```
board = atmega2560-stk500v2
board_bootloader.file = bootloader/avr/hex-files/stk500v2-<...>.hex
```

The "board" option here is important, as this is where it will get the fuse values to use.

***DANGER:** Here be dragons!* Fuse values were intentionally obscured from this process to reduce the risk of a mistake. If a bootloader becomes corrupt, you can always just burn a new one. However, if you mess up the fuses, you can brick your ATmega2560. So, if you decide to mess with them, make sure you choose the right values. The files for that are in the boards folder of the main project folder. __*You've been warned.*__

## Choosing a Bootloader
There are two main types to choose from: STK500v2 and urboot. When burning a bootloader, it is highly recommended you use urboot. You should only consider the STK500v2 bootloaders if you want to retain full compatibility with the Arduino IDE. Yes, that is the only reason to even consider an STK500v2 bootloader. The urboot bootloaders are smaller, faster, have more features, and are better in every other way.

### Names/Flavors
* `generic` - These will work on any ATmega2560 that meets the other requirements. It is not builder-specific.
* `experimental` - These experimental bootloaders were made to test something specific. You should not use these unless you know what you are doing.
* `...` - All other bootloaders are builder-/vendor-specific and should only be used on those builds. They typically will also have a hardware version and revision in their name. They are provided here for convenience only, in case you need to re-burn a bootloader.

### Variations
A few variants of each bootloader have been provided. Namely, a basic bootloader with nothing OSCR-specific, a bootloader for those with VSelect, and a bootloader with additional support for the integrated/on-board ATmega2560.

* `vsN` - These are bootloaders with support for VSelect. The `N` will either be a 3 or 5 and is the voltage at which VSelect will initially select. Unless you have CBUS support you probably want to stick with `vs3` (3.3V) bootloaders.
* `obmN` - These are bootloaders with support for the integrated/on-board ATmega2560. Like VSelect, the `N` is the mode that it will start in.
* `Nbps` - The `N` is the speed in bits per second at which firmware will be uploaded to the ATmega2560. STK500v2 bootloaders do not have this in their file name as they are all limited to a fixed rate of 115,200 bps. Higher speeds will result in faster flashing of the firmware, however, the upload is more likely to have issues if there is a lot of interference or you are using cheap/damaged USB cables.
  * For those using a module, 250,000 bps is the recommended "safe" speed if you are only updating occasionally.
  * For anyone with an integrated ATmega2560, or those using a module and are more comfortable with uploads failing occasionally, 1,000,000 bps is suitable. Especially for developers who upload frequently to test code as well as users who don't mind retrying an upload every now and then.
  * 2,000,000 bps is only provided pre-compiled as an option for those with the integrated ATmega2560, as the modules seem to have issues with this speed. This is the maximum theoretical speed the ATmega2560 and CH340 (the USB to UART chip used on the main PCB) support. Thus, it may not always work for everyone. Unless you are a developer that is uploading frequently to test new code, you should stick to the 1,000,000 bps bootloader.
* `Ns`/`Nms` - The `N` is the number of seconds (`s`) or milliseconds (`ms`) after a reset that the bootloader will wait for the USB host (your PC, typically) to try to upload firmware. Normally, the ATmega2560 is automatically reset by the UART chip on the board and thus not much time is needed. However, some people disable the auto reset by cutting the auto reset jumper because they do not wish for the ATmega2560 to reset when connecting to it via serial. This is a fairly niche thing, most useful for those who have no display and wish to be able to disconnect and reconnect to the OSCR without having it reset. For those people, a larger window to manually reset is helpful.

## Building a Custom Bootloader
TODO: Write this. Sorry, this is low priority and a fairly advanced user thing as it requires more than just the AVR toolchain (though you may already have the other tools needed if on Linux). You can find more info on the urboot github, though you will need to apply the OSCR-specific patch to have OSCR features. Once you do that, have a look at `build.sh` in the directory below this one for options.

If you are a builder and just want to add the hardware details to the bootloader, contact me (Ancyker/Remy) in Discord and I will compile one for you. Most of the process is just getting the build environment setup, once that's done it takes only a couple seconds to compile one. You'll need to do this anyway to get an ID assigned/added.
