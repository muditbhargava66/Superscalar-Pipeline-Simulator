#!/usr/bin/env python3

"""
Advanced Register Renaming Implementation

This module provides comprehensive register renaming with support for
multiple renaming schemes, precise exception handling, and performance
optimization.
"""

from collections import deque
from enum import Enum
import logging
from typing import Any, List, Optional


class RenamingScheme(Enum):
    """Register renaming schemes."""

    TOMASULO = "tomasulo"
    EXPLICIT = "explicit"
    HYBRID = "hybrid"


class RegisterState(Enum):
    """Physical register states."""

    FREE = "free"
    ALLOCATED = "allocated"
    COMMITTED = "committed"
    PENDING_FREE = "pending_free"


class PhysicalRegister:
    """Represents a physical register in the rename buffer."""

    def __init__(self, reg_id: int):
        self.reg_id = reg_id
        self.state = RegisterState.FREE
        self.value: int | None = None
        self.ready = True
        self.producer_instruction: int | None = None
        self.allocation_cycle = -1
        self.last_access_cycle = -1


class RenameMapEntry:
    """Entry in the register rename map."""

    def __init__(self, logical_reg: int, physical_reg: int):
        self.logical_reg = logical_reg
        self.physical_reg = physical_reg
        self.valid = True
        self.speculative = False


class ReorderBufferEntry:
    """Entry in the reorder buffer for precise exceptions."""

    def __init__(
        self,
        instruction_id: int,
        logical_dest: int | None,
        old_physical_reg: int | None,
        new_physical_reg: int | None,
    ):
        self.instruction_id = instruction_id
        self.logical_dest = logical_dest
        self.old_physical_reg = old_physical_reg
        self.new_physical_reg = new_physical_reg
        self.completed = False
        self.exception = False
        self.exception_info: str | None = None
        self.commit_cycle = -1


