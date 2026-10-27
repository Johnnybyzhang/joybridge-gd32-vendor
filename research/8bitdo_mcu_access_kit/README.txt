8BitDo receiver: full-flash access and bootloader replacement
GD32F103C8T6, LQFP48
Analysis date: 2026-10-25
Revision: live-probe reference-check fix

DECISION
========

There is NO factory USB DFU bootloader on this GD32F103C8. Its immutable
factory bootloader uses USART0 on PA9/PA10. Holding BOOT0 high does not make
this chip enumerate as a dfu-util device.

The existing 8BitDo USB update loader is custom HID, VID:PID 0483:5760.
The user's live probe now confirms operation 0x31 reading two identical copies
of metadata at 0x08003000, boot vectors at 0x08000000, and application vectors
at 0x08003400. All 12 HID transactions succeeded. The earlier probe stopped
only because its reference comparison included a device-specific ID word.
This revision corrects that check; see evidence/PROBE01_ANALYSIS.txt.
Full-range reads, physical capacity, read-protection behavior, and an
unrestricted USB erase/bootloader-write path remain unestablished.

For a supported complete erase and replacement path, trace SWDIO, SWCLK,
NRST, GND and the target voltage reference. A factory UART ISP route is
also available if its pins are easier to reach.

Author-side verification uses the supplied capture, updater disassembly,
recovered firmware, and an exact offline replay of the user's live probe.
The author did not connect to hardware. The read-only probe issued no
flash-write, erase, or unlock operation. The SWD instructions remain a
reviewed command path, not a hardware-tested flashing session.

WHAT IS IN THIS KIT
==================

usb/usb_readonly_backup.py       Experimental USB read-only probe and dumper
usb/README.md                    Full USB instructions and limitations
usb/verify_offline.py            Offline protocol verification
swd/receiver-cmsis-dap.cfg        SWD transport with connect under reset
swd/inspect.cfg                  Identification/protection inspection
swd/SWD_WORKFLOW.txt             Backup, erase, replacement and restore path
reference/v2.05_decrypted.bin     Previously recovered application reference
evidence/PROBE01_ANALYSIS.txt     Live readback diagnosis and the narrow fix
evidence/USB_PROTOCOL.txt        Original capture/DLL protocol analysis
evidence/selected_capture_packets.json  Exact selected USB wire records
evidence/openocd_source_revision.json   Official source revision checked
SHA256SUMS.txt                   File integrity hashes

Only the USB reader and the two initial SWD configuration files are runnable
helpers. The USB reader has no flash-write, erase, unlock, reset, or updater
command. Destructive SWD commands appear explicitly in SWD_WORKFLOW.txt.

PATH 1: TRY USB READBACK FIRST
============================

1. Close the 8BitDo updater and other programs accessing this receiver.
2. Put it into the same 8BitDo update mode used for the capture. If using
   the physical pairing-button procedure, hold the button while plugging
   it in. Confirm enumeration as 0483:5760; that identity is the actual gate.
   This is the vendor HID loader, not the factory UART bootloader.
3. Use Python 3 and install the HIDAPI wrapper on the machine with the USB
   receiver connected:

     python -m pip install hidapi

   The package is named hidapi and provides the Python module named hid.
   On Windows it uses the normal HID driver; this workflow does not require
   rebinding the receiver to WinUSB. Linux may require a hidraw permission
   rule. Do not launch the updater while this script owns the device.

4. From the root of the extracted kit, list candidate HID devices:

     python usb/usb_readonly_backup.py list

   Inspect the manufacturer/product/interface and choose the intended
   receiver's index. VID/PID alone is not a globally unique device identity.

5. Try the short read-only probe, substituting that index for 0:

     python usb/usb_readonly_backup.py probe --device-index 0 --out probe-01 --reference-app reference/v2.05_decrypted.bin

   The output directory must not already exist. The script reads the known
   metadata, boot vectors and application vectors twice, saves raw reports,
   and compares the results. The reference check is appropriate when this
   receiver still has v2.05 installed. Omit --reference-app for a different
   installed application version, retaining the vector plausibility checks.
   The first 28 application bytes must match; the word at +0x1C may differ
   only when the reference contains the erased 0xFFFFFFFF ID placeholder.
   The returned ID is retained in the dump and recorded in status.json.

