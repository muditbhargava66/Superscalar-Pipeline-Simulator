"""
Bimodal Branch Predictor Implementation

This module implements a bimodal branch predictor using 2-bit saturating
counters indexed by branch PC.
"""

from __future__ import annotations

import logging
from typing import Optional


class BimodalPredictor:
    """
    Bimodal branch predictor using 2-bit saturating counters.
    
    Each branch PC indexes into a table of 2-bit counters that track
    the branch behavior. The counter saturates at 0 (strongly not taken)
    and 3 (strongly taken).
    
    Counter states:
    - 0: Strongly Not Taken
    - 1: Weakly Not Taken
    - 2: Weakly Taken
    - 3: Strongly Taken
    
    Attributes:
        num_entries: Number of entries in the prediction table
        prediction_table: Table of 2-bit saturating counters
    """

    def __init__(self, num_entries: int = 1024) -> None:
        """
        Initialize the bimodal predictor.
        
        Args:
            num_entries: Number of entries in the prediction table (power of 2)
        """
        self.num_entries = num_entries
        # Initialize all counters to weakly taken (2)
        self.prediction_table = [2] * num_entries

        # Performance counters
        self.total_predictions = 0
        self.total_mispredictions = 0
        self.branch_history: List[Dict] = []  # For debugging/analysis

        logging.debug(f"Initialized Bimodal predictor with {num_entries} entries")

    def predict(self, instruction) -> Optional[int]:
        """
        Predict the outcome of a branch instruction.
        
        Args:
            instruction: The branch instruction (with PC address)
            
        Returns:
            Predicted target PC if taken, PC+4 if not taken
        """
        # Extract PC from instruction
        if hasattr(instruction, 'address'):
            pc = instruction.address
        elif hasattr(instruction, 'pc'):
            pc = instruction.pc
        elif isinstance(instruction, int):
            pc = instruction
        else:
            logging.error(f"Invalid instruction type for prediction: {type(instruction)}")
            return None

        # Get index into prediction table
        index = self._get_index(pc)

        # Read counter value
        counter = self.prediction_table[index]

        # Predict taken if counter >= 2
        prediction_taken = counter >= 2

        self.total_predictions += 1

        # Calculate predicted PC
        if prediction_taken:
            # For branch instructions, calculate target
            if hasattr(instruction, 'opcode'):
                opcode = instruction.opcode.upper()

                if opcode in ["BEQ", "BNE", "BLT", "BGE", "BLTU", "BGEU"]:
                    # Conditional branches
                    if hasattr(instruction, 'operands') and len(instruction.operands) >= 3:
                        try:
                            offset = int(instruction.operands[2])
                            return pc + 4 + (offset * 4)  # PC-relative
                        except (ValueError, IndexError):
                            return pc + 8  # Default taken target
                elif opcode in ["J", "JAL"]:
                    # Unconditional jumps
                    if hasattr(instruction, 'operands') and len(instruction.operands) >= 1:
                        try:
                            return int(instruction.operands[0])
                        except ValueError:
                            return pc + 4

            # Default taken behavior
            return pc + 8
        else:
            # Not taken - fall through to next instruction
            return pc + 4

    def update(self, instruction, actual_taken: bool) -> None:
        """
        Update the predictor with the actual branch outcome.
        
        Args:
            instruction: The branch instruction
            actual_taken: Whether the branch was actually taken
        """
        # Extract PC from instruction
        if hasattr(instruction, 'address'):
            pc = instruction.address
        elif hasattr(instruction, 'pc'):
            pc = instruction.pc
        elif isinstance(instruction, int):
            pc = instruction
        else:
            logging.error(f"Invalid instruction type for update: {type(instruction)}")
            return

        # Get index and current counter
        index = self._get_index(pc)
        counter = self.prediction_table[index]

        # Check if prediction was correct
        predicted_taken = counter >= 2
        if predicted_taken != actual_taken:
            self.total_mispredictions += 1

        # Update 2-bit saturating counter
        if actual_taken:
            # Increment counter (saturate at 3)
            self.prediction_table[index] = min(counter + 1, 3)
        else:
            # Decrement counter (saturate at 0)
            self.prediction_table[index] = max(counter - 1, 0)

        # Record for analysis
        self.branch_history.append({
            'pc': pc,
            'predicted': predicted_taken,
            'actual': actual_taken,
            'counter_before': counter,
            'counter_after': self.prediction_table[index]
        })

        logging.debug(f"Updated branch at PC {pc:#x}: predicted={predicted_taken}, "
                     f"actual={actual_taken}, counter={counter}->{self.prediction_table[index]}")

    def _get_index(self, pc: int) -> int:
        """
        Calculate the index into the prediction table.
        
        Args:
            pc: Program counter value
            
        Returns:
            Index into the prediction table
        """
        # Use lower bits of PC (ignore lower 2 bits for word alignment)
        # Mask to get index within table size
        return (pc >> 2) & (self.num_entries - 1)

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
        for counter in self.prediction_table:
            counter_distribution[counter] += 1

        # Calculate table utilization (unique PCs seen)
        unique_pcs = len(set(entry['pc'] for entry in self.branch_history))

        return {
            'total_predictions': self.total_predictions,
            'total_mispredictions': self.total_mispredictions,
            'accuracy': self.get_accuracy(),
            'counter_distribution': counter_distribution,
            'table_utilization': (unique_pcs / self.num_entries * 100) if self.num_entries > 0 else 0,
            'strongly_biased_entries': counter_distribution[0] + counter_distribution[3]
        }

    def get_branch_stats(self, pc: int) -> Optional[Dict]:
        """
        Get statistics for a specific branch.
        
        Args:
            pc: Program counter of the branch
            
        Returns:
            Statistics for the branch or None if not found
        """
        branch_entries = [entry for entry in self.branch_history if entry['pc'] == pc]

        if not branch_entries:
            return None

        taken_count = sum(1 for entry in branch_entries if entry['actual'])
        total_count = len(branch_entries)
        correct_count = sum(1 for entry in branch_entries
                          if entry['predicted'] == entry['actual'])

        return {
            'pc': pc,
            'total_executions': total_count,
            'taken_count': taken_count,
            'not_taken_count': total_count - taken_count,
            'correct_predictions': correct_count,
            'accuracy': (correct_count / total_count * 100) if total_count > 0 else 0,
            'current_counter': self.prediction_table[self._get_index(pc)]
        }

    def reset(self) -> None:
        """Reset the predictor to its initial state."""
        self.prediction_table = [2] * self.num_entries
        self.total_predictions = 0
        self.total_mispredictions = 0
        self.branch_history.clear()

        logging.info("Bimodal predictor reset to initial state")

    def __repr__(self) -> str:
        """String representation of the predictor."""
        return (f"BimodalPredictor(entries={self.num_entries}, "
                f"accuracy={self.get_accuracy():.1f}%)")


