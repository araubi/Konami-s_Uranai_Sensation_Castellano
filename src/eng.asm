; Uranai Sensation (Konami 1988) - motor de texto para la traducción al castellano
; Texto comprimido en los segmentos 4-7 del mapper (página 1), trozos de texto virtuales
; en lugar de los sectores japoneses y descompresión en un búfer de 256 bytes.
; Ensamblar con sjasmplus. Las constantes que dependen de los datos vienen de gen.inc.

	include "gen.inc"

BUF	equ 0DB00h		; búfer de texto descomprimido (libre en todas las escenas)
BUF2	equ 0DC00h		; búfer de la impresora de UI (hasta DCAFh)
DICT	equ 4000h		; diccionario de pares, al principio de cada segmento
CTABP	equ 41FEh		; puntero a la tabla de trozos virtuales (segmento 4)
PIDX	equ 4200h		; índice de partes: segmento, dirección (segmento 4)
TOK0	equ 5Eh			; primera ficha de la compresión
LOADRD	equ 8928h		; lectura de sectores del juego (A = función BDOS)
BOOTRD	equ 0C04Fh		; lectura de sectores del sector de arranque

; ---------------------------------------------------------------------------
; Ampliación del sector de arranque: carga el inicializador y lo ejecuta
	output "boot.bin"
	org 0C060h
boot:	ld de,0A000h
	ld bc,INITSEC
	ld hl,INITLEN*256
	call BOOTRD
	call 0A000h
	jp 8200h

; ---------------------------------------------------------------------------
; Inicializador (se carga en A000h; usa B000h-BFFFh como búfer de disco)
	output "init.bin"
	org 0A000h
init:	ld hl,resimg		; código residente a 8003h
	ld de,8003h
	ld bc,resend-res
	ldir
	in a,(0A8h)		; ¿está expandida la ranura de la RAM de la página 2?
	rrca
	rrca
	rrca
	rrca
	and 3
	ld e,a
	ld d,0
	ld hl,0FCC1h
	add hl,de
	ld a,(hl)
	and 80h
	ld (EXPF),a
	ld a,4			; ¿hay 128 KB? con 64 KB el segmento 4 es el 0 (página 3)
	call map_on
	ld a,(0C1F0h)
	cpl
	ld (41F0h),a
	ld b,a
	ld a,(0C1F0h)
	cp b
	push af
	call map_off
	pop af
	jr z,noram
	ld hl,runs		; bloques de disco -> mapper
.lp:	ld c,(hl)
	inc hl
	ld b,(hl)
	inc hl
	ld a,b
	and c
	inc a
	ret z
	ld a,(hl)		; sectores
	inc hl
	push hl
	ld h,a
	ld l,0
	ld de,0B000h
	push hl
	call BOOTRD
	pop bc			; B = sectores
	pop hl
	ld a,(hl)		; segmento
	inc hl
	ld e,(hl)
	inc hl
	ld d,(hl)
	inc hl
	push hl
	call map_on
	ld hl,0B000h
	ld c,0
	sla b			; B*512 bytes
	ldir
	call map_off
	pop hl
	jr .lp
noram:	ld hl,msg
.m:	ld a,(hl)
	or a
.h:	jr z,.h
	call 00A2h
	inc hl
	jr .m
msg:	db 12,"Uranai Sensation en castellano",13,10,13,10
	db "Lo siento: hacen falta 128 KB",13,10,"de RAM (MSX2 con mapper).",0
runs:	include "runs.inc"
	dw 0FFFFh

; ---------------------------------------------------------------------------
; Código residente: 8003h-81FFh
resimg:
	disp 8003h
res:
EXPF:	db 0
SAVA8:	db 0
SAVSUB:	db 0
SAVIFF:	db 0

; map_on: A = segmento. Pone RAM en la página 1 con ese segmento; interrupciones cortadas.
; Conserva BC, DE, HL.
map_on:	push bc
	push de
	ld b,a
	ld a,i
	di
	ld a,0
	jp po,.f
	inc a
.f:	ld (SAVIFF),a
	in a,(0A8h)
	ld (SAVA8),a
	ld c,a
	rrca
	rrca
	and 0Ch
	ld d,a
	ld a,c
	and 0F3h
	or d
	out (0A8h),a
	ld a,(EXPF)
	or a
	jr z,.ns
	ld a,(0FFFFh)
	cpl
	ld (SAVSUB),a
	ld c,a
	rrca
	rrca
	and 0Ch
	ld d,a
	ld a,c
	and 0F3h
	or d
	ld (0FFFFh),a
.ns:	ld a,b
	out (0FDh),a
	pop de
	pop bc
	ret

; map_off: deja la página 1 como estaba
map_off:
	ld a,2
	out (0FDh),a
	ld a,(EXPF)
	or a
	jr z,.ns
	ld a,(SAVSUB)
	ld (0FFFFh),a
