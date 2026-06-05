"""
Execute Stage Implementation

This module implements the execute stage of the pipeline, which performs
instruction execution using various functional units.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

# Handle imports for both package and direct execution
try:
    from ..cache.cache import DataCache, Memory
    from ..register_file.register_file import RegisterFile
    from ..utils.functional_unit import ALU, FPU, LSU, FunctionalUnitStats
    from ..utils.instruction import Instruction
except (ImportError, ValueError):
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from cache.cache import DataCache, Memory
    from register_file.register_file import RegisterFile
    from utils.functional_unit import ALU, FPU, LSU, FunctionalUnitStats
    from utils.instruction import Instruction


class ExecuteStage:
    """
    Execute stage of the pipeline.

    Manages multiple functional units and schedules instructions
    for execution based on availability and type.
    """

    def __init__(
        self,
        num_alu_units: int,
        num_fpu_units: int,
        num_lsu_units: int,
        register_file: RegisterFile,
        data_cache: DataCache,
        memory: Memory,
    ) -> None:
        """
        Initialize the execute stage with functional units.

        Args:
            num_alu_units: Number of ALU units
            num_fpu_units: Number of FPU units
            num_lsu_units: Number of LSU units
            register_file: Reference to register file
            data_cache: Reference to data cache
            memory: Reference to main memory
        """
        if not isinstance(register_file, RegisterFile):
            raise TypeError("register_file must be an instance of RegisterFile")

        self.register_file = register_file
        self.data_cache = data_cache
        self.memory = memory
        self.functional_units = []

        # Create ALU functional units
        for i in range(num_alu_units):
            alu = ALU(id=f"ALU{i}")
            self.functional_units.append(alu)

        # Create FPU functional units
        for i in range(num_fpu_units):
            fpu = FPU(id=f"FPU{i}")
            self.functional_units.append(fpu)

        # Create LSU functional units
        for i in range(num_lsu_units):
            lsu = LSU(id=f"LSU{i}", data_cache=self.data_cache, memory=self.memory)
            self.functional_units.append(lsu)

        # Performance tracking
        self.stats = FunctionalUnitStats()
        self.executed_count = 0

        logging.info(
            f"Initialized Execute Stage with {num_alu_units} ALUs, "
            f"{num_fpu_units} FPUs, {num_lsu_units} LSUs"
        )

    def execute(
        self, ready_instructions: List[Instruction]
    ) -> List[Tuple[Instruction, Any]]:
        """
        Execute ready instructions on available functional units.

        Args:
            ready_instructions: List of instructions ready for execution

        Returns:
            List of (instruction, result) tuples for completed instructions
        """
        executed_instructions = []
        scheduled_count = 0

        # Try to schedule each ready instruction
        for instruction in ready_instructions:
            if instruction is None:
                continue

            # Find a suitable free functional unit
            functional_unit = self.find_free_functional_unit(instruction.opcode)

            if functional_unit is not None:
                try:
                    # Execute the instruction
                    result = functional_unit.execute(instruction, self.register_file)

                    # Mark instruction as executing
                    instruction.status = "executing"
                    instruction.assigned_unit = functional_unit.id

                    # Record statistics
                    self.stats.record_execution(functional_unit.id, instruction.opcode)
                    scheduled_count += 1

                    logging.debug(f"Scheduled {instruction} on {functional_unit.id}")

                except Exception as e:
                    logging.error(f"Error executing instruction {instruction}: {e}")
                    # Continue with other instructions
            else:
                # No free functional unit available - structural hazard
                self.stats.record_stall()
                logging.debug(
                    f"Structural hazard: No free unit for {instruction.opcode}"
                )
                # Don't break - other instructions might find free units

        # Check for completed instructions
        for unit in self.functional_units:
            completed = unit.update()
            if completed:
                instruction, result = completed
                instruction.result = result
                instruction.status = "executed"
                executed_instructions.append((instruction, result))
                self.executed_count += 1

                logging.debug(
                    f"Completed execution of {instruction} with result {result}"
                )

        # Update cycle counter for statistics
        self.stats.update_cycle()

        return executed_instructions

    def find_free_functional_unit(self, opcode: str) -> Any | None:
        """
        Find a free functional unit that can execute the given opcode.

        Args:
            opcode: Instruction opcode

        Returns:
            Free functional unit or None if none available
        """
        for functional_unit in self.functional_units:
            if functional_unit.is_free() and functional_unit.can_execute(opcode):
                return functional_unit
        return None

    def update_functional_units(self) -> None:
        """
        Update all functional units for one cycle.

        This is called at the end of each cycle to progress
        multi-cycle operations.
        """
        completed_instructions = []

        for functional_unit in self.functional_units:
            # Update returns completed instruction if any
            completed = functional_unit.update()
            if completed:
                completed_instructions.append(completed)

        # Log completed instructions
        for instruction, result in completed_instructions:
            logging.debug(f"Functional unit completed: {instruction} -> {result}")

    def get_unit_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all functional units.

        Returns:
            List of unit status dictionaries
        """
        status = []
        for unit in self.functional_units:
            status.append(
                {
                    "id": unit.id,
                    "type": unit.__class__.__name__,
                    "busy": unit.busy,
                    "remaining_cycles": unit.remaining_cycles,
                    "current_instruction": str(unit.current_instruction)
                    if unit.current_instruction
                    else None,
                    "utilization": self.stats.get_utilization(unit.id),
                }
            )
        return status

    def get_statistics(self) -> dict[str, Any]:
        """
        Get execution stage statistics.

        Returns:
            Dictionary of statistics
        """
        # Calculate average utilization
        total_utilization = sum(
            self.stats.get_utilization(unit.id) for unit in self.functional_units
        )
        avg_utilization = (
            total_utilization / len(self.functional_units)
            if self.functional_units
            else 0
        )

        return {
            "executed_instructions": self.executed_count,
            "structural_stalls": self.stats.total_stalls,
            "structural_stall_rate": self.stats.get_structural_stall_rate(),
            "average_utilization": avg_utilization,
            "unit_utilization": {
                unit.id: self.stats.get_utilization(unit.id)
                for unit in self.functional_units
            },
            "opcode_distribution": self.stats.get_opcode_distribution(),
        }

    def reset(self) -> None:
        """Reset execution stage and all functional units."""
        self.executed_count = 0
        self.stats = FunctionalUnitStats()

        # Reset all functional units
        for unit in self.functional_units:
            unit.busy = False
            unit.remaining_cycles = 0
            unit.current_instruction = None
            unit.result = None

        logging.info("Execute stage reset")


