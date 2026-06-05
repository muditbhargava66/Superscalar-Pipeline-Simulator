#!/usr/bin/env python3

"""
Enhanced Hazard Detection and Pipeline Control

This module provides comprehensive hazard detection, pipeline stall logic,
and control mechanisms for cycle-accurate simulation.
"""

from enum import Enum
import logging
from typing import Any, List, Optional

# Handle imports for both package and direct execution
try:
    from ..utils.instruction import Instruction, InstructionType
except (ImportError, ValueError):
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.instruction import Instruction, InstructionType


class HazardType(Enum):
    """Types of pipeline hazards."""

    RAW = "read_after_write"  # True data dependency
    WAR = "write_after_read"  # Anti-dependency
    WAW = "write_after_write"  # Output dependency
    STRUCTURAL = "structural"  # Resource conflict
    CONTROL = "control"  # Branch/jump hazard


class StallReason(Enum):
    """Reasons for pipeline stalls."""

    DATA_HAZARD = "data_hazard"
    STRUCTURAL_HAZARD = "structural_hazard"
    CONTROL_HAZARD = "control_hazard"
    CACHE_MISS = "cache_miss"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    BRANCH_MISPREDICTION = "branch_misprediction"


class PipelineStage(Enum):
    """Pipeline stages."""

    FETCH = "fetch"
    DECODE = "decode"
    ISSUE = "issue"
    EXECUTE = "execute"
    MEMORY = "memory"
    WRITEBACK = "writeback"


class InstructionState:
    """Tracks instruction state through pipeline."""

    def __init__(self, instruction: Instruction, issue_cycle: int):
        self.instruction = instruction
        self.issue_cycle = issue_cycle
        self.current_stage = PipelineStage.FETCH
        self.stage_entry_cycle = issue_cycle
        self.completion_cycle = -1
        self.stalled = False
        self.stall_reason: StallReason | None = None
        self.stall_cycles = 0

        # Resource allocation
        self.allocated_resources: set[str] = set()

        # Dependency tracking
        self.dependencies: list[int] = []  # Instructions this depends on
        self.dependents: list[int] = []  # Instructions that depend on this


