#!/usr/bin/env python3
"""Offline execution of the recovered bootloader's actual update handlers.

No USB, HID, probe, serial, networking or hardware APIs are used. Flash pages
and programming are modeled in Unicorn memory. Generated custom images remain
in memory; this script is not an updater or a flashing tool.
"""
from pathlib import Path
import hashlib
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pydeps"))
sys.path.insert(0, str(ROOT / "recovery"))
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE
from unicorn.arm_const import *
import cryptdo8

FLASH = 0x08000000
APP = 0x08003400
RAM = 0x20000000
STACK = RAM + 0x7000
REQUEST = RAM + 0x1000
RETURN = FLASH + 0x2EF0
UPDATE = FLASH + 0x100C
DISPATCH = FLASH + 0x247C
ORIGINAL = (ROOT / "full_backup/backup-01/flash_backup.bin").read_bytes()
OUT = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Model:
    def __init__(self, inject_program_failure=False):
        self.uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
        self.uc.mem_map(FLASH, 0x20000)
        self.uc.mem_write(FLASH, ORIGINAL)
        self.uc.mem_map(RAM, 0x10000)
        self.uc.mem_map(0x40022000, 0x1000)
        self.events = []
        self.replies = []
        self.decoded_blocks = []
        self.pending_decode = None
        self.inject_program_failure = inject_program_failure
        self.failure_injected = False
        self.uc.hook_add(UC_HOOK_CODE, self.hook)

    def word(self, address):
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def ret(self, value=0):
        self.uc.reg_write(UC_ARM_REG_R0, value & 0xFFFFFFFF)
        self.uc.reg_write(UC_ARM_REG_PC, self.uc.reg_read(UC_ARM_REG_LR))

    def hook(self, uc, address, size, unused):
        r0, r1, r2, r3 = (uc.reg_read(x) for x in
                         (UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3))
        if address == FLASH + 0xD14:  # flash unlock: replace only FMC effects
            self.events.append({"event": "unlock"})
            self.ret()
        elif address == FLASH + 0xB80:  # flash lock
            self.events.append({"event": "lock"})
            self.ret()
        elif address == FLASH + 0xAF4:  # one-page hardware erase primitive
            assert r0 % 0x400 == 0 and FLASH <= r0 < FLASH + 0x20000
            uc.mem_write(r0, b"\xff" * 0x400)
            self.events.append({"event": "erase_page", "address": f"0x{r0:08x}"})
            self.ret(4)  # original helper's FMC_READY status
        elif address == FLASH + 0xBE8:  # one-halfword hardware programming primitive
            assert r0 % 2 == 0 and FLASH <= r0 < FLASH + 0x20000
            old = struct.unpack("<H", uc.mem_read(r0, 2))[0]
            value = r1 & 0xFFFF
            fail = self.inject_program_failure and not self.failure_injected
            if fail:
                self.failure_injected = True
            else:
                uc.mem_write(r0, struct.pack("<H", old & value))
            self.events.append({"event": "program_halfword", "address": f"0x{r0:08x}",
                                "value": f"0x{value:04x}", "injected_failure": fail})
            self.ret(4 if not fail else 2)
        elif address in (FLASH + 0x13A0, FLASH + 0x142C):
            count = self.word(uc.reg_read(UC_ARM_REG_SP))
            assert count <= 128
            payload = bytes(uc.mem_read(r3, count)) if count else b""
            reply = {"event": "reply", "builder": f"0x{address:08x}",
                     "transport": f"0x{r0:02x}", "opcode": f"0x{r2:02x}",
                     "payload_hex": payload.hex(), "bytes": count}
            self.events.append(reply)
            self.replies.append(reply)
            self.ret()
        elif address == FLASH + 0x26C4:
            self.pending_decode = (r0, r1, r2)
        elif address == FLASH + 0x1092 and self.pending_decode:
            buffer, offset, count = self.pending_decode
            decoded = bytes(uc.mem_read(buffer, count))
            self.decoded_blocks.append({"offset": offset, "bytes": count,
                                        "sha256": sha(decoded), "data_hex": decoded.hex()})
            self.pending_decode = None

    def call_update(self, command, payload=b"", version=None, base=APP, length=None,
                    reserved=b"\0" * 16):
        if command == 1:
            assert len(reserved) == 16
            payload = struct.pack("<III", version, base, length) + reserved
        if command in (0, 1, 5, 6):
            body = bytes((command,)) + struct.pack("<H", len(payload)) + payload
        else:
            body = bytes((command,))
        # Exercise the real USB subtype dispatcher as well as the update handler.
        request_body = b"\x00\x16" + struct.pack("<H", len(body)) + body
        self.uc.mem_write(REQUEST, request_body + bytes(128 - len(request_body)))
        self.uc.reg_write(UC_ARM_REG_SP, STACK)
        self.uc.reg_write(UC_ARM_REG_LR, RETURN | 1)
        self.uc.reg_write(UC_ARM_REG_R0, 0x97)  # observed USB transport
        self.uc.reg_write(UC_ARM_REG_R1, 0)
        self.uc.reg_write(UC_ARM_REG_R2, REQUEST)
        self.uc.reg_write(UC_ARM_REG_R3, len(request_body))
        start_events, start_replies = len(self.events), len(self.replies)
        self.uc.emu_start(DISPATCH | 1, RETURN, count=2000000)
        assert self.uc.reg_read(UC_ARM_REG_PC) == RETURN, "handler did not return"
        result = self.uc.reg_read(UC_ARM_REG_R0)
        state = [self.word(RAM + 0x34 + off) for off in (0x14, 0x18, 0x1C, 0x20, 0x24)]
        return {"command": f"0x{command:02x}", "payload_bytes": len(payload),
                "return_u32": f"0x{result:08x}",
                "processed": state[0], "declared_length": state[1],
                "base": f"0x{state[2]:08x}", "version": f"0x{state[3]:08x}",
                "buffered": state[4], "usb_exit_flag": self.uc.mem_read(RAM + 0x18, 1)[0],
                "replies": self.replies[start_replies:],
                "erase_pages": [e["address"] for e in self.events[start_events:]
                                if e["event"] == "erase_page"],
                "halfwords_programmed": sum(e["event"] == "program_halfword"
                                             for e in self.events[start_events:])}