class OutOfOrderExecuteStage(ExecuteStage):
    """
    Enhanced execute stage with out-of-order execution support.

    Adds:
    - Instruction window for better scheduling
    - Priority-based dynamic instruction selection (oldest-first)
    - Result forwarding tracking
    - Stall on window overflow instead of dropping instructions
    """

    def __init__(self, *args, window_size: int = 16, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.window_size = window_size
        self.instruction_window: List[Instruction] = []
        self.stall_cycles = 0

    def execute(
        self, ready_instructions: List[Instruction]
    ) -> List[Tuple[Instruction, Any]]:
        """
        Execute with out-of-order scheduling from instruction window.

        Uses oldest-first priority scheduling and stalls on window overflow
        instead of dropping instructions.
        """
        # Stall if window is full - do not drop instructions
        if len(self.instruction_window) >= self.window_size:
            self.stall_cycles += 1
            logging.debug(
                f"OoO window full ({self.window_size}), stalling. "
                f"New instructions will be accepted after window drains."
            )
            # Still check for completed instructions even while stalled
            return self._check_completions()

        # Add new instructions to window (up to capacity)
        available_slots = self.window_size - len(self.instruction_window)
        added = 0
        for instruction in ready_instructions:
            if added >= available_slots:
                break
            if instruction is not None:
                self.instruction_window.append(instruction)
                added += 1

        # Schedule instructions from window using oldest-first priority
        scheduled_instructions = []
        remaining_instructions = []

        # Sort by PC (oldest first) for priority-based selection
        sorted_window = sorted(
            self.instruction_window,
            key=lambda inst: getattr(inst, "pc", 0),
        )

        for instruction in sorted_window:
            unit = self.find_free_functional_unit(instruction.opcode)

            if unit is not None:
                try:
                    unit.execute(instruction, self.register_file)
                    instruction.status = "executing"
                    instruction.assigned_unit = unit.id
                    scheduled_instructions.append(instruction)

                    self.stats.record_execution(unit.id, instruction.opcode)
                    logging.debug(f"OoO scheduled {instruction} on {unit.id}")

                except Exception as e:
                    logging.error(f"Error in OoO execution: {e}")
                    remaining_instructions.append(instruction)
            else:
                remaining_instructions.append(instruction)

        # Update instruction window (remove scheduled, keep remaining)
        self.instruction_window = remaining_instructions

        # Check for completed instructions
        return self._check_completions()

    def _check_completions(self) -> List[Tuple[Instruction, Any]]:
        """Check functional units for completed instructions."""
        executed_instructions = []
        for unit in self.functional_units:
            completed = unit.update()
            if completed:
                instruction, result = completed
                instruction.result = result
                instruction.status = "executed"
                executed_instructions.append((instruction, result))
                self.executed_count += 1

        self.stats.update_cycle()
        return executed_instructions

    def get_window_status(self) -> dict[str, Any]:
        """Get status of the instruction window."""
        return {
            "window_size": self.window_size,
            "current_occupancy": len(self.instruction_window),
            "utilization": len(self.instruction_window) / self.window_size * 100,
            "stall_cycles": self.stall_cycles,
            "instructions": [str(inst) for inst in self.instruction_window],
        }
