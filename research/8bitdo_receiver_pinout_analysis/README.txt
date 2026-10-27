8BITDO RECEIVER: BUTTON / RGB LED / BLUETOOTH HCI PINOUT
======================================================
Analysis date: 2026-10-25 (client date)
Target reported by owner: GD32F103C8T6, LQFP48
Input: 8BitDo_Firmware_Updater_Win_WithFW.zip supplied by owner

RESULT
------
Function                      GPIO     LQFP48 pin    Active level / direction
Button                        PA1      11            Low; internal pull-up
RGB channel, driver mask 1    PB9      46            Low = on
RGB channel, driver mask 2    PB8      45            Low = on
RGB channel, driver mask 4    PB5      41            Low = on
HCI UART TX                   PA2      12            MCU -> Bluetooth RX
HCI UART RX                   PA3      13            Bluetooth TX -> MCU
Radio initialization SCL      PB10     21            Software I2C clock
Radio initialization SDA      PB11     22            Software I2C data
Radio enable/reset control    PB13     26            Driven low, then high

HCI peripheral: GD32 USART1, base 0x40004400 (STM32 naming: USART2).
HCI framing: H4 packets over 8N1 UART, hardware RTS/CTS disabled.
HCI baud: 115,200 during startup, then 1,500,000 after vendor configuration.

The owner confirms the physical LED is RGB, so all three channel pins are
relevant. The firmware proves the pin/mask assignments and active-low drive;
it does not provide reliable physical red/green/blue labels. Do not assume
R/G/B color order from mask order. Drive masks 1, 2 and 4 separately to observe
which die each controls. The normal status and PWM paths select PB5/mask 4.

Button released = PA1 high. Button pressed = PA1 low.
All LED channels off = PB5/PB8/PB9 high. Each channel lights when driven low.
Physical pin numbers are top-view package numbers, counted counterclockwise
from the pin-1 corner; see GigaDevice datasheet Figure 2-6 / Table 2-8.

The GPIO configuration, button polling, LED dispatcher, LED pattern logic,
LED wrapper and LED PWM regions are byte-for-byte identical, at the same
addresses, in v2.04 and v2.05. Evidence is recovered machine code and chip
documentation. The physical board was not electrically probed.

EVIDENCE CHAIN
--------------
1. The capture has one v2.05 update session, bus 2 / device 6, data EP 0x01.
   Header frame: 1345. Data frames: 1353 through 13829 (interleaved with ACKs
   and other USB traffic). There are 3,120 firmware-bearing OUT transfers,
   each containing 32 firmware bytes at offset 8 of its 64-byte report.
   3,120 * 32 = 99,840 bytes.

2. Reassembled USB firmware bytes equal v2.05.dat[28:] exactly. The firmware
   remains encrypted in transit. Its 28-byte plaintext .dat header has
   little-endian words [205, 0x08003400, 0x18600, 0, 0, 0, 0].

3. AeroModes' MIT-licensed 8CryptDo GD32 decoder recovers a coherent
   Cortex-M3 application. Re-encrypting the complete plaintext regenerates
   the entire original .dat exactly, including header. This is combined
   with valid vectors, executable code, meaningful constants, strings and
   peripheral accesses; a cipher round trip alone is not proof of a key.

4. GPIOA base 0x40010800, mask 0x0002, is configured at 0x08005824-583A
   using library input mode 0x48. The helper at 0x08005938 makes its CTL
   nibble 8 and sets the output latch, which selects the internal pull-up.
   Button polling at 0x080106C0 reads this same pin and enters its debounce /
   held-button path when the read returns zero. Reads at 0x080106D4,
   0x0801074C and 0x08010774 all use GPIOA / mask 2.

5. The indicator dispatcher at 0x08010DDC maps logical channel mask 4 to
   GPIOB / pin mask 0x20, i.e. PB5. Its nonzero state argument clears PB5
   using BC (0x40010C14), and its zero state sets PB5 using BOP
   (0x40010C10). Pattern initialization at 0x08010E30 stores channel 4 at
   0x08010EC6; the status/blink paths also explicitly select channel 4.
   Thus the normal status indication is on PB5 and uses active-low drive.

6. A second independent path, breathing/PWM setup at 0x0801120C, configures
   PB5 as alternate-function push-pull, applies partial TIMER2 remapping,
   and uses timer base 0x40000400. This is GD32 TIMER2_CH1 (equivalent to
   STM32 TIM3_CH2 naming), routed to PB5. The stop path at 0x0801115C
   restores PB5 to ordinary GPIO output.

7. Executed the original board initialization, indicator dispatcher and
   GPIO read helper under Unicorn using a minimal MMIO model. Nine cases
   pass: PA1 input pull-up, PB5 output nibble 1 (GP push-pull / 10MHz), all
   three defined indicator channels in both states, and PA1 low/high reads.
   This validates the decoded instructions and register writes; it is not
   a hardware/optical test. Details: evidence/gpio_emulation_results.json.

