8BitDo receiver: keeping the installed bootloader for custom firmware
====================================================================

Verdict
-------
The installed bootloader does not require a digitally signed application.
Keeping it is a practical path to using this receiver as a development board.
The USB upload protocol requires the recovered GD32 scrambling format, but the
normal update and launch paths do not authenticate the application body.

This conclusion is based on this receiver's complete flash readback, reachable
instruction analysis, and offline execution of the original loader instructions.
An independently encoded unsigned synthetic application was accepted by the
original update handler in emulation. No custom firmware has been flashed to
the physical receiver as part of this analysis.

Device: original 8BitDo USB receiver, GD32F103C8T6 MCU.
Source: backup-01, two complete 128 KiB reads from 0x08000000.
Both reads and flash_backup.bin have identical SHA256:
  e2139cea93cf56bc11e8455a23b60d2c61e4d9245e2da74e801901ab7585d1a6
Loader prefix 0x08000000..0x08002FFF SHA256:
  8d733de72baf8cc04ce3ada92e3df39be405b55587a749514c0c756eaad38692

1. Evidence for accepting an unsigned application
------------------------------------------------
Three separate analyses agree:

A. Original block decoder
   The real routines at 0x0800090C, 0x080026C4 and 0x080027F8 recover all
   99,840 bytes of captured v2.05 exactly. They also recover a new 1,536-byte
   arbitrary payload encrypted independently with the included cryptdo8.py.
   This test executes the original seed table and decoder initialization.
   It has no peripheral stubs and does not run any programming handler.

B. Original USB dispatcher and update handler
   The real dispatcher at 0x0800247C, handler at 0x0800100C, decoder, erase-loop
   helper and write-if-erased helper accept a new 1,024-byte synthetic image.
   The test image has valid vector words, an infinite-loop reset stub and
   arbitrary remaining contents; it is not an operational board application.
   It is independently encoded, has version 0x12345678 and the arbitrary text
   "not-a-signature!" in the final 16 bytes of its 28-byte transfer header.
   Decoded contents and installed version/tag bytes match expectations.

   A second case flips a ciphertext byte and supplies arbitrary tag words
   0x11111111, 0x22222222 and 0x33333333. The handler still acknowledges the
   update. Thus neither image authentication nor supplied-tag authentication
   is enforced by this path. A malformed image can still be accepted.

   Negative controls reject a wrong application base and a simulated flash
   programming/readback mismatch. A second tag installation is rejected
   because its destination words are no longer erased.

   Only low-level FMC hardware operations and USB reply transport are mocked.
   Flash contents, erase requests and programmed halfwords are tracked in
   emulator memory. The real MCU's programming hardware was not exercised.

C. Original startup and launch path
   Normal startup reaches the application with its installed ID, with erased
   application ID words, and with arbitrary application-body contents.
   The only application flash reads before handoff are the initial stack
   pointer and reset-vector words. The loader does not hash or scan the body.
   Clock/GPIO setup, busy delay and option-byte hardware maintenance are stubbed
   for this trace; their routines were examined separately. Execution stops at
   the application entry address, so this is not an application-runtime test.

The minimal launch check at 0x0800137C is:

  if ((*(uint32_t *)0x08003400 & 0x2FFE0000) != 0x20000000)
      return;
  destination = *(uint32_t *)0x08003404;
  set_MSP(*(uint32_t *)0x08003400);
  // The actual routine then pops two words: see the handoff caveat below.
  branch_to(destination);

This is a loose SRAM-address check, not complete vector-table validation.
The application must supply a valid aligned SRAM stack and a Thumb reset entry.

2. Scrambling, device identity and signatures are separate mechanisms
--------------------------------------------------------------------
The upload payload is reversibly scrambled in 512-byte blocks. The algorithm
and seed table are recovered, and an independent encoder is demonstrated to
interoperate with the original decoder. No private signing key is needed.

The three words at application offsets +0x1C, +0x20 and +0x24 are device-ID
stamps. Stock v2.05 validates them in its own code at 0x0800BC64:

  tag[i] = UID[i] XOR key[UID[i] & 15], for i = 0, 1, 2

