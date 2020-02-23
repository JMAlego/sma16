# SMA16 Architecture Document

## Introduction

### Overview

The SMA16 architecture is a simple somewhat minimal RISC-ish architecture. It is simple enough to implement a virtual machine for quickly, and has minimal instructions to comprehend. This has its trade-offs as the minimal-ish nature makes self-modifying code almost a necessity to create more complex programs (if fact, it is required for Turing completeness).

### Shorthand

Throughout this document the following shorthand will be used to refer to components of the architecture.

- Values starting with `0x` are encoded in hexadecimal (base 16).
- Values starting with `0b` are encoded in binary (base 2).
- `$X` will refer to the register `X` which may be memory mapped.
- `@X` will refer to named address `X`
- `X<Y>` will refer to bit `Y` of `X`.
  - `X<Y:>` will refer to all bits of `X` starting with `Y` inclusive.
  - `X<:Y>` will refer to all bits of `X` ending with `Y` inclusive.
  - `X<Y:Z>` will refer to all bits of `X` between `Y` and `Z` inclusive, where `Y` less than or equal to `Z`.
- `X[Y]` will refer to index  `Y` of `X` by word (16 bits).
- `X.DATA` will refer to bits 0 to 11 (inclusive) of `X`.
- `X.INST` will refer to bits 12 to 15 (inclusive) of `X`.
- `$IR` will refer to the instruction register.
- `$SR` will refer to the status register.
  - `$SR<H>` will refer to the halt flag bit of the status register.
  - `$SR<Z>` will refer to the zero flag bit of the status register.
- `STACK` will refer to the hardware stack.
- `MEMORY` will refer to the main memory.

### Concepts

#### Word Segments

Each 16-bit word is typically split into two separate segments, the 12-bit `DATA` segment and the 4-bit `INST` segment. The `DATA` segment takes up the lower 12-bits of a word, and the `INST` segment takes up the other upper 4-bits. Some registers or memory will store both the `INST` segment and `DATA` segment, whereas others may only store the `DATA` or `INST` segment. Similarly, some instructions will act on just the `DATA` segment, whereas others will act on the whole word.

#### RISC

The SMA16 architecture is widely a RISC (Reduced Instruction Set Computer), this translates to it having a small number of instructions, preferring to chain them to implement features rather than implementing them in "complex" instructions.

#### Minimal

The SMA16 aims to be widely minimal, while it is not truly minimal (a minimal machine would not have both a `AND` and an `XOR` instruction) it aims to be *use-ably* minimal, including certain quality-of-life instructions while staying small and simple. 

## System Registers

### Non-Memory-Mapped

| Name                 | Shorthand | Width  | Description                                                  |
| -------------------- | --------- | ------ | ------------------------------------------------------------ |
| Program Counter      | `$PC`     | 12-bit | The current program counter points to the memory location to next be loaded into the instruction register. |
| Instruction Register | `$IR`     | 16-bit | The instruction register contains the currently executing instruction and the data stored with it (which may be unrelated to the instruction). |
| Accumulator          | `$ACC`    | 16-bit | The accumulator is the only general purpose register.        |
| Status Register      | `$SR`     | 2-bit  | The status register contains the bit flags halt and zero.    |

### Memory-Mapped

| Name                      | Shorthand           | Address | Width  | Description                                                  |
| ------------------------- | ------------------- | ------- | ------ | ------------------------------------------------------------ |
| Interrupt Reason Register | `$INTERRUPT_REASON` | `0x008` | 16-bit | The interrupt reason register contains the reason for the last interrupt. |
| Interrupt Return Register | `$INTERRUPT_RETURN` | `0x009` | 12-bit | The interrupt return register stores the program counter at the point the last interrupt occurred plus one. |
| Stack Size Register       | `$STACK_SIZE`       | `0x00D` | 16-bit | The stack size register is set to the hardware stack size on startup. This register can be overwritten after startup, typically by a software stack replacement to indicate its maximum size. Stack sizes of greater than `0xffff` are technically possible, therefore `0xffff` represents equal to or greater than `0xffff` stack size. |
| Reserved                  |                     | `0x00E` |        |                                                              |
| Reserved                  |                     | `0x00F` |        |                                                              |

## Interrupt Vectors

