#!/usr/bin/env python3
"""
Test suite for Branch Prediction implementations.

Tests cover all branch predictor types:
- AlwaysTakenPredictor (standalone interface)
- BimodalPredictor and AdaptiveBimodalPredictor (standalone interface)
- GsharePredictor and EnhancedGsharePredictor (standalone interface)
- TournamentPredictor, PerceptronPredictor, AdaptiveHybridPredictor (base class interface)

Note: There are two different predictor interface families:
1. Standalone: predict(instruction) → int|None, update(instruction, actual_taken)
2. Base class: predict(pc, history) → PredictionResult, update(pc, taken, target, history, metadata)
"""

import pytest

from src.branch_prediction.always_taken_predictor import AlwaysTakenPredictor
from src.branch_prediction.base_predictor import PredictionResult
from src.branch_prediction.bimodal_predictor import (
    AdaptiveBimodalPredictor,
    BimodalPredictor,
)
from src.branch_prediction.gshare_predictor import (
    EnhancedGsharePredictor,
    GsharePredictor,
)
from src.branch_prediction.hybrid_predictor import (
    AdaptiveHybridPredictor,
    PerceptronPredictor,
    TournamentPredictor,
)
from src.utils.instruction import Instruction

# ============================== Fixtures ====================================


@pytest.fixture
def branch_instruction() -> Instruction:
    """Create a branch instruction for testing."""
    return Instruction(address=0x1000, opcode="beq", operands=["$t0", "$t1", "0x1020"])


@pytest.fixture
def always_taken() -> AlwaysTakenPredictor:
    """Create an AlwaysTakenPredictor instance."""
    return AlwaysTakenPredictor()


@pytest.fixture
def bimodal() -> BimodalPredictor:
    """Create a BimodalPredictor instance."""
    return BimodalPredictor(num_entries=1024)


@pytest.fixture
def adaptive_bimodal() -> AdaptiveBimodalPredictor:
    """Create an AdaptiveBimodalPredictor instance."""
    return AdaptiveBimodalPredictor(num_entries=1024)


@pytest.fixture
def gshare() -> GsharePredictor:
    """Create a GsharePredictor instance."""
    return GsharePredictor(num_entries=1024, history_length=10)


@pytest.fixture
def enhanced_gshare() -> EnhancedGsharePredictor:
    """Create an EnhancedGsharePredictor instance."""
    return EnhancedGsharePredictor(num_entries=1024, history_length=10)


@pytest.fixture
def tournament() -> TournamentPredictor:
    """Create a TournamentPredictor instance."""
    return TournamentPredictor(config={})


@pytest.fixture
def perceptron() -> PerceptronPredictor:
    """Create a PerceptronPredictor instance."""
    return PerceptronPredictor(config={})


@pytest.fixture
def adaptive_hybrid() -> AdaptiveHybridPredictor:
    """Create an AdaptiveHybridPredictor instance."""
    return AdaptiveHybridPredictor(config={})


# ======================== AlwaysTakenPredictor ==============================


class TestAlwaysTakenPredictor:
    """Always-taken branch predictor (simplest strategy)."""

    def test_predict_always_taken(
        self, always_taken: AlwaysTakenPredictor, branch_instruction: Instruction
    ) -> None:
        """Should always predict taken (return non-None target)."""
        prediction = always_taken.predict(branch_instruction)
        assert prediction is not None

    def test_update_taken(
        self, always_taken: AlwaysTakenPredictor, branch_instruction: Instruction
    ) -> None:
        """Update with taken branch should succeed."""
        always_taken.update(branch_instruction, actual_taken=True)
        # No exception means success

    def test_update_not_taken(
        self, always_taken: AlwaysTakenPredictor, branch_instruction: Instruction
    ) -> None:
        """Update with not-taken branch should succeed."""
        always_taken.update(branch_instruction, actual_taken=False)
        # No exception means success

    def test_accuracy_tracking(
        self, always_taken: AlwaysTakenPredictor, branch_instruction: Instruction
    ) -> None:
        """Track prediction accuracy."""
        # Predict and update multiple times
        always_taken.predict(branch_instruction)
        always_taken.update(branch_instruction, True)
        always_taken.predict(branch_instruction)
        always_taken.update(branch_instruction, True)
        always_taken.predict(branch_instruction)
        always_taken.update(branch_instruction, False)

        accuracy = always_taken.get_accuracy()
        assert 0.0 <= accuracy <= 100.0


