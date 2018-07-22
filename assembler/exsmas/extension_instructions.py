#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provides definitions for extended SMA16 instructions."""

from .base_instructions import BASE_INSTRUCTION_HALT, BASE_INSTRUCTION_UNDEF, \
    BASE_INSTRUCTION_JUMP, BASE_INSTRUCTION_JUMPZ, BASE_INSTRUCTION_LOAD, \
    BASE_INSTRUCTION_STORE, BASE_INSTRUCTION_LSHIFT, BASE_INSTRUCTION_RSHIFT, \
    BASE_INSTRUCTION_XOR, BASE_INSTRUCTION_AND, BASE_INSTRUCTION_FREE, \
    BASE_INSTRUCTION_ADD, BASE_INSTRUCTION_OR, BASE_INSTRUCTION_POP, \
    BASE_INSTRUCTION_PUSH, BASE_INSTRUCTION_NOOP
from .variables import VariablePlaceholder
from .values import ConstantValue


class ExtensionInstructionDefinition:
    """Extension Instruction Definition."""

    def __init__(self, name: str, mapping: list, arguments: list,
                 variables: list):
        """Initialise Extension Instruction Definition."""


EXTENSION_INSTRUCTIONS = [
    ExtensionInstructionDefinition("NOT", [
        (BASE_INSTRUCTION_XOR, VariablePlaceholder("X"), ConstantValue(0xfff))
    ], [VariablePlaceholder("X")], [])
]
