# Bootloader startup and application-launch findings

## Conclusion and scope

The recovered bootloader does **not authenticate the application before normal
launch**. Its launch routine checks only a mask of the first vector word, then
uses the second vector word as a branch target. Application installation-ID
words, application contents, CRCs, hashes and signatures are not read on this
path. Keeping this bootloader is therefore compatible with a custom application
linked at `0x08003400`, subject to the memory reservations and startup state below.
This is a conclusion from the recovered instructions and offline execution, not
a physical custom-firmware test.

Source: `full_backup/backup-01/flash_backup.bin`, 131072 bytes, mapped at
`0x08000000`, SHA-256
`e2139cea93cf56bc11e8455a23b60d2c61e4d9245e2da74e801901ab7585d1a6`.
Bootloader code/data occupy the first `0x3000` bytes. Reset vector is
`0x08000191`; reset code at `0x08000190` branches through `0x080000EC` and C runtime
initialization to main at `0x08002734`.

## Exact startup decisions

Main reads the bootloader's own three reserved vector words at `0x0800001C`,
`0x08000020`, and `0x08000024`. It tests whether **all three are erased**, without
comparing their values to a UID, key or application stamp. They are programmed in
this dump. These boot words must remain intact when preserving the bootloader.

Equivalent control flow, with descriptive function names:

```c
// main, 0x08002734
delay_loop(0x1000);
clock_and_gpio_setup();              // 0x08001CF8
boot_vector_and_interrupt_setup();   // 0x080014A0
copy_boot_stamp_words_to_ram();

if (boot_stamp[0] == 0xFFFFFFFF &&
    boot_stamp[1] == 0xFFFFFFFF &&
    boot_stamp[2] == 0xFFFFFFFF) {
    if (*(uint32_t *)0x0801F400 == 0xFFFFFFFF) {
        set_led(1, 1);
        for (;;) {}                 // 0x0800279E
    }
    for (;;) {                      // factory/alternate-image path
        delay_loop(100000);
        if (button_checked_twice()) // 0x0800131C
            launch(0x0801F400);
    }
}

maintain_flash_options();            // 0x08000D94; no app validation
if (*(uint32_t *)0x0801F400 != 0xFFFFFFFF ||
    *(uint32_t *)0x0801F800 != 0xFFFFFFFF) {
    result = erase_pages(0x0801F400, 0xC00); // call at 0x080027AC
    set_led(result < 0 ? 0 : 2, 1);
    for (;;) delay_loop(100);        // 0x080027C6
}

if (enter_update_mode())             // 0x0800133C, call at 0x080027CE
    usb_update_loop();              // 0x08001A80
launch(0x08003400);                  // call at 0x080027DA
return 0;                           // no explicit recovery if launch rejects SP
```

The tail-page tests inspect **only each page's first word**. The dump contains
erased bytes throughout `0x0801F400–0x0801FFFF`. Reserve this entire `0xC00` tail
region: startup cleanup and the updater can erase it. The application allocation
between `0x08003400` and `0x0801F400` is `0x1C000` bytes (112 KiB); this describes
the bootloader's layout, not an independent physical-capacity measurement.
Keep the metadata page `0x08003000–0x080033FF` separate as well.

## Button and SRAM marker

`enter_update_mode()` at `0x0800133C` first configures and starts SysTick, then
returns true under either condition:

1. The word at `0x20004FF0` equals `0x5A5AA5A5`.
2. The PA1 button remains low through the checks below.

The marker test is at `0x08001348–0x08001350`. This routine does not clear the
marker. It lies outside the bootloader's C-runtime-cleared RAM region. A custom
application using this software-entry mechanism should reserve the marker word
and explicitly clear it when appropriate after launch; otherwise a later reset
can enter update mode again while that SRAM value persists.

Button helper `0x080019B4` reads GPIOA input status at `0x40010808`, mask `0x0002`.
It returns true only after two low samples separated by `delay_loop(1000000)`.
The outer helper calls it twice, with another `delay_loop(1000000)` between
calls: a successful button entry therefore observes four low samples across
three busy delays. No wall-clock duration was inferred from these loop counts.
GPIO initialization configures PA1 with pull-up selection at
`0x08001DA2–0x08001DB6`.

Both marker and button checks occur **before any application-header read**.
Holding the button can therefore enter the loader even when the application's
first vector word is invalid. An invalid vector by itself does not select USB
recovery in this code.

## Launch routine and absence of application authentication

All direct callers of launch `0x0800137C` are:

| Call site | Source path | Image base |
|---|---|---|
| `0x080027DA` | Normal startup / return from USB update loop | `0x08003400` |
| `0x08001200` | Update-finish path for non-USB transport | `0x08003400` |
| `0x08002790` | Boot-stamps-erased factory/alternate path | `0x0801F400` |

The original launch instructions are:

```asm
0800137C  push    {r4, lr}
0800137E  ldr     r1, [r0]
08001380  ldr     r2, =0x2FFE0000
08001382  ands    r1, r2
08001384  cmp     r1, #0x20000000
08001388  bne     0x0800139A
0800138A  ldr     r4, [r0, #4]
0800138C  ldr     r0, [r0]
0800138E  bl      0x08000112        ; MSR MSP,r0; BX LR
08001392  mov     r12, r4
08001394  pop     {r4, lr}
08001398  bx      r12
0800139A  pop     {r4, pc}
```

