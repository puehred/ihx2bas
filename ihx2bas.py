#! /usr/bin/python
"""
Intel Hex to Basic conversion for Sharp pocket computers
"""
__author__ = 'Edgar Puehringer'
__copyright__ = '2016, Edgar Puehringer'

#***************************************************************************
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License as published by  *
#*   the Free Software Foundation; either version 2 of the License, or     *
#*   (at your option) any later version.                                   *
#*                                                                         *
#***************************************************************************/

import sys, os

MODE_COMPACT_STD = 2
MODE_COMPACT_STUB = 3
MODE_BASIC_STD = 4
MODE_BASIC_STUB = 5
MODE_FAST_STD = 6  
MODE_FAST_STUB = 7  

BAS_START_1350 = 28417
BAS_START_1360 = 65495
BAS_START_2500 = 28049

def init_global():
  global g_addr
  g_addr = -1
  global g_start
  g_start = 10
  global g_inc
  g_inc = 10
  global g_len
  g_len = 0
  global g_pos
  g_pos = 0
  global line
  line = ""

def usage():
  sys.stderr.write("usage: ihx2bas [-compact|fast] [-nostub] [-o basfile] [-p basptr] [ihxfile]\n")
  exit(-1)

def duplicate(param):
  sys.stderr.write("duplicate parameter '")
  sys.stderr.write(param)
  sys.stderr.write("'\n")
  usage()

def unknown(param):
  sys.stderr.write("unknown parameter '")
  sys.stderr.write(param)
  sys.stderr.write("'\n")
  usage()

def missing():
  sys.stderr.write("missing file name for basic file\n")
  usage()

def dupfile(param):
  sys.stderr.write("duplicate input file '")
  sys.stderr.write(param)
  sys.stderr.write("'\n")
  usage()

def cantcombine(pram):
  sys.stderr.write("can't combine -compact and -fast\n")
  usage()

def needsbasptr():
  sys.stderr.write("parameter -fast can't be used without parameter -p (loc. of BASIC start ptr)\n")
  usage()
  
def getByte(f):
  global g_addr
  global g_len
  global g_pos
  global line
  while (g_pos >= g_len):
    line = f.readline()
    if (not line):
      return -1
    if (line[0] != ':'):
      continue
    if (len(line) < 11):
      sys.stderr.write("Line to short: "+line+"\n")
      return -1
    g_len = 16*int(line[1], 16)+int(line[2], 16)
    if (len(line) < 2*g_len+11):
      g_len = 0
      sys.stderr.write("Line size doesn't match: "+line+"\n")
      return -1
    if (g_len == 0):
      continue
    addr = 16*16*16*int(line[3], 16)+16*16*int(line[4], 16)+16*int(line[5], 16)+int(line[6], 16)
    if (g_addr < 0):
      g_addr = addr
    if (addr != g_addr):
      g_len = 0
      print("addr =", hex(addr))
      sys.stderr.write("Address gap detected (should be "+hex(g_addr)+"): "+line+"\n")
      return -1
    g_pos = 0

  ch = 16*int(line[2*g_pos+9], 16)+int(line[2*g_pos+10], 16)
  g_pos = g_pos+1
  g_addr = g_addr+1
  
  return ch

def dumpbasic(srcfile, outfile, srcname, basptr):
  global g_start
  cols   = 0
  sadr   = 0
  eadr   = 0 # the next unused adress
  chksum = 0

  outfile.write(str(g_start)+'"D" REM ** IHXCONV STD **\n')
  g_start = g_start+g_inc
  ch      = getByte(srcfile)
  if (ch >= 0):
    sadr = g_addr-1
  while (ch >= 0):
    if (cols == 0):
      outfile.write(str(g_start)+" DATA ")
      g_start = g_start+g_inc
    else:
      outfile.write(",")
    chksum = chksum+ch
    outfile.write(str(ch))
    cols = cols+1
    if (cols >= 17):
      outfile.write("\n")
      cols = 0
    ch = getByte(srcfile)
  eadr = g_addr
  if (cols != 0):
    outfile.write("\n")
  outfile.write(str(g_start)+" A="+str(sadr)+":B="+str(eadr-sadr)+":C="+str(chksum))
  outfile.write(':S$="'+srcname+'"')
  if (basptr > 0):
    outfile.write(":D="+str(basptr))
  outfile.write("\n")
  g_start = g_start+g_inc
  return 0