class AdvancedRegisterRenaming:
    """
    Advanced register renaming system with multiple schemes and optimizations.

    Features:
    - Multiple renaming schemes (Tomasulo, Explicit, Hybrid)
    - Precise exception handling with reorder buffer
    - Speculative execution support
    - Register recycling and optimization
    - Performance monitoring and statistics
    """

    def __init__(
        self,
        num_logical_regs: int = 32,
        num_physical_regs: int = 128,
        reorder_buffer_size: int = 64,
        renaming_scheme: RenamingScheme = RenamingScheme.EXPLICIT,
    ):
        """
        Initialize register renaming system.

        Args:
            num_logical_regs: Number of logical (architectural) registers
            num_physical_regs: Number of physical registers
            reorder_buffer_size: Size of reorder buffer
            renaming_scheme: Renaming scheme to use
        """
        self.num_logical_regs = num_logical_regs
        self.num_physical_regs = num_physical_regs
        self.reorder_buffer_size = reorder_buffer_size
        self.renaming_scheme = renaming_scheme

        # Physical register file
        self.physical_registers = [
            PhysicalRegister(i) for i in range(num_physical_regs)
        ]

        # Free list of physical registers
        self.free_list = deque(range(num_logical_regs, num_physical_regs))

        # Register rename map (logical -> physical)
        self.rename_map: dict[int, int] = {}

        # Committed rename map (for recovery)
        self.committed_map: dict[int, int] = {}

        # Initialize architectural registers (1:1 mapping initially)
        for i in range(num_logical_regs):
            self.rename_map[i] = i
            self.committed_map[i] = i
            self.physical_registers[i].state = RegisterState.COMMITTED

        # Reorder buffer for precise exceptions
        self.reorder_buffer: deque[ReorderBufferEntry] = deque()
        self.rob_head = 0
        self.rob_tail = 0

        # Speculative state tracking
        self.speculative_instructions: set[int] = set()
        self.branch_checkpoints: list[dict[str, Any]] = []

        # Statistics
        self.current_cycle = 0
        self.stats = {
            "renames_performed": 0,
            "registers_allocated": 0,
            "registers_freed": 0,
            "rob_entries_used": 0,
            "stalls_no_physical_regs": 0,
            "stalls_rob_full": 0,
            "branch_mispredictions": 0,
            "recovery_cycles": 0,
            "average_register_lifetime": 0.0,
        }

        self.logger = logging.getLogger(__name__)

    def rename_instruction(
        self, instruction_id: int, src_regs: list[int], dst_reg: int | None
    ) -> tuple[bool, list[int], int | None]:
        """
        Rename registers for an instruction.

        Args:
            instruction_id: Unique instruction identifier
            src_regs: List of source logical register numbers
            dst_reg: Destination logical register number (if any)

        Returns:
            (success, renamed_src_regs, renamed_dst_reg) tuple
        """
        # Check if reorder buffer has space
        if len(self.reorder_buffer) >= self.reorder_buffer_size:
            self.stats["stalls_rob_full"] += 1
            return False, [], None

        # Check if we have enough physical registers
        if dst_reg is not None and not self.free_list:
            self.stats["stalls_no_physical_regs"] += 1
            return False, [], None

        # Rename source registers
        renamed_src_regs = []
        for src_reg in src_regs:
            if src_reg in self.rename_map:
                renamed_src_regs.append(self.rename_map[src_reg])
            else:
                # Should not happen in normal operation
                self.logger.warning(f"Source register {src_reg} not in rename map")
                renamed_src_regs.append(src_reg)

        # Rename destination register
        renamed_dst_reg = None
        old_physical_reg = None

        if dst_reg is not None:
            # Get old physical register for this logical register
            old_physical_reg = self.rename_map.get(dst_reg)

            # Allocate new physical register
            new_physical_reg = self.free_list.popleft()
            self.physical_registers[new_physical_reg].state = RegisterState.ALLOCATED
            self.physical_registers[
                new_physical_reg
            ].producer_instruction = instruction_id
            self.physical_registers[
                new_physical_reg
            ].allocation_cycle = self.current_cycle
            self.physical_registers[new_physical_reg].ready = False

            # Update rename map
            self.rename_map[dst_reg] = new_physical_reg
            renamed_dst_reg = new_physical_reg

            self.stats["registers_allocated"] += 1

        # Add entry to reorder buffer
        rob_entry = ReorderBufferEntry(
            instruction_id, dst_reg, old_physical_reg, renamed_dst_reg
        )
        self.reorder_buffer.append(rob_entry)
        self.stats["rob_entries_used"] += 1

        self.stats["renames_performed"] += 1
        self.logger.debug(
            f"Renamed instruction {instruction_id}: src={src_regs}->{renamed_src_regs}, dst={dst_reg}->{renamed_dst_reg}"
        )

        return True, renamed_src_regs, renamed_dst_reg

    def complete_instruction(
        self, instruction_id: int, result_value: int | None = None
    ) -> bool:
        """
        Mark instruction as completed and update register state.

        Args:
            instruction_id: Instruction identifier
            result_value: Result value to write to destination register

        Returns:
            True if instruction was found and completed
        """
        # Find instruction in reorder buffer
        for rob_entry in self.reorder_buffer:
            if rob_entry.instruction_id == instruction_id:
                rob_entry.completed = True

                # Update physical register if there's a destination
                if rob_entry.new_physical_reg is not None:
                    phys_reg = self.physical_registers[rob_entry.new_physical_reg]
                    phys_reg.ready = True
                    if result_value is not None:
                        phys_reg.value = result_value
                    phys_reg.last_access_cycle = self.current_cycle

                self.logger.debug(f"Completed instruction {instruction_id}")
                return True

        return False

    def commit_instructions(self) -> list[int]:
        """
        Commit completed instructions from head of reorder buffer.

        Returns:
            List of committed instruction IDs
        """
        committed_instructions = []

        while (
            self.reorder_buffer
            and self.reorder_buffer[0].completed
            and not self.reorder_buffer[0].exception
        ):
            rob_entry = self.reorder_buffer.popleft()
            rob_entry.commit_cycle = self.current_cycle

            # Update committed rename map
            if rob_entry.logical_dest is not None:
                self.committed_map[rob_entry.logical_dest] = rob_entry.new_physical_reg  # type: ignore[assignment]

                # Mark new register as committed
                if rob_entry.new_physical_reg is not None:
                    self.physical_registers[
                        rob_entry.new_physical_reg
                    ].state = RegisterState.COMMITTED

                # Free old physical register
                if rob_entry.old_physical_reg is not None:
                    self._free_physical_register(rob_entry.old_physical_reg)

            committed_instructions.append(rob_entry.instruction_id)
            self.logger.debug(f"Committed instruction {rob_entry.instruction_id}")

        return committed_instructions

    def handle_exception(self, instruction_id: int, exception_info: str) -> None:
        """
        Handle exception for an instruction.

        Args:
            instruction_id: Instruction that caused exception
            exception_info: Exception information
        """
        # Find instruction in reorder buffer
        for rob_entry in self.reorder_buffer:
            if rob_entry.instruction_id == instruction_id:
                rob_entry.exception = True
                rob_entry.exception_info = exception_info

                # Flush all younger instructions
                self._flush_younger_instructions(rob_entry)
                break

    def handle_branch_misprediction(self, branch_instruction_id: int) -> None:
        """
        Handle branch misprediction and recover state.

        Args:
            branch_instruction_id: ID of mispredicted branch instruction
        """
        self.stats["branch_mispredictions"] += 1
        recovery_start = self.current_cycle

        # Find branch instruction in reorder buffer
        branch_rob_index = -1
        for i, rob_entry in enumerate(self.reorder_buffer):
            if rob_entry.instruction_id == branch_instruction_id:
                branch_rob_index = i
                break

        if branch_rob_index == -1:
            self.logger.warning(
                f"Branch instruction {branch_instruction_id} not found in ROB"
            )
            return

        # Flush all instructions after the branch
        instructions_to_flush = list(self.reorder_buffer)[branch_rob_index + 1 :]

        for rob_entry in instructions_to_flush:
            # Free allocated physical registers
            if rob_entry.new_physical_reg is not None:
                self._free_physical_register(rob_entry.new_physical_reg)

            # Restore old mapping
            if (
                rob_entry.logical_dest is not None
                and rob_entry.old_physical_reg is not None
            ):
                self.rename_map[rob_entry.logical_dest] = rob_entry.old_physical_reg

        # Remove flushed instructions from reorder buffer
        for _ in range(len(instructions_to_flush)):
            self.reorder_buffer.pop()

        self.stats["recovery_cycles"] += self.current_cycle - recovery_start
        self.logger.info(
            f"Recovered from branch misprediction, flushed {len(instructions_to_flush)} instructions"
        )

    def create_checkpoint(self, branch_instruction_id: int) -> int:
        """
        Create checkpoint for speculative execution.

        Args:
            branch_instruction_id: ID of branch instruction

        Returns:
            Checkpoint ID
        """
        checkpoint = {
            "branch_instruction_id": branch_instruction_id,
            "rename_map": self.rename_map.copy(),
            "free_list": list(self.free_list),
            "cycle": self.current_cycle,
        }

        self.branch_checkpoints.append(checkpoint)
        return len(self.branch_checkpoints) - 1

    def restore_checkpoint(self, checkpoint_id: int) -> None:
        """
        Restore state from checkpoint.

        Args:
            checkpoint_id: Checkpoint to restore
        """
        if 0 <= checkpoint_id < len(self.branch_checkpoints):
            checkpoint = self.branch_checkpoints[checkpoint_id]

            # Restore rename map
            self.rename_map = checkpoint["rename_map"].copy()

            # Restore free list
            self.free_list = deque(checkpoint["free_list"])

            # Remove this and later checkpoints
            self.branch_checkpoints = self.branch_checkpoints[:checkpoint_id]

            self.logger.debug(f"Restored checkpoint {checkpoint_id}")

    def read_register(self, physical_reg: int) -> tuple[bool, int | None]:
        """
        Read value from physical register.

        Args:
            physical_reg: Physical register number

        Returns:
            (ready, value) tuple
        """
        if 0 <= physical_reg < self.num_physical_regs:
            phys_reg = self.physical_registers[physical_reg]
            phys_reg.last_access_cycle = self.current_cycle
            return phys_reg.ready, phys_reg.value

        return False, None

    def write_register(self, physical_reg: int, value: int) -> bool:
        """
        Write value to physical register.

        Args:
            physical_reg: Physical register number
            value: Value to write

        Returns:
            True if write was successful
        """
        if 0 <= physical_reg < self.num_physical_regs:
            phys_reg = self.physical_registers[physical_reg]
            phys_reg.value = value
            phys_reg.ready = True
            phys_reg.last_access_cycle = self.current_cycle
            return True

        return False

    def advance_cycle(self) -> None:
        """Advance renaming system by one cycle."""
        self.current_cycle += 1

        # Commit instructions if possible
        self.commit_instructions()

        # Update register lifetime statistics
        self._update_lifetime_stats()

    def _free_physical_register(self, physical_reg: int) -> None:
        """Free a physical register and return it to free list."""
        if 0 <= physical_reg < self.num_physical_regs:
            phys_reg = self.physical_registers[physical_reg]

            # Calculate lifetime
            if phys_reg.allocation_cycle >= 0:
                lifetime = self.current_cycle - phys_reg.allocation_cycle
                # Update average lifetime (simplified)
                self.stats["average_register_lifetime"] = (
                    self.stats["average_register_lifetime"]
                    * self.stats["registers_freed"]
                    + lifetime
                ) / (self.stats["registers_freed"] + 1)

            # Reset register state
            phys_reg.state = RegisterState.FREE
            phys_reg.value = None
            phys_reg.ready = True
            phys_reg.producer_instruction = None
            phys_reg.allocation_cycle = -1

            # Return to free list
            self.free_list.append(physical_reg)
            self.stats["registers_freed"] += 1

    def _flush_younger_instructions(
        self, exception_rob_entry: ReorderBufferEntry
    ) -> None:
        """Flush all instructions younger than the exception instruction."""
        # Find exception instruction index
        exception_index = -1
        for i, rob_entry in enumerate(self.reorder_buffer):
            if rob_entry.instruction_id == exception_rob_entry.instruction_id:
                exception_index = i
                break

        if exception_index == -1:
            return

        # Flush younger instructions
        instructions_to_flush = list(self.reorder_buffer)[exception_index + 1 :]

        for rob_entry in instructions_to_flush:
            # Free allocated physical registers
            if rob_entry.new_physical_reg is not None:
                self._free_physical_register(rob_entry.new_physical_reg)

            # Restore old mapping
            if (
                rob_entry.logical_dest is not None
                and rob_entry.old_physical_reg is not None
            ):
                self.rename_map[rob_entry.logical_dest] = rob_entry.old_physical_reg

        # Remove flushed instructions from reorder buffer
        for _ in range(len(instructions_to_flush)):
            self.reorder_buffer.pop()

    def _update_lifetime_stats(self) -> None:
        """Update register lifetime statistics."""
        # This would be called periodically to update statistics
        pass

    def get_statistics(self) -> dict[str, Any]:
        """Get register renaming statistics."""
        stats = self.stats.copy()

        # Add current state information
        stats.update(
            {
                "physical_registers_used": sum(
                    1
                    for reg in self.physical_registers
                    if reg.state != RegisterState.FREE
                ),
                "physical_registers_free": len(self.free_list),
                "reorder_buffer_occupancy": len(self.reorder_buffer),
                "reorder_buffer_utilization": len(self.reorder_buffer)
                / self.reorder_buffer_size,
                "current_cycle": self.current_cycle,
                "active_checkpoints": len(self.branch_checkpoints),
            }
        )

        # Calculate derived statistics
        if stats["registers_allocated"] > 0:
            stats["register_utilization"] = (
                stats["registers_allocated"] - stats["registers_freed"]
            ) / self.num_physical_regs

        return stats

    def reset_statistics(self) -> None:
        """Reset all statistics."""
        self.stats = {
            "renames_performed": 0,
            "registers_allocated": 0,
            "registers_freed": 0,
            "rob_entries_used": 0,
            "stalls_no_physical_regs": 0,
            "stalls_rob_full": 0,
            "branch_mispredictions": 0,
            "recovery_cycles": 0,
            "average_register_lifetime": 0.0,
        }

    def get_rename_map(self) -> dict[int, int]:
        """Get current rename map (for debugging)."""
        return self.rename_map.copy()

    def get_committed_map(self) -> dict[int, int]:
        """Get committed rename map (for debugging)."""
        return self.committed_map.copy()
