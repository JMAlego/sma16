#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Provides variables for use as placeholders or used variables."""


class Variable:
    """Provides a variable for assembly."""

    def __init__(self, name: str) -> None:
        """Initialise Variable."""
        self.name = name
        self.location = None

    def get_name(self) -> str:
        """Get the name of the variable."""
        return self.name

    def get_location(self) -> int:
        """Get the address of the variable."""

    def set_location(self) -> None:
        """Set the address of the variable."""

    def has_location(self) -> bool:
        """Return true if the variable has an address assigned, false otherwise."""
        return self.location is not None


class TempVariable(Variable):
    """Provides a temp location variable for assembly."""


class VariablePlaceholder:
    """Provides a placeholder for a variable or value in a instruction definition."""

    def __init__(self, name: str) -> None:
        """Initialise Placeholder for Variable."""
        self.name = name

    def get_name(self) -> str:
        """Get the name of the placeholder."""
        return self.name

    def realise(self) -> Variable:
        """Realise placeholder."""
        return Variable(self.name)