class HazardController:
    """
    Comprehensive hazard detection and pipeline control system.

    Features:
    - Cycle-accurate hazard detection
    - Pipeline stall and forwarding logic
    - Resource conflict resolution
    - Branch prediction integration
    - Performance monitoring
    """

    def __init__(self, pipeline_config: dict[str, Any]):
        """
        Initialize hazard controller.

        Args:
            pipeline_config: Pipeline configuration parameters
        """
        self.config = pipeline_config
        self.logger = logging.getLogger(__name__)

        # Pipeline state
        self.current_cycle = 0
        self.instructions_in_flight: dict[int, InstructionState] = {}
        self.completed_instructions: list[InstructionState] = []

        # Resource tracking
        execute_units = pipeline_config.get("execute_units", {})
        self.functional_units = {
            "ALU": execute_units.get("ALU", {}).get(
                "count", pipeline_config.get("alu_units", 2)
            ),
            "FPU": execute_units.get("FPU", {}).get(
                "count", pipeline_config.get("fpu_units", 1)
            ),
            "LSU": execute_units.get("LSU", {}).get(
                "count", pipeline_config.get("lsu_units", 1)
            ),
            "BRANCH": execute_units.get("BRANCH", {}).get(
                "count", pipeline_config.get("branch_units", 1)
            ),
        }
        self.allocated_units: dict[str, set[int]] = {
            unit: set() for unit in self.functional_units
        }

        # Register tracking for dependency analysis
        self.register_producers: dict[int, int] = {}  # reg -> instruction_id
        self.register_consumers: dict[int, list[int]] = {}  # reg -> [instruction_ids]

        # Pipeline stage occupancy
        self.stage_occupancy: dict[PipelineStage, set[int]] = {
            stage: set() for stage in PipelineStage
        }

        # Cumulative stage occupancy tracking (for utilization calculation)
        self.stage_occupancy_cycles: dict[PipelineStage, int] = dict.fromkeys(
            PipelineStage, 0
        )

        # Statistics
        self.stats = {
            "total_instructions": 0,
            "total_cycles": 0,
            "stall_cycles": 0,
            "hazards_detected": {
                HazardType.RAW: 0,
                HazardType.WAR: 0,
                HazardType.WAW: 0,
                HazardType.STRUCTURAL: 0,
                HazardType.CONTROL: 0,
            },
            "stalls_by_reason": dict.fromkeys(StallReason, 0),
            "forwarding_opportunities": 0,
            "forwarding_used": 0,
        }

        # Forwarding paths configuration
        self.forwarding_paths = {
            (PipelineStage.EXECUTE, PipelineStage.EXECUTE): 0,  # EX->EX (bypass)
            (PipelineStage.MEMORY, PipelineStage.EXECUTE): 1,  # MEM->EX
            (PipelineStage.WRITEBACK, PipelineStage.EXECUTE): 2,  # WB->EX
        }

    def issue_instruction(self, instruction: Instruction, instruction_id: int) -> bool:
        """
        Attempt to issue an instruction into the pipeline.

        Args:
            instruction: Instruction to issue
            instruction_id: Unique instruction identifier

        Returns:
            True if instruction was issued, False if stalled
        """
        # Check for hazards
        hazards = self._detect_hazards(instruction, instruction_id)

        if hazards:
            # Handle hazards
            can_issue = self._resolve_hazards(instruction, instruction_id, hazards)
            if not can_issue:
                return False

        # Check resource availability
        if not self._check_resources(instruction):
            self.stats["stalls_by_reason"][StallReason.RESOURCE_UNAVAILABLE] += 1  # type: ignore[index]
            return False

        # Issue instruction - start at ISSUE stage since fetch/decode already happened
        instr_state = InstructionState(instruction, self.current_cycle)
        instr_state.current_stage = PipelineStage.ISSUE  # Start at ISSUE stage
        instr_state.stage_entry_cycle = self.current_cycle
        self.instructions_in_flight[instruction_id] = instr_state

        # Allocate resources
        self._allocate_resources(instruction, instruction_id)

        # Update dependency tracking
        self._update_dependencies(instruction, instruction_id)

        self.stats["total_instructions"] += 1  # type: ignore[operator]
        self.logger.debug(
            f"Issued instruction {instruction.opcode} (ID: {instruction_id}) at cycle {self.current_cycle}"
        )

        return True

    def advance_cycle(self) -> list[tuple[int, InstructionState]]:
        """
        Advance pipeline by one cycle.

        Returns:
            List of (instruction_id, state) tuples for completed instructions
        """
        self.current_cycle += 1
        self.stats["total_cycles"] += 1  # type: ignore[operator]
        completed = []

        # Track stage occupancy for this cycle
        for stage, instr_ids in self.stage_occupancy.items():
            self.stage_occupancy_cycles[stage] += len(instr_ids)

        # Process all instructions in flight
        for instr_id, instr_state in list(self.instructions_in_flight.items()):
            # Check if instruction can advance
            if self._can_advance_stage(instr_state):
                self._advance_instruction_stage(instr_state)

                # Check if instruction completed
                if instr_state.current_stage == PipelineStage.WRITEBACK:
                    # Complete instruction
                    instr_state.completion_cycle = self.current_cycle
                    completed.append((instr_id, instr_state))

                    # Release resources
                    self._release_resources(instr_state.instruction, instr_id)

                    # Move to completed list
                    self.completed_instructions.append(instr_state)
                    del self.instructions_in_flight[instr_id]

                    self.logger.debug(
                        f"Completed instruction {instr_state.instruction.opcode} (ID: {instr_id})"
                    )
            else:
                # Instruction stalled
                instr_state.stalled = True
                instr_state.stall_cycles += 1
                self.stats["stall_cycles"] += 1  # type: ignore[operator]

        return completed

    def _detect_hazards(
        self, instruction: Instruction, instruction_id: int
    ) -> list[tuple[HazardType, int]]:
        """
        Detect all hazards for the given instruction.

        Returns:
            List of (hazard_type, conflicting_instruction_id) tuples
        """
        hazards = []

        # Get instruction operands
        src_regs = self._get_source_registers(instruction)
        dst_regs = self._get_destination_registers(instruction)

        # Check for data hazards
        for src_reg in src_regs:
            if src_reg in self.register_producers:
                producer_id = self.register_producers[src_reg]
                producer_state = self.instructions_in_flight.get(producer_id)

                if producer_state and not self._can_forward(
                    producer_state, instruction
                ):
                    hazards.append((HazardType.RAW, producer_id))
                    self.stats["hazards_detected"][HazardType.RAW] += 1  # type: ignore[index]

        # Check for WAR hazards (anti-dependencies)
        for dst_reg in dst_regs:
            if dst_reg in self.register_consumers:
                for consumer_id in self.register_consumers[dst_reg]:
                    consumer_state = self.instructions_in_flight.get(consumer_id)
                    if consumer_state and consumer_state.current_stage in [
                        PipelineStage.FETCH,
                        PipelineStage.DECODE,
                    ]:
                        hazards.append((HazardType.WAR, consumer_id))
                        self.stats["hazards_detected"][HazardType.WAR] += 1  # type: ignore[index]

        # Check for WAW hazards (output dependencies)
        for dst_reg in dst_regs:
            if dst_reg in self.register_producers:
                producer_id = self.register_producers[dst_reg]
                producer_state = self.instructions_in_flight.get(producer_id)
                if (
                    producer_state
                    and producer_state.current_stage != PipelineStage.WRITEBACK
                ):
                    hazards.append((HazardType.WAW, producer_id))
                    self.stats["hazards_detected"][HazardType.WAW] += 1  # type: ignore[index]

        # Check for structural hazards
        required_unit = self._get_required_functional_unit(instruction)
        if (
            required_unit
            and len(self.allocated_units[required_unit])
            >= self.functional_units[required_unit]
        ):
            hazards.append((HazardType.STRUCTURAL, -1))
            self.stats["hazards_detected"][HazardType.STRUCTURAL] += 1  # type: ignore[index]

        # Check for control hazards
        if instruction.instruction_type in [
            InstructionType.BRANCH,
            InstructionType.JUMP,
        ]:
            # Check if there are unresolved branches
            for other_id, other_state in self.instructions_in_flight.items():
                if other_state.instruction.instruction_type in [
                    InstructionType.BRANCH,
                    InstructionType.JUMP,
                ] and other_state.current_stage in [
                    PipelineStage.FETCH,
                    PipelineStage.DECODE,
                    PipelineStage.EXECUTE,
                ]:
                    hazards.append((HazardType.CONTROL, other_id))
                    self.stats["hazards_detected"][HazardType.CONTROL] += 1  # type: ignore[index]
                    break

        return hazards

    def _resolve_hazards(
        self,
        instruction: Instruction,
        instruction_id: int,
        hazards: list[tuple[HazardType, int]],
    ) -> bool:
        """
        Attempt to resolve detected hazards.

        Returns:
            True if hazards can be resolved and instruction can issue
        """
        for hazard_type, conflicting_id in hazards:
            if hazard_type == HazardType.RAW:
                # Check if forwarding is possible
                if conflicting_id in self.instructions_in_flight:
                    conflicting_state = self.instructions_in_flight[conflicting_id]
                    if self._can_forward(conflicting_state, instruction):
                        self.stats["forwarding_used"] += 1  # type: ignore[operator]
                        continue

                # Cannot resolve, must stall
                self.stats["stalls_by_reason"][StallReason.DATA_HAZARD] += 1  # type: ignore[index]
                return False

            elif hazard_type == HazardType.STRUCTURAL:
                # Cannot resolve structural hazards immediately
                self.stats["stalls_by_reason"][StallReason.STRUCTURAL_HAZARD] += 1  # type: ignore[index]
                return False

            elif hazard_type == HazardType.CONTROL:
                # Control hazards require branch resolution
                self.stats["stalls_by_reason"][StallReason.CONTROL_HAZARD] += 1  # type: ignore[index]
                return False

            # WAR and WAW hazards can often be resolved by renaming (simplified)

        return True

    def _can_forward(
        self, producer_state: InstructionState, consumer_instruction: Instruction
    ) -> bool:
        """
        Check if data can be forwarded from producer to consumer.

        Args:
            producer_state: State of producing instruction
            consumer_instruction: Consuming instruction

        Returns:
            True if forwarding is possible
        """
        # Check if producer is in a stage that allows forwarding
        if producer_state.current_stage in [
            PipelineStage.EXECUTE,
            PipelineStage.MEMORY,
            PipelineStage.WRITEBACK,
        ]:
            # Check forwarding path availability
            forwarding_path = (producer_state.current_stage, PipelineStage.EXECUTE)
            if forwarding_path in self.forwarding_paths:
                self.stats["forwarding_opportunities"] += 1  # type: ignore[operator]
                return True

        return False

    def _can_advance_stage(self, instr_state: InstructionState) -> bool:
        """Check if instruction can advance to next pipeline stage."""
        current_stage = instr_state.current_stage

        # Check stage-specific advancement conditions
        if current_stage == PipelineStage.FETCH:
            # Can always advance from fetch to decode
            return True

        elif current_stage == PipelineStage.DECODE:
            # Check if issue stage has capacity
            return len(self.stage_occupancy[PipelineStage.ISSUE]) < self.config.get(
                "issue_width", 4
            )

        elif current_stage == PipelineStage.ISSUE:
            # Instruction already allocated resources when issued
            return True

        elif current_stage == PipelineStage.EXECUTE:
            # Check if instruction has completed execution
            cycles_in_stage = self.current_cycle - instr_state.stage_entry_cycle
            return cycles_in_stage >= instr_state.instruction.latency

        elif current_stage == PipelineStage.MEMORY:
            # Memory stage completion depends on cache behavior
            return True  # Simplified

        elif current_stage == PipelineStage.WRITEBACK:
            # Already in final stage
            return True

        return False  # type: ignore[unreachable]

    def _advance_instruction_stage(self, instr_state: InstructionState) -> None:
        """Advance instruction to next pipeline stage."""
        # Remove from current stage
        if instr_state.current_stage in self.stage_occupancy:
            self.stage_occupancy[instr_state.current_stage].discard(id(instr_state))

        # Advance to next stage
        stage_order = [
            PipelineStage.FETCH,
            PipelineStage.DECODE,
            PipelineStage.ISSUE,
            PipelineStage.EXECUTE,
            PipelineStage.MEMORY,
            PipelineStage.WRITEBACK,
        ]

        current_index = stage_order.index(instr_state.current_stage)
        if current_index < len(stage_order) - 1:
            instr_state.current_stage = stage_order[current_index + 1]
            instr_state.stage_entry_cycle = self.current_cycle

            # Add to new stage
            self.stage_occupancy[instr_state.current_stage].add(id(instr_state))

        # Reset stall state
        instr_state.stalled = False
        instr_state.stall_reason = None

    def _check_resources(self, instruction: Instruction) -> bool:
        """Check if required resources are available."""
        required_unit = self._get_required_functional_unit(instruction)
        if required_unit:
            return (
                len(self.allocated_units[required_unit])
                < self.functional_units[required_unit]
            )
        return True

    def _allocate_resources(
        self, instruction: Instruction, instruction_id: int
    ) -> None:
        """Allocate resources for instruction execution."""
        required_unit = self._get_required_functional_unit(instruction)
        if required_unit:
            self.allocated_units[required_unit].add(instruction_id)

    def _release_resources(self, instruction: Instruction, instruction_id: int) -> None:
        """Release resources used by instruction."""
        required_unit = self._get_required_functional_unit(instruction)
        if required_unit:
            self.allocated_units[required_unit].discard(instruction_id)

    def _update_dependencies(
        self, instruction: Instruction, instruction_id: int
    ) -> None:
        """Update register dependency tracking."""
        src_regs = self._get_source_registers(instruction)
        dst_regs = self._get_destination_registers(instruction)

        # Update consumers for source registers
        for src_reg in src_regs:
            if src_reg not in self.register_consumers:
                self.register_consumers[src_reg] = []
            self.register_consumers[src_reg].append(instruction_id)

        # Update producers for destination registers
        for dst_reg in dst_regs:
            self.register_producers[dst_reg] = instruction_id

    def _get_source_registers(self, instruction: Instruction) -> list[int]:
        """Get list of source registers for instruction."""
        src_regs = []

        # Extract source registers from operands based on instruction type
        if instruction.instruction_type == InstructionType.ARITHMETIC:
            # For R-type: operands = [rd, rs, rt] -> sources are rs, rt
            if len(instruction.operands) >= 3:
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
            # For memory: operands = [rt, "offset(rs)"] -> source is rs (and rt for store)
            if len(instruction.operands) >= 2:
                # Parse "offset(rs)" format
                addr_operand = instruction.operands[1]
                if "(" in addr_operand:
                    rs_part = addr_operand.split("(")[1].rstrip(")")
                    src_regs.append(self._parse_register(rs_part))

                # For STORE, the register being stored (rt) is also a source
                if instruction.instruction_type == InstructionType.STORE:
                    src_regs.append(self._parse_register(instruction.operands[0]))
        elif instruction.instruction_type == InstructionType.BRANCH:
            # For branch: operands = [rs, rt, target] -> sources are rs, rt
            if len(instruction.operands) >= 2:
                src_regs.extend(
                    [
                        self._parse_register(instruction.operands[0]),
                        self._parse_register(instruction.operands[1]),
                    ]
                )

        return src_regs

    def _get_destination_registers(self, instruction: Instruction) -> list[int]:
        """Get list of destination registers for instruction."""
        dst_regs = []

        # Extract destination register from operands or destination field
        if instruction.destination:
            dst_regs.append(self._parse_register(instruction.destination))
        elif (
            instruction.instruction_type == InstructionType.ARITHMETIC
            and instruction.operands
        ):
            # For R-type: operands = [rd, rs, rt] -> destination is rd
            dst_regs.append(self._parse_register(instruction.operands[0]))
        elif (
            instruction.instruction_type == InstructionType.LOAD
            and instruction.operands
        ):
            # For load: operands = [rt, "offset(rs)"] -> destination is rt
            dst_regs.append(self._parse_register(instruction.operands[0]))

        return dst_regs

    def _parse_register(self, reg_str: str) -> int:
        """Parse register string to register number."""
        if reg_str.startswith("$"):
            reg_str = reg_str[1:]

        # Handle named registers
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
            return 0  # Default to $zero for unknown registers

    def _get_required_functional_unit(self, instruction: Instruction) -> str | None:
        """Get required functional unit type for instruction."""
        if instruction.instruction_type == InstructionType.FLOATING_POINT:
            return "FPU"
        elif instruction.instruction_type in [
            InstructionType.LOAD,
            InstructionType.STORE,
        ]:
            return "LSU"
        elif instruction.instruction_type in [
            InstructionType.BRANCH,
            InstructionType.JUMP,
        ]:
            return "BRANCH"
        elif instruction.instruction_type in [
            InstructionType.ARITHMETIC,
            InstructionType.LOGICAL,
            InstructionType.COMPARISON,
        ]:
            return "ALU"
        return None

    def get_statistics(self) -> dict[str, Any]:
        """Get hazard controller statistics."""
        stats = self.stats.copy()

        # Calculate derived statistics
        if stats["total_instructions"] > 0:  # type: ignore[operator]
            stats["average_stall_cycles"] = (
                stats["stall_cycles"] / stats["total_instructions"]  # type: ignore[operator]
            )
            stats["stall_percentage"] = (
                stats["stall_cycles"] / stats["total_cycles"]  # type: ignore[operator]
            ) * 100

        if stats["forwarding_opportunities"] > 0:  # type: ignore[operator]
            stats["forwarding_efficiency"] = (
                stats["forwarding_used"] / stats["forwarding_opportunities"]  # type: ignore[operator]
            ) * 100

        # Add current state information
        stats["instructions_in_flight"] = len(self.instructions_in_flight)
        stats["resource_utilization"] = {
            unit: len(allocated) / capacity
            for unit, allocated in self.allocated_units.items()
            for capacity in [self.functional_units[unit]]
        }

        # Add stage occupancy statistics (cumulative cycles each stage was occupied)
        stats["stage_occupancy"] = {
            stage.value: self.stage_occupancy_cycles[stage] for stage in PipelineStage
        }
        stats["instructions_completed"] = len(self.completed_instructions)

        return stats

    def reset_statistics(self) -> None:
        """Reset all statistics."""
        self.stats = {
            "total_instructions": 0,
            "total_cycles": 0,
            "stall_cycles": 0,
            "hazards_detected": {
                HazardType.RAW: 0,
                HazardType.WAR: 0,
                HazardType.WAW: 0,
                HazardType.STRUCTURAL: 0,
                HazardType.CONTROL: 0,
            },
            "stalls_by_reason": dict.fromkeys(StallReason, 0),
            "forwarding_opportunities": 0,
            "forwarding_used": 0,
        }