BLUETOOTH HCI EVIDENCE
----------------------
GPIO setup at 0x08005872-5894 configures PA2 (mask4) as AF push-pull and
PA3 (mask8) as floating input. The TX DMA routine at 0x08003FBC and RX DMA
setup at 0x08003F4C both target 0x40004404, the USART1 data register. The
RX interrupt path at 0x0800B5D8 reads the same peripheral.

Initial UART setup 0x0800B2A8 and runtime setter 0x080041C0 build 8N1,
RX+TX enabled (0x000C), flow-control field zero. The generic initializer
0x0800B35C clears CTSEN/RTSEN bits 9:8 in CTL2 at offset 0x14. PA1 is used
as the button, not RTS. PA9/PA10 are also configured as UART-capable GPIOs,
but this application's HCI transfer path is specifically PA2/PA3. No actual
use of PA9/PA10 as a debug UART was established.

Controller initialization at 0x08016640 calls the UART setter with 115200,
performs radio initialization, sends two vendor HCI writes, then sets the
MCU UART to 1500000. The baud table at 0x0801AF24 contains:
    Controller address 0x80000060 <- 0x0016E360 (1500000)
    Controller address 0x80000040 <- 0x0602B300

Exact transmitted H4 command packets (at the startup UART setting):
    01 02 FD 0A 80 01 60 00 00 80 60 E3 16 00
    01 02 FD 0A 80 01 40 00 00 80 00 B3 02 06
These use vendor opcode 0xFD02. They are part of the stock initialization
sequence, not a claim that these two packets alone completely initialize
an unconfigured controller. Delay argument 5 occurs after each table entry;
the timing unit was not independently established.

The H4 RX parser at 0x08014488 accepts 0x04 event packets and 0x02 ACL
packets; dispatch is at 0x0801437C. Packet TX at 0x0801444C prepends the
H4 type, and the command builders include type 0x01.

A second offline execution check ran the original 0x08016640 control flow
and original vendor packet builders. Hardware init, UART programming, and
delay calls were stubbed; call order and exact two packet payloads matched.
See evidence/hci_baud_verification.json and tools/verify_hci_baud.py.

ADDITIONAL RADIO CONNECTIONS
---------------------------
PB10 / pin21 is I2C SCL; PB11 / pin22 is I2C SDA. START/STOP and byte/ACK
routines show the roles directly. RF transactions at 0x08016600 use on-wire
address byte 0x2C (7-bit address 0x16, write), an 8-bit register address,
and big-endian 16-bit register values. The initial 47-entry RF table at
0x0801A9DC is used before and after release of the PB13 control line.

PB13 / pin26 is written by 0x08009758 and driven low, then high around radio
initialization at 0x08009524. This proves the MCU control pin and startup
levels. The plain RDA5876 datasheet calls its relevant control input LDO_ON,
not nRESET; PB13 -> RDA LDO_ON is a strong functional inference until checked
by continuity. It can cause a reset through power cycling.

If the fitted radio is the plain 32-pin RDA5876, its datasheet endpoints are:
    GD32 PA2  / pin12 TX  -> RDA UART_RX / pin1
    GD32 PA3  / pin13 RX  <- RDA UART_TX / pin32
    GD32 PB10 / pin21 SCL -> RDA I2C_SCL / pin12
    GD32 PB11 / pin22 SDA -> RDA I2C_SDA / pin11
    GD32 PB13 / pin26     -> likely RDA LDO_ON / pin16
The RDA-side pad numbers come from the RDA datasheet, not from firmware;
physical PCB routing was not measured. MCU pin assignments are confirmed
by code. No separate RTS/CTS lines are enabled by this application.

REGISTER QUICK REFERENCE
------------------------
RCU_APB2EN   0x40021018: bit 2 GPIOA clock; bit 3 GPIOB clock.
GPIOA_CTL0  0x40010800: PA1 configuration is bits 7:4; set to 0x8.
GPIOA_ISTAT 0x40010808: bit 1 is the button level.
GPIOA_BOP   0x40010810: write 0x0002 to select the PA1 pull-up.
GPIOB_CTL0  0x40010C00: PB5 configuration is bits 23:20; set to 0x1.
GPIOB_CTL1  0x40010C04: PB8/PB9 configuration is bits 3:0 / 7:4; each 0x1.
GPIOB_BOP   0x40010C10: write 0x0020 -> PB5 high -> LED off.
GPIOB_BC    0x40010C14: write 0x0020 -> PB5 low  -> LED on.
RGB pin masks: PB9=0x0200, PB8=0x0100, PB5=0x0020; combined=0x0320.
Writing any mask to BOP drives the respective channels off (high), while
writing it to BC drives them on (low).
The output speed field controls drive/slew capability, not blink frequency.
board_pins.h implements these operations without depending on a vendor SDK.
No AFIO remap is needed for the button or RGB channels in ordinary GPIO mode.

