"""Offline execution of recovered startup/launch instructions; no hardware I/O.

Clock/GPIO setup and option-byte maintenance are stubbed at named function
boundaries because this is not a peripheral model. Their bodies were reviewed
separately in boot_linear.asm. USB entry and application entry stop execution.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pydeps"))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_READ
from unicorn.arm_const import *

FLASH_BASE, APP_BASE = 0x08000000, 0x08003400
IMAGE = (ROOT / "full_backup/backup-01/flash_backup.bin").read_bytes()


def run_case(name, *, button=False, magic=False, erase_app_tags=False,
             corrupt_app_body=False, invalid_app_sp=False, blank_boot_tags=False,
             occupied_tail=False):
    data = bytearray(IMAGE)
    if erase_app_tags:
        data[0x341C:0x3428] = b"\xff" * 12
    if corrupt_app_body:
        # Keep vectors valid; replace the rest of the application with junk.
        data[0x3500:0x1F400] = b"\xa7" * (0x1F400 - 0x3500)
    if invalid_app_sp:
        struct.pack_into("<I", data, 0x3400, 0x10000000)
    if blank_boot_tags:
        data[0x1C:0x28] = b"\xff" * 12
    if occupied_tail:
        struct.pack_into("<I", data, 0x1F400, 0x20001000)
    initial_sp, reset = struct.unpack_from("<II", data, 0x3400)
    uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
    uc.mem_map(FLASH_BASE, 0x20000)
    uc.mem_write(FLASH_BASE, bytes(data))
    uc.mem_map(0x20000000, 0x20000)
    uc.mem_map(0x40000000, 0x30000)
    uc.mem_map(0xE000E000, 0x2000)
    uc.mem_write(0x40010808, struct.pack("<I", 0 if button else 2))
    if magic:
        uc.mem_write(0x20004FF0, struct.pack("<I", 0x5A5AA5A5))
    if 0x20000000 <= initial_sp < 0x2001FFF8:
        uc.mem_write(initial_sp, struct.pack("<II", 0x12345678, 0x87654321))
    uc.reg_write(UC_ARM_REG_SP, 0x20001658)
    uc.reg_write(UC_ARM_REG_LR, 0x08002FF1)
    result = {"case": name, "stubbed_calls": [], "data_reads_outside_boot": [],
              "erase_requests": [], "outcome": "instruction_limit"}

    def stop(outcome, address):
        result.update(outcome=outcome, stopped_at=f"0x{address:08x}",
                      initial_app_sp=f"0x{initial_sp:08x}",
                      msp=f"0x{uc.reg_read(UC_ARM_REG_MSP):08x}",
                      primask=uc.reg_read(UC_ARM_REG_PRIMASK),
                      control=uc.reg_read(UC_ARM_REG_CONTROL))
        for key, register in (("vtor", 0xE000ED08), ("systick_ctrl", 0xE000E010),
                              ("systick_load", 0xE000E014), ("nvic_iser0", 0xE000E100)):
            result[key] = f"0x{struct.unpack('<I', uc.mem_read(register, 4))[0]:08x}"
        uc.emu_stop()

    def code_hook(emu, address, size, unused):
        stubs = {0x08000938: "busy_delay", 0x08001CF8: "clock_gpio_setup",
                 0x08000D94: "option_byte_maintenance"}
        if address in stubs:
            if stubs[address] != "busy_delay":
                result["stubbed_calls"].append(stubs[address])
            emu.reg_write(UC_ARM_REG_PC, emu.reg_read(UC_ARM_REG_LR))
        elif address == 0x08000D52:
            result["erase_requests"].append({"address": f"0x{emu.reg_read(UC_ARM_REG_R0):08x}",
                                             "bytes": emu.reg_read(UC_ARM_REG_R1)})
            emu.reg_write(UC_ARM_REG_R0, 0)
            emu.reg_write(UC_ARM_REG_PC, emu.reg_read(UC_ARM_REG_LR))
        elif address == 0x08001A80:
            stop("usb_update_mode_entered", address)
        elif address == (reset & ~1):
            stop("application_entry_reached", address)
        elif address == 0x080027DE:
            stop("launch_rejected_sp_and_returned", address)
        elif address == 0x0800279E:
            stop("blank_boot_tags_and_no_factory_image_halt", address)
        elif address == 0x080027C6:
            stop("tail_cleanup_halt", address)

    def read_hook(emu, access, address, size, value, unused):
        if APP_BASE <= address < FLASH_BASE + len(IMAGE):
            result["data_reads_outside_boot"].append({"address": f"0x{address:08x}", "bytes": size})

    uc.hook_add(UC_HOOK_CODE, code_hook)
    uc.hook_add(UC_HOOK_MEM_READ, read_hook)
    uc.emu_start(0x08000191, 0, count=100000)
    return result


if __name__ == "__main__":
    results = [run_case("stock_header"),
               run_case("erased_application_id", erase_app_tags=True),
               run_case("arbitrary_application_body", corrupt_app_body=True),
               run_case("button_pressed", button=True),
               run_case("sram_update_magic", magic=True),
               run_case("invalid_stack_pointer", invalid_app_sp=True),
               run_case("erased_boot_tags", blank_boot_tags=True),
               run_case("occupied_tail_page", occupied_tail=True)]
    expected = ["application_entry_reached"] * 3 + ["usb_update_mode_entered"] * 2 + [
        "launch_rejected_sp_and_returned", "blank_boot_tags_and_no_factory_image_halt",
        "tail_cleanup_halt"]
    for result, outcome in zip(results, expected):
        assert result["outcome"] == outcome, result
    for result in results[:3]:
        assert int(result["msp"], 16) == int(result["initial_app_sp"], 16) + 8
        assert result["vtor"] == "0x08000000"
        assert result["systick_ctrl"] == "0x00000007"
        app_reads = [item["address"] for item in result["data_reads_outside_boot"]
                     if int(item["address"], 16) < 0x0801F400]
        assert app_reads == ["0x08003400", "0x08003404", "0x08003400"]
    print(json.dumps({"hardware_accessed": False,
                      "source_sha256": hashlib.sha256(IMAGE).hexdigest(),
                      "peripherals_emulated": False,
                      "all_expected_outcomes_observed": True,
                      "cases": results}, indent=2))