That check binds the stock application to a UID. It contains no digest of the
application body. A new application need not implement it. The loader's
SET_ENCODE_ID command accepts supplied tag values and writes erased slots;
the normal launch path does not validate the application tags.

The installed v2.05 image differs from the recovered distribution image only
in these 12 tag bytes and the four-byte version word at application +0x34.
All other bytes of the complete 99,840-byte application match exactly.

3. Flash layout for a custom application
---------------------------------------
Use these limits while keeping the existing loader and its recovery behavior:

  0x08000000..0x08002FFF  12 KiB      Existing loader: preserve
  0x08003000..0x080033FF   1 KiB      Vendor metadata: preserve
  0x08003400..0x0801F3FF 112 KiB      Application slot
  0x0801F400..0x0801FFFF   3 KiB      Loader-owned scratch/maintenance area

Application linker FLASH origin: 0x08003400
Application linker FLASH length: 0x1C000 (114,688 bytes)
Application vector-table address: 0x08003400

The top 3 KiB must remain outside the application's code, constants and
nonvolatile storage. Update exit subcommand 0x02 erases all three 1 KiB pages.
On startup, a non-erased first word at 0x0801F400 or 0x0801F800 also causes
cleanup of this area followed by a halt. Reset is then needed to continue.

112 KiB is the usable layout limit derived from this loader, not a new
manufacturer capacity rating. The dump contains distinct stock application
code above the nominal C8 64 KiB boundary, through 0x0801B9FF. The top end of
the proposed slot has not been qualified by a new physical write test.

Leave the following words erased (0xFFFFFFFF) in the uploaded plaintext if
using the normal update sequence:

  App offset    MCU address    Loader use
  +0x1C         0x0800341C     Device tag word 0
  +0x20         0x08003420     Device tag word 1
  +0x24         0x08003424     Device tag word 2
  +0x34         0x08003434     Version from transfer header

These are reserved Cortex-M3 vector positions. Some startup templates fill
reserved entries with zero; those four slots need explicit attention.
Their required erase state is a programming-format constraint, not a signature.

4. Application startup must accommodate the loader's handoff
-----------------------------------------------------------
The loader does not produce a fresh hardware-reset state before branching.
It leaves VTOR at 0x08000000 and enables SysTick and an NVIC interrupt during
its normal reset path. A custom application must initialize its own state.

There is an additional concrete bug in launch routine 0x0800137C:
  0x0800138E calls the helper that sets MSP to vector word 0.
  0x08001394 then executes POP {r4, lr} using that new MSP.
  0x08001398 branches to the application's reset vector.

Consequently the application sees MSP = vector_word_0 + 8. Both popped words
must lie in real readable SRAM before the application executes anything.
Merely correcting MSP after entry is insufficient if those reads are already
outside SRAM. Avoid the common initial-SP value of 0x20005000, one past the
20 KiB SRAM region. Reserve headroom; for example, vector SP 0x20004FE0 keeps
both reads in SRAM and leaves room above it for the boot-entry marker.

Use an early assembly reset stub that masks interrupts, restores the intended
MSP before a C prologue, disables/clears inherited interrupt state as needed,
sets VTOR to 0x08003400 with appropriate barriers, and then performs normal
runtime and clock/peripheral initialization. Do not rely on incoming LR, r4
or other register values, and do not return from Reset_Handler.

This report is a set of startup requirements, not a compiled startup file.
The stock application's entry state in the offline trace was:
  vector SP = 0x20003FB8, actual MSP = 0x20003FC0
  VTOR = 0x08000000, PRIMASK = 0
  SysTick CTRL = 7, LOAD = 0x00075300
  NVIC ISER0 bit 20 enabled
Peripheral behavior and asynchronous interrupt delivery were not emulated.

5. Re-entering the existing USB loader
------------------------------------
The loader checks the PA1 active-low button before starting the application.
It requires PA1 low through four samples spanning three busy delays. Hold the
button during reset or power-up to request its normal HID update mode.

The boot-entry test at 0x0800133C also recognizes:
  *(volatile uint32_t *)0x20004FF0 == 0x5A5AA5A5

