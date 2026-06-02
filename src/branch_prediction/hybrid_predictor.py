#!/usr/bin/env python3
"""
Hybrid Branch Predictor Implementation

This module implements advanced hybrid branch predictors that combine
multiple prediction mechanisms for improved accuracy.
"""

from enum import Enum
import logging
from typing import Any, Optional

try:
    from .base_predictor import BranchPredictor, PredictionResult
except (ImportError, ValueError):
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from base_predictor import (  # type: ignore[no-redef]
        BranchPredictor,
        PredictionResult,
    )


# Create simple predictor classes for tournament predictor
class BimodalPredictor(BranchPredictor):
    """Simple bimodal predictor for tournament use."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.size = config.get("size", 1024)
        self.table = [2] * self.size  # Initialize to weakly taken

    def predict(self, pc: int, history: int | None = None) -> PredictionResult:
        index = pc & (self.size - 1)
        taken = self.table[index] >= 2
        confidence = 0.8 if self.table[index] in [0, 3] else 0.6

        return PredictionResult(
            taken=taken, confidence=confidence, metadata={"counter": self.table[index]}
        )

    def update(
        self,
        pc: int,
        taken: bool,
        target: int | None = None,
        history: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        index = pc & (self.size - 1)

        if taken and self.table[index] < 3:
            self.table[index] += 1
        elif not taken and self.table[index] > 0:
            self.table[index] -= 1

        # Update base statistics
        self.predictions += 1
        if taken == (self.table[index] >= 2):
            self.correct_predictions += 1
        else:
            self.mispredictions += 1


class GSharePredictor(BranchPredictor):
    """Simple GShare predictor for tournament use."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.size = config.get("size", 1024)
        self.history_bits = config.get("history_bits", 10)
        self.table = [2] * self.size
        self.global_history = 0

    def predict(self, pc: int, history: int | None = None) -> PredictionResult:
        hist = history if history is not None else self.global_history
        index = (pc ^ hist) & (self.size - 1)
        taken = self.table[index] >= 2
        confidence = 0.8 if self.table[index] in [0, 3] else 0.6

        return PredictionResult(
            taken=taken,
            confidence=confidence,
            metadata={"counter": self.table[index], "history": hist},
        )

    def update(
        self,
        pc: int,
        taken: bool,
        target: int | None = None,
        history: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        hist = history if history is not None else self.global_history
        index = (pc ^ hist) & (self.size - 1)

        if taken and self.table[index] < 3:
            self.table[index] += 1
        elif not taken and self.table[index] > 0:
            self.table[index] -= 1

        # Update global history
        self.global_history = ((self.global_history << 1) | (1 if taken else 0)) & (
            (1 << self.history_bits) - 1
        )

        # Update base statistics
        self.predictions += 1
        if taken == (self.table[index] >= 2):
            self.correct_predictions += 1
        else:
            self.mispredictions += 1


class HybridPredictorType(Enum):
    """Types of hybrid predictors."""

    TOURNAMENT = "tournament"
    ALPHA = "alpha"
    AGREE = "agree"


class TournamentPredictor(BranchPredictor):
    """
    Tournament predictor that uses a meta-predictor to choose between
    two component predictors (typically bimodal and gshare).
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.predictor_1 = BimodalPredictor(config.get("predictor_1", {}))
        self.predictor_2 = GSharePredictor(config.get("predictor_2", {}))

        # Meta-predictor (chooser) configuration
        self.meta_bits = config.get("meta_bits", 12)
        self.meta_table_size = 1 << self.meta_bits
        self.meta_table = [1] * self.meta_table_size  # 0=pred1, 1=pred2

        # Statistics
        self.pred1_correct = 0
        self.pred2_correct = 0
        self.meta_correct = 0

        self.logger = logging.getLogger(__name__)

    def predict(self, pc: int, history: int | None = None) -> PredictionResult:
        """Make prediction using tournament selection."""
        # Get predictions from both predictors
        pred1_result = self.predictor_1.predict(pc, history)
        pred2_result = self.predictor_2.predict(pc, history)

        # Use meta-predictor to choose
        meta_index = pc & (self.meta_table_size - 1)
        use_pred2 = self.meta_table[meta_index] >= 2

        if use_pred2:
            chosen_result = pred2_result
            confidence = pred2_result.confidence * 0.9  # Slight penalty for indirection
        else:
            chosen_result = pred1_result
            confidence = pred1_result.confidence * 0.9

        return PredictionResult(
            taken=chosen_result.taken,
            confidence=confidence,
            target=chosen_result.target,
            metadata={
                "predictor_used": 2 if use_pred2 else 1,
                "pred1_taken": pred1_result.taken,
                "pred2_taken": pred2_result.taken,
                "meta_value": self.meta_table[meta_index],
            },
        )

    def update(
        self,
        pc: int,
        taken: bool,
        target: int | None = None,
        history: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Update all predictors and meta-predictor."""
        # Update both component predictors
        self.predictor_1.update(pc, taken, target, history)
        self.predictor_2.update(pc, taken, target, history)

        # Get what each predictor would have predicted
        pred1_result = self.predictor_1.predict(pc, history)
        pred2_result = self.predictor_2.predict(pc, history)

        pred1_correct = pred1_result.taken == taken
        pred2_correct = pred2_result.taken == taken

        # Update statistics
        if pred1_correct:
            self.pred1_correct += 1
        if pred2_correct:
            self.pred2_correct += 1

        # Update meta-predictor
        meta_index = pc & (self.meta_table_size - 1)

        if pred1_correct and not pred2_correct:
            # Predictor 1 was better, decrement toward 0
            if self.meta_table[meta_index] > 0:
                self.meta_table[meta_index] -= 1
        elif pred2_correct and not pred1_correct:
            # Predictor 2 was better, increment toward 3
            if self.meta_table[meta_index] < 3:
                self.meta_table[meta_index] += 1

        # Update base statistics
        self.predictions += 1
        use_pred2 = self.meta_table[meta_index] >= 2
        chosen_correct = pred2_correct if use_pred2 else pred1_correct
        if chosen_correct:
            self.correct_predictions += 1
        else:
            self.mispredictions += 1

    def get_stats(self) -> dict:
        """Get detailed statistics."""
        stats = super().get_stats()
        stats.update(
            {
                "predictor_1_accuracy": self.pred1_correct
                / max(1, self.predictions)
                * 100,
                "predictor_2_accuracy": self.pred2_correct
                / max(1, self.predictions)
                * 100,
                "meta_predictor_correct": self.meta_correct,
                "predictor_type": "tournament",
            }
        )
        return stats


class PerceptronPredictor(BranchPredictor):
    """
    Perceptron-based branch predictor using neural network concepts.
    Uses a single-layer perceptron with global history as input.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.history_length = config.get("history_length", 16)
        self.table_size = config.get("table_size", 1024)
        self.theta = config.get("theta", int(1.93 * self.history_length + 14))

        # Perceptron table: each entry is a list of weights
        self.perceptrons = {}
        for i in range(self.table_size):
            # Initialize weights (bias + history_length weights)
            self.perceptrons[i] = [0] * (self.history_length + 1)

        # Global history register
        self.global_history = 0

        self.logger = logging.getLogger(__name__)

    def predict(self, pc: int, history: int | None = None) -> PredictionResult:
        """Make prediction using perceptron."""
        index = pc & (self.table_size - 1)
        weights = self.perceptrons[index]

        # Use provided history or global history
        hist = history if history is not None else self.global_history

        # Calculate perceptron output
        output = weights[0]  # Bias weight

        for i in range(self.history_length):
            bit = (hist >> i) & 1
            # Convert 0/1 to -1/+1 for perceptron
            hist_bit = 1 if bit else -1
            output += weights[i + 1] * hist_bit

        taken = output >= 0
        confidence = min(abs(output) / self.theta, 1.0)

        return PredictionResult(
            taken=taken,
            confidence=confidence,
            target=None,  # Perceptron doesn't predict target
            metadata={"output": output, "theta": self.theta, "history": hist},
        )

    def update(
        self,
        pc: int,
        taken: bool,
        target: int | None = None,
        history: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Update perceptron weights."""
        index = pc & (self.table_size - 1)
        weights = self.perceptrons[index]

        # Use provided history or global history
        hist = history if history is not None else self.global_history

        # Calculate current output
        output = weights[0]
        for i in range(self.history_length):
            bit = (hist >> i) & 1
            hist_bit = 1 if bit else -1
            output += weights[i + 1] * hist_bit

        predicted_taken = output >= 0
        actual = 1 if taken else -1

        # Update weights if mispredicted or output magnitude is small
        if predicted_taken != taken or abs(output) <= self.theta:
            # Update bias weight
            weights[0] += actual

            # Update history weights
            for i in range(self.history_length):
                bit = (hist >> i) & 1
                hist_bit = 1 if bit else -1
                weights[i + 1] += actual * hist_bit

        # Update global history
        self.global_history = ((self.global_history << 1) | (1 if taken else 0)) & (
            (1 << self.history_length) - 1
        )

        # Update base statistics
        self.predictions += 1
        if predicted_taken == taken:
            self.correct_predictions += 1
        else:
            self.mispredictions += 1

    def get_stats(self) -> dict:
        """Get detailed statistics."""
        stats = super().get_stats()
        stats.update(
            {
                "history_length": self.history_length,
                "theta": self.theta,
                "table_size": self.table_size,
                "predictor_type": "perceptron",
            }
        )
        return stats


class AdaptiveHybridPredictor(BranchPredictor):
    """
    Adaptive hybrid predictor that dynamically adjusts its behavior
    based on workload characteristics.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.tournament = TournamentPredictor(config.get("tournament", {}))
        self.perceptron = PerceptronPredictor(config.get("perceptron", {}))

        # Adaptation parameters
        self.adaptation_window = config.get("adaptation_window", 1000)
        self.adaptation_threshold = config.get("adaptation_threshold", 0.05)

        # Current predictor selection
        self.use_perceptron = False
        self.window_predictions = 0
        self.tournament_correct = 0
        self.perceptron_correct = 0

        self.logger = logging.getLogger(__name__)

    def predict(self, pc: int, history: int | None = None) -> PredictionResult:
        """Make prediction using currently selected predictor."""
        if self.use_perceptron:
            result = self.perceptron.predict(pc, history)
            if result.metadata is None:
                result.metadata = {}
            result.metadata["active_predictor"] = "perceptron"
        else:
            result = self.tournament.predict(pc, history)
            if result.metadata is None:
                result.metadata = {}
            result.metadata["active_predictor"] = "tournament"

        return result

    def update(
        self,
        pc: int,
        taken: bool,
        target: int | None = None,
        history: int | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Update both predictors and adapt selection."""
        # Update both predictors
        tournament_pred = self.tournament.predict(pc, history)
        perceptron_pred = self.perceptron.predict(pc, history)

        self.tournament.update(pc, taken, target, history, metadata)
        self.perceptron.update(pc, taken, target, history, metadata)

        # Track accuracy for adaptation
        if tournament_pred.taken == taken:
            self.tournament_correct += 1
        if perceptron_pred.taken == taken:
            self.perceptron_correct += 1

        self.window_predictions += 1

        # Adapt predictor selection
        if self.window_predictions >= self.adaptation_window:
            tournament_acc = self.tournament_correct / self.window_predictions
            perceptron_acc = self.perceptron_correct / self.window_predictions

            # Switch if accuracy difference exceeds threshold
            if abs(tournament_acc - perceptron_acc) > self.adaptation_threshold:
                self.use_perceptron = perceptron_acc > tournament_acc

                self.logger.debug(
                    f"Adapted predictor: {'perceptron' if self.use_perceptron else 'tournament'} "
                    f"(T:{tournament_acc:.3f}, P:{perceptron_acc:.3f})"
                )

            # Reset window
            self.window_predictions = 0
            self.tournament_correct = 0
            self.perceptron_correct = 0

        # Update base statistics
        self.predictions += 1
        current_pred = (
            self.perceptron.predict(pc, history)
            if self.use_perceptron
            else self.tournament.predict(pc, history)
        )
        if current_pred.taken == taken:
            self.correct_predictions += 1
        else:
            self.mispredictions += 1

    def get_stats(self) -> dict:
        """Get comprehensive statistics."""
        stats = super().get_stats()
        stats.update(
            {
                "active_predictor": "perceptron"
                if self.use_perceptron
                else "tournament",
                "tournament_stats": self.tournament.get_stats(),
                "perceptron_stats": self.perceptron.get_stats(),
                "predictor_type": "adaptive_hybrid",
            }
        )
        return stats
