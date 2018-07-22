#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provides classes and data associated with the base instructions of the SMA16."""

from enum import Enum


class BaseInstructionType(Enum):
    """Base Instruction Type Enum.

    Values:
      DEFINED: Instruction definition represents a defined instruction
      UNDEFINED: Instruction definition does not represent a defined instruction
    """
    DEFINED = True
    UNDEFINED = False


class BaseInstructionDataType(Enum):
    """Base Instruction Data Type Enum.

    Values:
      IMMEDIATE: Data is used by instruction in an immediate way
      INDIRECT: Data is used by instruction in an indirect way
      DATA: Data is not used by instruction so other data can be stored
      UNDEFINED: Data may or may not be used IE don't put data here
    """
    IMMEDIATE = 1
    INDIRECT = 2
    DATA = 3
    UNDEFINED = 4


class BaseInstructionDefinition:
    """Base Instruction Definition.

    Defines a type of instruction supported directly by SMA16.
    """

    def __init__(self, name: str, opcode: int, inst_type: BaseInstructionType,
                 data_type: BaseInstructionDataType) -> None:
        """Initialise the instruction definition."""
        self.name = name
        self.data_type = data_type
        self.opcode = opcode
        self.inst_type = inst_type


class BaseInstructionInstance:
    """Base Instruction Instance.

    Defines an instance of an instruction IE the definition of the instruction
    and the data stored with that instruction.
    """

    def __init__(self,
                 inst_definition: BaseInstructionDefinition,
                 data: int = None):
        """Initialise the instruction."""
        data_defined = True
        if data is None:
            data_defined = False
            data = 0
        if data >= 2**12 or data < 0:
            raise ValueError("Data outside of valid range of 0 to 2**12-1")
        self.definition = inst_definition
        self.data = data
        self.data_defined = data_defined

    def get_base_assembly_line(self) -> str:
        """Get the SMA16 assembly representation of the instruction."""
        return "{name} {data}".format(
            name=self.definition.name,
            data=hex(self.data) if self.data_defined else "???")

    def get_bytecode(self) -> int:
        """Get the bytecode representation of the instruction."""
        return (self.definition.opcode << 12) + self.data

    def has_data(self) -> bool:
        """Check if the instruction has defined data."""
        return self.data_defined

    def set_data(self, data: int) -> None:
        """Sets instruction data."""
        if data >= 2**12 or data < 0:
            raise ValueError("Data outside of valid range of 0 to 2**12-1")
        self.data = data
        self.data_defined = True

    def get_data(self) -> int:
        """Get instruction data."""
        return self.data

    def clear_data(self):
        """Clear instruction data."""
        self.data = 0
        self.data_defined = False

    def get_instruction_name(self) -> str:
        """Get instruction name."""
        return self.definition.name

    def is_defined(self) -> bool:
        """Check if instruction represents a defined instruction."""
        return self.definition.inst_type == BaseInstructionType.DEFINED

    def instruction_uses_data_slot(self) -> bool:
        """Check if the instruction uses the associated data slot."""
        return self.definition.data_type != BaseInstructionDataType.DATA


BASE_INSTRUCTION_HALT = BaseInstructionDefinition(
    "HALT", 0x0, BaseInstructionType.DEFINED, BaseInstructionDataType.DATA),
BASE_INSTRUCTION_UNDEF = BaseInstructionDefinition(
    "FREE", 0x1, BaseInstructionType.UNDEFINED,
    BaseInstructionDataType.UNDEFINED),
BASE_INSTRUCTION_JUMP = BaseInstructionDefinition(
    "JUMP", 0x2, BaseInstructionType.DEFINED, BaseInstructionDataType.DATA),
BASE_INSTRUCTION_JUMPZ = BaseInstructionDefinition(
    "JUMPZ", 0x3, BaseInstructionType.DEFINED,
    BaseInstructionDataType.IMMEDIATE),
BASE_INSTRUCTION_LOAD = BaseInstructionDefinition(
    "LOAD", 0x4, BaseInstructionType.DEFINED,
    BaseInstructionDataType.INDIRECT),
BASE_INSTRUCTION_STORE = BaseInstructionDefinition(
    "STORE", 0x5, BaseInstructionType.DEFINED,
    BaseInstructionDataType.INDIRECT),
BASE_INSTRUCTION_LSHIFT = BaseInstructionDefinition(
    "LSHIFT", 0x6, BaseInstructionType.DEFINED,
    BaseInstructionDataType.IMMEDIATE),
BASE_INSTRUCTION_RSHIFT = BaseInstructionDefinition(
    "RSHIFT", 0x7, BaseInstructionType.DEFINED,
    BaseInstructionDataType.IMMEDIATE),
BASE_INSTRUCTION_XOR = BaseInstructionDefinition(
    "XOR", 0x8, BaseInstructionType.DEFINED,
    BaseInstructionDataType.IMMEDIATE),
BASE_INSTRUCTION_AND = BaseInstructionDefinition(
    "AND", 0x9, BaseInstructionType.DEFINED,
    BaseInstructionDataType.IMMEDIATE),
BASE_INSTRUCTION_FREE = BaseInstructionDefinition(
    "FREE", 0xa, BaseInstructionType.UNDEFINED,
    BaseInstructionDataType.UNDEFINED),
BASE_INSTRUCTION_ADD = BaseInstructionDefinition(
    "ADD", 0xb, BaseInstructionType.DEFINED,
    BaseInstructionDataType.IMMEDIATE),
BASE_INSTRUCTION_OR = BaseInstructionDefinition(
    "OR", 0xc, BaseInstructionType.DEFINED, BaseInstructionDataType.IMMEDIATE),
BASE_INSTRUCTION_POP = BaseInstructionDefinition(
    "POP", 0xd, BaseInstructionType.DEFINED, BaseInstructionDataType.DATA),
BASE_INSTRUCTION_PUSH = BaseInstructionDefinition(
    "PUSH", 0xe, BaseInstructionType.DEFINED, BaseInstructionDataType.DATA),
BASE_INSTRUCTION_NOOP = BaseInstructionDefinition(
    "NOOP", 0xf, BaseInstructionType.DEFINED, BaseInstructionDataType.DATA),

BASE_INSTRUCTIONS = [
    BASE_INSTRUCTION_HALT, BASE_INSTRUCTION_UNDEF, BASE_INSTRUCTION_JUMP,
    BASE_INSTRUCTION_JUMPZ, BASE_INSTRUCTION_LOAD, BASE_INSTRUCTION_STORE,
    BASE_INSTRUCTION_LSHIFT, BASE_INSTRUCTION_RSHIFT, BASE_INSTRUCTION_XOR,
    BASE_INSTRUCTION_AND, BASE_INSTRUCTION_FREE, BASE_INSTRUCTION_ADD,
    BASE_INSTRUCTION_OR, BASE_INSTRUCTION_POP, BASE_INSTRUCTION_PUSH,
    BASE_INSTRUCTION_NOOP
]
