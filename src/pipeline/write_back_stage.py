"""
Write-Back Stage Implementation

This module implements the write-back stage of the pipeline, which writes
instruction results back to the register file.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Optional

# Handle imports for both package and direct execution
try:
    from ..register_file.register_file import RegisterFile
    from ..utils.instruction import Instruction
except (ImportError, ValueError):
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from register_file.register_file import RegisterFile
    from utils.instruction import Instruction


class WriteBackStage:
    """
    Write-back stage of the pipeline.
    
    Responsible for:
    - Writing results to destination registers
    - Updating architectural state
    - Handling instruction completion
    - Managing write port conflicts
    """

    def __init__(self, register_file: RegisterFile, num_write_ports: int = 2) -> None:
        """
        Initialize the write-back stage.
        
        Args:
            register_file: Reference to the register file
            num_write_ports: Number of write ports available
        """
        if not isinstance(register_file, RegisterFile):
            raise TypeError("register_file must be an instance of RegisterFile")

        self.register_file = register_file
        self.num_write_ports = num_write_ports

        # Performance counters
        self.writeback_count = 0
        self.write_port_conflicts = 0
        self.completed_instructions = []

        logging.debug(f"Initialized Write-Back Stage with {num_write_ports} write ports")

    def write_back(self, memory_results: List[Tuple[Instruction, Any]]) -> List[Instruction]:
        """
        Write instruction results back to register file.
        
        Args:
            memory_results: List of (instruction, result) tuples from memory stage
            
        Returns:
            List of completed instructions
        """
        completed = []
        writes_this_cycle = 0

        for instruction, result in memory_results:
            if instruction is None:
                continue

            # Check if we have available write ports
            if writes_this_cycle >= self.num_write_ports:
                # Write port conflict - stall remaining instructions
                self.write_port_conflicts += 1
                logging.debug(f"Write port conflict: delaying {instruction}")
                break

            try:
                if instruction.has_destination_register():
                    # Get destination register
                    destination_register = instruction.get_destination_register()

                    if destination_register:
                        # Write result to register file
                        self.register_file.write_register(destination_register, result)
                        writes_this_cycle += 1

                        logging.debug(f"Write-back: {destination_register} = {result} "
                                    f"(from {instruction.opcode})")

                # Mark instruction as completed
                instruction.status = "completed"
                instruction.completion_cycle = getattr(self, 'current_cycle', 0)

                completed.append(instruction)
                self.completed_instructions.append(instruction)
                self.writeback_count += 1

            except ValueError as e:
                logging.error(f"Error in write-back for {instruction}: {e}")
                instruction.status = "failed"
            except Exception as e:
                logging.error(f"Unexpected error in write-back: {e}")
                instruction.status = "failed"

        return completed

    def handle_exceptions(self, instruction: Instruction, exception_type: str) -> None:
        """
        Handle exceptions during write-back.
        
        Args:
            instruction: Instruction that caused exception
            exception_type: Type of exception
        """
        logging.warning(f"Exception in write-back: {exception_type} for {instruction}")

        # In a real processor, this would trigger exception handling
        # For simulation, we just mark the instruction
        instruction.exception = exception_type
        instruction.status = "exception"

    def get_write_port_utilization(self) -> float:
        """
        Calculate write port utilization.
        
        Returns:
            Utilization percentage
        """
        if self.writeback_count == 0:
            return 0.0

        # Average writes per cycle when writing
        avg_writes = self.writeback_count / max(1, self.writeback_count - self.write_port_conflicts)
        return (avg_writes / self.num_write_ports) * 100

    def get_statistics(self) -> dict:
        """Get write-back stage statistics."""
        return {
            'completed_instructions': self.writeback_count,
            'write_port_conflicts': self.write_port_conflicts,
            'write_port_utilization': self.get_write_port_utilization(),
            'average_latency': self._calculate_average_latency()
        }

    def _calculate_average_latency(self) -> float:
        """Calculate average instruction latency."""
        if not self.completed_instructions:
            return 0.0

        total_latency = 0
        count = 0

        for inst in self.completed_instructions:
            if hasattr(inst, 'issue_cycle') and hasattr(inst, 'completion_cycle'):
                latency = inst.completion_cycle - inst.issue_cycle
                total_latency += latency
                count += 1

        return total_latency / count if count > 0 else 0.0

    def reset(self) -> None:
        """Reset write-back stage."""
        self.writeback_count = 0
        self.write_port_conflicts = 0
        self.completed_instructions.clear()

        logging.info("Write-back stage reset")


class ReorderBuffer:
    """
    Reorder buffer for out-of-order execution with in-order commit.
    
    Ensures instructions complete in program order despite
    out-of-order execution.
    """

    def __init__(self, size: int = 64) -> None:
        """
        Initialize reorder buffer.
        
        Args:
            size: Number of entries in the reorder buffer
        """
        self.size = size
        self.buffer: List[Optional[ROBEntry]] = [None] * size
        self.head = 0  # Oldest instruction (commit point)
        self.tail = 0  # Newest instruction (allocation point)
        self.count = 0

        logging.debug(f"Initialized Reorder Buffer with {size} entries")

    def allocate(self, instruction: Instruction) -> Optional[int]:
        """
        Allocate a ROB entry for an instruction.
        
        Args:
            instruction: Instruction to allocate entry for
            
        Returns:
            ROB index or None if full
        """
        if self.is_full():
            return None

        # Allocate at tail
        rob_id = self.tail
        self.buffer[rob_id] = ROBEntry(
            instruction=instruction,
            ready=False,
            exception=None,
            result=None
        )

        # Update tail and count
        self.tail = (self.tail + 1) % self.size
        self.count += 1

        # Store ROB ID in instruction
        instruction.rob_id = rob_id

        logging.debug(f"Allocated ROB entry {rob_id} for {instruction}")

        return rob_id

    def mark_ready(self, rob_id: int, result: Any = None) -> None:
        """
        Mark a ROB entry as ready to commit.
        
        Args:
            rob_id: ROB entry index
            result: Instruction result
        """
        if self.buffer[rob_id] is not None:
            self.buffer[rob_id].ready = True
            self.buffer[rob_id].result = result

            logging.debug(f"ROB entry {rob_id} marked ready")

    def commit(self, register_file: RegisterFile) -> List[Instruction]:
        """
        Commit ready instructions in program order.
        
        Args:
            register_file: Register file to update
            
        Returns:
            List of committed instructions
        """
        committed = []

        # Commit from head while instructions are ready
        while self.count > 0 and self.buffer[self.head] is not None:
            entry = self.buffer[self.head]

            if not entry.ready:
                # Cannot commit yet - wait for instruction to complete
                break

            if entry.exception:
                # Handle exception
                logging.warning(f"Exception at commit: {entry.exception}")
                # In real processor, would trigger exception handler

            # Commit the instruction
            instruction = entry.instruction

            if instruction.has_destination_register():
                dest_reg = instruction.get_destination_register()
                if dest_reg and entry.result is not None:
                    register_file.write_register(dest_reg, entry.result)

            committed.append(instruction)

            # Free ROB entry
            self.buffer[self.head] = None
            self.head = (self.head + 1) % self.size
            self.count -= 1

            logging.debug(f"Committed {instruction} from ROB")

        return committed

    def flush(self, starting_from: int) -> None:
        """
        Flush ROB entries (for misprediction recovery).
        
        Args:
            starting_from: ROB index to start flushing from
        """
        # Flush all entries from starting_from to tail
        current = starting_from
        flushed = 0

        while current != self.tail:
            if self.buffer[current] is not None:
                self.buffer[current] = None
                flushed += 1

            current = (current + 1) % self.size

        self.tail = starting_from
        self.count -= flushed

        logging.debug(f"Flushed {flushed} ROB entries")

    def is_full(self) -> bool:
        """Check if ROB is full."""
        return self.count >= self.size

    def is_empty(self) -> bool:
        """Check if ROB is empty."""
        return self.count == 0

    def get_occupancy(self) -> float:
        """Get ROB occupancy percentage."""
        return (self.count / self.size) * 100


@dataclass
class ROBEntry:
    """Entry in the reorder buffer."""
    instruction: Instruction
    ready: bool = False
    exception: Optional[str] = None
    result: Optional[Any] = None
    completion_cycle: Optional[int] = None


class AdvancedWriteBackStage(WriteBackStage):
    """
    Enhanced write-back stage with reorder buffer support.
    
    Provides:
    - Out-of-order execution with in-order commit
    - Precise exception handling
    - Speculative execution support
    """

    def __init__(self, register_file: RegisterFile,
                 rob_size: int = 64, num_write_ports: int = 2) -> None:
        super().__init__(register_file, num_write_ports)
        self.rob = ReorderBuffer(rob_size)

    def write_back(self, memory_results: List[Tuple[Instruction, Any]]) -> List[Instruction]:
        """
        Mark instructions as ready in ROB instead of immediately writing back.
        """
        # Mark instructions as ready in ROB
        for instruction, result in memory_results:
            if instruction is None:
                continue

            if hasattr(instruction, 'rob_id'):
                self.rob.mark_ready(instruction.rob_id, result)
                logging.debug(f"Marked {instruction} ready in ROB")

        # Commit instructions from ROB in order
        committed = self.rob.commit(self.register_file)

        # Update statistics
        self.writeback_count += len(committed)
        self.completed_instructions.extend(committed)

        return committed

    def allocate_rob_entry(self, instruction: Instruction) -> bool:
        """
        Allocate a ROB entry for an instruction.
        
        Args:
            instruction: Instruction to allocate entry for
            
        Returns:
            True if allocation successful, False if ROB full
        """
        rob_id = self.rob.allocate(instruction)
        return rob_id is not None

    def handle_misprediction(self, mispredicted_instruction: Instruction) -> None:
        """
        Handle branch misprediction by flushing ROB.
        
        Args:
            mispredicted_instruction: The mispredicted branch
        """
        if hasattr(mispredicted_instruction, 'rob_id'):
            # Flush all instructions after the mispredicted branch
            flush_point = (mispredicted_instruction.rob_id + 1) % self.rob.size
            self.rob.flush(flush_point)

            logging.info(f"Flushed ROB due to misprediction at {mispredicted_instruction}")

    def get_statistics(self) -> dict:
        """Get enhanced statistics including ROB information."""
        stats = super().get_statistics()
        stats.update({
            'rob_occupancy': self.rob.get_occupancy(),
            'rob_size': self.rob.size,
            'rob_entries_used': self.rob.count
        })
        return stats
