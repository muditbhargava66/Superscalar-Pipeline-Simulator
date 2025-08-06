"""
Gshare Branch Predictor Implementation

This module implements the gshare branch prediction algorithm, which uses
global branch history XORed with the PC to index into a pattern history table.
"""

from __future__ import annotations

import logging
from typing import Optional


class GsharePredictor:
    """
    Gshare branch predictor using global history and PC XOR indexing.
    
    The gshare predictor maintains a global history register that tracks
    the outcome of recent branches, and uses this history XORed with the
    branch PC to index into a pattern history table of 2-bit saturating counters.
    
    Attributes:
        num_entries: Number of entries in the pattern history table
        history_length: Number of bits in the global history register
        history_register: Global history of recent branch outcomes
        pattern_history_table: Table of 2-bit saturating counters
    """

    def __init__(self, num_entries: int = 1024, history_length: int = 8) -> None:
        """
        Initialize the gshare predictor.
        
        Args:
            num_entries: Number of entries in the pattern history table (power of 2)
            history_length: Number of bits in the global history register
        """
        self.num_entries = num_entries
        self.history_length = history_length
        self.history_register = 0

        # Initialize pattern history table with weakly taken (2)
        # Counter values: 0=strongly not taken, 1=weakly not taken,
        #                 2=weakly taken, 3=strongly taken
        self.pattern_history_table = [2] * num_entries

        # Performance counters
        self.total_predictions = 0
        self.total_mispredictions = 0
        self.branch_history: List[Dict] = []  # For debugging/analysis

        logging.debug(f"Initialized Gshare predictor with {num_entries} entries, "
                     f"{history_length}-bit history")

    def predict(self, instruction) -> Optional[int]:
        """
        Predict the outcome of a branch instruction.
        
        Args:
            instruction: The branch instruction (with PC address)
            
        Returns:
            Predicted target PC if branch taken, None if not taken
        """
        # Handle both Instruction objects and raw PC values
        if hasattr(instruction, 'address'):
            pc = instruction.address
        elif isinstance(instruction, int):
            pc = instruction
        else:
            logging.error(f"Invalid instruction type for prediction: {type(instruction)}")
            return None

        # Get index into pattern history table
        index = self._get_index(pc)

        # Read counter value
        counter = self.pattern_history_table[index]

        # Predict taken if counter >= 2
        prediction_taken = counter >= 2

        self.total_predictions += 1

        # Calculate predicted PC
        if hasattr(instruction, 'is_branch') and instruction.is_branch():
            if prediction_taken:
                # For branch instructions, return target address
                if hasattr(instruction, 'operands') and len(instruction.operands) >= 3:
                    # Conditional branches: beq/bne have target as 3rd operand
                    try:
                        target_offset = int(instruction.operands[2])
                        return pc + 4 + (target_offset * 4)  # PC-relative addressing
                    except (ValueError, IndexError):
                        return pc + 4  # Default to next instruction
                elif hasattr(instruction, 'operands') and len(instruction.operands) >= 1:
                    # Unconditional jumps: j/jal have absolute target
                    try:
                        return int(instruction.operands[0])
                    except ValueError:
                        return pc + 4

        # Not taken or not a branch
        return pc + 4 if not prediction_taken else None

    def update(self, instruction, actual_taken: bool) -> None:
        """
        Update the predictor with the actual branch outcome.
        
        Args:
            instruction: The branch instruction (with PC address)
            actual_taken: Whether the branch was actually taken
        """
        # Handle both Instruction objects and raw PC values
        if hasattr(instruction, 'address'):
            pc = instruction.address
        elif isinstance(instruction, int):
            pc = instruction
        else:
            logging.error(f"Invalid instruction type for update: {type(instruction)}")
            return

        # Get index and current counter
        index = self._get_index(pc)
        counter = self.pattern_history_table[index]

        # Check if prediction was correct
        predicted_taken = counter >= 2
        if predicted_taken != actual_taken:
            self.total_mispredictions += 1

        # Update 2-bit saturating counter
        if actual_taken:
            # Increment counter (saturate at 3)
            self.pattern_history_table[index] = min(counter + 1, 3)
        else:
            # Decrement counter (saturate at 0)
            self.pattern_history_table[index] = max(counter - 1, 0)

        # Update global history register
        self.history_register = ((self.history_register << 1) | (1 if actual_taken else 0)) & ((1 << self.history_length) - 1)

        # Record for analysis
        self.branch_history.append({
            'pc': pc,
            'predicted': predicted_taken,
            'actual': actual_taken,
            'counter_before': counter,
            'counter_after': self.pattern_history_table[index],
            'history': self.history_register
        })

        logging.debug(f"Updated branch at PC {pc}: predicted={predicted_taken}, "
                     f"actual={actual_taken}, counter={counter}->{self.pattern_history_table[index]}")

    def _get_index(self, pc: int) -> int:
        """
        Calculate the index into the pattern history table.
        
        Uses XOR of PC bits and global history register.
        
        Args:
            pc: Program counter value
            
        Returns:
            Index into the pattern history table
        """
        # Use lower bits of PC (ignore lower 2 bits for word alignment)
        pc_bits = (pc >> 2) & (self.num_entries - 1)

        # XOR with history register
        index = pc_bits ^ self.history_register

        # Ensure index is within bounds
        return index & (self.num_entries - 1)

    def get_total_predictions(self) -> int:
        """Get the total number of predictions made."""
        return self.total_predictions

    def get_total_mispredictions(self) -> int:
        """Get the total number of mispredictions."""
        return self.total_mispredictions

    def get_accuracy(self) -> float:
        """
        Calculate the prediction accuracy.
        
        Returns:
            Accuracy as a percentage (0-100)
        """
        if self.total_predictions == 0:
            return 0.0

        correct_predictions = self.total_predictions - self.total_mispredictions
        return (correct_predictions / self.total_predictions) * 100.0

    def get_statistics(self) -> Dict:
        """
        Get comprehensive statistics about the predictor.
        
        Returns:
            Dictionary containing various statistics
        """
        # Count counter states
        counter_distribution = {0: 0, 1: 0, 2: 0, 3: 0}
        for counter in self.pattern_history_table:
            counter_distribution[counter] += 1

        return {
            'total_predictions': self.total_predictions,
            'total_mispredictions': self.total_mispredictions,
            'accuracy': self.get_accuracy(),
            'history_register': bin(self.history_register),
            'counter_distribution': counter_distribution,
            'table_utilization': len(set(self.branch_history[-1000:])) / self.num_entries * 100 if self.branch_history else 0
        }

    def reset(self) -> None:
        """Reset the predictor to its initial state."""
        self.history_register = 0
        self.pattern_history_table = [2] * self.num_entries
        self.total_predictions = 0
        self.total_mispredictions = 0
        self.branch_history.clear()

        logging.info("Gshare predictor reset to initial state")

    def __repr__(self) -> str:
        """String representation of the predictor."""
        return (f"GsharePredictor(entries={self.num_entries}, "
                f"history_bits={self.history_length}, "
                f"accuracy={self.get_accuracy():.1f}%)")


