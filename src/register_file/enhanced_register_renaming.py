#!/usr/bin/env python3

"""
Enhanced Register Renaming with Deep Reorder Buffer

This module implements advanced register renaming with larger reorder buffers,
improved issue queues, and better RAW hazard resolution.
"""

from dataclasses import dataclass, field
from enum import Enum
import logging
from typing import Any, List, Optional

try:
    from ..utils.instruction import Instruction, InstructionType
except (ImportError, ValueError):
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.instruction import Instruction, InstructionType


class ROBEntryState(Enum):
    """Reorder Buffer entry states."""

    ALLOCATED = "allocated"
    ISSUED = "issued"
    EXECUTING = "executing"
    COMPLETED = "completed"
    COMMITTED = "committed"


@dataclass
class ROBEntry:
    """Reorder Buffer entry."""

    instruction: Instruction
    state: ROBEntryState = ROBEntryState.ALLOCATED
    physical_dest: int | None = None
    old_physical_dest: int | None = None
    result: int | None = None
    exception: str | None = None
    ready: bool = False
    issue_cycle: int = 0
    complete_cycle: int | None = None


@dataclass
class IssueQueueEntry:
    """Issue Queue entry for out-of-order execution."""

    rob_id: int
    instruction: Instruction
    src1_ready: bool = False
    src2_ready: bool = False
    src1_physical: int | None = None
    src2_physical: int = None  # type: ignore[assignment]
    dest_physical: int | None = None
    functional_unit_type: str | None = None
    priority: int = 0


