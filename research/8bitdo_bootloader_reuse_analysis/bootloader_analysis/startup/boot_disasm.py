"""Annotated Thumb disassembly helper for the recovered 12 KiB bootloader.

Linear output includes data pools; conclusions require reachable code tracing.
"""
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pydeps"))
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
from capstone.arm import ARM_OP_MEM, ARM_REG_PC

BASE = 0x08000000
DATA = (ROOT / "full_backup/backup-01/flash_backup.bin").read_bytes()[:0x3000]
CS = Cs(CS_ARCH_ARM, CS_MODE_THUMB | CS_MODE_MCLASS)
CS.detail = True
CS.skipdata = True


def disasm(start, stop):
    for ins in CS.disasm(DATA[start - BASE:stop - BASE], start):
        comment = ""
        if ins.id:
            for operand in ins.operands:
                if operand.type == ARM_OP_MEM and operand.mem.base == ARM_REG_PC:
                    loc = ((ins.address + 4) & ~3) + operand.mem.disp
                    if BASE <= loc <= BASE + len(DATA) - 4:
                        value = struct.unpack_from("<I", DATA, loc - BASE)[0]
                        comment += f" ; [{loc:08x}]={value:08x}"
        yield f"{ins.address:08x}: {ins.bytes.hex():10} {ins.mnemonic:10} {ins.op_str}{comment}"


if __name__ == "__main__":
    start = int(sys.argv[1], 0) if len(sys.argv) > 1 else BASE + 0xEC
    stop = int(sys.argv[2], 0) if len(sys.argv) > 2 else BASE + len(DATA)
    print("\n".join(disasm(start, stop)))
