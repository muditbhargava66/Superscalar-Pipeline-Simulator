"""
Always Taken Branch Predictor Implementation

This module implements the simplest branch predictor that always predicts
branches as taken. Used as a baseline for comparison.
"""

from __future__ import annotations

import logging
from typing import Optional


class AlwaysTakenPredictor:
    """
    Always Taken branch predictor.
    
    This is the simplest branch predictor that always predicts branches
    as taken. It serves as a baseline for comparing more sophisticated
    branch prediction algorithms.
    """

    def __init__(self) -> None:
        """Initialize the always taken predictor."""
        self.total_predictions = 0
        self.total_mispredictions = 0
        logging.debug("Initialized Always Taken predictor")

    def predict(self, instruction) -> Optional[int]:
        """
        Predict the outcome of a branch instruction (always taken).
        
        Args:
            instruction: The branch instruction (with PC address)
            
        Returns:
            Predicted target PC (branch target for branches, target address for jumps)
        """
        self.total_predictions += 1

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

        # For branch/jump instructions, calculate target
        if hasattr(instruction, 'opcode'):
            opcode = instruction.opcode.upper()

            if opcode in ["BEQ", "BNE", "BLT", "BGE", "BLTU", "BGEU"]:
                # Conditional branches - always predict taken
                if hasattr(instruction, 'operands') and len(instruction.operands) >= 3:
                    try:
                        # Branch offset is typically the third operand
                        offset = int(instruction.operands[2])
                        # PC-relative addressing: PC + 4 + (offset * 4)
                        return pc + 4 + (offset * 4)
                    except (ValueError, IndexError):
                        # If we can't parse offset, just return PC + 8 as a guess
                        return pc + 8
            elif opcode in ["J", "JAL"]:
                # Unconditional jumps - extract target address
                if hasattr(instruction, 'operands') and len(instruction.operands) >= 1:
                    try:
                        # Direct jump to address
                        target_str = instruction.operands[0]
                        if target_str.startswith('0x'):
                            return int(target_str, 16)
                        else:
                            return int(target_str)
                    except ValueError:
                        return pc + 4
            elif opcode in ["JR", "JALR"]:
                # Register jumps - can't predict statically, return a default
                return pc + 4  # This will likely be wrong, but we have no info

        # Default: predict branch taken (PC + 8)
        return pc + 8

    def update(self, instruction, actual_taken: bool) -> None:
        """
        Update the predictor with the actual branch outcome.
        
        Since this is an always-taken predictor, no state is updated,
        but we track mispredictions for statistics.
        
        Args:
            instruction: The branch instruction
            actual_taken: Whether the branch was actually taken
        """
        if not actual_taken:
            self.total_mispredictions += 1

        # Log the update for debugging
        pc = getattr(instruction, 'address', getattr(instruction, 'pc', instruction))
        logging.debug(f"Always Taken predictor update: PC={pc:#x}, actual={actual_taken}, "
                     f"mispredicted={not actual_taken}")

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

    def reset(self) -> None:
        """Reset the predictor statistics."""
        self.total_predictions = 0
        self.total_mispredictions = 0
        logging.info("Always Taken predictor reset")

    def __repr__(self) -> str:
        """String representation of the predictor."""
        return f"AlwaysTakenPredictor(accuracy={self.get_accuracy():.1f}%)"
