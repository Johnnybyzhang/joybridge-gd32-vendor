; Reset and runtime entry
080000ec: dff80cd0   ldr.w      sp, [pc, #0xc] ; [080000fc]=20001658
080000f0: 00f076f8   bl         #0x80001e0
080000f4: 0048       ldr        r0, [pc, #0] ; [080000f8]=08002735
080000f6: 0047       bx         r0
080000f8: 3527       movs       r7, #0x35
080000fa: 0008       lsrs       r0, r0, #0x20
080000fc: 5816       asrs       r0, r3, #0x19
080000fe: 0020       movs       r0, #0
08000100: eff30980   mrs        r0, psp
08000104: 7047       bx         lr
08000106: 80f30988   msr        psp, r0
0800010a: 7047       bx         lr
0800010c: eff30880   mrs        r0, msp
08000110: 7047       bx         lr
08000112: 80f30888   msr        msp, r0
08000116: 7047       bx         lr
08000118: 40ba       rev16      r0, r0
0800011a: 7047       bx         lr
0800011c: c0ba       revsh      r0, r0
0800011e: 7047       bx         lr
08000120: 30bf       wfi        
08000122: 7047       bx         lr
08000124: 20bf       wfe        
08000126: 7047       bx         lr
08000128: 40bf       sev        
0800012a: 7047       bx         lr
0800012c: bff36f8f   isb        sy
08000130: 7047       bx         lr
08000132: bff34f8f   dsb        sy
08000136: 7047       bx         lr
08000138: bff35f8f   dmb        sy
0800013c: 7047       bx         lr
0800013e: 01df       svc        #1
08000140: 7047       bx         lr
08000142: eff31480   mrs        r0, control
08000146: 7047       bx         lr
08000148: 80f31488   msr        control, r0
0800014c: bff36f8f   isb        sy
08000150: 7047       bx         lr
08000152: eff30980   mrs        r0, psp
08000156: 7047       bx         lr
08000158: 80f30988   msr        psp, r0
0800015c: 7047       bx         lr
0800015e: eff30880   mrs        r0, msp
08000162: 7047       bx         lr
08000164: 80f30888   msr        msp, r0
08000168: 7047       bx         lr
0800016a: 72b6       cpsid      i
0800016c: 7047       bx         lr
0800016e: 62b6       cpsie      i
08000170: 7047       bx         lr
08000172: 71b6       cpsid      f
08000174: 7047       bx         lr
08000176: 61b6       cpsie      f
08000178: 7047       bx         lr
0800017a: 80f31188   msr        basepri, r0
0800017e: 7047       bx         lr
08000180: eff31280   mrs        r0, basepri_max
08000184: 7047       bx         lr
08000186: 40ba       rev16      r0, r0
08000188: 7047       bx         lr
0800018a: 00ba       rev        r0, r0
0800018c: 7047       bx         lr
0800018e: 0000       movs       r0, r0
08000190: 0048       ldr        r0, [pc, #0] ; [08000194]=080000ed
08000192: 0047       bx         r0
08000194: ed00       lsls       r5, r5, #3
08000196: 0008       lsrs       r0, r0, #0x20

; C runtime initialization
080001e0: 064c       ldr        r4, [pc, #0x18] ; [080001fc]=08002ad4
080001e2: 074d       ldr        r5, [pc, #0x1c] ; [08000200]=08002af4
080001e4: 06e0       b          #0x80001f4
080001e6: e068       ldr        r0, [r4, #0xc]
080001e8: 40f00103   orr        r3, r0, #1
080001ec: 94e80700   ldm.w      r4, {r0, r1, r2}
080001f0: 9847       blx        r3
080001f2: 1034       adds       r4, #0x10
080001f4: ac42       cmp        r4, r5
080001f6: f6d3       blo        #0x80001e6
080001f8: fff77cff   bl         #0x80000f4
080001fc: d42a       cmp        r2, #0xd4
080001fe: 0008       lsrs       r0, r0, #0x20
08000200: f42a       cmp        r2, #0xf4
08000202: 0008       lsrs       r0, r0, #0x20

; Main boot decisions
08002734: 70b5       push       {r4, r5, r6, lr}
08002736: 4ff48050   mov.w      r0, #0x1000
0800273a: fef7fdf8   bl         #0x8000938
0800273e: fff7dbfa   bl         #0x8001cf8
08002742: fef7adfe   bl         #0x80014a0
08002746: 4ff00062   mov.w      r2, #0x8000000
0800274a: 2648       ldr        r0, [pc, #0x98] ; [080027e4]=20000018
0800274c: d169       ldr        r1, [r2, #0x1c]
0800274e: 264c       ldr        r4, [pc, #0x98] ; [080027e8]=0801f400
08002750: c160       str        r1, [r0, #0xc]
08002752: 136a       ldr        r3, [r2, #0x20]
08002754: 0361       str        r3, [r0, #0x10]
08002756: 526a       ldr        r2, [r2, #0x24]
08002758: 4261       str        r2, [r0, #0x14]
0800275a: 491c       adds       r1, r1, #1
0800275c: 03d1       bne        #0x8002766
0800275e: 5b1c       adds       r3, r3, #1
08002760: 01d1       bne        #0x8002766
08002762: 521c       adds       r2, r2, #1
08002764: 06d0       beq        #0x8002774
08002766: fef715fb   bl         #0x8000d94
0800276a: 2168       ldr        r1, [r4]
0800276c: 2046       mov        r0, r4
0800276e: 491c       adds       r1, r1, #1
08002770: 1ad1       bne        #0x80027a8
08002772: 15e0       b          #0x80027a0
08002774: 2068       ldr        r0, [r4]
08002776: 401c       adds       r0, r0, #1
08002778: 0dd0       beq        #0x8002796
0800277a: 1c4d       ldr        r5, [pc, #0x70] ; [080027ec]=000186a0
0800277c: fff7bafa   bl         #0x8001cf4
08002780: 2846       mov        r0, r5
08002782: fef7d9f8   bl         #0x8000938
08002786: fef7c9fd   bl         #0x800131c
0800278a: 0028       cmp        r0, #0
0800278c: f6d0       beq        #0x800277c
0800278e: 2046       mov        r0, r4
08002790: fef7f4fd   bl         #0x800137c
08002794: f2e7       b          #0x800277c
08002796: 0121       movs       r1, #1
08002798: 0846       mov        r0, r1
0800279a: fff77dfa   bl         #0x8001c98
0800279e: fee7       b          #0x800279e
080027a0: 1349       ldr        r1, [pc, #0x4c] ; [080027f0]=0801f800
080027a2: 0968       ldr        r1, [r1]
080027a4: 491c       adds       r1, r1, #1
080027a6: 12d0       beq        #0x80027ce
080027a8: 4ff44061   mov.w      r1, #0xc00
080027ac: fef7d1fa   bl         #0x8000d52
080027b0: 0028       cmp        r0, #0
080027b2: 4ff00101   mov.w      r1, #1
080027b6: 01da       bge        #0x80027bc
080027b8: 0020       movs       r0, #0
080027ba: 00e0       b          #0x80027be
080027bc: 0220       movs       r0, #2
080027be: fff76bfa   bl         #0x8001c98
080027c2: fff797fa   bl         #0x8001cf4
080027c6: 6420       movs       r0, #0x64
080027c8: fff78ef9   bl         #0x8001ae8
080027cc: fbe7       b          #0x80027c6
080027ce: fef7b5fd   bl         #0x800133c
080027d2: 08b1       cbz        r0, #0x80027d8
080027d4: fff754f9   bl         #0x8001a80
080027d8: 0648       ldr        r0, [pc, #0x18] ; [080027f4]=08003400
080027da: fef7cffd   bl         #0x800137c
080027de: 0020       movs       r0, #0
080027e0: 70bd       pop        {r4, r5, r6, pc}
080027e2: 0000       movs       r0, r0
080027e4: 1800       movs       r0, r3
080027e6: 0020       movs       r0, #0
080027e8: 00f40108   and        r8, r0, #0x810000
080027ec: a086       strh       r0, [r4, #0x34]
080027ee: 0100       movs       r1, r0
080027f0: 00f8       .byte      0x00, 0xf8
080027f2: 0108       lsrs       r1, r0, #0x20
080027f4: 0034       adds       r4, #0
080027f6: 0008       lsrs       r0, r0, #0x20

; Button/marker checks and application launch
0800131c: 10b5       push       {r4, lr}
0800131e: 00f049fb   bl         #0x80019b4
08001322: 38b1       cbz        r0, #0x8001334
08001324: 0448       ldr        r0, [pc, #0x10] ; [08001338]=000f4240
08001326: fff707fb   bl         #0x8000938
0800132a: 00f043fb   bl         #0x80019b4
0800132e: 08b1       cbz        r0, #0x8001334
08001330: 0120       movs       r0, #1
08001332: 10bd       pop        {r4, pc}
08001334: 0020       movs       r0, #0
08001336: 10bd       pop        {r4, pc}
08001338: 4042       rsbs       r0, r0, #0
0800133a: 0f00       movs       r7, r1
0800133c: 10b5       push       {r4, lr}
0800133e: 0b48       ldr        r0, [pc, #0x2c] ; [0800136c]=00075300
08001340: 00f090ff   bl         #0x8002264
08001344: 00f0b2ff   bl         #0x80022ac
08001348: 0948       ldr        r0, [pc, #0x24] ; [08001370]=20004ff0
0800134a: 0a49       ldr        r1, [pc, #0x28] ; [08001374]=5a5aa5a5
0800134c: 0068       ldr        r0, [r0]
0800134e: 8842       cmp        r0, r1
08001350: 08d0       beq        #0x8001364
08001352: 00f02ffb   bl         #0x80019b4
08001356: 38b1       cbz        r0, #0x8001368
08001358: 0748       ldr        r0, [pc, #0x1c] ; [08001378]=000f4240
0800135a: fff7edfa   bl         #0x8000938
0800135e: 00f029fb   bl         #0x80019b4
08001362: 08b1       cbz        r0, #0x8001368
08001364: 0120       movs       r0, #1
08001366: 10bd       pop        {r4, pc}
08001368: 0020       movs       r0, #0
0800136a: 10bd       pop        {r4, pc}
0800136c: 0053       strh       r0, [r0, r4]
0800136e: 0700       movs       r7, r0
08001370: f04f       ldr        r7, [pc, #0x3c0] ; [08001734]=5080f44f
08001372: 0020       movs       r0, #0
08001374: a5a5       adr        r5, #0x294
08001376: 5a5a       ldrh       r2, [r3, r1]
08001378: 4042       rsbs       r0, r0, #0
0800137a: 0f00       movs       r7, r1
0800137c: 10b5       push       {r4, lr}
0800137e: 0168       ldr        r1, [r0]
08001380: 064a       ldr        r2, [pc, #0x18] ; [0800139c]=2ffe0000
08001382: 1140       ands       r1, r2
08001384: b1f1005f   cmp.w      r1, #0x20000000
08001388: 07d1       bne        #0x800139a
0800138a: 4468       ldr        r4, [r0, #4]
0800138c: 0068       ldr        r0, [r0]
0800138e: fef7c0fe   bl         #0x8000112
08001392: a446       mov        ip, r4
08001394: bde81040   pop.w      {r4, lr}
08001398: 6047       bx         ip
0800139a: 10bd       pop        {r4, pc}
0800139c: 0000       movs       r0, r0
0800139e: fe2f       cmp        r7, #0xfe

; Raw button helper
080019b4: 10b5       push       {r4, lr}
080019b6: 094c       ldr        r4, [pc, #0x24] ; [080019dc]=40010800
080019b8: 0221       movs       r1, #2
080019ba: 2046       mov        r0, r4
080019bc: fff779fa   bl         #0x8000eb2
080019c0: 38b9       cbnz       r0, #0x80019d2
080019c2: 0748       ldr        r0, [pc, #0x1c] ; [080019e0]=000f4240
080019c4: fef7b8ff   bl         #0x8000938
080019c8: 0221       movs       r1, #2
080019ca: 2046       mov        r0, r4
080019cc: fff771fa   bl         #0x8000eb2
080019d0: 08b1       cbz        r0, #0x80019d6
080019d2: 0020       movs       r0, #0
080019d4: 10bd       pop        {r4, pc}
080019d6: 0120       movs       r0, #1
080019d8: 10bd       pop        {r4, pc}
080019da: 0000       movs       r0, r0
080019dc: 0008       lsrs       r0, r0, #0x20
080019de: 0140       ands       r1, r0
080019e0: 4042       rsbs       r0, r0, #0
080019e2: 0f00       movs       r7, r1

; Boot interrupt setup
080014a0: 08b5       push       {r3, lr}
080014a2: 0021       movs       r1, #0
080014a4: 4ff00060   mov.w      r0, #0x8000000
080014a8: 00f064f8   bl         #0x8001574
080014ac: 4ff4c060   mov.w      r0, #0x600
080014b0: 00f054f8   bl         #0x800155c
080014b4: 1420       movs       r0, #0x14
080014b6: 8df80000   strb.w     r0, [sp]
080014ba: 0020       movs       r0, #0
080014bc: 8df80200   strb.w     r0, [sp, #2]
080014c0: 0120       movs       r0, #1
080014c2: 8df80300   strb.w     r0, [sp, #3]
080014c6: 6846       mov        r0, sp
080014c8: 00f00af8   bl         #0x80014e0
080014cc: 08bd       pop        {r3, pc}

; VTOR helper
08001574: 024a       ldr        r2, [pc, #8] ; [08001580]=1fffff80
08001576: 1140       ands       r1, r2
08001578: 0143       orrs       r1, r0
0800157a: 0248       ldr        r0, [pc, #8] ; [08001584]=e000ed08
0800157c: 0160       str        r1, [r0]
0800157e: 7047       bx         lr
08001580: 80ff       .byte      0x80, 0xff
08001582: ff1f       subs       r7, r7, #7
08001584: 08ed00e0   stc        p0, c14, [r8, #-0]

; SysTick setup and controls
08002238: 10b5       push       {r4, lr}
0800223a: fff767f8   bl         #0x800130c
0800223e: 0248       ldr        r0, [pc, #8] ; [08002248]=20000030
08002240: 0168       ldr        r1, [r0]
08002242: 0a31       adds       r1, #0xa
08002244: 0160       str        r1, [r0]
08002246: 10bd       pop        {r4, pc}
08002248: 3000       movs       r0, r6
0800224a: 0020       movs       r0, #0
0800224c: 4ff0e021   mov.w      r1, #-0x1fff2000
08002250: 0428       cmp        r0, #4
08002252: 0869       ldr        r0, [r1, #0x10]
08002254: 03d0       beq        #0x800225e
08002256: 20f00400   bic        r0, r0, #4
0800225a: 0861       str        r0, [r1, #0x10]
0800225c: 7047       bx         lr
0800225e: 40f00400   orr        r0, r0, #4
08002262: fae7       b          #0x800225a
08002264: 10b5       push       {r4, lr}
08002266: 0446       mov        r4, r0
08002268: 0420       movs       r0, #4
0800226a: fff7efff   bl         #0x800224c
0800226e: 0622       movs       r2, #6
08002270: 0121       movs       r1, #1
08002272: 0548       ldr        r0, [pc, #0x14] ; [08002288]=0002c39a
08002274: fff788f9   bl         #0x8001588
08002278: 2046       mov        r0, r4
0800227a: 00f02bf8   bl         #0x80022d4
0800227e: bde81040   pop.w      {r4, lr}
08002282: 0120       movs       r0, #1
08002284: 00f01ab8   b.w        #0x80022bc
08002288: 9ac3       stm        r3!, {r1, r3, r4, r7}
0800228a: 0200       movs       r2, r0
0800228c: 4ff0e021   mov.w      r1, #-0x1fff2000
08002290: 30b1       cbz        r0, #0x80022a0
08002292: 0128       cmp        r0, #1
08002294: 0869       ldr        r0, [r1, #0x10]
08002296: 06d0       beq        #0x80022a6
08002298: 20f00100   bic        r0, r0, #1
0800229c: 0861       str        r0, [r1, #0x10]
0800229e: 7047       bx         lr
080022a0: 0020       movs       r0, #0
080022a2: 8861       str        r0, [r1, #0x18]
080022a4: 7047       bx         lr
080022a6: 40f00100   orr        r0, r0, #1
080022aa: f7e7       b          #0x800229c
080022ac: 0249       ldr        r1, [pc, #8] ; [080022b8]=20000000
080022ae: 0020       movs       r0, #0
080022b0: 4860       str        r0, [r1, #4]
080022b2: 0120       movs       r0, #1
080022b4: fff7eabf   b.w        #0x800228c
080022b8: 0000       movs       r0, r0
080022ba: 0020       movs       r0, #0
080022bc: 4ff0e021   mov.w      r1, #-0x1fff2000
080022c0: 0028       cmp        r0, #0
080022c2: 0869       ldr        r0, [r1, #0x10]
080022c4: 02d0       beq        #0x80022cc
080022c6: 40f00200   orr        r0, r0, #2
080022ca: 01e0       b          #0x80022d0
080022cc: 20f00200   bic        r0, r0, #2
080022d0: 0861       str        r0, [r1, #0x10]
080022d2: 7047       bx         lr
080022d4: 4ff0e021   mov.w      r1, #-0x1fff2000
080022d8: 4861       str        r0, [r1, #0x14]
080022da: 7047       bx         lr

; Clock and GPIO setup
08001cf8: 2de9f84f   push.w     {r3, r4, r5, r6, r7, r8, sb, sl, fp, lr}
08001cfc: 4ff48035   mov.w      r5, #0x10000
08001d00: 544c       ldr        r4, [pc, #0x150] ; [08001e54]=20000000
08001d02: 2e11       asrs       r6, r5, #4
08001d04: fff770fd   bl         #0x80017e8
08001d08: 2846       mov        r0, r5
08001d0a: fff7bbfd   bl         #0x8001884
08001d0e: fff709fe   bl         #0x8001924
08001d12: 2070       strb       r0, [r4]
08001d14: 0128       cmp        r0, #1
08001d16: 03d0       beq        #0x8001d20
08001d18: 3046       mov        r0, r6
08001d1a: fef70dfe   bl         #0x8000938
08001d1e: f1e7       b          #0x8001d04
08001d20: 1020       movs       r0, #0x10
08001d22: fef73fff   bl         #0x8000ba4
08001d26: 0220       movs       r0, #2
08001d28: fef7e8ff   bl         #0x8000cfc
08001d2c: 0020       movs       r0, #0
08001d2e: fff79ffd   bl         #0x8001870
08001d32: 0020       movs       r0, #0
08001d34: fff7ccfd   bl         #0x80018d0
08001d38: 4ff48060   mov.w      r0, #0x400
08001d3c: fff7befd   bl         #0x80018bc
08001d40: 4ff40044   mov.w      r4, #0x8000
08001d44: 2046       mov        r0, r4
08001d46: fff72dfd   bl         #0x80017a4
08001d4a: 6101       lsls       r1, r4, #5
08001d4c: 2846       mov        r0, r5
08001d4e: fff7cffd   bl         #0x80018f0
08001d52: 0120       movs       r0, #1
08001d54: fff7c6fd   bl         #0x80018e4
08001d58: 3920       movs       r0, #0x39
08001d5a: fff769fd   bl         #0x8001830
08001d5e: 0028       cmp        r0, #0
08001d60: fad0       beq        #0x8001d58
08001d62: 0220       movs       r0, #2
08001d64: fff7cefd   bl         #0x8001904
08001d68: fff77afd   bl         #0x8001860
08001d6c: 0828       cmp        r0, #8
08001d6e: fbd1       bne        #0x8001d68
08001d70: 0121       movs       r1, #1
08001d72: 44f21d00   movw       r0, #0x401d
08001d76: fff72bfd   bl         #0x80017d0
08001d7a: 0121       movs       r1, #1
08001d7c: 4804       lsls       r0, r1, #0x11
08001d7e: fff71bfd   bl         #0x80017b8
08001d82: 4ff40076   mov.w      r6, #0x200
08001d86: adf80060   strh.w     r6, [sp]
08001d8a: 0225       movs       r5, #2
08001d8c: dff8c8a0   ldr.w      sl, [pc, #0xc8] ; [08001e58]=40010c00
08001d90: 8df80250   strb.w     r5, [sp, #2]
08001d94: 4827       movs       r7, #0x48
08001d96: 8df80370   strb.w     r7, [sp, #3]
08001d9a: 6946       mov        r1, sp
08001d9c: 5046       mov        r0, sl
08001d9e: fff73bf8   bl         #0x8000e18
08001da2: adf80050   strh.w     r5, [sp]
08001da6: dff8b490   ldr.w      sb, [pc, #0xb4] ; [08001e5c]=40010800
08001daa: 8df80250   strb.w     r5, [sp, #2]
08001dae: 8df80370   strb.w     r7, [sp, #3]
08001db2: 6946       mov        r1, sp
08001db4: 4846       mov        r0, sb
08001db6: fff72ff8   bl         #0x8000e18
08001dba: adf80040   strh.w     r4, [sp]
08001dbe: 8df80250   strb.w     r5, [sp, #2]
08001dc2: 1025       movs       r5, #0x10
08001dc4: 8df80350   strb.w     r5, [sp, #3]
08001dc8: 6946       mov        r1, sp
08001dca: 5046       mov        r0, sl
08001dcc: fff724f8   bl         #0x8000e18
08001dd0: 0427       movs       r7, #4
08001dd2: adf80070   strh.w     r7, [sp]
08001dd6: 1820       movs       r0, #0x18
08001dd8: 8df80300   strb.w     r0, [sp, #3]
08001ddc: 6946       mov        r1, sp
08001dde: 4846       mov        r0, sb
08001de0: fff71af8   bl         #0x8000e18
08001de4: 0820       movs       r0, #8
08001de6: adf80000   strh.w     r0, [sp]
08001dea: 4ff00108   mov.w      r8, #1
08001dee: 8df80280   strb.w     r8, [sp, #2]
08001df2: 8df80370   strb.w     r7, [sp, #3]
08001df6: 6946       mov        r1, sp
08001df8: 4846       mov        r0, sb
08001dfa: fff70df8   bl         #0x8000e18
08001dfe: 2020       movs       r0, #0x20
08001e00: adf80000   strh.w     r0, [sp]
08001e04: 8df80280   strb.w     r8, [sp, #2]
08001e08: 8df80350   strb.w     r5, [sp, #3]
08001e0c: 6946       mov        r1, sp
08001e0e: 5046       mov        r0, sl
08001e10: fff702f8   bl         #0x8000e18
08001e14: 2801       lsls       r0, r5, #4
08001e16: adf80000   strh.w     r0, [sp]
08001e1a: 6946       mov        r1, sp
08001e1c: 5046       mov        r0, sl
08001e1e: fef7fbff   bl         #0x8000e18
08001e22: adf80060   strh.w     r6, [sp]
08001e26: 6946       mov        r1, sp
08001e28: 5046       mov        r0, sl
08001e2a: fef7f5ff   bl         #0x8000e18
08001e2e: 0021       movs       r1, #0
08001e30: 0220       movs       r0, #2
08001e32: fff731ff   bl         #0x8001c98
08001e36: 0021       movs       r1, #0
08001e38: 0420       movs       r0, #4
08001e3a: fff72dff   bl         #0x8001c98
08001e3e: 0021       movs       r1, #0
08001e40: 0120       movs       r0, #1
08001e42: fff729ff   bl         #0x8001c98
08001e46: 2146       mov        r1, r4
08001e48: 5046       mov        r0, sl
08001e4a: fff73bf8   bl         #0x8000ec4
08001e4e: bde8f88f   pop.w      {r3, r4, r5, r6, r7, r8, sb, sl, fp, pc}
08001e52: 0000       movs       r0, r0
08001e54: 0000       movs       r0, r0
08001e56: 0020       movs       r0, #0
08001e58: 000c       lsrs       r0, r0, #0x10
08001e5a: 0140       ands       r1, r0
08001e5c: 0008       lsrs       r0, r0, #0x20
08001e5e: 0140       ands       r1, r0

; Protection maintenance
08000d94: 10b5       push       {r4, lr}
08000d96: fff7cdfe   bl         #0x8000b34
08000d9a: 0128       cmp        r0, #1
08000d9c: 06d0       beq        #0x8000dac
08000d9e: fff7b9ff   bl         #0x8000d14
08000da2: 0120       movs       r0, #1
08000da4: fff764ff   bl         #0x8000c70
08000da8: fff7eafe   bl         #0x8000b80
08000dac: fff7e0fe   bl         #0x8000b70
08000db0: 084c       ldr        r4, [pc, #0x20] ; [08000dd4]=20000018
08000db2: 6060       str        r0, [r4, #4]
08000db4: 6068       ldr        r0, [r4, #4]
08000db6: 00f0c000   and        r0, r0, #0xc0
08000dba: a060       str        r0, [r4, #8]
08000dbc: a068       ldr        r0, [r4, #8]
08000dbe: 0028       cmp        r0, #0
08000dc0: 06d0       beq        #0x8000dd0
08000dc2: fff75dfe   bl         #0x8000a80
08000dc6: 4ff0ff30   mov.w      r0, #-1
08000dca: fff703fe   bl         #0x80009d4
08000dce: 6070       strb       r0, [r4, #1]
08000dd0: 10bd       pop        {r4, pc}
08000dd2: 0000       movs       r0, r0
08000dd4: 1800       movs       r0, r3
08000dd6: 0020       movs       r0, #0

; USB update loop
08001a80: 2de9f041   push.w     {r4, r5, r6, r7, r8, lr}
08001a84: 0024       movs       r4, #0
08001a86: 2746       mov        r7, r4
08001a88: 1448       ldr        r0, [pc, #0x50] ; [08001adc]=00075300
08001a8a: 00f0ebfb   bl         #0x8002264
08001a8e: 00f00dfc   bl         #0x80022ac
08001a92: 00f03dfc   bl         #0x8002310
08001a96: 3225       movs       r5, #0x32
08001a98: 114e       ldr        r6, [pc, #0x44] ; [08001ae0]=20000018
08001a9a: fff753fa   bl         #0x8000f44
08001a9e: b0fbf5f0   udiv       r0, r0, r5
08001aa2: a042       cmp        r0, r4
08001aa4: 09d9       bls        #0x8001aba
08001aa6: fff74dfa   bl         #0x8000f44
08001aaa: b0fbf5f4   udiv       r4, r0, r5
08001aae: 77b1       cbz        r7, #0x8001ace
08001ab0: 0021       movs       r1, #0
08001ab2: 0f46       mov        r7, r1
08001ab4: 0220       movs       r0, #2
08001ab6: 00f0eff8   bl         #0x8001c98
08001aba: 3078       ldrb       r0, [r6]
08001abc: 48b1       cbz        r0, #0x8001ad2
08001abe: 0948       ldr        r0, [pc, #0x24] ; [08001ae4]=2000005c
08001ac0: 0068       ldr        r0, [r0]
08001ac2: 0628       cmp        r0, #6
08001ac4: 08d0       beq        #0x8001ad8
08001ac6: bde8f041   pop.w      {r4, r5, r6, r7, r8, lr}
08001aca: fff753ba   b.w        #0x8000f74
08001ace: 0121       movs       r1, #1
08001ad0: efe7       b          #0x8001ab2
08001ad2: fff73dfa   bl         #0x8000f50
08001ad6: e0e7       b          #0x8001a9a
08001ad8: bde8f081   pop.w      {r4, r5, r6, r7, r8, pc}
08001adc: 0053       strh       r0, [r0, r4]
08001ade: 0700       movs       r7, r0
08001ae0: 1800       movs       r0, r3
08001ae2: 0020       movs       r0, #0
08001ae4: 5c00       lsls       r4, r3, #1
08001ae6: 0020       movs       r0, #0

; USB exit
08000f74: 0548       ldr        r0, [pc, #0x14] ; [08000f8c]=200000e4
08000f76: 10b5       push       {r4, lr}
08000f78: 4068       ldr        r0, [r0, #4]
08000f7a: 8047       blx        r0
08000f7c: 00f0ecfb   bl         #0x8001758
08000f80: fff7e2fc   bl         #0x8000948
08000f84: 0249       ldr        r1, [pc, #8] ; [08000f90]=2000005c
08000f86: 0620       movs       r0, #6
08000f88: 0860       str        r0, [r1]
08000f8a: 10bd       pop        {r4, pc}
08000f8c: e400       lsls       r4, r4, #3
08000f8e: 0020       movs       r0, #0
08000f90: 5c00       lsls       r4, r3, #1
08000f92: 0020       movs       r0, #0

; USB shutdown
08001758: 10b5       push       {r4, lr}
0800175a: 064c       ldr        r4, [pc, #0x18] ; [08001774]=40005c40
0800175c: 0120       movs       r0, #1
0800175e: 2060       str        r0, [r4]
08001760: 211d       adds       r1, r4, #4
08001762: 0020       movs       r0, #0
08001764: 0860       str        r0, [r1]
08001766: 00f0c5fd   bl         #0x80022f4
0800176a: 0320       movs       r0, #3
0800176c: 2060       str        r0, [r4]
0800176e: 0020       movs       r0, #0
08001770: 10bd       pop        {r4, pc}
08001772: 0000       movs       r0, r0
08001774: 405c       ldrb       r0, [r0, r1]
08001776: 0040       ands       r0, r0
