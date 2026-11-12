; Uranai Sensation - sexo de la persona para {o}/{a}. Va en 7FA0h de cada segmento del mapper con
; texto (es el que está en la página 1 mientras se descomprime). Ensamblar con sjasmplus.
	output "sexo.bin"
	org 7FA0h
; sexo: Z = hombre. Busca en la lista (D700h, fichas de 48 bytes, sexo en +16h) la persona cuyo
; nombre está en D218h (el que se pone en {N}); si no está, la persona activa (DAF0h-DAF2h).
sexo:	push bc
	push de
	push hl
	ld a,(0D218h)
	inc a
	jr z,.idx
	ld hl,0D700h
	ld b,21
.lp:	push hl
	ld de,0D218h
	ld c,8
.cmp:	ld a,(de)
	cp (hl)
	jr nz,.nx
	inc hl
	inc de
	dec c
	jr nz,.cmp
	pop hl
	ld de,16h
	add hl,de
	jr .res
.nx:	pop hl
	ld de,30h
	add hl,de
	djnz .lp
.idx:	ld hl,0DAF0h
	ld b,3
.il:	ld a,(hl)
	cp 21
	jr c,.got
	inc hl
	djnz .il
	xor a
	jr .fin
.got:	ld l,a
	ld h,0
	add hl,hl
	add hl,hl
	add hl,hl
	add hl,hl
	ld d,h
	ld e,l
	add hl,hl
	add hl,de
	ld de,0D716h
	add hl,de
.res:	ld a,(hl)
	cp 2
	jr c,.fin
	xor a
.fin:	and 1
	pop hl
	pop de
	pop bc
	ret

	assert $ <= 8000h