def dumpcompact(srcfile, outfile, srcname, basptr):
  global g_start
  cols   = 0
  sadr   = 0
  eadr   = 0 # the next unused adress
  chksum = 0

# Warning: The following REM line is designed to have the same length as a DATA line, so don't change it
  if (basptr == BAS_START_1360):
    outfile.write(str(g_start)+'"D" REM ** IHXCONV COMPACT ********************************************\n')
  else:
    outfile.write(str(g_start)+'"D" REM ** IHXCONV COMPACT *******************************************\n')
  g_start = g_start+g_inc
  ch = getByte(srcfile)
  if (ch >= 0):
    sadr = g_addr-1
  while (ch >= 0):
    if (cols == 0):
      outfile.write(str(g_start)+' DATA "')
      g_start = g_start+g_inc
    chksum = chksum+ch
    outfile.write(str.upper(hex(256+ch)[3:]))
    cols = cols+1
    if (cols >= 32):
      outfile.write('"\n')
      cols = 0
    ch = getByte(srcfile)
  eadr = g_addr
  if (cols != 0):
    outfile.write('"\n')
  outfile.write(str(g_start)+" CLEAR:A="+str(sadr)+":B="+str(eadr-sadr)+":C="+str(chksum))
  outfile.write(':S$="'+srcname+'"')
  if (basptr > 0):
    outfile.write(":D="+str(basptr))
  outfile.write("\n")
  g_start = g_start+g_inc
  return 0

def dumpstub1(srcfile, outfile):
  global g_start
  outfile.write(str(g_start)+" REM ** IHXCONV STD **\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' B=A+B-1:E=0:RESTORE "D":WAIT 15:PRINT "LOADING ";S$\n')
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" FOR I=A TO B:READ J:POKE I,J:E=E+J:NEXT I\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' IF C<>E BEEP 3:PRINT "CHECKSUM ERROR":END\n')
  g_start = g_start+g_inc
  return 0

def dumpstub2(srcfile, outfile, basptr):
  global g_start
  outfile.write(str(g_start)+" REM ** IHXCONV COMPACT **\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" DIM BA$(0)*64:J=0\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' RESTORE "D":WAIT 15\n')
  g_start = g_start+g_inc
  if (basptr == BAS_START_1350 or basptr == BAS_START_1360 or basptr == BAS_START_2500):
# Q = pointer to start of executive text
    if (basptr == BAS_START_1360):
      outfile.write(str(g_start)+' E=D-&E7:Q=PEEK E+256*PEEK(E+1):PRINT "MOVE EXEC PTR"\n')
      g_start = g_start+g_inc
      outfile.write(str(g_start)+' Q=Q+72+72*INT (B/72):IF 13<>PEEK Q THEN PRINT "BAD POINTER":END\n')
    else:
      outfile.write(str(g_start)+' E=D+&1B:Q=PEEK E+256*PEEK(E+1):PRINT "MOVE EXEC PTR"\n')
      g_start = g_start+g_inc
      outfile.write(str(g_start)+' Q=Q+71+71*INT (B/71):IF 13<>PEEK Q THEN PRINT "BAD POINTER":END\n')
    g_start = g_start+g_inc
# Move pointers to get out of the region with written data
    outfile.write(str(g_start)+" POKE E,(Q-256* INT (Q/256)):POKE E+1,INT (Q/256)\n")
    g_start = g_start+g_inc
  outfile.write(str(g_start)+' B=A+B-1:PRINT "LOADING ";S$\n')
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" FOR I=A TO B\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" IF J<=0 READ BA$(0):J=LEN BA$(0):K=1\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" L=ASC MID$(BA$(0),K,1)\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" IF L<58 LET L=L-48\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" IF L>64 LET L=L-55\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" POKE I,16*L:L=ASC MID$(BA$(0),K+1,1)\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" IF L<58 LET L=L-48\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" IF L>64 LET L=L-55\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" POKE I,L+PEEK I:K=K+2:J=J-2:NEXT I\n")
  g_start = g_start+g_inc