.ns:	ld a,(SAVA8)
	out (0A8h),a
	ld a,(SAVIFF)
	or a
	ret z
	ei
	ret

; chk: si HL apunta a F0 nn nn, descomprime esa parte en BUF y deja HL = BUF.
; chku hace lo mismo en BUF2 (textos de la impresora de UI, que pueden convivir con los otros).
; Conservan BC y DE.
chk:	ld a,(hl)
	cp 0F0h
	ret nz
	push bc
	push de
	ld bc,BUF
	jr chkc
chku:	ld a,(hl)
	cp 0F0h
	ret nz
	push bc
	push de
	ld bc,BUF2
chkc:	ld (DST),bc
	inc hl
	ld e,(hl)
	inc hl
	ld d,(hl)
	ld a,4
	call map_on
	ld h,d
	ld l,e
	add hl,hl
	add hl,de
	ld de,PIDX
	add hl,de
	ld a,(hl)
	inc hl
	ld e,(hl)
	inc hl
	ld d,(hl)
	out (0FDh),a
	ex de,hl
	ld de,(DST)
.lp:	ld a,(hl)
	inc hl
	cp 0FFh
	jr z,.fin
	cp 0F0h
	jr z,.sig
	cp 0F3h
	jr z,.raw
	call emit
	jr .lp
.raw:	ldi			; F3 xx: byte tal cual (coordenadas de la UI)
	jr .lp
.sig:	ld (de),a		; F0 y número de la parte siguiente
	inc de
	ldi
	ldi
	jr .ok
.fin:	ld (de),a
.ok:	call map_off
	ld hl,(DST)
	pop de
	pop bc
	ret
DST:	dw 0

; uixy: lee [x][y] de la impresora de UI (8B4Eh) y mira si sigue un texto comprimido
uixy:	ld d,(hl)
	inc hl
	ld e,(hl)
	inc hl
	jr chku

; emit: escribe en (DE) el código A, deshaciendo fichas y marcas de género
emit:	cp TOK0
	jr c,.lit
	cp 0F0h
	jr nc,.ctl
	push hl
	sub TOK0
	ld l,a
	ld h,0
	add hl,hl
	ld bc,DICT
	add hl,bc
	ld a,(hl)
	inc hl
	push hl
	call emit
	pop hl
	ld a,(hl)
	call emit
	pop hl
	ret
.ctl:	cp 0F1h
	jr z,.go
	cp 0F2h
	jr z,.ga
.lit:	ld (de),a
	inc de
	ret
.go:	call SEXO		; {o}: o / a
	ld a,0Fh
	jr z,.lit
	ld a,01h
	jr .lit
.ga:	call SEXO		; {a}: nada / a
	ret z
	ld a,01h
	jr .lit

SEXO	equ 7FA0h		; sexo.asm, al final de cada segmento del mapper con texto

; vload: sustituye a la lectura de sectores (8908h). BC = sector, DE = destino, H = sectores
vload:	push hl
	push de
	ld a,4
	call map_on
	ld hl,(CTABP)
.lp:	ld e,(hl)
	inc hl
	ld d,(hl)
	inc hl
	ld a,d
	and e
	inc a
	jr z,.no
	ld a,e
	cp c
	jr nz,.nx
	ld a,d
	cp b
	jr z,.si
.nx:	ld de,6
	add hl,de
	jr .lp
.no:	call map_off
	pop de
	pop hl
	ld a,2Fh
	jp LOADRD
.si:	ld a,(hl)
	out (0FDh),a
	inc hl
	ld e,(hl)
	inc hl
	ld d,(hl)
	inc hl
	ld c,(hl)
	inc hl
	ld b,(hl)
	inc hl
	ld a,(hl)		; modo: 0 copia, 1 huecos de 32 bytes
	ex de,hl
	pop de
	push de
	or a
	jr nz,.hu
	ldir
	jr .ok
.hu:	push bc
	ld bc,4
	ldir
	ld b,28
	xor a
.z:	ld (de),a
	inc de
	djnz .z
	pop bc
	dec bc
	ld a,b
	or c
	jr nz,.hu
.ok:	call map_off
	pop de
	pop hl
	xor a
	ret

; avance de 6 píxeles para la fuente latina
adv6:	ld a,d
	add a,6
	ld d,a
	ret

	include "thunks.inc"

; omikuji: salto de línea (12 px más abajo, vuelta al margen)
omisalto:
	ld a,e
	add a,12
	ld e,a
	ld d,8Ah
	ret

; nlen: longitud del nombre (D218h, hasta 8 letras, FF = fin). A = longitud (mínimo 1), HL = D218h
nlen:	push bc
	ld hl,0D218h
	ld bc,0800h
.l:	ld a,(hl)
	inc a
	jr z,.f
	inc c
	inc hl
	djnz .l
.f:	ld a,c
	or a
	jr nz,.ok
	inc a