class EnhancedRegisterRenaming:
    """
    Enhanced register renaming with deep reorder buffer and
    improved out-of-order execution support.
    """

    def __init__(self, config: dict):
        self.config = config

        # Architecture registers
        self.arch_registers = config.get("arch_registers", 32)

        # Physical register file
        self.physical_registers = config.get("physical_registers", 128)
        self.physical_reg_file = [0] * self.physical_registers
        self.physical_reg_ready = [True] * self.physical_registers

        # Register mapping
        self.rat = {}  # Register Alias Table: arch_reg -> physical_reg
        self.free_list = list(range(self.arch_registers, self.physical_registers))

        # Initialize RAT with identity mapping for architectural registers
        for i in range(self.arch_registers):
            self.rat[i] = i

        # Reorder Buffer (ROB)
        self.rob_size = config.get("rob_size", 64)
        self.rob: list[ROBEntry | None] = [None] * self.rob_size
        self.rob_head = 0
        self.rob_tail = 0
        self.rob_count = 0

        # Issue Queue
        self.issue_queue_size = config.get("issue_queue_size", 32)
        self.issue_queue: list[IssueQueueEntry | None] = []

        # Functional unit tracking
        self.functional_units = {
            "ALU": config.get("alu_count", 4),
            "FPU": config.get("fpu_count", 2),
            "LSU": config.get("lsu_count", 2),
        }
        self.fu_busy = {
            unit: [False] * count for unit, count in self.functional_units.items()
        }

        # Statistics
        self.stats = {
            "instructions_renamed": 0,
            "instructions_issued": 0,
            "instructions_completed": 0,
            "instructions_committed": 0,
            "rob_stalls": 0,
            "issue_queue_stalls": 0,
            "raw_hazards_resolved": 0,
            "war_hazards_resolved": 0,
            "waw_hazards_resolved": 0,
            "branch_mispredictions": 0,
            "squashed_instructions": 0,
        }

        self.current_cycle = 0
        self.logger = logging.getLogger(__name__)

    def rename_instruction(self, instruction: Instruction) -> int | None:
        """
        Rename instruction registers and allocate ROB entry.

        Returns:
            ROB ID if successful, None if stalled
        """
        # Check ROB space
        if self.rob_count >= self.rob_size:
            self.stats["rob_stalls"] += 1
            return None

        # Parse source and destination registers
        src_regs = self._get_source_registers(instruction)
        dest_reg = self._get_destination_register(instruction)

        # Check for available physical registers
        if dest_reg is not None and not self.free_list:
            self.stats["rob_stalls"] += 1
            return None

        # Allocate ROB entry
        rob_id = self.rob_tail

        # Allocate physical register for destination
        physical_dest = None
        old_physical_dest = None

        if dest_reg is not None:
            physical_dest = self.free_list.pop(0)
            old_physical_dest = self.rat.get(dest_reg)
            self.rat[dest_reg] = physical_dest
            self.physical_reg_ready[physical_dest] = False

        # Create ROB entry
        rob_entry = ROBEntry(
            instruction=instruction,
            state=ROBEntryState.ALLOCATED,
            physical_dest=physical_dest,
            old_physical_dest=old_physical_dest,
            issue_cycle=self.current_cycle,
        )

        self.rob[rob_id] = rob_entry
        self.rob_tail = (self.rob_tail + 1) % self.rob_size
        self.rob_count += 1

        # Create issue queue entry
        self._create_issue_queue_entry(rob_id, instruction, src_regs, physical_dest)

        self.stats["instructions_renamed"] += 1
        self.logger.debug(f"Renamed instruction {instruction.opcode} -> ROB[{rob_id}]")

        return rob_id

    def issue_instructions(self) -> list[tuple[int, str]]:
        """
        Issue ready instructions from issue queue.

        Returns:
            List of (rob_id, functional_unit) pairs for issued instructions
        """
        issued = []

        # Sort issue queue by priority (oldest first)
        ready_entries = [
            entry
            for entry in self.issue_queue
            if entry and entry.src1_ready and entry.src2_ready
        ]
        ready_entries.sort(key=lambda x: x.rob_id)

        for entry in ready_entries:
            # Find available functional unit
            fu_type = entry.functional_unit_type
            if fu_type and fu_type in self.fu_busy:
                for i, busy in enumerate(self.fu_busy[fu_type]):
                    if not busy:
                        # Issue instruction
                        self.fu_busy[fu_type][i] = True

                        # Update ROB entry
                        rob_entry = self.rob[entry.rob_id]
                        if rob_entry:
                            rob_entry.state = ROBEntryState.ISSUED

                        # Remove from issue queue
                        self.issue_queue.remove(entry)

                        issued.append((entry.rob_id, f"{fu_type}_{i}"))
                        self.stats["instructions_issued"] += 1

                        self.logger.debug(
                            f"Issued ROB[{entry.rob_id}] to {fu_type}_{i}"
                        )
                        break

        return issued

    def complete_instruction(
        self, rob_id: int, result: int | None = None, exception: str | None = None
    ) -> bool:
        """
        Complete instruction execution.

        Returns:
            True if completed successfully
        """
        if rob_id >= self.rob_size or not self.rob[rob_id]:
            return False

        rob_entry = self.rob[rob_id]
        rob_entry.state = ROBEntryState.COMPLETED  # type: ignore[union-attr]
        rob_entry.result = result  # type: ignore[union-attr]
        rob_entry.exception = exception  # type: ignore[union-attr]
        rob_entry.ready = True  # type: ignore[union-attr]
        rob_entry.complete_cycle = self.current_cycle  # type: ignore[union-attr]

        # Make destination register ready
        if rob_entry.physical_dest is not None:  # type: ignore[union-attr]
            self.physical_reg_ready[rob_entry.physical_dest] = True  # type: ignore[union-attr]
            if result is not None:
                self.physical_reg_file[rob_entry.physical_dest] = result  # type: ignore[union-attr]

        # Wake up dependent instructions
        self._wakeup_dependents(rob_entry.physical_dest)  # type: ignore[union-attr]

        self.stats["instructions_completed"] += 1
        self.logger.debug(f"Completed ROB[{rob_id}]")

        return True

    def commit_instructions(self) -> list[int]:
        """
        Commit instructions from ROB head in order.

        Returns:
            List of committed ROB IDs
        """
        committed = []

        while (
            self.rob_count > 0
            and self.rob[self.rob_head]
            and self.rob[self.rob_head].ready  # type: ignore[union-attr]
            and self.rob[self.rob_head].state == ROBEntryState.COMPLETED  # type: ignore[union-attr]
        ):
            rob_entry = self.rob[self.rob_head]

            # Handle exceptions
            if rob_entry.exception:  # type: ignore[union-attr]
                self._handle_exception(rob_entry)  # type: ignore[arg-type]
                break

            # Commit instruction
            rob_entry.state = ROBEntryState.COMMITTED  # type: ignore[union-attr]

            # Free old physical register
            if rob_entry.old_physical_dest is not None:  # type: ignore[union-attr]
                self.free_list.append(rob_entry.old_physical_dest)  # type: ignore[union-attr]

            committed.append(self.rob_head)
            self.stats["instructions_committed"] += 1

            # Clear ROB entry
            self.rob[self.rob_head] = None
            self.rob_head = (self.rob_head + 1) % self.rob_size
            self.rob_count -= 1

            self.logger.debug(f"Committed ROB[{self.rob_head - 1}]")

        return committed

    def handle_branch_misprediction(self, mispredicted_rob_id: int) -> int:
        """
        Handle branch misprediction by squashing younger instructions.

        Returns:
            Number of squashed instructions
        """
        squashed_count = 0

        # Squash all instructions younger than mispredicted branch
        current = (mispredicted_rob_id + 1) % self.rob_size

        while current != self.rob_tail:
            if self.rob[current]:
                rob_entry = self.rob[current]

                # Restore old register mapping
                if rob_entry.physical_dest is not None:
                    dest_reg = self._get_destination_register(rob_entry.instruction)
                    if dest_reg is not None and rob_entry.old_physical_dest is not None:
                        self.rat[dest_reg] = rob_entry.old_physical_dest

                    # Free allocated physical register
                    self.free_list.append(rob_entry.physical_dest)

                # Clear ROB entry
                self.rob[current] = None
                squashed_count += 1

            current = (current + 1) % self.rob_size

        # Update ROB tail
        self.rob_tail = (mispredicted_rob_id + 1) % self.rob_size
        self.rob_count -= squashed_count

        # Clear issue queue of squashed instructions
        self.issue_queue = [
            entry
            for entry in self.issue_queue
            if entry and entry.rob_id <= mispredicted_rob_id
        ]

        self.stats["branch_mispredictions"] += 1
        self.stats["squashed_instructions"] += squashed_count

        self.logger.debug(f"Squashed {squashed_count} instructions after misprediction")

        return squashed_count

    def advance_cycle(self) -> None:
        """Advance renaming unit by one cycle."""
        self.current_cycle += 1

        # Free functional units (simplified - assumes 1 cycle execution)
        for fu_type in self.fu_busy:
            for i in range(len(self.fu_busy[fu_type])):
                self.fu_busy[fu_type][i] = False

    def _get_source_registers(self, instruction: Instruction) -> list[int]:
        """Extract source registers from instruction."""
        src_regs = []

        if instruction.instruction_type == InstructionType.ARITHMETIC:
            if len(instruction.operands) >= 3:
                # R-type: [rd, rs, rt] -> sources are rs, rt
                src_regs.extend(
                    [
                        self._parse_register(instruction.operands[1]),
                        self._parse_register(instruction.operands[2]),
                    ]
                )
        elif instruction.instruction_type in [
            InstructionType.LOAD,
            InstructionType.STORE,
        ]:
            if len(instruction.operands) >= 2 and "(" in instruction.operands[1]:
                # Memory: [rt, "offset(rs)"] -> source is rs
                rs_part = instruction.operands[1].split("(")[1].rstrip(")")
                src_regs.append(self._parse_register(rs_part))
        elif instruction.instruction_type == InstructionType.BRANCH:
            if len(instruction.operands) >= 2:
                # Branch: [rs, rt, target] -> sources are rs, rt
                src_regs.extend(
                    [
                        self._parse_register(instruction.operands[0]),
                        self._parse_register(instruction.operands[1]),
                    ]
                )

        return src_regs

    def _get_destination_register(self, instruction: Instruction) -> int | None:
        """Extract destination register from instruction."""
        if instruction.destination:
            return self._parse_register(instruction.destination)
        elif (
            instruction.instruction_type == InstructionType.ARITHMETIC
            and instruction.operands
        ) or (
            instruction.instruction_type == InstructionType.LOAD
            and instruction.operands
        ):
            return self._parse_register(instruction.operands[0])

        return None

    def _parse_register(self, reg_str: str) -> int:
        """Parse register string to register number."""
        if reg_str.startswith("$"):
            reg_str = reg_str[1:]

        register_map = {
            "zero": 0,
            "at": 1,
            "v0": 2,
            "v1": 3,
            "a0": 4,
            "a1": 5,
            "a2": 6,
            "a3": 7,
            "t0": 8,
            "t1": 9,
            "t2": 10,
            "t3": 11,
            "t4": 12,
            "t5": 13,
            "t6": 14,
            "t7": 15,
            "s0": 16,
            "s1": 17,
            "s2": 18,
            "s3": 19,
            "s4": 20,
            "s5": 21,
            "s6": 22,
            "s7": 23,
            "t8": 24,
            "t9": 25,
            "k0": 26,
            "k1": 27,
            "gp": 28,
            "sp": 29,
            "fp": 30,
            "ra": 31,
        }

        if reg_str in register_map:
            return register_map[reg_str]
        elif reg_str.isdigit():
            return int(reg_str)
        else:
            return 0

    def _create_issue_queue_entry(
        self,
        rob_id: int,
        instruction: Instruction,
        src_regs: list[int],
        physical_dest: int | None,
    ) -> None:
        """Create issue queue entry for instruction."""
        # Map source registers to physical registers
        src1_physical = self.rat.get(src_regs[0]) if len(src_regs) > 0 else None
        src2_physical = self.rat.get(src_regs[1]) if len(src_regs) > 1 else None

        # Check if sources are ready
        src1_ready = src1_physical is None or self.physical_reg_ready[src1_physical]
        src2_ready = src2_physical is None or self.physical_reg_ready[src2_physical]

        # Determine functional unit type
        fu_type = self._get_functional_unit_type(instruction)

        entry = IssueQueueEntry(
            rob_id=rob_id,
            instruction=instruction,
            src1_ready=src1_ready,
            src2_ready=src2_ready,
            src1_physical=src1_physical,
            src2_physical=src2_physical,  # type: ignore[arg-type]
            dest_physical=physical_dest,
            functional_unit_type=fu_type,
            priority=rob_id,  # Older instructions have higher priority
        )

        self.issue_queue.append(entry)

    def _get_functional_unit_type(self, instruction: Instruction) -> str:
        """Determine required functional unit type."""
        if instruction.instruction_type == InstructionType.FLOATING_POINT:
            return "FPU"
        elif instruction.instruction_type in [
            InstructionType.LOAD,
            InstructionType.STORE,
        ]:
            return "LSU"
        else:
            return "ALU"

    def _wakeup_dependents(self, physical_reg: int | None) -> None:
        """Wake up instructions waiting for this physical register."""
        if physical_reg is None:
            return

        for entry in self.issue_queue:
            if entry.src1_physical == physical_reg:  # type: ignore[union-attr]
                entry.src1_ready = True  # type: ignore[union-attr]
                self.stats["raw_hazards_resolved"] += 1
            if entry.src2_physical == physical_reg:  # type: ignore[union-attr]
                entry.src2_ready = True  # type: ignore[union-attr]
                self.stats["raw_hazards_resolved"] += 1

    def _handle_exception(self, rob_entry: ROBEntry) -> None:
        """Handle instruction exception."""
        self.logger.error(f"Exception in ROB[{self.rob_head}]: {rob_entry.exception}")
        # In a real implementation, this would trigger exception handling

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive statistics."""
        stats = self.stats.copy()

        # Add utilization metrics
        stats.update(
            {
                "rob_utilization": self.rob_count / self.rob_size * 100,
                "issue_queue_utilization": len(self.issue_queue)
                / self.issue_queue_size
                * 100,
                "physical_reg_utilization": (
                    self.physical_registers - len(self.free_list)
                )
                / self.physical_registers
                * 100,
                "average_rob_occupancy": self.rob_count,
                "current_cycle": self.current_cycle,
            }
        )

        return stats

    def reset_stats(self) -> None:
        """Reset all statistics."""
        for key in self.stats:
            self.stats[key] = 0