6. If the probe succeeds, request a 128 KiB candidate flash span:

     python usb/usb_readonly_backup.py dump --device-index 0 --out backup-01 --length 0x20000 --reference-app reference/v2.05_decrypted.bin

   This command repeats the probe in the same connection before reading.
   It preserves two complete reads, compares them, and checks included
   probe spans against the dump. It creates flash_backup.bin only after
   these checks succeed. It never interprets 128 KiB as a proven capacity.

   The optional --path-sha256 value printed by list binds the selection to
   that HID path, avoiding index drift if other devices appear or disappear.

If the command times out, rejects a reply, or fails a vector check, stop and
retain status.json and raw_requests_replies.jsonl. The original capture
used reads after an update; the user's later probe succeeded using only read
commands in its recorded session. Future failures could still reflect
session state or address limits. It does not prove read protection. Do not
perform an update or send write opcode 0x32 merely to make the probe work.

Successful repeated reads establish reproducibility of returned bytes; the
protocol has no echoed address or validated application checksum. Compare
known application code at its expected offsets before using a dump as a
restoration image. A failed conservative vector check can also mean a
different legitimate bootloader/SRAM layout; the raw bytes are retained.

PATH 2: SWD FOR DUMP / WIPE / REPLACEMENT
======================================

MCU signal     LQFP48 lead      Debug-probe connection
PA13/SWDIO     34               SWDIO
PA14/SWCLK     37               SWCLK
NRST           7               Probe-supported nRESET
VSS           23,35,47         Ground
VDD           24,36,48         VTref on probes requiring a target reference

Use the board's existing 3.3 V logic rail. A probe VTref input is not another
power supply. The board can be powered by its USB connector with common GND.
Only use a probe/firmware combination that actually drives the reset line.

The stock application DISABLES BOTH SWD AND JTAG during GPIO setup. The
instruction at 0x08005918 calls a remap helper selecting SWJ_CFG=4. This is
why NRST matters: attach under hardware reset before that instruction runs.
An ordinary attach failure is not sufficient evidence of read protection.

With OpenOCD installed and a CMSIS-DAP probe wired as above, change into
the swd directory and start with:

     openocd -f receiver-cmsis-dap.cfg -l receiver-identify.log -f inspect.cfg

This inspects target IDs, flash geometry, raw option bytes and active
protection state. It performs hardware reset/halt but no flash or option
writes. If the log reports a different actual SW-DP ID, the full workflow
explains the CPUTAPID override. Do not guess a flash size override yet.

Read SWD_WORKFLOW.txt for the full, separate backup and destructive stages.
It includes commands for two candidate 128 KiB main-flash reads, option
bytes, the electronic signature, verification, a mass erase, installation
at 0x08000000, and restoration. A new standalone application can itself be
linked at 0x08000000; a custom flash bootloader is optional for SWD use.

READ PROTECTION AND BACKUP SIZE
==============================

GD32F103 uses SPC=0xA5 for unprotected flash, with complement 0x5A. The
unprotected halfword at 0x1FFFF800 is therefore 0x5AA5. This is not the
0xAA convention used by various later STM32 families.

Changing a protected part back to unprotected automatically mass-erases
main flash. Neither factory UART nor SWD can first dump protected main
flash through the ordinary documented read path. Do not run an unlock or
option-writing operation during the backup phase. The proprietary loader
runs user code in main flash, so its readback behavior under protection
must be tested separately; it is not established by the capture.

The C8 nominal specification is 64 KiB, but your recorded update starts at
0x08003400 and ends at 0x0801BA00 exclusive. A 64 KiB file cannot cover that
recorded image. Investigate the 128 KiB address span and compare valid code
above 0x08010000 with the recovered image before erasing. The flash density
register at 0x1FFFF7E0, the debugger's geometry and actual contents must be
reconciled. Repeated or aliased upper bytes are not proof of extra flash.

A complete main-flash backup starts at 0x08000000, not at the application
address 0x08003400. It must retain the loader/configuration prefix and the
remaining flash after the application's recorded end. The old .dat recovery
does not include this lower prefix or the rest of main flash.