| Name            | Shorthand          | Address         | Maximum Instructions | Description                                                  |
| --------------- | ------------------ | --------------- | -------------------- | ------------------------------------------------------------ |
| Reset Vector    | `@RESET_VECTOR`    | `0x000`         | 1                    | Location which is `JUMP`ed to when a reset or initial startup occurs. |
| Fault Vector    | `@FAULT_VECTOR`    | `0x001`         | 1                    | Location which is `JUMP`ed to when a fault occurs.           |
| Software Vector | `@SOFTWARE_VECTOR` | `0x002`-`0x007` | 6                    | Location which is `JUMP`ed to for software interrupts. `@INTERRUPT_REASON` describes why the software interrupt occurred. |

## Memory-Mapped Components

### Console Output

| Name                            | Shorthand          | Address | Width  | Description                                                  |
| ------------------------------- | ------------------ | ------- | ------ | ------------------------------------------------------------ |
| Terminal Configuration Register | `$TERMINAL_CONFIG` | `0x00C` | 16-bit | The terminal configuration register stores the configuration for the on-board serial output. |
| Console Output, ASCII           | `@ASCII_OUT`       | `0x00A` | 8-bit  | This memory address will output the ASCII character written to it to the system's primary console output (if any). **NB**: NULL *is* sent. |
| Console Output, SMALL           | `@SMALL_OUT`       | `0x00B` | 12-bit | This memory address will output the SMALL (for SMALL encoding see [Appendix A](#appendix-a---small-encoding)) character written to it to the system's primary console output (if any). **NB**: NULL is *not* sent, characters which are NULL are omitted. |

## Stack

The SMA16 typically has a hardware stack. The hardware stack must be at least 16 items deep if implemented in hardware, and can be any size if implemented in software (see below). The stack is optional and may not be implemented, though this is considered unusual. The stack stores 16-bit words and can only be interacted with via `POP` and `PUSH`.

If the stack is not-implemented, then using `POP` or `PUSH` will cause a fault as described in the [Instruction Set](#instruction-set) section below. This can be used to implement a fall back software stack, if required.

The `$STACK_SIZE` register is set to the maximum stack depth available on startup. If no stack is available it will be set to `0x0000`. If a software implementation exists, it should set `$STACK_SIZE`   to the software implementation's maximum depth, after startup.

## Initial Conditions

On startup the following registers will contain the following values:

| Registers | Value   |
| --------- | ------- |
| `$PC`     | `0x000` |
| `$SR`     | `0b00`  |

All other registers may contain any value, though will usually contain `0x0000`.

## Instruction Set

### Instruction Format

All instructions fall under two categories and have the same format. All instructions are 16-bits long with a 4-bit `INST` segment (opcode) and a 12-bit `DATA` segment (operand). However, the `DATA` may not be used by the instruction, such as in the case of `POP` and `PUSH`. This means that data unrelated to the instruction may be stored with it to save memory.

### Instruction Set Table

All instructions, unless otherwise noted, increment the program counter by 1.

| Opcode | Name       | Description                                                  |
| ------ | ---------- | ------------------------------------------------------------ |
| `0x0`  | `HALT`     | Halts the CPU by setting `$SR<H>` to `0b1`.                  |
| `0x1`  | Reserved 1 | Undefined. Some implementations may cause a fault, in which case they must cause the CPU to store the `$PC` plus 1 in the `$INTERRUPT_RETURN` register, jump to `@FAULT_VECTOR`, and set the `$INTERRUPT_REASON` register to `0x0ff1`. |
| `0x2`  | `JUMP`     | Set `$PC` to `$IR.DATA`. Does *not* increment program counter post instruction. |
| `0x3`  | `JUMPZ`    | Set `$PC` to `$IR.DATA` if `$SR<Z>` is `0b1`, else increment `$PC` as normal. Does *not* increment program counter post instruction. |
| `0x4`  | `LOAD`     | Set `$ACC` to `MEMORY[$IR.DATA]`.                            |
| `0x5`  | `STORE`    | Set `MEMORY[$IR.DATA].DATA` to `$ACC.DATA`.                  |
| `0x6`  | `LSHFT`    | If `$IR.DATA<0> ` is `0b1` then shift `$ACC.DATA` left by `$IR.DATA<1:> `, else shift `$ACC` left by `$IR.DATA<1:> `. |
| `0x7`  | `RSHFT`    | If `$IR.DATA<0> ` is `0b1` then shift `$ACC.DATA` right by `$IR.DATA<1:> `, else shift `$ACC` right by `$IR.DATA<1:> `. |
| `0x8`  | `XOR`      | Set `$ACC.DATA` to `$ACC.DATA` bit-wise exclusive-or with `$IR.DATA`. |
| `0x9`  | `AND`      | Set `$ACC.DATA` to `$ACC.DATA` bit-wise and with `$IR.DATA`. |
| `0xA`  | `SFULL`    | Set `MEMORY[$IR.DATA]` to `$ACC`.                            |
| `0xB`  | `ADD`      | Set `$ACC` to `$ACC` arithmetic add `$IR.DATA`, then set `$SR<Z>` to `0b1` if `$ACC.DATA` is now zero and `0b0` if it is not zero. |
| `0xC`  | Reserved 2 | Undefined. Some implementations may cause a fault, in which case they must cause the CPU to store the `$PC` plus 1 in the `$INTERRUPT_RETURN` register, jump to `@FAULT_VECTOR`, and set the `$INTERRUPT_REASON` register to `0x0ffC`. |
| `0xD`  | `POP`      | Pop an item off the `STACK` and set `$ACC` to the popped value. |
| `0xE`  | `PUSH`     | Push the value of `$ACC` onto the `STACK`.                   |
| `0xF`  | `NOOP`     | No operation.                                                |

### Unimplemented Instructions

If an instruction is not implemented then implementations must cause a fault and store the `$PC` in the `$INTERRUPT_RETURN` register, jump to `@FAULT_VECTOR`, and set the `$INTERRUPT_REASON` register to `0x0ffX` where `X` is the opcode of the instruction which is not implemented. This mirrors the behaviour of undefined instructions, however, it is required unlike for undefined instructions for which it is simply optional.

The only instructions which are which may make sense to omitted are the `POP` and `PUSH` instructions, as their functionality can be replicated in software, albeit at the cost of quite a sizeable number of instruction cycles.

## Appendices

### Appendix A - SMALL Encoding

The SMALL encoding is a 6-bit character encoding designed to pack two characters into a 12-bit space. This is useful as it means that two characters can be output in a single `STORE` instruction. It also allows for two characters to be stored in the data segment of a memory address, allowing for efficient storage next to instructions which don't use their data segment.

| Character | Encoding (Decimal) |
| --------- | ------------------ |
| A         | 0                  |
| B         | 1                  |
| C         | 2                  |
| D         | 3                  |
| E         | 4                  |
| F         | 5                  |
| G         | 6                  |
| H         | 7                  |
| I         | 8                  |
| J         | 9                  |
| K         | 10                 |
| L         | 11                 |
| M         | 12                 |
| N         | 13                 |
| O         | 14                 |
| P         | 15                 |
| Q         | 16                 |
| R         | 17                 |
| S         | 18                 |
| T         | 19                 |
| U         | 20                 |
| V         | 21                 |
| W         | 22                 |
| X         | 23                 |
| Y         | 24                 |
| Z         | 25                 |
| a         | 26                 |
| b         | 27                 |
| c         | 28                 |
| d         | 29                 |
| e         | 30                 |
| f         | 31                 |
| g         | 32                 |
| h         | 33                 |
| i         | 34                 |
| j         | 35                 |
| k         | 36                 |
| l         | 37                 |
| m         | 38                 |
| n         | 39                 |
| o         | 40                 |
| p         | 41                 |
| q         | 42                 |
| r         | 43                 |
| s         | 44                 |
| t         | 45                 |
| u         | 46                 |
| v         | 47                 |
| w         | 48                 |
| x         | 49                 |
| y         | 50                 |
| z         | 51                 |
| 0         | 52                 |
| 1         | 53                 |
| 2         | 54                 |
| 3         | 55                 |
| 4         | 56                 |
| 5         | 57                 |
| 6         | 58                 |
| 7         | 59                 |
| 8         | 60                 |
| 9         | 61                 |
| SPACE     | 62                 |
| NULL      | 63                 |