A custom application can reserve this SRAM word, store the magic and request
a system reset to enter update mode, subject to the normal retention of SRAM
through that reset. The button path provides entry independent of whether the
custom application's USB or Bluetooth code works. The bootloader does not
clear the SRAM marker; the custom application should reserve and clear it as
appropriate. See startup findings for the detailed loader control flow.

6. Uploading uses the existing HID protocol
------------------------------------------
This loader is still the vendor HID loader, not USB DFU for dfu-util. Target
acceptance is established; arbitrary-file acceptance by the vendor Windows
updater UI has not been tested. A small host uploader can follow the captured
HID sequence without changing the loader itself.

The relevant nested subtype 0x16 commands are:
  0x01: submit 28-byte header (version, base, length, 16 ignored bytes)
  0x00: submit encoded data in ordinary 32-byte chunks
  0x06: install the 12-byte device tag into erased slots
  0x02: erase loader scratch area and request exit/start

The accepted header base is exactly 0x08003400. Use a positive payload length
padded with 0xFF to a 512-byte multiple, at most 0x1C000 bytes after padding.
The loader erases to a 1 KiB boundary and checks programmed-halfword readback.
It does not impose a safe application-length upper bound. A rejected header
also leaves caller-supplied base/length in state. A correct client must validate
all bounds itself and stop immediately on every error. No malformed continuing
write sequence was built or tested here.

For a correctly linked and checked app.bin, the included encoder's packaging
command is:
  python recovery/cryptdo8.py encrypt app.bin -c gd32 -v 205 -a 0x08003400 -o app.dat

This only creates a file; it does not transmit or flash anything. The encoder's
generic GD32 maximum is larger than this board's safe application slot, so the
0x1C000 bound must be checked separately. No live uploader is included here.
There is no need to modify metadata opcode 0x32 for the acceptance demonstration;
its separate behavior and length-accounting issue are recorded in update notes.

The loader also performs option-byte/protection maintenance in startup. Flash
readout protection is separate from image signatures. This main-flash dump
does not include the physical option bytes, and emulation does not establish
their current hardware state or the effect of changing them.

7. Evidence and reproduction
---------------------------
All emulation and validation programs in this archive operate on local files.
The update test models flash writes only in emulator memory. It does not use
HID, serial, USB or debug-probe APIs. Synthetic fixtures remain in memory.

Important files:
  bootloader_analysis/backup/backup_validation.json
  bootloader_analysis/backup/bootloader_decoder_emulation.json
  bootloader_analysis/update/update_handler_emulation.json
  bootloader_analysis/startup/emulation_results.json
  bootloader_analysis/update/update_path_findings.txt
  bootloader_analysis/startup/startup_findings.md
  evidence/bootloader_08000000_0x3000.bin
  full_backup/backup-01/flash_backup.bin

The annotated linear disassemblies include literal pools and embedded tables;
interpret reachable code paths, not every linear listing as instructions.
The older application-ID and updater-ID notes under evidence/ are historical
supporting analysis. Their statements about the loader not yet being available
are superseded by the current full dump and the present report.

Install Python dependencies from requirements.txt, then run the commands in
REPRODUCE.txt from the archive root. Reference JSON is included so reading the
findings does not require installing an emulator. Scripts retain the same
relative directory layout as the original analysis workspace.

The independent encoder is AeroModes' 8CryptDo, MIT license, included with its
license. Source: https://github.com/aeromodes/8cryptdo
Analyzed revision: aaffcebafa481631de9c1d722a5693d02234e43a
The source hash is recorded in the decoder emulation JSON.

Hardware documentation used earlier in this investigation:
  GD32F103xx datasheet Rev3.3:
  https://www.gd32mcu.com/download/down/document_id/237/path_type/1
  GD32F10x user manual Rev2.9:
  https://www.gd32mcu.com/data/documents/userManual/GD32F10x_User_Manual_Rev2.9.pdf

Practical next step
-------------------
Retain this loader and build a minimal custom application at 0x08003400 with
the reserved-vector slots and handoff stub described above. Follow it with a
bounded HID uploader and complete readback comparison. The remaining work is
ordinary image layout, startup and transport implementation; application
signing is not a blocker for this recovered loader.
