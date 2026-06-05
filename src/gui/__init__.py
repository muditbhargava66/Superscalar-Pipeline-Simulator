"""
GUI components for the superscalar processor simulator.

This module provides graphical user interface components for configuration
and visualization of the simulator.
"""

try:
    from .config_gui import ConfigurationGUI

    __all__ = ["ConfigurationGUI"]
except ImportError:
    # GUI dependencies not available
    __all__ = []
