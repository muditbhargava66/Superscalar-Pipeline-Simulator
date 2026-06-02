"""
Enhanced branch prediction algorithms for the superscalar processor simulator.

This module provides various branch prediction algorithms including:
- Always taken/not taken predictors
- Bimodal predictor
- GShare predictor
- Tournament predictor
- Perceptron predictor
- Adaptive hybrid predictor
"""

from .always_taken_predictor import AlwaysTakenPredictor
from .bimodal_predictor import BimodalPredictor
from .gshare_predictor import GsharePredictor
from .hybrid_predictor import (
    AdaptiveHybridPredictor,
    PerceptronPredictor,
    TournamentPredictor,
)

__all__ = [
    "AdaptiveHybridPredictor",
    "AlwaysTakenPredictor",
    "BimodalPredictor",
    "GsharePredictor",
    "PerceptronPredictor",
    "TournamentPredictor",
]
