#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provides definitions for extended SMA16 instructions."""

from .base_instructions import *
from .variables import VariablePlaceholder, TempVariable
from .values import ConstantValue


class ExtensionInstructionDefinition:
    """Extension Instruction Definition."""

    def __init__(self, name: str, mapping: list, arguments: list,
                 outputs: list, variables: list):
        """Initialise Extension Instruction Definition.

        Parameters
        ----------
            - name: str -- Name used to refer to the variable
            - mapping: list[(BaseInstructionDefinition, [Value|Variable]),...] -- Mapping of lines
              of base assembly and arguments to extension instruction
            - arguments: list[Variable] -- Input variables to instruction
            - outputs: list[Variable] -- Output variables from instruction
            - variables: list[Variable] -- Persistant variables

        """


EXTENSION_INSTRUCTIONS = [
    ExtensionInstructionDefinition("NOT", [
        (BASE_INSTRUCTION_LOAD, VariablePlaceholder("in")),
        (BASE_INSTRUCTION_XOR, ConstantValue(0xfff)),
        (BASE_INSTRUCTION_STORE, VariablePlaceholder("out")),
    ], [VariablePlaceholder("in")], [VariablePlaceholder("out")], []),
    ExtensionInstructionDefinition("PEAK", [
        (BASE_INSTRUCTION_POP, ),
        (BASE_INSTRUCTION_PUSH, ),
        (BASE_INSTRUCTION_STORE, VariablePlaceholder("out")),
    ], [], [VariablePlaceholder("out")], []),
    ExtensionInstructionDefinition("SWAP", [
        (BASE_INSTRUCTION_POP, ),
        (BASE_INSTRUCTION_STORE, TempVariable("x")),
        (BASE_INSTRUCTION_POP, ),
        (BASE_INSTRUCTION_STORE, TempVariable("y")),
        (BASE_INSTRUCTION_LOAD, TempVariable("x")),
        (BASE_INSTRUCTION_PUSH, ),
        (BASE_INSTRUCTION_LOAD, TempVariable("y")),
        (BASE_INSTRUCTION_PUSH, ),
    ], [], [], [])
]
