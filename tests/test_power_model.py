#!/usr/bin/env python3
"""
Test suite for Power Model implementations.

Covers ComponentPowerModel and ProcessorPowerModel: dynamic/static power
calculation, DVFS, clock gating, power gating, thermal modeling, energy
tracking, and comprehensive statistics reporting.
"""

from itertools import count

import pytest

from src.profiling.power_model import (
    ComponentPowerModel,
    PowerDomain,
    PowerEvent,
    PowerParameters,
    PowerState,
    ProcessorPowerModel,
)
from src.utils.instruction import Instruction, InstructionType

# ============================== Fixtures ====================================


@pytest.fixture
def power_params() -> PowerParameters:
    """Standard power parameters mimicking a 45nm technology node."""
    return PowerParameters(
        voltage=1.0,
        frequency=2.0,  # GHz
        switching_capacitance=100.0,  # pF
        leakage_current=10.0,  # nA
        base_leakage_current=10.0,
        activity_factor=0.1,
    )


@pytest.fixture
def component_model(power_params: PowerParameters) -> ComponentPowerModel:
    return ComponentPowerModel(name="alu", params=power_params)


@pytest.fixture
def processor_model() -> ProcessorPowerModel:
    return ProcessorPowerModel(
        config={
            "dvfs_enabled": True,
            "clock_gating_enabled": True,
            "power_gating_enabled": True,
            "ambient_temp": 25.0,
            "thermal_resistance": 1.0,
        }
    )


_instruction_counter = count(1)


def _make_instruction(opcode: str, itype: InstructionType) -> Instruction:
    """Helper to build a minimal Instruction for power tracking."""
    return Instruction(
        address=next(_instruction_counter) * 4,
        opcode=opcode,
        operands=[],
        instruction_type=itype,
    )


# ==================== PowerParameters dataclass =============================


class TestPowerParameters:
    """Verify the PowerParameters dataclass defaults and custom values."""

    def test_defaults(self) -> None:
        params = PowerParameters()
        assert params.technology_node == 45.0
        assert params.voltage == 1.0
        assert params.frequency == 2.0
        assert params.switching_capacitance == 100.0
        assert params.activity_factor == 0.1

    def test_custom_values(self, power_params: PowerParameters) -> None:
        assert power_params.voltage == 1.0
        assert power_params.frequency == 2.0
        assert power_params.switching_capacitance == 100.0
        assert power_params.leakage_current == 10.0


# ==================== Power Enums ===========================================


class TestPowerEnums:
    """Verify power-related enums have expected members."""

    def test_power_state_members(self) -> None:
        assert PowerState.ACTIVE.value == "active"
        assert PowerState.IDLE.value == "idle"
        assert PowerState.SLEEP.value == "sleep"
        assert PowerState.OFF.value == "off"

    def test_power_domain_members(self) -> None:
        assert PowerDomain.CORE.value == "core"
        assert PowerDomain.CACHE_L1I.value == "l1i_cache"
        assert PowerDomain.CACHE_L1D.value == "l1d_cache"
        assert PowerDomain.CACHE_L2.value == "l2_cache"


# ==================== ComponentPowerModel ===================================


class TestComponentPowerModel:
    """Per-component power model: dynamic/static power, activity tracking."""

    def test_instantiation(self, component_model: ComponentPowerModel) -> None:
        assert component_model is not None
        assert component_model.name == "alu"

    def test_initial_state(self, component_model: ComponentPowerModel) -> None:
        assert component_model.current_state == PowerState.IDLE
        assert component_model.total_cycles == 0
        assert component_model.active_cycles == 0
        assert component_model.dynamic_energy == 0.0
        assert component_model.static_energy == 0.0

    def test_calculate_dynamic_power(
        self, component_model: ComponentPowerModel
    ) -> None:
        power = component_model.calculate_dynamic_power()
        assert isinstance(power, float)
        assert power >= 0.0

    def test_dynamic_power_scales_with_activity(
        self, component_model: ComponentPowerModel
    ) -> None:
        low = component_model.calculate_dynamic_power(activity_factor=0.1)
        high = component_model.calculate_dynamic_power(activity_factor=0.9)
        assert high > low

    def test_calculate_static_power(self, component_model: ComponentPowerModel) -> None:
        power = component_model.calculate_static_power()
        assert isinstance(power, float)
        assert power >= 0.0

    def test_record_activity(self, component_model: ComponentPowerModel) -> None:
        component_model.record_activity(
            cycle=1, event_type="execute", activity_factor=0.5
        )
        assert component_model.active_cycles >= 1
        assert component_model.dynamic_energy > 0.0

    def test_set_power_state(self, component_model: ComponentPowerModel) -> None:
        component_model.set_power_state(PowerState.ACTIVE, cycle=0)
        assert component_model.current_state == PowerState.ACTIVE

    def test_get_total_energy(self, component_model: ComponentPowerModel) -> None:
        # Record some activity so energy accumulates
        component_model.record_activity(1, "test", 0.5)
        total = component_model.get_total_energy()
        assert total > 0.0

    def test_get_stats(self, component_model: ComponentPowerModel) -> None:
        stats = component_model.get_stats()
        assert "component" in stats
        assert stats["component"] == "alu"
        assert "total_energy_pJ" in stats
        assert "average_power_mW" in stats

    def test_get_average_power_initial(
        self, component_model: ComponentPowerModel
    ) -> None:
        # Before any cycles, average power should be 0
        avg = component_model.get_average_power()
        assert avg == 0.0