def custom_image():
    # This is a test fixture, not an operational application. Its reset vector
    # points to a self-loop; the remaining bytes include a non-vendor pattern.
    plain = bytearray((i * 73 + 0x29) & 0xFF for i in range(1024))
    for offset in range(0, 0xEC, 4):
        struct.pack_into("<I", plain, offset, APP + 0x101)
    struct.pack_into("<II", plain, 0, RAM + 0x3F00, APP + 0x101)
    plain[0x1C:0x28] = b"\xff" * 12
    plain[0x34:0x38] = b"\xff" * 4
    plain[0x100:0x102] = b"\xfe\xe7"  # Thumb b .
    return bytes(plain)


def exercise_full_update(plain, corrupt_cipher=False, arbitrary_tag=False):
    version = 0x12345678  # deliberately outside the distributor's version sequence
    packed = cryptdo8.build_section(plain, cryptdo8.GD32(), version, addr=APP)
    cipher = bytearray(packed[28:])
    if corrupt_cipher:
        cipher[0x180] ^= 0x40  # changes decoded bytes; no signature/tag recomputed
    model = Model()
    commands = [model.call_update(1, version=version, length=len(cipher),
                                  reserved=b"not-a-signature!")]
    for offset in range(0, len(cipher), 32):
        commands.append(model.call_update(0, bytes(cipher[offset:offset + 32])))
    installed_before_tag = bytes(model.uc.mem_read(APP, len(plain)))
    # SET_ENCODE_ID has no device-ID verification; a separate case uses arbitrary words.
    tag = (bytes.fromhex("111111112222222233333333") if arbitrary_tag else
           bytes.fromhex("f975ca555052a0d011b6ef60"))
    commands.append(model.call_update(6, tag))
    commands.append(model.call_update(2))
    expected = bytearray(plain)
    struct.pack_into("<I", expected, 0x34, version)
    expected_before_tag = bytes(expected)
    expected[0x1C:0x28] = tag
    installed = bytes(model.uc.mem_read(APP, len(plain)))
    decoded = b"".join(bytes.fromhex(b["data_hex"]) for b in model.decoded_blocks)
    assert all(c["return_u32"] == "0x00000000" for c in commands)
    assert all(r["opcode"] == "0x14" for c in commands for r in c["replies"])
    assert commands[-1]["usb_exit_flag"] == 1
    assert bytes(model.uc.mem_read(FLASH, 0x3000)) == ORIGINAL[:0x3000]
    assert bytes(model.uc.mem_read(FLASH + 0x3000, 0x400)) == ORIGINAL[0x3000:0x3400]
    assert bytes(model.uc.mem_read(FLASH + 0x1F400, 0xC00)) == b"\xff" * 0xC00
    if not corrupt_cipher:
        assert decoded == plain
        assert installed_before_tag == expected_before_tag
        assert installed == expected
    else:
        assert decoded != plain and installed_before_tag != expected_before_tag
    # A second attempt to set the same tag is rejected because the slots aren't erased.
    second_tag = model.call_update(6, tag)
    assert second_tag["return_u32"] == "0xfffffffc"
    assert second_tag["replies"][0]["opcode"] == "0x18"
    return {"case": "corrupted_cipher_and_arbitrary_tag" if corrupt_cipher else "unsigned_custom_fixture",
            "unsigned_plaintext_sha256": sha(plain), "plaintext_bytes": len(plain),
            "cipher_sha256": sha(cipher), "version": f"0x{version:08x}",
            "ignored_header_bytes_12_27_hex": b"not-a-signature!".hex(),
            "supplied_tag_hex": tag.hex(), "decoded_equals_original_plaintext": decoded == plain,
            "installed_equals_expected_plaintext_with_metadata": installed == expected,
            "bootloader_unchanged": True, "metadata_page_unchanged": True,
            "finalization_erased_tail": True, "commands": commands,
            "decode_blocks": [{k: v for k, v in b.items() if k != "data_hex"}
                              for b in model.decoded_blocks],
            "repeat_tag_attempt": second_tag}