class AdaptiveBimodalPredictor(BimodalPredictor):
    """
    Enhanced bimodal predictor with adaptive features.
    
    Adds:
    - Dynamic threshold adjustment
    - Hysteresis for frequently mispredicted branches
    - Pattern detection for systematic behavior
    """

    def __init__(self, num_entries: int = 1024) -> None:
        super().__init__(num_entries)
        self.misprediction_counts: Dict[int, int] = {}  # PC -> mispredict count
        self.hysteresis_table = [0] * num_entries  # Additional state bits

    def update(self, instruction, actual_taken: bool) -> None:
        """Update with adaptive features."""
        pc = getattr(instruction, 'address', getattr(instruction, 'pc', instruction))
        index = self._get_index(pc)

        # Check if this was a misprediction
        counter = self.prediction_table[index]
        predicted_taken = counter >= 2

        if predicted_taken != actual_taken:
            # Track mispredictions per PC
            self.misprediction_counts[pc] = self.misprediction_counts.get(pc, 0) + 1

            # Apply hysteresis for frequently mispredicted branches
            if self.misprediction_counts[pc] > 5:
                # Use 3-bit counter effectively by adding hysteresis
                if self.hysteresis_table[index] == 0:
                    # First misprediction after hysteresis reset
                    self.hysteresis_table[index] = 1
                    # Don't update main counter yet
                    return
                else:
                    # Second misprediction - update normally and reset hysteresis
                    self.hysteresis_table[index] = 0

        # Normal update
        super().update(instruction, actual_taken)

    def get_problem_branches(self, threshold: int = 10) -> List[Dict]:
        """
        Identify branches with high misprediction rates.
        
        Args:
            threshold: Minimum mispredictions to be considered problematic
            
        Returns:
            List of problematic branches with their statistics
        """
        problem_branches = []

        for pc, mispredict_count in self.misprediction_counts.items():
            if mispredict_count >= threshold:
                stats = self.get_branch_stats(pc)
                if stats:
                    stats['misprediction_count'] = mispredict_count
                    problem_branches.append(stats)

        return sorted(problem_branches, key=lambda x: x['misprediction_count'], reverse=True)