.ok:	ld hl,0D218h
	pop bc
	ret

; año de la ficha en VER DATOS (módulo 7Dh): BCD Showa -> dos últimas cifras del año (9E51h)
yr2:	ld a,(hl)
	push af
	add a,25h
	daa
	ld (hl),a
	call 9E5Dh
	dec hl
	pop af
	ld (hl),a
	inc hl
	ret

; nomafin: nombre de la ficha A en DE (x,y), color C; deja D tras el nombre y un espacio (módulo AAh, sangre)
nomafin:
	push bc
	push de
	call 98F7h		; HL = ficha
	pop de
	push de
	call 98AEh		; nombre, 6 px por letra
	pop hl			; H = x inicial, L = y
	pop bc
	ld a,d
	sub h
	ld b,a			; ancho del color
	ld a,l
	sub 8
	ld l,a
	push de
	ld e,c
	ld c,10h
	ld d,14
	call 0A003h
	pop de
	ld a,d
	add a,6
	ld d,a
	ret

resend:
	ent
	assert resend-res <= 01FDh
	assert $ <= 0B000h
; ---------------------------------------------------------------------------
; Rutinas del módulo de registro (6Fh, cargado en 9C00h), en los huecos de EE14h y EE91h (tras los stubs)
	output "m6f_a.bin"
	org 0AC1Ah
; cursor (sprite) del cuadro del nombre: 8 posiciones de 6 píxeles
curtab:
	dup 8, i
	db 42h, 10h+6*i, 0Ch, 08h
	edup

	output "m6f_b.bin"
	org 0AC97h
; anio: en el registro, el año (BCD de la era Showa) se escribe como 19xx (llamado desde A96Bh)
anio:	ld a,b
	cp 3
	jp nz,0A977h
	push hl
	push de
	ld hl,TMPY
	ld (hl),19h
	ld a,d
	sub 16
	ld d,a
	call 0A977h
	pop de
	pop hl
	ld a,(hl)
	add a,25h
	daa
	push hl
	ld hl,TMPY
	ld (hl),a
	call 0A977h
	pop hl
	ret
TMPY:	db 0

	output "m6f_c.bin"
	org 0AC66h		; hueco tras el stub de EE5Fh (en ACE5h está el menú del grupo sanguíneo)
; mar: en el mapa del lugar de nacimiento, sobre el mar se escribe «Mar» (eran dos letras, うみ);
; los tres dígitos se imprimen sumando 36h a cada byte (llamado desde AEF7h)
mar:	push hl
	ld (hl),27h-36h		; M
	inc hl
	ld (hl),01h-36h		; a
	inc hl
	ld (hl),12h-36h		; r
	pop hl
	ret
	assert $ <= 0AC89h


; ---------------------------------------------------------------------------
; Sangre (módulo AAh, en 9800h): «María y Rubén / ¿Sois compatibles?» en dos renglones,
; con la «y» y el segundo nombre detrás del primero
	output "maa.bin"
	org 9872h
	ld hl,9A39h
	call 8275h
	ld de,407Ah
	ld bc,(0DAF2h)
	push bc
	ld a,c
	ld c,2
	call nomafin
	ld a,19h		; y
	call 827Eh
	ld a,d
	add a,12
	ld d,a
	pop bc
	ld a,b
	ld c,9
	call nomafin
	call 8203h
	jp 984Fh
	assert $ <= 98AEh

; ---------------------------------------------------------------------------
; Horóscopo (módulo B8h, en 9800h): «Rubén: ascendente Capricornio» en lugar de «ああああの上昇宮は はくよう宮です»
; El nombre va en x=20h y lo demás detrás, a 6 píxeles por letra. Cuadro más ancho (987Dh y 988Bh, en build.py).
	output "mb8_a.bin"
	org 985Eh
	jp hasc
HSASC:	include "horo_a.inc"	; «: ascendente » FF
hcol:	pop af			; color del nombre (ancho en A)
	ld b,a
	ld hl,20A0h
	ld de,0E04h
	ld c,10h
	jp 9E48h
	assert $ <= 987Dh
	output "mb8_b.bin"
	org 9894h
hasc:	ex de,hl		; HL = ficha
	ld de,20A8h
	call 9C53h		; nombre, D = x tras el nombre
	ld a,d
	sub 20h
	push af			; ancho del color del nombre
	ld bc,00FFh		; C = FFh: la impresora hace AND C con cada código
	ld a,b
	ld (0D1CCh),a
	ld hl,HSASC
	call 8278h
	ld a,(9232h)		; signo: nombres seguidos, acabados en FF
	ld hl,HSIG
	or a
	jr z,.p
	ld b,a
.l:	ld a,(hl)
	inc hl
	inc a
	jr nz,.l
	djnz .l
.p:	ld c,0FFh
	call 8278h
	jp hcol
HSIG:	include "horo_b.inc"
	assert $ <= 9925h