def rejection_checks(plain):
    wrong = Model()
    before = bytes(wrong.uc.mem_read(FLASH, len(ORIGINAL)))
    rejected = wrong.call_update(1, version=7, base=FLASH, length=1024)
    assert rejected["return_u32"] == "0xffffffff"
    assert rejected["replies"][0]["opcode"] == "0x18"
    assert not rejected["erase_pages"]
    assert bytes(wrong.uc.mem_read(FLASH, len(ORIGINAL))) == before
    # Original erase helper runs; the modeled primitive fails its first program.
    failed = Model(inject_program_failure=True)
    packed = cryptdo8.build_section(plain, cryptdo8.GD32(), 7, addr=APP)
    failed.call_update(1, version=7, length=len(plain))
    result = None
    for offset in range(0, 512, 32):
        result = failed.call_update(0, packed[28 + offset:28 + offset + 32])
    assert result["return_u32"] == "0xfffffffe"
    assert result["replies"][0]["opcode"] == "0x18"
    assert failed.failure_injected
    return {"wrong_base_rejected_without_flash_changes": rejected,
            "program_readback_mismatch_rejected": result}


def main():
    plain = custom_image()
    result = {"hardware_accessed": False, "flashable_custom_files_written": False,
              "bootloader_source_sha256": sha(ORIGINAL[:0x3000]),
              "full_backup_sha256": sha(ORIGINAL),
              "original_entry": "0x0800247c", "original_update_handler": "0x0800100c",
              "original_decoder": ["0x080026c4", "0x080027f8"],
              "mocked_functions": {"0x08000d14": "FMC unlock",
                                   "0x08000b80": "FMC lock",
                                   "0x08000af4": "one-page hardware erase",
                                   "0x08000be8": "one-halfword hardware program",
                                   "0x080013a0": "USB nested reply transport",
                                   "0x0800142c": "USB generic reply transport"},
              "cases": [exercise_full_update(plain),
                        exercise_full_update(plain, corrupt_cipher=True, arbitrary_tag=True)],
              "negative_checks": rejection_checks(plain)}
    path = OUT / "update_handler_emulation.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": True, "hardware_accessed": False,
                      "result": str(path), "cases": [c["case"] for c in result["cases"]]}))


if __name__ == "__main__":
    main()
