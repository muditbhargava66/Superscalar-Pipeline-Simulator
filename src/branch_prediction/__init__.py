"""
Branch prediction algorithms for the superscalar processor simulator.

This module provides various branch prediction algorithms including
always taken, bimodal, and gshare predictors.
"""

from .always_taken_predictor import AlwaysTakenPredictor
from .bimodal_predictor import BimodalPredictor
from .gshare_predictor import GsharePredictor

__all__ = [
    'AlwaysTakenPredictor',
    'BimodalPredictor',
    'GsharePredictor'
]