class EnhancedGsharePredictor(GsharePredictor):
    """
    Enhanced gshare predictor with additional features.
    
    Adds:
    - Per-branch statistics tracking
    - Adaptive history length
    - Confidence estimation
    """

    def __init__(self, num_entries: int = 1024, history_length: int = 8) -> None:
        super().__init__(num_entries, history_length)
        self.per_branch_stats: Dict[int, Dict] = {}
        self.confidence_threshold = 0.9

    def update(self, instruction, actual_taken: bool) -> None:
        """Update with per-branch tracking."""
        super().update(instruction, actual_taken)

        # Track per-branch statistics
        pc = instruction.address if hasattr(instruction, 'address') else instruction
        if pc not in self.per_branch_stats:
            self.per_branch_stats[pc] = {
                'taken_count': 0,
                'not_taken_count': 0,
                'mispredictions': 0
            }

        stats = self.per_branch_stats[pc]
        if actual_taken:
            stats['taken_count'] += 1
        else:
            stats['not_taken_count'] += 1

        # Check if mispredicted
        index = self._get_index(pc)
        predicted_taken = self.pattern_history_table[index] >= 2
        if predicted_taken != actual_taken:
            stats['mispredictions'] += 1

    def get_branch_bias(self, pc: int) -> Optional[float]:
        """
        Get the bias (taken probability) for a specific branch.
        
        Args:
            pc: Program counter of the branch
            
        Returns:
            Taken probability (0-1) or None if no history
        """
        if pc not in self.per_branch_stats:
            return None

        stats = self.per_branch_stats[pc]
        total = stats['taken_count'] + stats['not_taken_count']
        if total == 0:
            return None

        return stats['taken_count'] / total

    def is_high_confidence(self, pc: int) -> bool:
        """
        Check if prediction for this branch is high confidence.
        
        Args:
            pc: Program counter of the branch
            
        Returns:
            True if high confidence prediction
        """
        bias = self.get_branch_bias(pc)
        if bias is None:
            return False

        # High confidence if strongly biased
        return bias > self.confidence_threshold or bias < (1 - self.confidence_threshold)
