"""
Unit tests for branch prediction algorithms.

This module tests the functionality of various branch predictors including
always taken, bimodal, and gshare predictors.

Author: Mudit Bhargava
Date: August2025
Python Version: 3.10+
"""

from pathlib import Path
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.branch_prediction import (
    AlwaysTakenPredictor,
    BimodalPredictor,
    GsharePredictor,
)
from src.utils import BranchInstruction


class TestBranchPrediction(unittest.TestCase):
    """Test suite for branch prediction algorithms."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.branch_addresses = [0x100, 0x200, 0x300, 0x400]
        self.test_instructions = [
            BranchInstruction(address=addr, pc=addr, opcode="BEQ", operands=["$t0", "$t1", "label"])
            for addr in self.branch_addresses
        ]
    
    def test_always_taken_predictor(self):
        """Test the always taken predictor."""
        predictor = AlwaysTakenPredictor()
        
        # Create test branch instructions
        branch1 = BranchInstruction(address=0x100, pc=0x100, opcode="BEQ", operands=["$t0", "$t1", "8"])
        branch2 = BranchInstruction(address=0x200, pc=0x200, opcode="BNE", operands=["$t2", "$t3", "16"])
        
        # Always taken predictor should always predict taken
        for branch in [branch1, branch2]:
            prediction = predictor.predict(branch)
            # Should return next PC + offset for taken prediction
            self.assertIsNotNone(prediction)
            self.assertNotEqual(prediction, branch.pc + 4)  # Not fall-through
        
        # Update with different outcomes shouldn't change prediction
        predictor.update(branch1, True)
        predictor.update(branch1, False)
        predictor.update(branch2, False)
        
        # Still should predict taken
        for branch in [branch1, branch2]:
            prediction = predictor.predict(branch)
            self.assertIsNotNone(prediction)
            self.assertNotEqual(prediction, branch.pc + 4)
    
    def test_gshare_predictor_basic(self):
        """Test basic gshare predictor functionality."""
        predictor = GsharePredictor(num_entries=256, history_length=8)
        
        branch = BranchInstruction(address=0x100, pc=0x100, opcode="BEQ", operands=["$t0", "$t1", "8"])
        
        # Initial prediction (weakly taken)
        initial_pred = predictor.predict(branch)
        self.assertIsNotNone(initial_pred)
        
        # Train the predictor
        # Repeatedly not taken
        for _ in range(3):
            predictor.update(branch, False)
        
        # Should now predict not taken
        pred_after_training = predictor.predict(branch)
        self.assertEqual(pred_after_training, branch.pc + 4)  # Fall-through
        
        # Train taken
        for _ in range(4):
            predictor.update(branch, True)
        
        # Should now predict taken again
        pred_after_taken = predictor.predict(branch)
        self.assertNotEqual(pred_after_taken, branch.pc + 4)
    
    def test_gshare_predictor_pattern(self):
        """Test gshare predictor with patterns."""
        predictor = GsharePredictor(num_entries=1024, history_length=8)
        
        # Create a pattern: T, T, NT, T, T, NT...
        pattern = [True, True, False]
        branch = BranchInstruction(address=0x100, pc=0x100, opcode="BEQ", operands=["$t0", "$t1", "8"])
        
        # Train the pattern
        for _ in range(10):
            for outcome in pattern:
                predictor.update(branch, outcome)
        
        # Test prediction accuracy
        correct_predictions = 0
        total_predictions = 0
        
        for _ in range(3):
            for expected in pattern:
                pred = predictor.predict(branch)
                if expected:
                    correct = pred != branch.pc + 4
                else:
                    correct = pred == branch.pc + 4
                
                if correct:
                    correct_predictions += 1
                total_predictions += 1
                
                predictor.update(branch, expected)
        
        accuracy = correct_predictions / total_predictions
        self.assertGreater(accuracy, 0.6)  # Should learn the pattern reasonably well
    
    def test_gshare_predictor_aliasing(self):
        """Test gshare predictor with potential aliasing."""
        predictor = GsharePredictor(num_entries=64, history_length=4)  # Small table
        
        # Create branches that might alias
        branch1 = BranchInstruction(address=0x100, pc=0x100, opcode="BEQ", operands=["$t0", "$t1", "8"])
        branch2 = BranchInstruction(address=0x140, pc=0x140, opcode="BEQ", operands=["$t2", "$t3", "8"])  # May alias
        
        # Train branch1 as always taken
        for _ in range(5):
            predictor.update(branch1, True)
        
        # Train branch2 as always not taken
        for _ in range(5):
            predictor.update(branch2, False)
        
        # Check predictions
        pred1 = predictor.predict(branch1)
        _pred2 = predictor.predict(branch2)
        
        # Even with potential aliasing, recent training should dominate
        self.assertNotEqual(pred1, branch1.pc + 4)  # Branch1 should be taken
        # Branch2 prediction depends on aliasing
    
    def test_bimodal_predictor(self):
        """Test bimodal predictor functionality."""
        predictor = BimodalPredictor(num_entries=1024)
        
        branch1 = BranchInstruction(address=0x100, pc=0x100, opcode="BEQ", operands=["$t0", "$t1", "8"])
        branch2 = BranchInstruction(address=0x200, pc=0x200, opcode="BNE", operands=["$t2", "$t3", "16"])
        
        # Initial predictions (weakly taken)
        pred1_init = predictor.predict(branch1)
        pred2_init = predictor.predict(branch2)
        self.assertIsNotNone(pred1_init)
        self.assertIsNotNone(pred2_init)
        
        # Train branch1 as not taken
        for _ in range(3):
            predictor.update(branch1, False)
        
        # Train branch2 as taken
        for _ in range(3):
            predictor.update(branch2, True)
        
        # Check predictions
        pred1_trained = predictor.predict(branch1)
        pred2_trained = predictor.predict(branch2)
        
        self.assertEqual(pred1_trained, branch1.pc + 4)  # Not taken
        self.assertNotEqual(pred2_trained, branch2.pc + 4)  # Taken
    
    def test_predictor_statistics(self):
        """Test predictor statistics tracking."""
        predictor = GsharePredictor(num_entries=256, history_length=8)
        
        branches = [
            BranchInstruction(address=0x100 + i*4, pc=0x100 + i*4, opcode="BEQ", operands=["$t0", "$t1", "8"])
            for i in range(10)
        ]
        
        # Make predictions and updates
        for i, branch in enumerate(branches):
            # Predict
            _pred = predictor.predict(branch)
            
            # Actual outcome alternates
            actual = i % 2 == 0
            predictor.update(branch, actual)
        
        # Check statistics
        total_preds = predictor.get_total_predictions()
        total_mispreds = predictor.get_total_mispredictions()
        accuracy = predictor.get_accuracy()
        
        self.assertEqual(total_preds, 10)
        self.assertGreaterEqual(total_mispreds, 0)
        self.assertLessEqual(total_mispreds, total_preds)
        self.assertGreaterEqual(accuracy, 0.0)
        self.assertLessEqual(accuracy, 100.0)
    
    def test_predictor_with_jumps(self):
        """Test predictor with unconditional jumps."""
        predictor = AlwaysTakenPredictor()
        
        # Unconditional jump
        jump = BranchInstruction(address=0x100, pc=0x100, opcode="J", operands=["0x1000"])
        
        pred = predictor.predict(jump)
        # For jumps, prediction should be to the target
        self.assertEqual(pred, 0x1000)
    
    def test_bimodal_saturation(self):
        """Test bimodal predictor saturation behavior."""
        predictor = BimodalPredictor(num_entries=64)
        branch = BranchInstruction(address=0x100, pc=0x100, opcode="BEQ", operands=["$t0", "$t1", "8"])
        
        # Saturate to strongly not taken
        for _ in range(10):
            predictor.update(branch, False)
        
        # Should stay not taken even after one taken
        predictor.update(branch, True)
        pred = predictor.predict(branch)
        self.assertEqual(pred, branch.pc + 4)  # Still not taken
        
        # But should eventually switch
        for _ in range(3):
            predictor.update(branch, True)
        
        pred = predictor.predict(branch)
        self.assertNotEqual(pred, branch.pc + 4)  # Now taken


if __name__ == '__main__':
    unittest.main()