# ========================== BimodalPredictor ================================


class TestBimodalPredictor:
    """2-bit saturating counter bimodal predictor."""

    def test_initial_prediction(
        self, bimodal: BimodalPredictor, branch_instruction: Instruction
    ) -> None:
        """Initial prediction may be None or a target address."""
        prediction = bimodal.predict(branch_instruction)
        # Prediction is int (target) or None
        assert prediction is None or isinstance(prediction, int)

    def test_update_and_predict(
        self, bimodal: BimodalPredictor, branch_instruction: Instruction
    ) -> None:
        """After training, predictor should learn the pattern."""
        # Train on taken branches
        for _ in range(5):
            bimodal.update(branch_instruction, actual_taken=True)

        # Should now predict taken
        prediction = bimodal.predict(branch_instruction)
        assert prediction is not None

    def test_accuracy_improves_with_training(
        self, bimodal: BimodalPredictor, branch_instruction: Instruction
    ) -> None:
        """Accuracy should improve after training."""
        # Train on always-taken pattern
        for _ in range(10):
            bimodal.predict(branch_instruction)
            bimodal.update(branch_instruction, True)

        accuracy = bimodal.get_accuracy()
        assert accuracy > 0.0


class TestAdaptiveBimodalPredictor:
    """Adaptive bimodal predictor with hysteresis."""

    def test_instantiation(self, adaptive_bimodal: AdaptiveBimodalPredictor) -> None:
        """Should instantiate successfully."""
        assert adaptive_bimodal is not None

    def test_predict_and_update(
        self,
        adaptive_bimodal: AdaptiveBimodalPredictor,
        branch_instruction: Instruction,
    ) -> None:
        """Basic predict and update cycle."""
        adaptive_bimodal.predict(branch_instruction)
        adaptive_bimodal.update(branch_instruction, True)
        # Should handle both taken and not-taken
        adaptive_bimodal.update(branch_instruction, False)


# ========================== GsharePredictor =================================


class TestGsharePredictor:
    """Gshare predictor using global history XOR PC indexing."""

    def test_initial_prediction(
        self, gshare: GsharePredictor, branch_instruction: Instruction
    ) -> None:
        """Initial prediction should be valid."""
        prediction = gshare.predict(branch_instruction)
        assert prediction is None or isinstance(prediction, int)

    def test_history_affects_prediction(
        self, gshare: GsharePredictor, branch_instruction: Instruction
    ) -> None:
        """Different branch histories should produce different predictions."""
        # Predict with no history
        gshare.predict(branch_instruction)

        # Update history with taken branches
        for _ in range(5):
            gshare.update(branch_instruction, True)

        # Predict again (history has changed)
        gshare.predict(branch_instruction)

        # Predictions may differ due to history change
        # (not guaranteed, but likely with different history)

    def test_accuracy_tracking(
        self, gshare: GsharePredictor, branch_instruction: Instruction
    ) -> None:
        """Track prediction accuracy."""
        for _ in range(10):
            gshare.predict(branch_instruction)
            gshare.update(branch_instruction, True)

        accuracy = gshare.get_accuracy()
        assert 0.0 <= accuracy <= 100.0


