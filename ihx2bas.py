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

MODE_WAV_OLD = 0
MODE_WAV_NEW = 1
MODE_COMPACT_STD = 2
MODE_COMPACT_STUB = 3
MODE_BASIC_STD = 4
MODE_BASIC_STUB = 5

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
  sys.stderr.write("usage: ihx2bas [-compact] [-nostub] [-o basfile] [ihxfile]\n")
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

def dumpbasic(srcfile, outfile):
  global g_start
  cols   = 0
  sadr   = 0
  eadr   = 0 # the next unused adress
  chksum = 0

  outfile.write(str(g_start)+" REM ** IHXCONV **\n")
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
  outfile.write(str(g_start)+" A="+str(sadr)+":B="+str(eadr-sadr)+":C="+str(chksum)+":RETURN\n")
  return 0

def dumpcompact(srcfile, outfile):
  global g_start
  cols   = 0
  sadr   = 0
  eadr   = 0 # the next unused adress
  chksum = 0

  ch = getByte(srcfile)
  if (ch >= 0):
    sadr = g_addr-1
  while (ch >= 0):
    if (cols == 0):
      outfile.write(str(g_start)+' DATA "')
      g_start = g_start+g_inc
    chksum = chksum+ch
    outfile.write(hex(256+ch)[3:])
    cols = cols+1
    if (cols >= 32):
      outfile.write('"\n')
      cols = 0
    ch = getByte(srcfile)
  eadr = g_addr
  if (cols != 0):
    outfile.write('"\n')
  outfile.write(str(g_start)+" A="+str(sadr)+":B="+str(eadr-sadr)+":C="+str(chksum)+":RETURN\n")
  return 0

def dumpstub1(srcfile, outfile):
  global g_start
  outfile.write(str(g_start)+" REM ** IHXCONV **\n")
  g_start = g_start+g_inc
  tagadr  = g_start
  outfile.write(str(g_start)+' GOSUB "'+str(tagadr)+'":B=A+B-1:RESTORE "'+str(tagadr)+'"\n')
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" FOR I=A TO B:READ J:POKE I,J:NEXT I:END\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' "'+str(tagadr)+'" REM START OF DATA SECTION\n')
  g_start = g_start+g_inc
  return 0

def dumpstub2(srcfile, outfile):
  global g_start
  outfile.write(str(g_start)+" REM ** IHXCONV **\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" DIM BA$(0)*64:J=0\n")
  g_start = g_start+g_inc
  tagadr  = g_start
  outfile.write(str(g_start)+' GOSUB "'+str(tagadr)+'":B=A+B-1:RESTORE "'+str(tagadr)+'"\n')
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" FOR I=A TO B\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" IF J<=0 READ BA$(0):J=LEN BA$(0):K=1\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" L=ASC MID$(BA$(0),K,1)\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" IF L<58 LET L=L-48\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" IF L>96 LET L=L-87\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" POKE I,16*L:L=ASC MID$(BA$(0),K+1,1)\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" IF L<58 LET L=L-48\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" IF L>96 LET L=L-87\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+" POKE I,L+PEEK I:K=K+2:J=J-2:NEXT I:END\n")
  g_start = g_start+g_inc
  outfile.write(str(g_start)+' "'+str(tagadr)+'" REM START OF DATA SECTION\n')
  g_start = g_start+g_inc
  return 0

def ihxconv(srcfile, outfile, mode):
  if (mode == MODE_COMPACT_STUB):
    dumpstub2(srcfile, outfile)
    dumpcompact(srcfile, outfile)
  elif (mode == MODE_COMPACT_STD):
    dumpcompact(srcfile, outfile)
  elif(mode == MODE_BASIC_STUB):
    dumpstub1(srcfile, outfile)
    dumpbasic(srcfile, outfile)
  elif (mode == MODE_BASIC_STD):
    dumpbasic(srcfile, outfile)
  return 0

def main():
  init_global()
  args = sys.argv[1:]
  mode = MODE_BASIC_STUB
  basname = ""
  srcname = ""
  basfile = sys.stdout
  srcfile = sys.stdin 
  i = 0

  while i<len(args):
    arg = args[i]
    if (arg == "-compact"):
      if (mode == MODE_COMPACT_STD or mode == MODE_COMPACT_STUB):
        duplicate(arg)
      if (mode == MODE_BASIC_STUB):
        mode = MODE_COMPACT_STUB
      else:
        mode = MODE_COMPACT_STD
    elif (arg == "-nostub"):
      if (mode == MODE_BASIC_STD or mode == MODE_COMPACT_STD):
        duplicate(arg)
      if (mode == MODE_BASIC_STUB):
        mode = MODE_BASIC_STD
      else:
        mode = MODE_COMPACT_STD
    elif (arg == "-o"):
      if (basname):
        duplicate(arg)
      if (i+1 == len(args)):
        missing()
      i = i+1
      basname = args[i]
    elif (arg[0:1] == "-"):
      unknown(arg)
    else:
      if (srcname):
        dupfile(arg)
      srcname = arg
    i = i+1
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
  i = ihxconv(srcfile, basfile, mode) 
  if (basname):
    basfile.close()
  if (srcname):
    srcfile.close()
  exit(i)

main()

