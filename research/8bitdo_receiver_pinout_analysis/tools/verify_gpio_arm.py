#!/usr/bin/env python3
"""Execute recovered ARM routines with a minimal GPIO MMIO model; no hardware I/O.
Requires unicorn. Usage: python verify_gpio_arm.py [firmware.bin]
"""
from pathlib import Path
import sys, json, struct
try:
    import unicorn
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pydeps'))
    import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_MODE_MCLASS, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC, UC_ARM_REG_XPSR
BASE=0x08003400
ROOT=Path(__file__).resolve().parents[1]
FW=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'firmware/v2.05_decrypted.bin'
blob=FW.read_bytes()
if len(blob)<0xdf00: raise ValueError('Application image too short')
regs=(UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2)

def call(addr,*args, initial=None):
    u=Uc(UC_ARCH_ARM, UC_MODE_THUMB|UC_MODE_MCLASS)
    for base,size in [(0x08000000,0x40000),(0x20000000,0x10000),(0x40000000,0x30000),(0x420e0000,0x1000),(0xe000e000,0x2000)]:
        u.mem_map(base,size)
    u.mem_write(BASE,blob)
    u.reg_write(UC_ARM_REG_SP,0x20008000)
    u.reg_write(UC_ARM_REG_LR,0x08000001)
    u.reg_write(UC_ARM_REG_XPSR,0x01000000)
    for reg,value in zip(regs,args):u.reg_write(reg,value)
    def w32(a,v):u.mem_write(a,struct.pack('<I',v&0xffffffff))
    def r32(a):return struct.unpack('<I',u.mem_read(a,4))[0]
    for base in [0x40010800,0x40010c00,0x40011000]:
        w32(base,0x44444444);w32(base+4,0x44444444)
    if initial:
        for a,v in initial.items():w32(a,v)
    events=[]
    def on_write(uc,access,a,size,value,unused):
        if 0x40010800<=a<0x40011800:
            events.append(dict(pc=f'0x{uc.reg_read(UC_ARM_REG_PC):08X}',address=f'0x{a:08X}',size=size,value=f'0x{value:08X}'))
            base=a&~0x3ff
            off=a-base
            if off==0x10:w32(base+0xc,(r32(base+0xc)|(value&0xffff))&~(value>>16))
            if off==0x14:w32(base+0xc,r32(base+0xc)&~(value&0xffff))
    def on_code(uc,a,size,unused):
        if a==0x08000000:uc.emu_stop()
    u.hook_add(UC_HOOK_MEM_WRITE,on_write)
    u.hook_add(UC_HOOK_CODE,on_code)
    u.emu_start(addr|1,0x08000000,count=100000)
    if u.reg_read(UC_ARM_REG_PC)!=0x08000000:raise RuntimeError('Routine did not return')
    return u,events,r32

result={'firmware':FW.name,'tests':[],'method':'Execute original Thumb code with Unicorn and a minimal GPIO BOP/BC output-latch model; no physical board access.'}
u,events,r32=call(0x080057f4)
a_nibble=(r32(0x40010800)>>4)&15
b_nibble=(r32(0x40010c00)>>20)&15
assert a_nibble==8 and r32(0x4001080c)&2
assert b_nibble==1
assert r32(0x40010c04)&0xff == 0x11
result['tests'].append({'name':'Original board initialization','PA1_CTL_nibble':a_nibble,'PA1_output_latch_pullup':bool(r32(0x4001080c)&2),'PB5_CTL_nibble':b_nibble,'writes':events})
for logical,mask in [(4,0x20),(2,0x100),(1,0x200)]:
    for on in (0,1):
        u,events,r32=call(0x08010ddc,logical,on)
        expected=0x40010c14 if on else 0x40010c10
        assert len(events)==1 and int(events[0]['address'],16)==expected and int(events[0]['value'],16)==mask
        result['tests'].append({'name':'Original indicator dispatcher','logical_channel':logical,'on_argument':on,'writes':events})
for level in (0,1):
    u,events,r32=call(0x08005a48,0x40010800,2,initial={0x40010808:level<<1})
    got=u.reg_read(UC_ARM_REG_R0)
    assert got==level
    result['tests'].append({'name':'Original GPIO read helper PA1','input_level':level,'returned_level':got})
result['all_passed']=True
out=ROOT/'evidence/gpio_emulation_results.json'
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'all_passed':True,'tests':len(result['tests']),'output':str(out),'PA1_input_pullup':True,'PB5_push_pull_10MHz':True,'PB5_on_write':'0x20 -> 0x40010C14','PB5_off_write':'0x20 -> 0x40010C10'},indent=2))
