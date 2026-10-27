#!/usr/bin/env python3
"""Re-disassemble relevant original GPIO and HCI routines. Requires capstone.
Usage: python tools/annotate_gpio.py firmware/v2.05_decrypted.bin
All displayed addresses are flash addresses. Literal pools remain data.
"""
import sys,struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_MCLASS
from capstone.arm import ARM_OP_MEM,ARM_REG_PC
root=Path(__file__).resolve().parents[1]
fw=Path(sys.argv[1]) if len(sys.argv)>1 else root/'firmware/v2.05_decrypted.bin'
b=fw.read_bytes();base=0x08003400
cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB|CS_MODE_MCLASS);cs.detail=True;cs.skipdata=True
ranges=[('UART RX and TX DMA',0x08003F4C,0x08004024),('UART baud setter',0x080041C0,0x080041F4),('GPIO init and helpers',0x080057F4,0x08005A7C),('Radio init, I2C and startup control',0x08009524,0x08009798),('UART configuration',0x0800B2A8,0x0800B3E8),('Button polling',0x080106C0,0x080107AC),('RGB dispatcher and patterns',0x08010DDC,0x08011088),('LED PWM',0x0801115C,0x08011298),('H4 framing',0x08014350,0x08014510),('Baud transition and vendor commands',0x080165F0,0x080167B2)]
for title,start,end in ranges:
 print(f'\n; {title}: 0x{start:08X}..0x{end:08X} (end exclusive)')
 for ins in cs.disasm(b[start-base:end-base],start):
  comments=[]
  if ins.id:
   for op in ins.operands:
    if op.type==ARM_OP_MEM and op.mem.base==ARM_REG_PC:
     a=((ins.address+4)&~3)+op.mem.disp
     if base<=a<=base+len(b)-4:
      v=struct.unpack_from('<I',b,a-base)[0]
      comments.append(f'[0x{a:08X}] = 0x{v:08X}')
  suffix=' ; '+', '.join(comments) if comments else ''
  print(f'{ins.address:08X}: {ins.bytes.hex():10} {ins.mnemonic:9} {ins.op_str}{suffix}')
