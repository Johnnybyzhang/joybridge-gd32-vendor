#!/usr/bin/env python3
"""Verify the baud-transition path by executing recovered Thumb instructions.

Requires Unicorn. This is offline emulation, with no connection to the board.
Hardware initialization and timing are stubbed; the original control flow and
HCI packet-building instructions execute unchanged.
"""
import json
from pathlib import Path
import sys

try:
    import unicorn
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pydeps'))
    import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_SP, UC_ARM_REG_LR,
    UC_ARM_REG_PC, UC_ARM_REG_XPSR)

root = Path(__file__).resolve().parent
fw = Path(sys.argv[1]) if len(sys.argv) > 1 else root.parent / 'firmware/v2.05_decrypted.bin'
uc = Uc(UC_ARCH_ARM, UC_MODE_THUMB | UC_MODE_MCLASS)
uc.mem_map(0x08000000, 0x40000)
uc.mem_map(0x20000000, 0x10000)
uc.mem_write(0x08003400, fw.read_bytes())
uc.reg_write(UC_ARM_REG_SP, 0x20008000)
uc.reg_write(UC_ARM_REG_LR, 0x08000001)
uc.reg_write(UC_ARM_REG_XPSR, 0x01000000)
events = []


def hook(uc, addr, size, unused):
    if addr == 0x08000000:
        uc.emu_stop()
        return
    if addr == 0x080041c0:
        events.append({'event': 'configure_uart', 'baud': uc.reg_read(UC_ARM_REG_R0)})
    elif addr == 0x08009524:
        events.append({'event': 'controller_reset_rf_and_core_initialization',
                       'emulation': 'stubbed; analyzed separately'})
    elif addr == 0x08018520:
        events.append({'event': 'delay', 'argument': uc.reg_read(UC_ARM_REG_R0)})
    elif addr == 0x0800b268:
        ptr, length = uc.reg_read(UC_ARM_REG_R0), uc.reg_read(UC_ARM_REG_R1)
        payload = bytes(uc.mem_read(ptr, length))
        events.append({'event': 'hci_tx', 'bytes': length, 'hex': payload.hex(' ')})
    else:
        return
    uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))


uc.hook_add(UC_HOOK_CODE, hook)
uc.emu_start(0x08016641, 0x08000000, count=100000)
assert uc.reg_read(UC_ARM_REG_PC) == 0x08000000
assert [e['baud'] for e in events if e['event'] == 'configure_uart'] == [115200, 1500000]
assert [e['hex'] for e in events if e['event'] == 'hci_tx'] == [
    '01 02 fd 0a 80 01 60 00 00 80 60 e3 16 00',
    '01 02 fd 0a 80 01 40 00 00 80 00 b3 02 06',
]
result = dict(method=__doc__.strip(), entry='0x08016640', all_passed=True,
              events=events)
(root.parent / 'evidence/hci_baud_verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