#  outfile.write(str(g_start)+' "'+str(tagadr)+'" REM START OF DATA SECTION\n')
#  g_start = g_start+g_inc
  return 0

def dumpstub3(srcfile, outfile, basptr):
# ML loader will be stored in BASIC arrays. Check
# "System- und Trickbuch fuer den SHARP PC 1350", ISBN 3-924986-08-8
# for details on memory allocation for BASIC arrays
  global g_start
  outfile.write(str(g_start)+" REM ** IHXCONV FAST **\n")
  g_start = g_start+g_inc
#  tagadr  = g_start
  outfile.write(str(g_start)+' E=A:F=B:G=C:T$=S$:RESTORE "P":WAIT 15:PRINT "INITIALIZING ..."\n')
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' GOSUB "P":DIM P$(1)*50:C=D+6\n')
  g_start = g_start+g_inc
# P = pointer to start of data area
  outfile.write(str(g_start)+" P=7+PEEK C+256*PEEK(C+1):B=P+B-1\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' FOR I=P TO B:READ J:POKE I,J:NEXT I:DIM B$(0)*64\n')
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" A=7+PEEK C+256*PEEK(C+1)\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" POKE P+2,(A-256* INT (A/256)): POKE P+6, INT (A/256)\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' A=E:B=F:C=G:S$=T$:RESTORE "D"\n')
  g_start = g_start+g_inc
  if (basptr == BAS_START_1350 or basptr == BAS_START_1360 or basptr == BAS_START_2500):
# Q = pointer to start of executive text
    if (basptr == BAS_START_1360):
      outfile.write(str(g_start)+' E=D-&E7:Q=PEEK E+256*PEEK(E+1):PRINT "MOVE EXEC PTR":H=32+32*INT ((B-1)/32)\n')
      g_start = g_start+g_inc
# H = memory consumption of programm adjusted to 32 byte blocks - 2 extra bytes for checksum 
      outfile.write(str(g_start)+' Q=Q+72+72*INT ((H+2)/72):IF 13<>PEEK Q THEN PRINT "BAD POINTER":END\n')
    else:
      outfile.write(str(g_start)+' E=D+&1B:Q=PEEK E+256*PEEK(E+1):PRINT "MOVE EXEC PTR":H=32+32*INT ((B-1)/32)\n')
      g_start = g_start+g_inc
# H = memory consumption of programm adjusted to 32 byte blocks - 2 extra bytes for checksum 
      outfile.write(str(g_start)+' Q=Q+71+71*INT ((H+2)/71):IF 13<>PEEK Q THEN PRINT "BAD POINTER":END\n')
    g_start = g_start+g_inc
# Move pointers to get out of the region with written data
    outfile.write(str(g_start)+" POKE E,(Q-256* INT (Q/256)):POKE E+1,INT (Q/256)\n")
    g_start = g_start+g_inc
  outfile.write(str(g_start)+' B=A+B-1:PRINT "LOADING ";S$:H=0\n')
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" FOR I=A TO B STEP 32:READ B$(0)\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" POKE P+10,(I-256* INT (I/256)): POKE P+14, INT (I/256)\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' CALL P:H=H+PEEK(I+32)+256*PEEK(I+33):NEXT I:IF H=C GOTO "E"\n')
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' BEEP 3:PRINT "CHECKSUM ERROR":END\n')
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' "P" REM ASSEMBLED FROM HEXCONV.ASM\n')
  g_start = g_start+g_inc
# Paste *.bas file assembled from hexconv.asm here and modify it to use g_start as line number
  outfile.write(str(g_start)+" DATA 132,2,49,219,133,2,108,219,134,2,64,219,135,2,105,219,5\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" DATA 7,0,255,136,96,0,137,96,0,2,31,52,131,3,0,2,1\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" DATA 52,219,88,219,36,103,0,40,3,0,0,103,97,58,4,117,87\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" DATA 71,103,65,58,4,117,55,71,103,48,58,4,117,48,71,47,32\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" DATA 219,128,219,70,219,38,87,136,68,42,2,200,47,52,219,38,137\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" DATA 219,38,55\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' A=26874:B=88:C=7229:S$=""\n')
  g_start = g_start+g_inc
