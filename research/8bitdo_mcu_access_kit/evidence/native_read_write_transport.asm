100053a0:	55                   	push   ebp
100053a1:	8b ec                	mov    ebp,esp
100053a3:	81 ec 0c 01 00 00    	sub    esp,0x10c
100053a9:	a1 e4 bf 1c 10       	mov    eax,ds:0x101cbfe4
100053ae:	33 c5                	xor    eax,ebp
100053b0:	89 45 fc             	mov    DWORD PTR [ebp-0x4],eax
100053b3:	80 3d bb 49 1d 10 00 	cmp    BYTE PTR ds:0x101d49bb,0x0
100053ba:	0f 85 db 00 00 00    	jne    0x1000549b
100053c0:	83 3d bc 49 1d 10 00 	cmp    DWORD PTR ds:0x101d49bc,0x0
100053c7:	0f 85 ce 00 00 00    	jne    0x1000549b
100053cd:	80 3d ba 49 1d 10 00 	cmp    BYTE PTR ds:0x101d49ba,0x0
100053d4:	56                   	push   esi
100053d5:	57                   	push   edi
100053d6:	75 12                	jne    0x100053ea
100053d8:	80 3d b9 49 1d 10 00 	cmp    BYTE PTR ds:0x101d49b9,0x0
100053df:	75 09                	jne    0x100053ea
100053e1:	80 3d b8 49 1d 10 00 	cmp    BYTE PTR ds:0x101d49b8,0x0
100053e8:	74 51                	je     0x1000543b
100053ea:	8b 75 08             	mov    esi,DWORD PTR [ebp+0x8]
100053ed:	8d bd 7d ff ff ff    	lea    edi,[ebp-0x83]
100053f3:	c6 85 7c ff ff ff 81 	mov    BYTE PTR [ebp-0x84],0x81
100053fa:	b9 0f 00 00 00       	mov    ecx,0xf
100053ff:	f3 a5                	rep movs DWORD PTR es:[edi],DWORD PTR ds:[esi]
10005401:	8b 0d b4 49 1d 10    	mov    ecx,DWORD PTR ds:0x101d49b4
10005407:	33 c0                	xor    eax,eax
10005409:	66 a5                	movs   WORD PTR es:[edi],WORD PTR ds:[esi]
1000540b:	a4                   	movs   BYTE PTR es:[edi],BYTE PTR ds:[esi]
1000540c:	83 f9 ff             	cmp    ecx,0xffffffff
1000540f:	74 18                	je     0x10005429
10005411:	50                   	push   eax
10005412:	8d 85 f8 fe ff ff    	lea    eax,[ebp-0x108]
10005418:	50                   	push   eax
10005419:	6a 40                	push   0x40
1000541b:	8d 85 7c ff ff ff    	lea    eax,[ebp-0x84]
10005421:	50                   	push   eax
10005422:	51                   	push   ecx
10005423:	ff 15 70 a4 17 10    	call   DWORD PTR ds:0x1017a470
10005429:	5f                   	pop    edi
1000542a:	5e                   	pop    esi
1000542b:	8b 4d fc             	mov    ecx,DWORD PTR [ebp-0x4]
1000542e:	33 cd                	xor    ecx,ebp
10005430:	e8 ad 23 14 00       	call   0x101477e2
10005435:	8b e5                	mov    esp,ebp
10005437:	5d                   	pop    ebp
10005438:	c2 08 00             	ret    0x8
1000543b:	0f b6 75 0c          	movzx  esi,BYTE PTR [ebp+0xc]
1000543f:	33 ff                	xor    edi,edi
10005441:	c6 85 fc fe ff ff 00 	mov    BYTE PTR [ebp-0x104],0x0
10005448:	85 f6                	test   esi,esi
1000544a:	74 13                	je     0x1000545f
1000544c:	56                   	push   esi
1000544d:	ff 75 08             	push   DWORD PTR [ebp+0x8]
10005450:	8d 85 fd fe ff ff    	lea    eax,[ebp-0x103]
10005456:	50                   	push   eax
10005457:	e8 54 44 14 00       	call   0x101498b0
1000545c:	83 c4 0c             	add    esp,0xc
1000545f:	8b 0d b4 49 1d 10    	mov    ecx,DWORD PTR ds:0x101d49b4
10005465:	83 f9 ff             	cmp    ecx,0xffffffff
10005468:	74 1d                	je     0x10005487
1000546a:	6a 00                	push   0x0
1000546c:	8d 85 f4 fe ff ff    	lea    eax,[ebp-0x10c]
10005472:	50                   	push   eax
10005473:	8d 46 01             	lea    eax,[esi+0x1]
10005476:	50                   	push   eax
10005477:	8d 85 fc fe ff ff    	lea    eax,[ebp-0x104]
1000547d:	50                   	push   eax
1000547e:	51                   	push   ecx
1000547f:	ff 15 70 a4 17 10    	call   DWORD PTR ds:0x1017a470
10005485:	8b f8                	mov    edi,eax
10005487:	8b c7                	mov    eax,edi
10005489:	5f                   	pop    edi
1000548a:	5e                   	pop    esi
1000548b:	8b 4d fc             	mov    ecx,DWORD PTR [ebp-0x4]
1000548e:	33 cd                	xor    ecx,ebp
10005490:	e8 4d 23 14 00       	call   0x101477e2
10005495:	8b e5                	mov    esp,ebp
10005497:	5d                   	pop    ebp
10005498:	c2 08 00             	ret    0x8
1000549b:	8b 45 08             	mov    eax,DWORD PTR [ebp+0x8]
1000549e:	33 c9                	xor    ecx,ecx
100054a0:	88 8d 7c ff ff ff    	mov    BYTE PTR [ebp-0x84],cl
100054a6:	0f 10 00             	movups xmm0,XMMWORD PTR [eax]
100054a9:	0f 11 85 7d ff ff ff 	movups XMMWORD PTR [ebp-0x83],xmm0
100054b0:	0f 10 40 10          	movups xmm0,XMMWORD PTR [eax+0x10]
100054b4:	0f 11 45 8d          	movups XMMWORD PTR [ebp-0x73],xmm0
100054b8:	0f 10 40 20          	movups xmm0,XMMWORD PTR [eax+0x20]
100054bc:	0f 11 45 9d          	movups XMMWORD PTR [ebp-0x63],xmm0
100054c0:	0f 10 40 30          	movups xmm0,XMMWORD PTR [eax+0x30]
100054c4:	a1 b4 49 1d 10       	mov    eax,ds:0x101d49b4
100054c9:	0f 11 45 ad          	movups XMMWORD PTR [ebp-0x53],xmm0
100054cd:	83 f8 ff             	cmp    eax,0xffffffff
100054d0:	74 1a                	je     0x100054ec
100054d2:	51                   	push   ecx
100054d3:	8d 8d f8 fe ff ff    	lea    ecx,[ebp-0x108]
100054d9:	51                   	push   ecx
100054da:	6a 41                	push   0x41
100054dc:	8d 8d 7c ff ff ff    	lea    ecx,[ebp-0x84]
100054e2:	51                   	push   ecx
100054e3:	50                   	push   eax
100054e4:	ff 15 70 a4 17 10    	call   DWORD PTR ds:0x1017a470
100054ea:	8b c8                	mov    ecx,eax
100054ec:	8b c1                	mov    eax,ecx
100054ee:	8b 4d fc             	mov    ecx,DWORD PTR [ebp-0x4]
100054f1:	33 cd                	xor    ecx,ebp
100054f3:	e8 ea 22 14 00       	call   0x101477e2
100054f8:	8b e5                	mov    esp,ebp
100054fa:	5d                   	pop    ebp
100054fb:	c2 08 00             	ret    0x8
100054fe:	cc                   	int3
100054ff:	cc                   	int3
10005720:	55                   	push   ebp
10005721:	8b ec                	mov    ebp,esp
10005723:	81 ec 34 01 00 00    	sub    esp,0x134
10005729:	a1 e4 bf 1c 10       	mov    eax,ds:0x101cbfe4
1000572e:	33 c5                	xor    eax,ebp
10005730:	89 45 fc             	mov    DWORD PTR [ebp-0x4],eax
10005733:	80 3d ba 49 1d 10 00 	cmp    BYTE PTR ds:0x101d49ba,0x0
1000573a:	56                   	push   esi
1000573b:	57                   	push   edi
1000573c:	8b 7d 08             	mov    edi,DWORD PTR [ebp+0x8]
1000573f:	0f 84 d1 00 00 00    	je     0x10005816
10005745:	83 3d b0 49 1d 10 ff 	cmp    DWORD PTR ds:0x101d49b0,0xffffffff
1000574c:	0f 84 ab 00 00 00    	je     0x100057fd
10005752:	68 64 e2 1a 10       	push   0x101ae264
10005757:	6a 01                	push   0x1
10005759:	6a 01                	push   0x1
1000575b:	6a 00                	push   0x0
1000575d:	ff 15 40 a4 17 10    	call   DWORD PTR ds:0x1017a440
10005763:	8b f0                	mov    esi,eax
10005765:	c7 85 e8 fe ff ff 00 	mov    DWORD PTR [ebp-0x118],0x0
1000576c:	00 00 00 
1000576f:	8d 85 e0 fe ff ff    	lea    eax,[ebp-0x120]
10005775:	89 b5 f0 fe ff ff    	mov    DWORD PTR [ebp-0x110],esi
1000577b:	50                   	push   eax
1000577c:	8d 85 f8 fe ff ff    	lea    eax,[ebp-0x108]
10005782:	c7 85 ec fe ff ff 00 	mov    DWORD PTR [ebp-0x114],0x0
10005789:	00 00 00 
1000578c:	50                   	push   eax
1000578d:	6a 40                	push   0x40
1000578f:	8d 85 7c ff ff ff    	lea    eax,[ebp-0x84]
10005795:	50                   	push   eax
10005796:	ff 35 b0 49 1d 10    	push   DWORD PTR ds:0x101d49b0
1000579c:	ff 15 6c a4 17 10    	call   DWORD PTR ds:0x1017a46c
100057a2:	68 2c 01 00 00       	push   0x12c
100057a7:	56                   	push   esi
100057a8:	ff 15 3c a4 17 10    	call   DWORD PTR ds:0x1017a43c
100057ae:	8b f0                	mov    esi,eax
100057b0:	81 fe 02 01 00 00    	cmp    esi,0x102
100057b6:	74 08                	je     0x100057c0
100057b8:	81 fe 80 00 00 00    	cmp    esi,0x80
100057be:	75 0c                	jne    0x100057cc
100057c0:	ff 35 b0 49 1d 10    	push   DWORD PTR ds:0x101d49b0
100057c6:	ff 15 38 a4 17 10    	call   DWORD PTR ds:0x1017a438
100057cc:	85 f6                	test   esi,esi
100057ce:	75 32                	jne    0x10005802
100057d0:	0f b6 45 0c          	movzx  eax,BYTE PTR [ebp+0xc]
100057d4:	85 c0                	test   eax,eax
100057d6:	74 2a                	je     0x10005802
100057d8:	50                   	push   eax
100057d9:	8d 85 7d ff ff ff    	lea    eax,[ebp-0x83]
100057df:	50                   	push   eax
100057e0:	57                   	push   edi
100057e1:	e8 ca 40 14 00       	call   0x101498b0
100057e6:	83 c4 0c             	add    esp,0xc
100057e9:	8b c6                	mov    eax,esi
100057eb:	5f                   	pop    edi
100057ec:	5e                   	pop    esi
100057ed:	8b 4d fc             	mov    ecx,DWORD PTR [ebp-0x4]
100057f0:	33 cd                	xor    ecx,ebp
100057f2:	e8 eb 1f 14 00       	call   0x101477e2
100057f7:	8b e5                	mov    esp,ebp
100057f9:	5d                   	pop    ebp
100057fa:	c2 08 00             	ret    0x8
100057fd:	be 80 00 00 00       	mov    esi,0x80
10005802:	5f                   	pop    edi
10005803:	8b c6                	mov    eax,esi
10005805:	5e                   	pop    esi
10005806:	8b 4d fc             	mov    ecx,DWORD PTR [ebp-0x4]
10005809:	33 cd                	xor    ecx,ebp
1000580b:	e8 d2 1f 14 00       	call   0x101477e2
10005810:	8b e5                	mov    esp,ebp
10005812:	5d                   	pop    ebp
10005813:	c2 08 00             	ret    0x8
10005816:	83 3d b0 49 1d 10 ff 	cmp    DWORD PTR ds:0x101d49b0,0xffffffff
1000581d:	0f 84 b5 00 00 00    	je     0x100058d8
10005823:	53                   	push   ebx
10005824:	68 62 e2 1a 10       	push   0x101ae262
10005829:	6a 01                	push   0x1
1000582b:	6a 01                	push   0x1
1000582d:	6a 00                	push   0x0
1000582f:	ff 15 40 a4 17 10    	call   DWORD PTR ds:0x1017a440
10005835:	0f b6 5d 0c          	movzx  ebx,BYTE PTR [ebp+0xc]
10005839:	8b f0                	mov    esi,eax
1000583b:	8d 85 cc fe ff ff    	lea    eax,[ebp-0x134]
10005841:	89 b5 dc fe ff ff    	mov    DWORD PTR [ebp-0x124],esi
10005847:	50                   	push   eax
10005848:	8d 85 f4 fe ff ff    	lea    eax,[ebp-0x10c]
1000584e:	c7 85 d4 fe ff ff 00 	mov    DWORD PTR [ebp-0x12c],0x0
10005855:	00 00 00 
10005858:	50                   	push   eax
10005859:	8d 43 01             	lea    eax,[ebx+0x1]
1000585c:	c7 85 d8 fe ff ff 00 	mov    DWORD PTR [ebp-0x128],0x0
10005863:	00 00 00 
10005866:	50                   	push   eax
10005867:	8d 85 fc fe ff ff    	lea    eax,[ebp-0x104]
1000586d:	50                   	push   eax
1000586e:	ff 35 b0 49 1d 10    	push   DWORD PTR ds:0x101d49b0
10005874:	ff 15 6c a4 17 10    	call   DWORD PTR ds:0x1017a46c
1000587a:	68 2c 01 00 00       	push   0x12c
1000587f:	56                   	push   esi
10005880:	ff 15 3c a4 17 10    	call   DWORD PTR ds:0x1017a43c
10005886:	8b f0                	mov    esi,eax
10005888:	ff 15 48 a4 17 10    	call   DWORD PTR ds:0x1017a448
1000588e:	81 fe 02 01 00 00    	cmp    esi,0x102
10005894:	74 08                	je     0x1000589e
10005896:	81 fe 80 00 00 00    	cmp    esi,0x80
1000589c:	75 0c                	jne    0x100058aa
1000589e:	ff 35 b0 49 1d 10    	push   DWORD PTR ds:0x101d49b0
100058a4:	ff 15 38 a4 17 10    	call   DWORD PTR ds:0x1017a438
100058aa:	85 f6                	test   esi,esi
100058ac:	75 15                	jne    0x100058c3
100058ae:	85 db                	test   ebx,ebx
100058b0:	74 11                	je     0x100058c3
100058b2:	53                   	push   ebx
100058b3:	8d 85 fd fe ff ff    	lea    eax,[ebp-0x103]
100058b9:	50                   	push   eax
100058ba:	57                   	push   edi
100058bb:	e8 f0 3f 14 00       	call   0x101498b0
100058c0:	83 c4 0c             	add    esp,0xc
100058c3:	5b                   	pop    ebx
100058c4:	5f                   	pop    edi
100058c5:	8b c6                	mov    eax,esi
100058c7:	5e                   	pop    esi
100058c8:	8b 4d fc             	mov    ecx,DWORD PTR [ebp-0x4]
100058cb:	33 cd                	xor    ecx,ebp
100058cd:	e8 10 1f 14 00       	call   0x101477e2
100058d2:	8b e5                	mov    esp,ebp
100058d4:	5d                   	pop    ebp
100058d5:	c2 08 00             	ret    0x8
100058d8:	8b 4d fc             	mov    ecx,DWORD PTR [ebp-0x4]
100058db:	b8 80 00 00 00       	mov    eax,0x80
100058e0:	5f                   	pop    edi
100058e1:	33 cd                	xor    ecx,ebp
100058e3:	5e                   	pop    esi
100058e4:	e8 f9 1e 14 00       	call   0x101477e2
100058e9:	8b e5                	mov    esp,ebp
100058eb:	5d                   	pop    ebp
100058ec:	c2 08 00             	ret    0x8
100058ef:	cc                   	int3
10009c60:	55                   	push   ebp
10009c61:	8b ec                	mov    ebp,esp
10009c63:	81 ec 04 04 00 00    	sub    esp,0x404
10009c69:	a1 e4 bf 1c 10       	mov    eax,ds:0x101cbfe4
10009c6e:	33 c5                	xor    eax,ebp
10009c70:	89 45 fc             	mov    DWORD PTR [ebp-0x4],eax
10009c73:	8b 45 08             	mov    eax,DWORD PTR [ebp+0x8]
10009c76:	c7 85 fc fb ff ff 00 	mov    DWORD PTR [ebp-0x404],0x2c3200
10009c7d:	32 2c 00 
10009c80:	c7 85 00 fc ff ff 00 	mov    DWORD PTR [ebp-0x400],0x8003000
10009c87:	30 00 08 
10009c8a:	6a 40                	push   0x40
10009c8c:	0f 10 00             	movups xmm0,XMMWORD PTR [eax]
10009c8f:	68 78 5a 1d 10       	push   0x101d5a78
10009c94:	0f 11 85 04 fc ff ff 	movups XMMWORD PTR [ebp-0x3fc],xmm0
10009c9b:	0f 10 40 10          	movups xmm0,XMMWORD PTR [eax+0x10]
10009c9f:	0f 11 85 14 fc ff ff 	movups XMMWORD PTR [ebp-0x3ec],xmm0
10009ca6:	f3 0f 7e 40 20       	movq   xmm0,QWORD PTR [eax+0x20]
10009cab:	66 0f d6 85 24 fc ff 	movq   QWORD PTR [ebp-0x3dc],xmm0
10009cb2:	ff 
10009cb3:	0f 10 85 fc fb ff ff 	movups xmm0,XMMWORD PTR [ebp-0x404]
10009cba:	c6 05 78 5a 1d 10 30 	mov    BYTE PTR ds:0x101d5a78,0x30
10009cc1:	0f 11 05 79 5a 1d 10 	movups XMMWORD PTR ds:0x101d5a79,xmm0
10009cc8:	0f 10 85 0c fc ff ff 	movups xmm0,XMMWORD PTR [ebp-0x3f4]
10009ccf:	0f 11 05 89 5a 1d 10 	movups XMMWORD PTR ds:0x101d5a89,xmm0
10009cd6:	0f 10 85 1c fc ff ff 	movups xmm0,XMMWORD PTR [ebp-0x3e4]
10009cdd:	0f 11 05 99 5a 1d 10 	movups XMMWORD PTR ds:0x101d5a99,xmm0
10009ce4:	e8 b7 b6 ff ff       	call   0x100053a0
10009ce9:	8b 4d fc             	mov    ecx,DWORD PTR [ebp-0x4]
10009cec:	f7 d8                	neg    eax
10009cee:	1b c0                	sbb    eax,eax
10009cf0:	33 cd                	xor    ecx,ebp
10009cf2:	f7 d8                	neg    eax
10009cf4:	48                   	dec    eax
10009cf5:	e8 e8 da 13 00       	call   0x101477e2
10009cfa:	8b e5                	mov    esp,ebp
10009cfc:	5d                   	pop    ebp
10009cfd:	c3                   	ret
10009cfe:	cc                   	int3
10009cff:	cc                   	int3
10009d00:	55                   	push   ebp
10009d01:	8b ec                	mov    ebp,esp
10009d03:	81 ec 00 04 00 00    	sub    esp,0x400
10009d09:	53                   	push   ebx
10009d0a:	56                   	push   esi
10009d0b:	57                   	push   edi
10009d0c:	0f 57 c0             	xorps  xmm0,xmm0
10009d0f:	c7 85 00 fc ff ff 00 	mov    DWORD PTR [ebp-0x400],0x1b3100
10009d16:	31 1b 00 
10009d19:	8b 85 00 fc ff ff    	mov    eax,DWORD PTR [ebp-0x400]
10009d1f:	33 f6                	xor    esi,esi
10009d21:	6a 40                	push   0x40
10009d23:	c7 85 04 fc ff ff 00 	mov    DWORD PTR [ebp-0x3fc],0x8003000
10009d2a:	30 00 08 
10009d2d:	8b 8d 04 fc ff ff    	mov    ecx,DWORD PTR [ebp-0x3fc]
10009d33:	68 78 5a 1d 10       	push   0x101d5a78
10009d38:	0f 11 05 c4 59 1d 10 	movups XMMWORD PTR ds:0x101d59c4,xmm0
10009d3f:	c6 05 78 5a 1d 10 08 	mov    BYTE PTR ds:0x101d5a78,0x8
10009d46:	0f 11 05 d4 59 1d 10 	movups XMMWORD PTR ds:0x101d59d4,xmm0
10009d4d:	a3 79 5a 1d 10       	mov    ds:0x101d5a79,eax
10009d52:	66 0f d6 05 e4 59 1d 	movq   QWORD PTR ds:0x101d59e4,xmm0
10009d59:	10 
10009d5a:	89 0d 7d 5a 1d 10    	mov    DWORD PTR ds:0x101d5a7d,ecx
10009d60:	e8 3b b6 ff ff       	call   0x100053a0
10009d65:	c6 05 9e ca 1c 10 31 	mov    BYTE PTR ds:0x101cca9e,0x31
10009d6c:	8d 5e 1b             	lea    ebx,[esi+0x1b]
10009d6f:	90                   	nop
10009d70:	6a 40                	push   0x40
10009d72:	68 38 5a 1d 10       	push   0x101d5a38
10009d77:	e8 a4 b9 ff ff       	call   0x10005720
10009d7c:	85 c0                	test   eax,eax
10009d7e:	0f 85 e1 00 00 00    	jne    0x10009e65
10009d84:	38 05 39 5a 1d 10    	cmp    BYTE PTR ds:0x101d5a39,al
10009d8a:	75 e4                	jne    0x10009d70
10009d8c:	80 3d 3a 5a 1d 10 14 	cmp    BYTE PTR ds:0x101d5a3a,0x14
10009d93:	75 db                	jne    0x10009d70
10009d95:	80 3d 9e ca 1c 10 31 	cmp    BYTE PTR ds:0x101cca9e,0x31
10009d9c:	75 d2                	jne    0x10009d70
10009d9e:	0f b6 0d 3c 5a 1d 10 	movzx  ecx,BYTE PTR ds:0x101d5a3c
10009da5:	0f b6 05 3b 5a 1d 10 	movzx  eax,BYTE PTR ds:0x101d5a3b
10009dac:	66 c1 e1 08          	shl    cx,0x8
10009db0:	66 0b c8             	or     cx,ax
10009db3:	0f b7 c6             	movzx  eax,si
10009db6:	66 83 e9 04          	sub    cx,0x4
10009dba:	05 c4 59 1d 10       	add    eax,0x101d59c4
10009dbf:	0f b7 f9             	movzx  edi,cx
10009dc2:	57                   	push   edi
10009dc3:	68 3d 5a 1d 10       	push   0x101d5a3d
10009dc8:	50                   	push   eax
10009dc9:	e8 e2 fa 13 00       	call   0x101498b0
10009dce:	03 f7                	add    esi,edi
10009dd0:	83 c4 0c             	add    esp,0xc
10009dd3:	66 83 fe 28          	cmp    si,0x28
10009dd7:	0f 83 88 00 00 00    	jae    0x10009e65
10009ddd:	b8 28 00 00 00       	mov    eax,0x28
10009de2:	0f b7 ce             	movzx  ecx,si
10009de5:	2b c6                	sub    eax,esi
10009de7:	66 c7 85 00 fc ff ff 	mov    WORD PTR [ebp-0x400],0x3100
10009dee:	00 31 
10009df0:	0f b7 c0             	movzx  eax,ax
10009df3:	83 f8 1b             	cmp    eax,0x1b
10009df6:	c6 05 78 5a 1d 10 08 	mov    BYTE PTR ds:0x101d5a78,0x8
10009dfd:	6a 40                	push   0x40
10009dff:	0f 47 c3             	cmova  eax,ebx
10009e02:	81 c1 00 30 00 08    	add    ecx,0x8003000
10009e08:	83 c0 04             	add    eax,0x4
10009e0b:	88 8d 04 fc ff ff    	mov    BYTE PTR [ebp-0x3fc],cl
10009e11:	88 85 02 fc ff ff    	mov    BYTE PTR [ebp-0x3fe],al
10009e17:	c1 e8 08             	shr    eax,0x8
10009e1a:	88 85 03 fc ff ff    	mov    BYTE PTR [ebp-0x3fd],al
10009e20:	8b c1                	mov    eax,ecx
10009e22:	c1 e8 08             	shr    eax,0x8
10009e25:	88 85 05 fc ff ff    	mov    BYTE PTR [ebp-0x3fb],al
10009e2b:	8b c1                	mov    eax,ecx
10009e2d:	c1 e8 10             	shr    eax,0x10
10009e30:	c1 e9 18             	shr    ecx,0x18
10009e33:	88 85 06 fc ff ff    	mov    BYTE PTR [ebp-0x3fa],al
10009e39:	8b 85 00 fc ff ff    	mov    eax,DWORD PTR [ebp-0x400]
10009e3f:	88 8d 07 fc ff ff    	mov    BYTE PTR [ebp-0x3f9],cl
10009e45:	8b 8d 04 fc ff ff    	mov    ecx,DWORD PTR [ebp-0x3fc]
10009e4b:	68 78 5a 1d 10       	push   0x101d5a78
10009e50:	a3 79 5a 1d 10       	mov    ds:0x101d5a79,eax
10009e55:	89 0d 7d 5a 1d 10    	mov    DWORD PTR ds:0x101d5a7d,ecx
10009e5b:	e8 40 b5 ff ff       	call   0x100053a0
10009e60:	e9 0b ff ff ff       	jmp    0x10009d70
10009e65:	5f                   	pop    edi
10009e66:	5e                   	pop    esi
10009e67:	5b                   	pop    ebx
10009e68:	8b e5                	mov    esp,ebp
10009e6a:	5d                   	pop    ebp
10009e6b:	c3                   	ret
10009e6c:	cc                   	int3
10009e6d:	cc                   	int3
10009e6e:	cc                   	int3
10009e6f:	cc                   	int3
