"""
Enhanced register file implementation for the superscalar processor simulator.

This module provides the register file with support for multiple read/write
ports, register locking for hazard prevention, and advanced register renaming.
"""

from .enhanced_register_renaming import EnhancedRegisterRenaming
from .register_file import RegisterFile
from .register_renaming import AdvancedRegisterRenaming

__all__ = ["AdvancedRegisterRenaming", "EnhancedRegisterRenaming", "RegisterFile"]