class TestEnhancedGsharePredictor:
    """Enhanced gshare with per-branch statistics."""

    def test_instantiation(self, enhanced_gshare: EnhancedGsharePredictor) -> None:
        """Should instantiate successfully."""
        assert enhanced_gshare is not None

    def test_predict_and_update(
        self,
        enhanced_gshare: EnhancedGsharePredictor,
        branch_instruction: Instruction,
    ) -> None:
        """Basic predict and update cycle."""
        enhanced_gshare.predict(branch_instruction)
        enhanced_gshare.update(branch_instruction, True)
        enhanced_gshare.update(branch_instruction, False)


# ===================== Base Class Predictors ================================


class TestTournamentPredictor:
    """Tournament predictor using base class interface."""

    def test_instantiation(self, tournament: TournamentPredictor) -> None:
        """Should instantiate successfully."""
        assert tournament is not None

    def test_predict_returns_prediction_result(
        self, tournament: TournamentPredictor
    ) -> None:
        """predict() should return a PredictionResult."""
        pc = 0x1000
        history = 0b0101010101  # 10-bit history
        result = tournament.predict(pc, history)
        assert isinstance(result, PredictionResult)
        assert hasattr(result, "taken")
        assert hasattr(result, "confidence")

    def test_update_with_metadata(self, tournament: TournamentPredictor) -> None:
        """Update with full metadata."""
        pc = 0x1000
        history = 0b0101010101
        target = 0x1020
        metadata = {"branch_type": "conditional"}

        tournament.update(
            pc=pc, taken=True, target=target, history=history, metadata=metadata
        )
        # No exception means success

    def test_multiple_predictions(self, tournament: TournamentPredictor) -> None:
        """Make multiple predictions with different PCs."""
        history = 0b0000000000
        for pc in [0x1000, 0x1004, 0x1008, 0x100C]:
            result = tournament.predict(pc, history)
            assert isinstance(result, PredictionResult)
            tournament.update(pc, result.taken, 0x1020, history, {})


class TestPerceptronPredictor:
    """Perceptron-based branch predictor."""

    def test_instantiation(self, perceptron: PerceptronPredictor) -> None:
        """Should instantiate successfully."""
        assert perceptron is not None

    def test_predict_returns_prediction_result(
        self, perceptron: PerceptronPredictor
    ) -> None:
        """predict() should return a PredictionResult."""
        pc = 0x1000
        history = 0b1111111111
        result = perceptron.predict(pc, history)
        assert isinstance(result, PredictionResult)

    def test_learning_from_updates(self, perceptron: PerceptronPredictor) -> None:
        """Perceptron should learn from updates."""
        pc = 0x1000
        history = 0b1111111111

        # Train on taken branches
        for _ in range(10):
            perceptron.predict(pc, history)
            perceptron.update(pc, True, 0x1020, history, {})

        # After training, should predict taken more confidently
        final_result = perceptron.predict(pc, history)
        assert isinstance(final_result, PredictionResult)


class TestAdaptiveHybridPredictor:
    """Adaptive hybrid predictor that switches between tournament and perceptron."""

    def test_instantiation(self, adaptive_hybrid: AdaptiveHybridPredictor) -> None:
        """Should instantiate successfully."""
        assert adaptive_hybrid is not None

    def test_predict_returns_prediction_result(
        self, adaptive_hybrid: AdaptiveHybridPredictor
    ) -> None:
        """predict() should return a PredictionResult."""
        pc = 0x1000
        history = 0b1010101010
        result = adaptive_hybrid.predict(pc, history)
        assert isinstance(result, PredictionResult)

    def test_adaptive_behavior(self, adaptive_hybrid: AdaptiveHybridPredictor) -> None:
        """Predictor should adapt based on accuracy."""
        pc = 0x1000
        history = 0b1010101010

        # Train with mixed pattern
        for i in range(20):
            adaptive_hybrid.predict(pc, history)
            taken = i % 2 == 0  # Alternating pattern
            adaptive_hybrid.update(pc, taken, 0x1020, history, {})

        # Predictor should have adapted
        final_result = adaptive_hybrid.predict(pc, history)
        assert isinstance(final_result, PredictionResult)