Save the 16 option bytes at 0x1FFFF800 separately. They configure protection
and boot/watchdog behavior, and should not be blindly restored as ordinary
flash. The 20-byte region at 0x1FFFF7E0 records density and the factory ID.
For an archival copy of the medium-density factory system-memory region,
an optional SWD read is: dump_image receiver-system.bin 0x1ffff000 0x800.
This region is not needed to restore the replaceable 8BitDo loader.

PATH 3: FACTORY UART ISP, WITHOUT SWD
===================================

MCU signal     LQFP48 lead      Connection / state
PA9            30              MCU TX -> 3.3 V USB-UART adapter RX
PA10           31              MCU RX <- 3.3 V USB-UART adapter TX
BOOT0          44              High when reset is released
PB2/BOOT1      20              Low when reset is released
NRST            7              Pulse low after setting boot straps
VSS                            Adapter ground

Use 3.3 V UART logic, not RS-232 voltage levels. Check existing board
connections before driving boot strap pins. PA2/PA3, the Bluetooth HCI
UART identified earlier, are NOT this C8 device's factory ISP port.

1. Set BOOT0=1 and BOOT1=0, then reset the MCU.
2. Open GigaDevice's GD32 All-In-One Programmer and select its UART/serial
   interface, the correct COM port, and the GD32F103 target.
3. The factory protocol is 8 data bits, EVEN parity, one stop bit. Start at
   115200 baud, within the documented 1200-115200 range. If inspecting the
   protocol manually, sync byte 0x7F should receive ACK 0x79. The official
   programmer handles this exchange; no manual terminal is needed.
4. Identify the part and protection state, and use memory-read/save to
   preserve main flash and options before any erase. Apply the same size
   discrepancy checks as the SWD path. If a GUI refuses the required upper
   range, do not call its 64 KiB output a full backup.
5. Once backup is complete or loss of protected contents has been accepted,
   erase main flash and program the replacement raw image at 0x08000000
   (or use the actual addresses in an ELF/HEX image). Verify the written data.
6. Return BOOT0 to zero and reset to boot main flash.

Actual GUI labels can vary with the programmer version. Its support for
DFU on other chip families does not add USB DFU to this chip's ROM.

WHAT CAN BE REPLACED
===================

The 8BitDo bootloader, application, and user configuration in main flash
can be erased/replaced subject to protection settings. GigaDevice's factory
system-memory loader and factory signature cannot be erased/programmed by
the user. A main-flash mass erase leaves the UART ROM recovery path intact.

A future board-compatible USB DFU loader could be installed in main flash
over SWD or UART, making dfu-util useful afterward. That requires an actual
GD32/board-compatible build, correct clock/USB setup, and matching application
offset/vector relocation. This kit does not include such a replacement
firmware image and does not assume a generic Blue Pill image will work.

PRIMARY REFERENCES
==================

GigaDevice GD32F103xx Datasheet Rev3.3: boot modes, section3.4 p48;
LQFP48 pin definitions, Table2-8 pp42-44.
https://www.gd32mcu.com/download/down/document_id/237/path_type/1

GigaDevice AN002 Programming Flash Memory Manual: supported bootloader
interfaces, Table10 p9; UART framing/commands, Tables11-13 pp9-10.
https://www.gd32mcu.com/download/down/document_id/9/path_type/1

GigaDevice GD32F10x User Manual Rev2.9: memory/signature pp42-45;
option bytes and security protection pp52-53; AFIO remapping chapter7.
https://www.gd32mcu.com/data/documents/userManual/GD32F10x_User_Manual_Rev2.9.pdf

Official programmer downloads:
https://www.gd32mcu.com/en/download/7

OpenOCD flash driver compatibility, flash/option commands:
https://openocd.org/doc/html/Flash-Commands.html
OpenOCD memory read/verify commands:
https://openocd.org/doc/html/General-Commands.html
OpenOCD connect-under-reset:
https://openocd.org/doc/html/Reset-Configuration.html

HIDAPI Python wrapper and report-ID API contract:
https://github.com/trezor/cython-hidapi
https://libusb.info/hidapi/group__API.html

Board-specific conclusions additionally use the user's capture, native
updater DLL and recovered firmware. Evidence files retain the frame numbers,
instruction addresses, exact bytes and remaining uncertainties.
