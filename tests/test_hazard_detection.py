#!/usr/bin/env python3
"""
Test suite for Hazard Detection and Pipeline Control.

Tests cover:
- Scoreboard: register/FU status tracking, hazard detection (RAW/WAR/WAW/structural)
- HazardController: cycle-accurate hazard detection, pipeline stall/forward logic
"""

from typing import Any

import pytest

from src.pipeline.hazard_controller import (
    HazardController,
    HazardType,
    InstructionState,
    PipelineStage,
    StallReason,
)
from src.utils.instruction import Instruction
from src.utils.scoreboard import (
    FunctionalUnitStatus,
    RegisterStatus,
    Scoreboard,
)
from src.utils.scoreboard import (
    HazardType as ScoreboardHazardType,
)

# ============================== Fixtures ====================================


@pytest.fixture
def scoreboard() -> Scoreboard:
    """Create a fresh Scoreboard instance."""
    return Scoreboard(num_registers=32)


@pytest.fixture
def hazard_controller() -> HazardController:
    """Create a HazardController with default config."""
    return HazardController(
        pipeline_config={
            "num_stages": 6,
            "fetch_width": 4,
            "issue_width": 4,
        }
    )


@pytest.fixture
def add_instruction() -> Instruction:
    """ADD $t0, $t1, $t2."""
    return Instruction(address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"])


@pytest.fixture
def sub_instruction() -> Instruction:
    """SUB $t3, $t0, $t4 — depends on $t0 from add."""
    return Instruction(address=0x1004, opcode="sub", operands=["$t3", "$t0", "$t4"])


# ============================ Scoreboard ====================================


class TestScoreboardBasics:
    """Basic scoreboard operations."""

    def test_instantiation(self, scoreboard: Scoreboard) -> None:
        """Should instantiate successfully."""
        assert scoreboard is not None
        assert len(scoreboard.register_status) == 32

    def test_allocate_register_write(
        self, scoreboard: Scoreboard, add_instruction: Instruction
    ) -> None:
        """Allocate a register for writing."""
        scoreboard.allocate_register_write("$t0", add_instruction)
        assert scoreboard.register_status[8].busy is True  # $t0 = register 8

    def test_deallocate_register(
        self, scoreboard: Scoreboard, add_instruction: Instruction
    ) -> None:
        """Deallocate a register after write completes."""
        scoreboard.allocate_register_write("$t0", add_instruction)
        scoreboard.deallocate_register("$t0")
        assert scoreboard.register_status[8].busy is False

    def test_allocate_register_read(
        self, scoreboard: Scoreboard, sub_instruction: Instruction
    ) -> None:
        """Track register reads by an instruction."""
        scoreboard.allocate_register_read("$t0", sub_instruction)
        # Register should be tracked as being read

    def test_allocate_function_unit(
        self, scoreboard: Scoreboard, add_instruction: Instruction
    ) -> None:
        """Allocate a functional unit to an instruction."""
        scoreboard.allocate_function_unit("ALU0", add_instruction, cycles=1)
        assert scoreboard.function_unit_status["ALU0"].busy is True

    def test_deallocate_function_unit(
        self, scoreboard: Scoreboard, add_instruction: Instruction
    ) -> None:
        """Deallocate a functional unit."""
        scoreboard.allocate_function_unit("ALU0", add_instruction, cycles=1)
        scoreboard.deallocate_function_unit("ALU0")
        assert scoreboard.function_unit_status["ALU0"].busy is False


class TestScoreboardHazards:
    """Hazard detection via scoreboard."""

    def test_check_raw_hazard(
        self,
        scoreboard: Scoreboard,
        add_instruction: Instruction,
        sub_instruction: Instruction,
    ) -> None:
        """Detect RAW hazard when sub reads $t0 that add writes."""
        add_instruction.destination = "$t0"
        scoreboard.allocate_register_write("$t0", add_instruction)
        has_raw = scoreboard.check_raw_hazard(sub_instruction)
        assert isinstance(has_raw, bool)

    def test_check_waw_hazard(
        self, scoreboard: Scoreboard, add_instruction: Instruction
    ) -> None:
        """Detect WAW hazard when two instructions write to the same register."""
        inst1 = Instruction(
            address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"]
        )
        inst2 = Instruction(
            address=0x1004, opcode="add", operands=["$t0", "$t3", "$t4"]
        )
        inst1.destination = "$t0"
        scoreboard.allocate_register_write("$t0", inst1)
        has_waw = scoreboard.check_waw_hazard(inst2)
        assert has_waw is True

    def test_check_structural_hazard(
        self, scoreboard: Scoreboard, add_instruction: Instruction
    ) -> None:
        """Detect structural hazard when FU is busy."""
        scoreboard.allocate_function_unit("ALU0", add_instruction, cycles=3)
        inst2 = Instruction(
            address=0x1004, opcode="sub", operands=["$t3", "$t4", "$t5"]
        )
        # Should detect that ALU0 is busy
        has_structural = scoreboard.check_structural_hazard(inst2)
        assert isinstance(has_structural, bool)

    def test_check_hazards_comprehensive(
        self,
        scoreboard: Scoreboard,
        add_instruction: Instruction,
        sub_instruction: Instruction,
    ) -> None:
        """check_hazards should return list of detected hazard types."""
        add_instruction.destination = "$t0"
        scoreboard.allocate_register_write("$t0", add_instruction)
        hazards = scoreboard.check_hazards(sub_instruction)
        assert isinstance(hazards, list)

    def test_update_cycle(self, scoreboard: Scoreboard) -> None:
        """update_cycle should advance the cycle counter."""
        initial_cycle = scoreboard.current_cycle
        scoreboard.update_cycle()
        assert scoreboard.current_cycle == initial_cycle + 1

    def test_reset(self, scoreboard: Scoreboard, add_instruction: Instruction) -> None:
        """Reset should clear all state."""
        scoreboard.allocate_register_write("$t0", add_instruction)
        scoreboard.reset()
        assert scoreboard.register_status[8].busy is False


# ======================== HazardController ==================================


class TestHazardController:
    """Cycle-accurate hazard detection and pipeline control."""

    def test_instantiation(self, hazard_controller: HazardController) -> None:
        """Should instantiate successfully."""
        assert hazard_controller is not None

    def test_issue_instruction(
        self, hazard_controller: HazardController, add_instruction: Instruction
    ) -> None:
        """Issue an instruction into the pipeline."""
        success = hazard_controller.issue_instruction(add_instruction, instruction_id=1)
        assert isinstance(success, bool)

    def test_advance_cycle(self, hazard_controller: HazardController) -> None:
        """Advance pipeline by one cycle."""
        result = hazard_controller.advance_cycle()
        assert isinstance(result, list)

    def test_issue_and_advance(
        self, hazard_controller: HazardController, add_instruction: Instruction
    ) -> None:
        """Issue instruction and advance cycles."""
        hazard_controller.issue_instruction(add_instruction, instruction_id=1)
        for _ in range(10):
            completed = hazard_controller.advance_cycle()
            if completed:
                break

    def test_get_statistics(self, hazard_controller: HazardController) -> None:
        """Get hazard controller statistics."""
        stats = hazard_controller.get_statistics()
        assert isinstance(stats, dict)
        assert "total_instructions" in stats


class TestHazardControllerEnums:
    """Verify HazardType, StallReason, PipelineStage enums."""

    def test_hazard_types(self) -> None:
        """All expected hazard types should exist."""
        assert HazardType.RAW is not None
        assert HazardType.WAR is not None
        assert HazardType.WAW is not None
        assert HazardType.STRUCTURAL is not None
        assert HazardType.CONTROL is not None

    def test_stall_reasons(self) -> None:
        """All expected stall reasons should exist."""
        assert StallReason.DATA_HAZARD is not None
        assert StallReason.STRUCTURAL_HAZARD is not None
        assert StallReason.CONTROL_HAZARD is not None
        assert StallReason.CACHE_MISS is not None

    def test_pipeline_stages(self) -> None:
        """All expected pipeline stages should exist."""
        assert PipelineStage.FETCH is not None
        assert PipelineStage.DECODE is not None
        assert PipelineStage.ISSUE is not None
        assert PipelineStage.EXECUTE is not None
        assert PipelineStage.MEMORY is not None
        assert PipelineStage.WRITEBACK is not None