# ==================== ProcessorPowerModel ===================================


class TestProcessorPowerModel:
    """Complete processor power model with DVFS, thermal, and gating."""

    def test_instantiation(self, processor_model: ProcessorPowerModel) -> None:
        assert processor_model is not None
        assert processor_model.current_cycle == 0
        assert "core" in processor_model.components
        assert "alu" in processor_model.components

    def test_advance_cycle(self, processor_model: ProcessorPowerModel) -> None:
        processor_model.advance_cycle()
        assert processor_model.current_cycle == 1

    def test_record_instruction_execution(
        self, processor_model: ProcessorPowerModel
    ) -> None:
        instr = _make_instruction("add", InstructionType.ARITHMETIC)
        processor_model.record_instruction_execution(instr, "alu_0")
        assert processor_model.instructions_executed == 1

    def test_record_cache_access(self, processor_model: ProcessorPowerModel) -> None:
        # cache_level expects digit like "1" for L1
        processor_model.record_cache_access(cache_level="1", hit=True)
        processor_model.record_cache_access(cache_level="1", hit=False)
        # No exception means success

    def test_record_memory_access(self, processor_model: ProcessorPowerModel) -> None:
        processor_model.record_memory_access(access_type="read")
        processor_model.record_memory_access(access_type="write")

    def test_apply_dvfs(self, processor_model: ProcessorPowerModel) -> None:
        processor_model.apply_dvfs(voltage=0.9, frequency=1.5)
        # Verify voltage changed on core component
        assert processor_model.components["core"].params.voltage == 0.9
        assert processor_model.components["core"].params.frequency == 1.5

    def test_apply_clock_gating(self, processor_model: ProcessorPowerModel) -> None:
        processor_model.apply_clock_gating(component="alu", gated=True)
        assert processor_model.components["alu"].params.is_clock_gated is True

    def test_apply_power_gating(self, processor_model: ProcessorPowerModel) -> None:
        processor_model.apply_power_gating(component="core", gated=True)
        assert processor_model.components["core"].current_state == PowerState.OFF

    def test_update_thermal_model(self, processor_model: ProcessorPowerModel) -> None:
        # Run some cycles to generate heat
        for _ in range(5):
            processor_model.advance_cycle()
        processor_model.update_thermal_model()
        # Temperature should have changed (even if slightly)
        assert isinstance(processor_model.current_temperature, float)

    def test_get_energy_per_instruction(
        self, processor_model: ProcessorPowerModel
    ) -> None:
        # Zero instructions → zero EPI
        assert processor_model.get_energy_per_instruction() == 0.0

        instr = _make_instruction("add", InstructionType.ARITHMETIC)
        processor_model.record_instruction_execution(instr, "alu_0")
        epi = processor_model.get_energy_per_instruction()
        assert epi > 0.0

    def test_get_power_breakdown(self, processor_model: ProcessorPowerModel) -> None:
        breakdown = processor_model.get_power_breakdown()
        assert "total_power_mW" in breakdown
        assert "core" in breakdown

    def test_get_comprehensive_stats(
        self, processor_model: ProcessorPowerModel
    ) -> None:
        stats = processor_model.get_comprehensive_stats()
        assert "total_cycles" in stats
        assert "instructions_executed" in stats
        assert "power_breakdown" in stats
        assert "component_stats" in stats
        assert "total_energy_pJ" in stats

    def test_reset_stats(self, processor_model: ProcessorPowerModel) -> None:
        # Advance cycles and execute instructions
        instr = _make_instruction("sub", InstructionType.ARITHMETIC)
        processor_model.record_instruction_execution(instr, "alu_0")
        processor_model.advance_cycle()

        processor_model.reset_stats()
        assert processor_model.current_cycle == 0
        assert processor_model.instructions_executed == 0
