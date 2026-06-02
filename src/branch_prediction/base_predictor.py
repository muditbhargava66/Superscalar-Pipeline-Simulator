#!/usr/bin/env python3
"""
Base Branch Predictor Classes

This module provides base classes and common interfaces for branch predictors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
import logging
from typing import Any, Optional


@dataclass
class PredictionResult:
    """Result of a branch prediction."""

    taken: bool
    confidence: float = 0.5  # Confidence in prediction (0.0 to 1.0)
    target: int | None = None  # Predicted target address
    metadata: dict[str, Any] | None = None  # Additional predictor-specific data

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BranchPredictor(ABC):
    """
    Abstract base class for branch predictors.

    All branch predictors should inherit from this class and implement
    the predict and update methods.
    """

    def __init__(self, config: dict):
        self.config = config
        self.predictions = 0
        self.correct_predictions = 0
        self.mispredictions = 0
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def predict(self, pc: int, history: int | None = None) -> PredictionResult:
        """
        Make a branch prediction.

        Args:
            pc: Program counter of the branch instruction
            history: Optional global history register value

        Returns:
            PredictionResult containing prediction and metadata
        """
        pass

    @abstractmethod
    def update(
        self,
        pc: int,
        taken: bool,
        target: int | None = None,
        history: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        """
        Update predictor with actual branch outcome.

        Args:
            pc: Program counter of the branch instruction
            taken: Whether the branch was actually taken
            target: Actual target address (if taken)
            history: Global history register value
            metadata: Additional update information
        """
        pass

    def get_accuracy(self) -> float:
        """Get prediction accuracy as a percentage."""
        if self.predictions == 0:
            return 0.0
        return (self.correct_predictions / self.predictions) * 100.0

    def get_stats(self) -> dict[str, Any]:
        """Get predictor statistics."""
        return {
            "predictions": self.predictions,
            "correct_predictions": self.correct_predictions,
            "mispredictions": self.mispredictions,
            "accuracy": self.get_accuracy(),
            "predictor_type": self.__class__.__name__,
        }

    def reset_stats(self) -> None:
        """Reset all statistics."""
        self.predictions = 0
        self.correct_predictions = 0
        self.mispredictions = 0

    def update_stats(self, predicted: bool, actual: bool) -> None:
        """Update prediction statistics."""
        self.predictions += 1
        if predicted == actual:
            self.correct_predictions += 1
        else:
            self.mispredictions += 1


class SimpleBranchPredictor(BranchPredictor):
    """
    Base class for simple branch predictors that don't use complex metadata.
    """

    def predict(self, pc: int, history: int | None = None) -> PredictionResult:
        """Make a simple prediction."""
        taken = self._predict_taken(pc, history)
        confidence = self._get_confidence(pc, history)

        return PredictionResult(
            taken=taken,
            confidence=confidence,
            target=None,  # Simple predictors don't predict targets
            metadata={"pc": pc, "history": history},
        )

    def update(
        self,
        pc: int,
        taken: bool,
        target: int | None = None,
        history: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Update simple predictor."""
        # Get what we would have predicted
        predicted = self._predict_taken(pc, history)

        # Update statistics
        self.update_stats(predicted, taken)

        # Update predictor state
        self._update_predictor(pc, taken, history)

    @abstractmethod
    def _predict_taken(self, pc: int, history: int | None = None) -> bool:
        """Predict if branch is taken (to be implemented by subclasses)."""
        pass

    @abstractmethod
    def _update_predictor(
        self, pc: int, taken: bool, history: int | None = None
    ) -> None:
        """Update predictor state (to be implemented by subclasses)."""
        pass

    def _get_confidence(self, pc: int, history: int | None = None) -> float:
        """Get confidence in prediction (can be overridden by subclasses)."""
        return 0.5  # Default neutral confidence
