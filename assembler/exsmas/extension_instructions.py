#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provides definitions for extended SMA16 instructions."""

from .base_instructions import *
from .variables import VariablePlaceholder, TempVariable
from .values import ConstantValue


class ExtensionInstructionDefinition:
    """Extension Instruction Definition."""

    def __init__(self, name: str, mapping: list, arguments: list, outputs: list,
                 variables: list):
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
        self.name = name
        self.mapping = mapping
        self.arguments = arguments
        self.outputs = outputs
        self.variables = variables


class ExtensionInstructionInstance:
    """Extension Instruction Instance.

    Defines an instance of an instruction IE the definition of the instruction and the data
    stored with that instruction.
    """

    def __init__(self,
                 inst_definition: ExtensionInstructionDefinition,
                 data: Optional[int] = None):
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


EXTENSION_INSTRUCTIONS = [
    ExtensionInstructionDefinition(
        name="NOT",
        mapping=[
            (BASE_INSTRUCTION_LOAD, VariablePlaceholder("in")),
            (BASE_INSTRUCTION_XOR, ConstantValue(0xfff)),
            (BASE_INSTRUCTION_STORE, VariablePlaceholder("out")),
        ],
        arguments=[VariablePlaceholder("in")],
        outputs=[VariablePlaceholder("out")],
        variables=[]),
    ExtensionInstructionDefinition(
        name="PEAK",
        mapping=[
            (BASE_INSTRUCTION_POP,),
            (BASE_INSTRUCTION_PUSH,),
            (BASE_INSTRUCTION_STORE, VariablePlaceholder("out")),
        ],
        arguments=[],
        outputs=[VariablePlaceholder("out")],
        variables=[]),
    ExtensionInstructionDefinition(
        name="SWAP",
        mapping=[
            (BASE_INSTRUCTION_POP,),
            (BASE_INSTRUCTION_STORE, TempVariable("x")),
            (BASE_INSTRUCTION_POP,),
            (BASE_INSTRUCTION_STORE, TempVariable("y")),
            (BASE_INSTRUCTION_LOAD, TempVariable("x")),
            (BASE_INSTRUCTION_PUSH,),
            (BASE_INSTRUCTION_LOAD, TempVariable("y")),
            (BASE_INSTRUCTION_PUSH,),
        ],
        arguments=[],
        outputs=[],
        variables=[])
]
