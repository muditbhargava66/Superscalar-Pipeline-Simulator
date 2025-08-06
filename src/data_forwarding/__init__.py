"""
Data forwarding unit for the superscalar processor simulator.

This module provides data forwarding capabilities to reduce pipeline stalls
caused by data hazards through bypassing mechanisms.
"""

from .data_forwarding_unit import DataForwardingUnit

__all__ = ['DataForwardingUnit']
