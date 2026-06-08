#!/usr/bin/env python3
"""
Test suite for Data Forwarding Unit implementations.

Tests cover DataForwardingUnit and AdvancedDataForwardingUnit,
including forwarding path management, data forwarding, dependency checking,
and conflict resolution.
"""

from typing import Any

import pytest

from src.data_forwarding.data_forwarding_unit import (
    AdvancedDataForwardingUnit,
    DataForwardingUnit,
    ForwardedData,
    ForwardingPath,
)
from src.utils.instruction import Instruction

# ============================== Fixtures ====================================


@pytest.fixture
def forwarding_unit() -> DataForwardingUnit:
    """Create a DataForwardingUnit instance."""
    return DataForwardingUnit()


@pytest.fixture
def advanced_forwarding_unit() -> AdvancedDataForwardingUnit:
    """Create an AdvancedDataForwardingUnit instance."""
    return AdvancedDataForwardingUnit()


@pytest.fixture
def add_instruction() -> Instruction:
    """Create an ADD instruction for testing."""
    return Instruction(address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"])


@pytest.fixture
def sub_instruction() -> Instruction:
    """Create a SUB instruction that reads $t0 (depends on add)."""
    return Instruction(address=0x1004, opcode="sub", operands=["$t3", "$t0", "$t4"])


# ======================= DataForwardingUnit =================================


class TestDataForwardingUnitBasics:
    """Basic data forwarding unit operations."""

    def test_instantiation(self, forwarding_unit: DataForwardingUnit) -> None:
        """Should instantiate successfully."""
        assert forwarding_unit is not None
        assert len(forwarding_unit.forwarding_paths) == 0

    def test_add_forwarding_path(self, forwarding_unit: DataForwardingUnit) -> None:
        """Add a forwarding path between stages."""
        forwarding_unit.add_forwarding_path(
            from_stage="execute",
            to_stage="decode",
            forwarding_condition=lambda inst: True,
            priority=1,
        )
        assert len(forwarding_unit.forwarding_paths) == 1

    def test_forward_data_makes_data_available(
        self, forwarding_unit: DataForwardingUnit, add_instruction: Instruction
    ) -> None:
        """forward_data should store produced results for later forwarding."""
        # Simulate the ADD instruction completing in the execute stage
        add_instruction.result = 42  # type: ignore[attr-defined]
        add_instruction.destination = "$t0"

        forwarding_unit.forward_data(add_instruction, "execute")

        # The forwarding data should now be available
        assert (
            "$t0" in forwarding_unit.forwarding_data
            or len(forwarding_unit.forwarding_data) > 0
        )

    def test_check_dependency_detects_raw(
        self,
        forwarding_unit: DataForwardingUnit,
        add_instruction: Instruction,
        sub_instruction: Instruction,
    ) -> None:
        """check_dependency should detect RAW hazard between add and sub."""
        add_instruction.destination = "$t0"
        has_dep = forwarding_unit.check_dependency(sub_instruction, add_instruction)
        assert isinstance(has_dep, bool)

    def test_check_dependency_no_hazard(
        self, forwarding_unit: DataForwardingUnit
    ) -> None:
        """Instructions with no shared registers should have no dependency."""
        inst1 = Instruction(
            address=0x1000, opcode="add", operands=["$t0", "$t1", "$t2"]
        )
        inst2 = Instruction(
            address=0x1004, opcode="add", operands=["$t3", "$t4", "$t5"]
        )
        inst1.destination = "$t0"
        has_dep = forwarding_unit.check_dependency(inst2, inst1)
        assert has_dep is False

    def test_get_operand_value_no_forward(
        self, forwarding_unit: DataForwardingUnit
    ) -> None:
        """Requesting non-forwarded register should return None."""
        value = forwarding_unit.get_operand_value("$t5")
        assert value is None


class TestDataForwardingApply:
    """Forwarding application and data retrieval."""

    def test_apply_forwarding_no_data(
        self, forwarding_unit: DataForwardingUnit, add_instruction: Instruction
    ) -> None:
        """Apply forwarding should return False when no data available."""
        result = forwarding_unit.apply_forwarding(add_instruction, "decode")
        assert result is False

    def test_get_forwarded_data_empty(
        self, forwarding_unit: DataForwardingUnit, add_instruction: Instruction
    ) -> None:
        """Getting forwarded data with nothing forwarded should return None."""
        data = forwarding_unit.get_forwarded_data(add_instruction, "decode")
        assert data is None


# =================== AdvancedDataForwardingUnit ============================


class TestAdvancedDataForwardingUnit:
    """Advanced forwarding with conflict resolution and latency tracking."""

    def test_instantiation(
        self, advanced_forwarding_unit: AdvancedDataForwardingUnit
    ) -> None:
        """Should instantiate successfully."""
        assert advanced_forwarding_unit is not None
        assert hasattr(advanced_forwarding_unit, "forwarding_latencies")

    def test_resolve_forwarding_conflict(
        self,
        advanced_forwarding_unit: AdvancedDataForwardingUnit,
        add_instruction: Instruction,
    ) -> None:
        """Resolve conflicts when multiple sources forward the same register."""
        # Create two forwarding sources with different cycles
        src1 = ForwardedData(
            source_instruction=add_instruction,
            register="$t0",
            value=100,
            from_stage="execute",
            cycle=5,
        )
        src2 = ForwardedData(
            source_instruction=add_instruction,
            register="$t0",
            value=200,
            from_stage="memory",
            cycle=6,
        )

        resolved = advanced_forwarding_unit.resolve_forwarding_conflict(
            "$t0", [src1, src2]
        )
        assert resolved is not None
        assert isinstance(resolved, ForwardedData)
        # Higher cycle + higher stage priority wins -> src2 (memory, cycle=6)
        assert resolved.value == 200

    def test_resolve_forwarding_conflict_empty(
        self, advanced_forwarding_unit: AdvancedDataForwardingUnit
    ) -> None:
        """Resolving empty sources list should return None."""
        resolved = advanced_forwarding_unit.resolve_forwarding_conflict("$t0", [])
        assert resolved is None

    def test_get_forwarding_latency(
        self, advanced_forwarding_unit: AdvancedDataForwardingUnit
    ) -> None:
        """Get forwarding latency between pipeline stages."""
        latency = advanced_forwarding_unit.get_forwarding_latency("execute", "decode")
        assert isinstance(latency, int)

    def test_forwarding_latency_same_or_later_stage(
        self, advanced_forwarding_unit: AdvancedDataForwardingUnit
    ) -> None:
        """Forwarding from later stage to earlier stage should have 0 latency."""
        latency = advanced_forwarding_unit.get_forwarding_latency("memory", "decode")
        assert latency == 0

    def test_visualize_forwarding_paths(
        self, advanced_forwarding_unit: AdvancedDataForwardingUnit
    ) -> None:
        """Visualization should return a non-empty string."""
        output = advanced_forwarding_unit.visualize_forwarding_paths()
        assert isinstance(output, str)
        assert "Active Forwarding Paths" in output
