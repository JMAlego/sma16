#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from .base_instructions import *


class VariablePlaceholder:

    def __init__(self, *args, **kwargs):
        """Initialise Placeholder for Variable."""


class ConstantValue:

    def __init__(self, *args, **kwargs):
        """Initialise Constant Value."""


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
