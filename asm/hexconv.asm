
	;; Build it with
	;;   as61860 -los hexconv.asm 
	;; and
	;;   aslink -imwu hexconv.ihx hexconv.rel
	;;
	;; Use this assembler: http://shop-pdp.net/ashtml/asxxxx.htm
	;;
	;; Convert the resulting *.ihx file to a BASIC listing using
	;;   ihx2bas.py -nostub hexconv.ihx
	;; and paste the result into ihx2bas.py at alocation, where
	;; the comments tell you to do so 

	;;***************************************************************************
	;;*                                                                         *
	;;*   This program is free software; you can redistribute it and/or modify  *
	;;*   it under the terms of the GNU General Public License as published by  *
	;;*   the Free Software Foundation; either version 2 of the License, or     *
	;;*   (at your option) any later version.                                   *
	;;*                                                                         *
	;;***************************************************************************

.area hexconv (REL)

; CPU registers

REG_I	=    0x00               ; index register
REG_J	=    0x01               ; index register
REG_A	=    0x02               ; accumulator
REG_B	=    0x03               ; accumulator
REG_XL	=    0x04               ; LSB of adress pointer
REG_XH	=    0x05               ; MSB of adress pointer
REG_YL	=    0x06               ; LSB of adress pointer
REG_YH	=    0x07               ; MSB of adress pointer
REG_K	=    0x08               ; counter
REG_L	=    0x09               ; counter
REG_M	=    0x0A               ; counter
REG_N	=    0x0B               ; counter

;.org 0x0000
.org 0x68fa
	LP REG_XL
	LIA  0x31					; POKE low byte of variable BA$ here (start of text)
	EXAM
	LP REG_XH
	LIA 0x6c					; POKE high byte of variable BA$ here (start of text)
	EXAM
	LP REG_YL
	LIA 0x40					; POKE low byte of target address here
	EXAM
	LP REG_YH
	LIA 0x69					; POKE high byte of target address here
	EXAM
	DX
	DY
	LII 0xff					; Output mask
	LP REG_K
	ANIM 0
	LP REG_L
	ANIM 0						; LK = 0 (checksum)
	LIA 31
	PUSH						; Loop 32 times
loop32:
	LP REG_B
	LIB 0
	LIA 1
	PUSH						; Loop 2 times
loop2:
	EXAM
	SWP							; Xchange low and high nibble of B
	EXAM
	IXL
	CPIA 0
	JRNZP skpterm
;	POP							; Remove loop counters
;	POP							;  from stack
;	RTN							;  and return
	LII 0						; Set output mask to 0
skpterm:
	CPIA 'a						; Compare with 'a'
	JRCP skpa
	SBIA 'a-0x0a
	ORMA
skpa:
	CPIA 'A						; Compare with 'A'
	JRCP skpA
	SBIA 'A-0x0a
	ORMA
skpA:
	CPIA '0						; Compare with '0'
	JRCP skp0
	SBIA '0
	ORMA
skp0:
	LOOP loop2
	EXAM
	LP REG_I
	EXAM
	ANMA						; After the first zero-byte, set all bytes to zero
	EXAM
	IYS
	LDD							; Read it back to detect RAM errors
	LP REG_K
	ADM							; Add to checksum
	JRNCP noovl
	INCL
noovl:
	LOOP loop32
	EXAM						; Append checksum - P still points to reg. K
	IYS
	LP REG_L
	EXAM
	IYS 
	RTN

