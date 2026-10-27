#!/usr/bin/env python3
"""Offline execution of the receiver's original block decoder in Unicorn.

Two cases only: captured v2.05 ciphertext, and a deterministic synthetic payload
encrypted with the previously inspected cryptdo8 implementation. No USB or
target-device operation is implemented. No update/program handler is executed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--backup", type=Path, required=True)
    ap.add_argument("--ciphertext", type=Path, required=True)
    ap.add_argument("--plaintext", type=Path, required=True)
    ap.add_argument("--cryptdo8-dir", type=Path, required=True)
    ap.add_argument("--python-deps", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    sys.path.insert(0, str(args.cryptdo8_dir))
    sys.path.insert(0, str(args.python_deps))
    import cryptdo8
    import unicorn
    from unicorn import Uc, UC_ARCH_ARM, UC_MODE_MCLASS, UC_MODE_THUMB
    from unicorn import UC_HOOK_CODE, UC_PROT_READ, UC_PROT_EXEC, UC_PROT_WRITE
    from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
    from unicorn.arm_const import UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC

    flash = args.backup.read_bytes()
    assert len(flash) == 0x20000
    firmware_cipher = args.ciphertext.read_bytes()
    firmware_plain = args.plaintext.read_bytes()
    assert len(firmware_cipher) == len(firmware_plain) == 0x18600
    synthetic_plain = bytes(((i * 73) ^ (i >> 3) ^ 0xA5) & 0xFF for i in range(1536))
    synthetic_words = struct.unpack("<384I", synthetic_plain)
    synthetic_cipher = struct.pack("<384I", *cryptdo8.encrypt_payload(synthetic_words, cryptdo8.GD32()))
    args.out.mkdir(parents=True, exist_ok=True)

    FLASH_BASE, RAM_BASE, RAM_SIZE = 0x08000000, 0x20000000, 0x5000
    INIT, WRAPPER, INNER = 0x0800090C, 0x080026C4, 0x080027F8
    GLOBALS, BUFFER, STACK, RETURN = 0x20000034, 0x20000178, 0x20004000, 0x08002BF0
    ALLOWED = ((INIT, 0x0800092E), (WRAPPER, 0x08002720), (INNER, 0x08002848))
    cases = []

    def run_case(name, ciphertext, expected):
        uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
        uc.mem_map(FLASH_BASE, len(flash), UC_PROT_READ | UC_PROT_EXEC)
        uc.mem_write(FLASH_BASE, flash)
        uc.mem_map(RAM_BASE, RAM_SIZE, UC_PROT_READ | UC_PROT_WRITE)
        counter = {"instructions": 0, "inner_calls": 0}

        def hook_code(emulator, pc, size, context):
            assert any(lo <= pc < hi for lo, hi in ALLOWED), f"Unexpected executed address {pc:08X}"
            counter["instructions"] += 1
            if pc == INNER:
                counter["inner_calls"] += 1

        uc.hook_add(UC_HOOK_CODE, hook_code)

        def call(function, r0=0, r1=0, r2=0, r3=0):
            for register, value in ((UC_ARM_REG_R0, r0), (UC_ARM_REG_R1, r1),
                                    (UC_ARM_REG_R2, r2), (UC_ARM_REG_R3, r3),
                                    (UC_ARM_REG_SP, STACK), (UC_ARM_REG_LR, RETURN | 1)):
                uc.reg_write(register, value)
            uc.emu_start(function | 1, RETURN, count=100000)
            assert uc.reg_read(UC_ARM_REG_PC) == RETURN, "Did not return normally"
            assert uc.reg_read(UC_ARM_REG_SP) == STACK, "Stack was not restored"

        call(INIT)
        initialized = struct.unpack("<10I", bytes(uc.mem_read(GLOBALS, 40)))
        assert initialized == (1, 9, 18, 3, 0x92A753FA, 0, 0, 0, 0, 0)
        decoded = bytearray()
        block_reports = []
        for offset in range(0, len(ciphertext), 512):
            chunk = ciphertext[offset:offset + 512]
            uc.mem_write(BUFFER, chunk)
            call(WRAPPER, BUFFER, offset, len(chunk))
            result = bytes(uc.mem_read(BUFFER, len(chunk)))
            assert result == expected[offset:offset + len(chunk)], f"Mismatch at payload offset 0x{offset:X}"
            decoded.extend(result)
            block_reports.append({"offset": offset, "bytes": len(chunk), "matches": True})
        assert bytes(decoded) == expected
        assert counter["inner_calls"] == len(block_reports)
        return {"name": name, "bytes": len(ciphertext), "block_count": len(block_reports),
                "every_block_matches": True, "complete_result_matches": True,
                "ciphertext_sha256": sha(ciphertext), "expected_plaintext_sha256": sha(expected),
                "emulated_result_sha256": sha(decoded),
                "initialized_globals_le32": [f"0x{x:08x}" for x in initialized],
                "executed_instructions": counter["instructions"], "original_inner_calls": counter["inner_calls"],
                "normal_returns_and_restored_stack": True,
                "executed_only_original_init_wrapper_inner": True}

    cases.append(run_case("captured_v2.05", firmware_cipher, firmware_plain))
    cases.append(run_case("synthetic_custom_plaintext", synthetic_cipher, synthetic_plain))
    report = {
        "schema": "8bitdo-original-bootloader-decoder-emulation-v1",
        "bootloader_source_sha256": sha(flash), "bootloader_prefix_0x3000_sha256": sha(flash[:0x3000]),
        "unicorn_version": unicorn.__version__, "cryptdo8_source_sha256": sha((args.cryptdo8_dir / "cryptdo8.py").read_bytes()),
        "original_code": {"initializer": "0x0800090c", "wrapper": "0x080026c4", "inner": "0x080027f8",
                          "seed_table": "0x0800284c", "seed_table_bytes": 512},
        "emulator_configuration": {"flash": "0x08000000..0x0801ffff, read/execute",
                                   "ram": "0x20000000..0x20004fff, read/write, initially zero",
                                   "stack": f"0x{STACK:08x}", "globals": f"0x{GLOBALS:08x}",
                                   "buffer": f"0x{BUFFER:08x}", "return_sentinel": f"0x{RETURN:08x}",
                                   "wrapper_arguments": "r0=buffer, r1=cumulative encrypted payload byte offset, r2=chunk byte count <=512",
                                   "other_regions_mapped": False, "peripheral_stubs": False,
                                   "instruction_limit_per_call": 100000,
                                   "init_called_once_per_case": True,
                                   "flash_protected_against_emulated_writes": True},
        "cases": cases,
        "synthetic_fixture": {"bytes": 1536,
                              "plaintext_formula": "byte[i] = ((i*73) XOR (i>>3) XOR 0xA5) & 0xFF, i=0..1535",
                              "encryption": "cryptdo8.encrypt_payload(LE32 words, cryptdo8.GD32())",
                              "purpose": "Arbitrary-content decoder compatibility test; not a deployable application image."},
        "interpretation": "The installed original bootloader decoder recovers both the captured distributed firmware and independently encrypted arbitrary synthetic content exactly. Its own initializer and seed-table addressing are executed without replacement.",
        "scope_of_signature_finding": "The inspected decoder branches on chunk lengths/counters, not decoded payload contents, and contains no payload-signature or UID validation. This does not by itself establish full update-handler or startup acceptance; those paths are analyzed separately.",
        "hardware_access": False, "update_or_flash_program_handler_executed": False,
        "source_and_files_read_only_except_local_report": True}
    path = args.out / "bootloader_decoder_emulation.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"report": str(path), "cases": cases}, indent=2))


if __name__ == "__main__":
    main()