Use from your own firmware after startup:
    board_gpio_init();
    board_led_channels_set(board_button_pressed() ? 7u : 0u);

For color identification, call board_led_channels_set(1), then (2), then
(4), with a visible delay between each. Each call switches the other two
channels off. Record the observed colors; a mask is not a color label.
The example mirrors the instantaneous button level; add application-level
button debounce if desired. The helper is not a full board support package,
clock setup, linker script, bootloader, or flashable application.

RECOVERED IMAGE
---------------
File: firmware/v2.05_decrypted.bin
Raw application load address: 0x08003400
Length: 99,840 bytes (0x18600)
Range: 0x08003400 through 0x0801B9FF inclusive
Initial SP: 0x20003FB8
Reset vector: 0x08003571 (Thumb; first instruction 0x08003570)
SHA-256: 36817322fc13106cb0663b6d84edb8f3fb35dd6b94722f514675e83350b84b83

For Ghidra/IDA import as raw ARM Cortex-M / little endian / Thumb at the
above load address. All firmware addresses in this report are absolute;
raw-file offset = absolute address - 0x08003400.

The captured image contains only the application. The flash region below
0x08003400, including existing bootloader and configuration, is absent.
Do not interpret the recovered file as a full-chip backup. Its address
range extends beyond the C8 part's nominal 64KiB flash rating; the capture
and code establish the image sent, not a guaranteed capacity for all C8
parts. No bootloader upload of custom firmware or flash capacity probing
was performed in this analysis.

REPRODUCING RECOVERY
-------------------
From the extracted bundle root, with Python 3 (standard library only):

    python tools/recover_firmware.py source/Updatev205.pcapng \
        --dat source/v2.05.dat --out reproduced

That checks framing, lengths, source .dat equality, vector plausibility,
and exact full-file re-encryption; it writes firmware, summary and packet
provenance. The bundled source capture and .dat files are unchanged copies
from the uploaded archive.

To decrypt either .dat directly:

    python tools/cryptdo8.py decrypt source/v2.05.dat -c gd32 -o app.bin
    python tools/cryptdo8.py decrypt source/v2.04.dat -c gd32 -o app204.bin

To reproduce the original-code execution check, install Python package
unicorn in your analysis environment and run:

    python tools/verify_gpio_arm.py firmware/v2.05_decrypted.bin
    python tools/verify_hci_baud.py firmware/v2.05_decrypted.bin

To regenerate selected disassembly, install Python package capstone and run:

    python tools/annotate_gpio.py firmware/v2.05_decrypted.bin

FILES
-----
board_pins.h: SDK-independent button/RGB helper and HCI pin/rate constants.
firmware/: decoded v2.04 and v2.05 application images.
source/: original capture and firmware containers from the uploaded archive.
tools/: recovery, upstream decryption, raw ARM execution and annotation tools.
evidence/: packet provenance, cross-version hashes, emulation results,
          annotated GPIO/UART disassembly, extracted initialization tables,
          recovery metadata and source revision.
references/: URLs and exact primary-document locations.
SHA256SUMS.txt: hashes of every other bundled file.

CIPHER CREDIT / LICENSE
----------------------
Decryption implementation and cipher discovery: AeroModes, 8CryptDo.
Repository: https://github.com/aeromodes/8cryptdo
Recorded revision: aaffcebafa481631de9c1d722a5693d02234e43a
Unmodified cryptdo8.py and its MIT license are included in tools/.
Reverse-engineered function names in our notes are descriptive labels,
not original vendor debug symbols. No recovered vendor firmware is
relicensed under the decoder's MIT license.

PRIMARY REFERENCES
------------------
GigaDevice GD32F103xx Datasheet Rev3.3, Figure 2-6 (p16) and Table 2-8
(pp42-44): PA1 = pin11; PB5 = pin41; PB8 = pin45; PB9 = pin46.
https://www.gd32mcu.com/download/down/document_id/237/path_type/1

GigaDevice GD32F10x User Manual Rev2.9, GPIO chapter pp155-177:
configuration fields, pull direction, set/clear registers and timer remap.
https://www.gd32mcu.com/data/documents/userManual/GD32F10x_User_Manual_Rev2.9.pdf

8BitDo original USB adapter official manual: pairing makes the LED blink;
successful connection makes it steady. Behavioral context only; the GPIO
assignment above was recovered from machine code.
https://support.8bitdo.com/Manual/USB_Adapter/switchpro_windows.html

RDA Microelectronics RDA5876 Datasheet V1.2, original printed p16,
Table10-1; original p6 has VIO electrical limits. Reproduced in an FCC filing
at combined PDF pages24 and14 (one-based). Plain RDA5876, not RDA5876A.
https://fccid.io/m/c4f44cb21ba8cab77de92bd1cc7990ac3168e489df6ae4becea31bb31b25c0c4.pdf
