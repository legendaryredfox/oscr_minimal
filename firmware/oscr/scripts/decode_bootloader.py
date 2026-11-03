import click # pyright: ignore[reportMissingImports]
from os import getcwd
from os.path import join, isfile
from SCons.Script import ARGUMENTS # pyright: ignore[reportMissingImports]
from SCons.Errors import UserError # pyright: ignore[reportMissingImports]
import crutils
import subprocess

# 87efff695820c105

OSCR_CLOCKGEN         = (1 <<  0) # Clock Generator
OSCR_VSELECT          = (1 <<  1) # VSelect
OSCR_RTC              = (1 <<  2) # RTC
OSCR_SSR_LCD          = (1 <<  7) # Using LCD from StarshadeRETRO/BigTreeTech
OSCR_OBM              = (1 <<  0) # Integrated ATmega2560
OSCR_CBUS             = (1 <<  1) # Cartridge Bus
OSCR_VOLTMON          = (1 <<  2) # Voltage Monitors
OSCR_STAT_LED         = (1 <<  3) # Status LED
OSCR_SVN_SLT          = (1 <<  5) # Seven-slot Adapter
OSCR_USBC             = (1 <<  6) # Integrated USB C port
OSCR_AUX              = (1 <<  7) # AUX Capability
OSCR_GBX              = (1 <<  0) # GB slot
OSCR_NES              = (1 <<  1) # NES slot
OSCR_FC               = (1 <<  2) # Famicom slot
OSCR_SNES             = (1 <<  3) # SNES/SFC slot
OSCR_N64              = (1 <<  4) # N64 slot
OSCR_MD               = (1 <<  5) # Mega Drive/Genesis slot
OSCR_SMS              = (1 <<  6) # SMS slot
OSCR_GG               = (1 <<  7) # Game Gear slot

print("")
print("")
print("========== ATTACHED OSCR FEATURE CHECKER ==========")
print("")
print("Communicating with bootloader ... ", end="")

result = subprocess.run(["avrdude.exe", "-patmega2560", "-curclock", "-PCOM7", "-b250000", "-qq", "-xid=F.-16.8", "-xshowid"], capture_output=True, text=True)

if (result.returncode != 0):
  print("")
  exit(1)

oscr_string = result.stdout.strip()
oscr_raw = list(reversed([int(oscr_string[i:i + 2], 16) for i in range(0, len(oscr_string), 2)]))

print("ident = " + ''.join('%02X' % x for x in oscr_raw) + " ... ", end="")

if (oscr_raw[0] == 0x05) and (oscr_raw[1] == 0xC1) and (oscr_raw[2] == 0x20):
  print("ok")
else:
  print("invalid")
  print("")
  print(oscr_raw)
  print("")
  exit(1)

oscr_ver = (oscr_raw[3] & 0xF0) >> 4
oscr_rev = (oscr_raw[3] & 0x0F)

oscr_bldrid = oscr_raw[4]
oscr_slots = oscr_raw[5]
oscr_hardware = oscr_raw[6]
oscr_integrated = oscr_raw[7]

print("")
print("")

print("[[ OSCR Hardware Version {ver}, Revision {rev} ]]".format(ver=oscr_ver, rev=oscr_rev))

if (oscr_bldrid > 0):
  print("Builder: ", end="")

  match (oscr_bldrid):
    case 0x69:  print("StarshadeRETRO")
    case _:     print("Unknown")


if (oscr_hardware > 0):
  print("Basic Hardware:")

  if (oscr_hardware & OSCR_CLOCKGEN):
    print(" + Clock Generator");
  if (oscr_hardware & OSCR_VSELECT):
    print(" + Automatic Voltage Select");
  if (oscr_hardware & OSCR_RTC):
    print(" + Real-Time Clock");
  if (oscr_hardware & OSCR_SSR_LCD):
    print(" + StarshadeRETRO LCD");

if (oscr_integrated > 0):
  print("Integrated Hardware:")

  if (oscr_integrated & OSCR_OBM):
    print(" + Integrated ATmega2560");
  if (oscr_integrated & OSCR_CBUS):
    print(" + Cartridge Bus");
  if (oscr_integrated & OSCR_VOLTMON):
    print(" + Voltage Monitoring");
  if (oscr_integrated & OSCR_STAT_LED):
    print(" + Status LED");

  if (oscr_integrated & OSCR_SVN_SLT):
    print(" + Seven-Slot Top PCB");
  if (oscr_integrated & OSCR_USBC):
    print(" + USB C Port");
  if (oscr_integrated & OSCR_AUX):
    print(" + AUX Accessory Port");

if (oscr_slots > 0):
  print("Available Slots:")

  if (oscr_slots & OSCR_GBX):
    print(" + Game Boy");
  if (oscr_slots & OSCR_NES):
    print(" + NES");
  if (oscr_slots & OSCR_FC):
    print(" + Famicom");
  if (oscr_slots & OSCR_SNES):
    print(" + SNES/SFC");
  if (oscr_slots & OSCR_N64):
    print(" + N64");
  if (oscr_slots & OSCR_MD):
    print(" + Mega Drive/Genesis");
  if (oscr_slots & OSCR_SMS):
    print(" + SMS");
  if (oscr_slots & OSCR_GG):
    print(" + Game Gear");

print("")
print("Note: This list is what your bootloader says is physically part of your OSCR. It is not an indication of enabled or added features of the firmware.")
print("")