# END pasted section
  outfile.write(str(g_start)+" RETURN\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' "E" REM END\n')
  return 0

def ihxconv(srcfile, outfile, mode, srcname, basptr):
  if (mode == MODE_COMPACT_STUB):
    dumpcompact(srcfile, outfile, srcname, basptr)
    dumpstub2(srcfile, outfile, basptr)
  elif (mode == MODE_COMPACT_STD or mode == MODE_FAST_STD):
    dumpcompact(srcfile, outfile, srcname, basptr)
  elif (mode == MODE_FAST_STUB):
    dumpcompact(srcfile, outfile, srcname, basptr)
    dumpstub3(srcfile, outfile, basptr)
  elif(mode == MODE_BASIC_STUB):
    dumpbasic(srcfile, outfile, srcname, basptr)
    dumpstub1(srcfile, outfile)
  elif (mode == MODE_BASIC_STD):
    dumpbasic(srcfile, outfile, srcname, basptr)
  return 0

def main():
  init_global()
  args = sys.argv[1:]
  mode = MODE_BASIC_STUB
  basname = ""
  srcname = ""
  basfile = sys.stdout
  srcfile = sys.stdin
  proglbl = ""
  basptr = 0
  i = 0

  while i<len(args):
    arg = args[i]
    if (arg == "-compact"):
      if (mode == MODE_COMPACT_STD or mode == MODE_COMPACT_STUB):
        duplicate(arg)
      if (mode == MODE_FAST_STD or mode == MODE_FAST_STUB):
        cantcombine(arg)
      if (mode == MODE_BASIC_STUB):
        mode = MODE_COMPACT_STUB
      else:
        mode = MODE_COMPACT_STD
    elif (arg == "-fast"):
      if (mode == MODE_FAST_STD or mode == MODE_FAST_STUB):
        duplicate(arg)
      if (mode == MODE_COMPACT_STD or mode == MODE_COMPACT_STUB):
        cantcombine(arg)
      if (mode == MODE_BASIC_STUB):
        mode = MODE_FAST_STUB
      else:
        mode = MODE_FAST_STD
    elif (arg == "-nostub"):
      if (mode == MODE_BASIC_STD or mode == MODE_COMPACT_STD or mode == MODE_FAST_STD):
        duplicate(arg)
      if (mode == MODE_BASIC_STUB):
        mode = MODE_BASIC_STD
      elif (mode == MODE_FAST_STUB):
        mode = MODE_FAST_STD
      else:
        mode = MODE_COMPACT_STD
    elif (arg == "-o"):
      if (basname):
        duplicate(arg)
      if (i+1 == len(args)):
        missing()
      i = i+1
      basname = args[i]
    elif (arg == "-p"):
      if (basptr):
        duplicate(arg)
      if (i+1 == len(args)):
        missing()
      i = i+1
      basptr = int(args[i])
    elif (arg[0:1] == "-"):
      unknown(arg)
    else:
      if (srcname):
        dupfile(arg)
      srcname = arg
    i = i+1
  if ((mode == MODE_FAST_STD or mode == MODE_FAST_STUB) and not basptr):
    needsbasptr()
  if (basname):
    try:
      basfile = open(basname, 'w')
    except IOError as ioex:
      sys.stderr.write(basname)
      sys.stderr.write(": ")
      sys.stderr.write(os.strerror(ioex.errno))
      sys.stderr.write("\n")
      exit(-2)
  if (srcname):
    try:
      srcfile = open(srcname, 'r')
    except IOError as ioex:
      sys.stderr.write(srcname)
      sys.stderr.write(": ")
      sys.stderr.write(os.strerror(ioex.errno))
      sys.stderr.write("\n")
      if (basname):
        basfile.close()
      exit(-3)
  if (basname):
    proglbl = str.upper(basname.split(".")[0][:7])
  i = ihxconv(srcfile, basfile, mode, proglbl, basptr) 
  if (basname):
    basfile.close()
  if (srcname):
    srcfile.close()
  exit(i)

main()