Thus the sole acceptance condition is:

```c
(initial_sp & 0x2FFE0000) == 0x20000000
```

This is a coarse mask, not a complete SRAM-size, alignment or reset-address
validation. The routine does not explicitly check the reset vector's address
range or Thumb bit; a custom image must still supply a valid Thumb entry point.
It reads only image offsets `0`, `4`, and `0` again. It does not inspect the
installation-ID words at `+0x1C/+0x20/+0x24`, the version word at `+0x34`, or any
application body bytes.

### Handoff is not reset state

The `POP` after `MSR MSP` uses the **new application stack**. In the ordinary
reset path (Thread mode using MSP), entry MSP is therefore `initial_sp + 8`.
R4 and LR are loaded from the two words at that new stack location. Offline
execution of the exact instructions confirmed the stock image's
`0x20003FB8` vector reaches its reset entry with MSP `0x20003FC0`.

**The initial vector SP must leave readable headroom.** For nominal 20 KiB SRAM,
`0x20005000` is the one-past-end address. Although it passes the loader's mask,
the loader would read words at `0x20005000` and `0x20005004` before entering the
application, outside that SRAM allocation. Restoring MSP in the application's
reset stub cannot repair a fault that occurs before the branch. A conservative
custom layout can set its vector SP / stack top to `0x20004FE0`, reserve the top
32 SRAM bytes, and keep the update marker at `0x20004FF0` within that reservation.
The loader's two reads then remain inside nominal SRAM, clear of the marker.
This is a static consequence of the POP sequence, not a hardware boundary test.

The stock application compensates immediately: reset entry `0x08003570` branches
to `0x080034EC`, whose first instruction reloads SP from `0x080034FC`.

Other inherited state on the normal startup path:

| Item | Observed instruction effect / offline entry state |
|---|---|
| VTOR | `0x08000000`, set at `0x080014A8`; launch never relocates it |
| SysTick control | `7`: enabled, interrupt enabled, processor clock selected |
| SysTick reload | `0x00075300` (480000), configured by `0x08001340` |
| NVIC | External interrupt 20 enabled by `0x080014C8` |
| PRIMASK / CONTROL | `0` / `0` in the reset-path execution; no handoff masking |
| Clocks / GPIO | Already configured by `0x08001CF8`; launch does not reset them |
| Application MSP | Vector value plus 8 after the post-MSR POP |

Static clock setup selects HSE-sourced PLL with multiplier encoding `0x00100000`,
PLL as system source, AHB and APB2 divisors of 1, and APB1 divisor of 2. It also
changes flash access settings and GPIO modes. The emulator does not model those
hardware transitions. USB-loop exit shuts down USB through `0x08000F74`, but does
not perform a global interrupt/peripheral reset or relocate VTOR.

A custom reset entry should mask interrupts immediately, restore its intended
MSP, stop/clear inherited SysTick and interrupt state, establish VTOR at
`0x08003400`, and initialize the clocks/peripherals it uses before enabling
interrupts. It must not assume the bootloader provides a clean reset environment.

## Flash-option maintenance: separate from application validation

For this dump's programmed boot stamps, main calls `0x08000D94` before the tail
and button checks. Static instruction effects are:

- Read `FMC + 0x1C`, bit 1, via `0x08000B34`; if clear, unlock and call
  `0x08000C70(1)`, an option erase/program routine that writes zero to the
  security-protection option-byte address `0x1FFFF800`.
- Read `FMC + 0x20` via `0x08000B70`; if `(value & 0xC0) != 0`, call
  `0x08000A80` (option erase/program sequence writing `0xA5` at `0x1FFFF800`),
  then `0x080009D4(0xFFFFFFFF)`, whose complemented argument yields zero bytes
  for the four write-protection option locations `0x1FFFF808/80A/80C/80E`.

These are inferred protection-maintenance operations from register accesses and
the documented register map. No current option bytes were read in the supplied
main-flash dump. Their actual loaded state, changes across reset, protection
effects and hardware side effects are **not established by this analysis**.
These functions are explicitly stubbed in the offline execution. They do not
read application contents or compare an application signature.

## Evidence files and limits

- `boot_linear.asm`: annotated disassembly; includes literal/data regions, so
  only traced instruction ranges support conclusions.
- `startup_key_functions.asm`: the relevant traced routines grouped for review.
- `boot_disasm.py`: reproduces annotated disassembly from the original dump.
- `emulate_startup.py` and `emulation_results.json`: eight offline scenarios.

The exact runtime initialization, boot decisions, SysTick/NVIC setup and launch
instructions were executed. Busy delays, clock/GPIO setup and option-byte
maintenance have explicit named stubs. An erase request is recorded and returned
as success in the tail-cleanup scenario; no flash is modified outside emulator
memory. The model does not deliver asynchronous interrupts or emulate hardware
protection/clock behavior.

Stock app headers, erased application-ID words, and an application body replaced
with arbitrary bytes all reach the reset-vector target. Execution stops **before
that target runs**, so this establishes lack of boot-time content validation,
not that corrupted or custom code works. Separate cases confirm button entry,
marker entry, rejection of a bad stack mask, the erased-boot-stamp halt, and the
reserved-tail erase/halt path. No device was accessed or written.
