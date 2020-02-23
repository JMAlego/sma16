# SMA16

## Introduction

SMA16 is a compact RISC-ish 16/12-bit architecture. SMA16 lends itself to simple VMs due to the small number of instructions and it's support for partial implementations of the instruction set. This does not, however, mean it is simple to write for as self modifying code is a requirement for any mildly complex program.

## Architecture

For architecture documentation, see [SMA16.md](./SMA16.md).

## Components

### sma16vm.c

`sma16vm.c` is a simple VM for the architecture.

#### Usage

```
make
./sma16vm program.bin
```

### sma16asm.py

`sma16asm.py` is a simple assembler for the architecture.

#### Usage


```
python3 sma16asm.py program.a16 --output program.bin
```

#### Example Assembly

```
.vec.reset @main
.vec.fault @RESET_VECTOR

.sec program

main:
  load @hi
  store @SMALL_OUT
  halt
  
.sec constant

hi: .const s"hi"
```
