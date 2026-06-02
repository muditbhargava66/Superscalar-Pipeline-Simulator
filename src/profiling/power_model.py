#!/usr/bin/env python3

"""
Power and Energy Modeling

This module implements power consumption modeling for superscalar processors,
including dynamic and static power estimation based on activity factors.
"""

from dataclasses import dataclass, field
from enum import Enum
import logging
import math
from typing import Any, Optional, Set

try:
    from ..utils.instruction import Instruction, InstructionType
except (ImportError, ValueError):
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.instruction import Instruction, InstructionType


class PowerDomain(Enum):
    """Power domains in the processor."""

    CORE = "core"
    CACHE_L1I = "l1i_cache"
    CACHE_L1D = "l1d_cache"
    CACHE_L2 = "l2_cache"
    MEMORY_CONTROLLER = "memory_controller"
    INTERCONNECT = "interconnect"


class PowerState(Enum):
    """Power states for components."""

    ACTIVE = "active"
    IDLE = "idle"
    SLEEP = "sleep"
    OFF = "off"


@dataclass
class PowerParameters:
    """Power model parameters for a component."""

    # Technology parameters
    technology_node: float = 45.0  # nm
    voltage: float = 1.0  # V
    frequency: float = 2.0  # GHz

    # Capacitance values (pF)
    switching_capacitance: float = 100.0
    leakage_current: float = 10.0  # nA

    # Activity factors
    activity_factor: float = 0.1
    clock_gating_efficiency: float = 0.8

    # Area (mm²)
    area: float = 1.0


@dataclass
class PowerEvent:
    """Power consumption event."""

    cycle: int
    component: str
    event_type: str
    energy: float  # pJ
    power: float  # mW


class ComponentPowerModel:
    """Power model for a processor component."""

    def __init__(self, name: str, params: PowerParameters):
        self.name = name
        self.params = params

        # Power states
        self.current_state = PowerState.IDLE
        self.state_cycles = dict.fromkeys(PowerState, 0)

        # Activity tracking
        self.activity_events = []  # type: ignore[var-annotated]
        self.total_cycles = 0
        self.active_cycles = 0

        # Energy accumulation
        self.dynamic_energy = 0.0  # pJ
        self.static_energy = 0.0  # pJ

        self.logger = logging.getLogger(__name__)

    def calculate_dynamic_power(self, activity_factor: float | None = None) -> float:
        """
        Calculate dynamic power consumption.
        P_dynamic = alpha * C * V² * f
        """
        alpha = activity_factor or self.params.activity_factor
        capacitance = self.params.switching_capacitance * 1e-12  # Convert pF to F
        voltage = self.params.voltage
        frequency = self.params.frequency * 1e9  # Convert GHz to Hz

        # Apply clock gating
        effective_alpha = alpha * (1 - self.params.clock_gating_efficiency)

        power_watts = effective_alpha * capacitance * voltage**2 * frequency
        return power_watts * 1000  # Convert to mW

    def calculate_static_power(self) -> float:
        """
        Calculate static (leakage) power consumption.
        P_static = I_leak * V
        """
        leakage_current = self.params.leakage_current * 1e-9  # Convert nA to A
        voltage = self.params.voltage

        power_watts = leakage_current * voltage
        return power_watts * 1000  # Convert to mW

    def record_activity(
        self, cycle: int, event_type: str, activity_factor: float | None = None
    ) -> None:
        """Record an activity event."""
        dynamic_power = self.calculate_dynamic_power(activity_factor)
        static_power = self.calculate_static_power()
        total_power = dynamic_power + static_power

        # Energy for one cycle (assuming 1 cycle = 1/frequency seconds)
        cycle_time = 1.0 / (self.params.frequency * 1e9)  # seconds
        energy = total_power * cycle_time * 1e12  # Convert to pJ

        event = PowerEvent(
            cycle=cycle,
            component=self.name,
            event_type=event_type,
            energy=energy,
            power=total_power,
        )

        self.activity_events.append(event)
        self.dynamic_energy += dynamic_power * cycle_time * 1e12
        self.static_energy += static_power * cycle_time * 1e12

        if event_type != "idle":
            self.active_cycles += 1

        self.total_cycles += 1

    def set_power_state(self, state: PowerState, cycle: int) -> None:
        """Set component power state."""
        if self.current_state != state:
            self.logger.debug(
                f"{self.name} power state: {self.current_state} -> {state} at cycle {cycle}"
            )
            self.current_state = state

        self.state_cycles[state] += 1

    def get_average_power(self) -> float:
        """Get average power consumption over all cycles."""
        if not self.activity_events:
            return 0.0

        total_power = sum(event.power for event in self.activity_events)
        return total_power / len(self.activity_events)

    def get_total_energy(self) -> float:
        """Get total energy consumption (pJ)."""
        return self.dynamic_energy + self.static_energy

    def get_stats(self) -> dict[str, Any]:
        """Get power statistics."""
        return {
            "component": self.name,
            "total_energy_pJ": self.get_total_energy(),
            "dynamic_energy_pJ": self.dynamic_energy,
            "static_energy_pJ": self.static_energy,
            "average_power_mW": self.get_average_power(),
            "activity_factor": self.active_cycles / max(1, self.total_cycles),
            "total_cycles": self.total_cycles,
            "active_cycles": self.active_cycles,
            "power_state_distribution": {
                state.value: cycles for state, cycles in self.state_cycles.items()
            },
        }


class ProcessorPowerModel:
    """Complete processor power model."""

    def __init__(self, config: dict):
        self.config = config
        self.current_cycle = 0

        # Initialize component models
        self.components = {}  # type: ignore[var-annotated]
        self._init_component_models()

        # Global power management
        self.dvfs_enabled = config.get("dvfs_enabled", False)
        self.clock_gating_enabled = config.get("clock_gating_enabled", True)
        self.power_gating_enabled = config.get("power_gating_enabled", False)

        # Thermal model (simplified)
        self.ambient_temperature = config.get("ambient_temp", 25.0)  # °C
        self.thermal_resistance = config.get("thermal_resistance", 1.0)  # °C/W
        self.current_temperature = self.ambient_temperature

        # Energy efficiency metrics
        self.instructions_executed = 0
        self.total_energy_consumed = 0.0

        self.logger = logging.getLogger(__name__)

    def _init_component_models(self) -> None:
        """Initialize power models for all components."""
        # Core components
        core_params = PowerParameters(
            switching_capacitance=200.0,
            leakage_current=50.0,
            activity_factor=0.3,
            area=2.0,
        )
        self.components["core"] = ComponentPowerModel("core", core_params)

        # L1 Instruction Cache
        l1i_params = PowerParameters(
            switching_capacitance=50.0,
            leakage_current=20.0,
            activity_factor=0.8,  # High activity for instruction fetch
            area=0.5,
        )
        self.components["l1i_cache"] = ComponentPowerModel("l1i_cache", l1i_params)

        # L1 Data Cache
        l1d_params = PowerParameters(
            switching_capacitance=80.0,
            leakage_current=30.0,
            activity_factor=0.4,
            area=0.8,
        )
        self.components["l1d_cache"] = ComponentPowerModel("l1d_cache", l1d_params)

        # L2 Cache
        l2_params = PowerParameters(
            switching_capacitance=300.0,
            leakage_current=100.0,
            activity_factor=0.1,  # Lower activity, accessed on L1 miss
            area=4.0,
        )
        self.components["l2_cache"] = ComponentPowerModel("l2_cache", l2_params)

        # Functional Units
        for unit_type in ["ALU", "FPU", "LSU"]:
            unit_params = PowerParameters(
                switching_capacitance=150.0 if unit_type == "FPU" else 100.0,
                leakage_current=40.0,
                activity_factor=0.2,
                area=1.5 if unit_type == "FPU" else 1.0,
            )
            self.components[unit_type.lower()] = ComponentPowerModel(
                unit_type.lower(), unit_params
            )

    def record_instruction_execution(
        self, instruction: Instruction, functional_unit: str
    ) -> None:
        """Record power consumption for instruction execution."""
        # Core activity
        self.components["core"].record_activity(
            self.current_cycle, "instruction_execute", 0.5
        )

        # Functional unit activity
        fu_name = functional_unit.split("_", maxsplit=1)[0].lower()  # Extract unit type
        if fu_name in self.components:
            activity_factor = self._get_instruction_activity_factor(instruction)
            self.components[fu_name].record_activity(
                self.current_cycle,
                f"execute_{instruction.opcode.lower()}",
                activity_factor,
            )

        self.instructions_executed += 1

    def record_cache_access(
        self, cache_level: str, hit: bool, access_type: str = "read"
    ) -> None:
        """Record power consumption for cache access."""
        cache_name = (
            f"l{cache_level}_cache" if cache_level.isdigit() else f"{cache_level}_cache"
        )

        if cache_name in self.components:
            # Higher activity for misses due to additional logic
            activity_factor = 0.3 if hit else 0.8
            event_type = f"{access_type}_{'hit' if hit else 'miss'}"

            self.components[cache_name].record_activity(
                self.current_cycle, event_type, activity_factor
            )

    def record_memory_access(self, access_type: str = "read") -> None:
        """Record power consumption for main memory access."""
        # Memory controller activity (if modeled)
        if "memory_controller" in self.components:
            self.components["memory_controller"].record_activity(
                self.current_cycle, f"memory_{access_type}", 0.9
            )

    def apply_dvfs(self, voltage: float, frequency: float) -> None:
        """Apply Dynamic Voltage and Frequency Scaling."""
        if not self.dvfs_enabled:
            return

        self.logger.info(
            f"DVFS: V={voltage}V, f={frequency}GHz at cycle {self.current_cycle}"
        )

        # Update all component parameters
        for component in self.components.values():
            component.params.voltage = voltage
            component.params.frequency = frequency

    def apply_clock_gating(self, component: str, gated: bool) -> None:
        """Apply clock gating to a component."""
        if not self.clock_gating_enabled or component not in self.components:
            return

        # Adjust clock gating efficiency
        efficiency = 0.9 if gated else 0.0
        self.components[component].params.clock_gating_efficiency = efficiency

        # Set power state
        state = PowerState.IDLE if gated else PowerState.ACTIVE
        self.components[component].set_power_state(state, self.current_cycle)

    def apply_power_gating(self, component: str, gated: bool) -> None:
        """Apply power gating to a component."""
        if not self.power_gating_enabled or component not in self.components:
            return

        state = PowerState.OFF if gated else PowerState.ACTIVE
        self.components[component].set_power_state(state, self.current_cycle)

        self.logger.debug(f"Power gating {component}: {'ON' if gated else 'OFF'}")

    def update_thermal_model(self) -> None:
        """Update processor temperature based on power consumption."""
        # Calculate total power
        total_power = sum(comp.get_average_power() for comp in self.components.values())
        total_power_watts = total_power / 1000.0  # Convert mW to W

        # Simple thermal model: T = T_ambient + P * R_thermal
        self.current_temperature = self.ambient_temperature + (
            total_power_watts * self.thermal_resistance
        )

        # Apply temperature-dependent leakage scaling
        for component in self.components.values():
            # Leakage increases exponentially with temperature
            temp_factor = math.exp((self.current_temperature - 25) / 100)
            component.params.leakage_current *= temp_factor

    def advance_cycle(self) -> None:
        """Advance power model by one cycle."""
        self.current_cycle += 1

        # Record idle power for inactive components
        for component in self.components.values():
            if component.current_state == PowerState.IDLE:
                component.record_activity(self.current_cycle, "idle", 0.0)

        # Update thermal model periodically
        if self.current_cycle % 100 == 0:
            self.update_thermal_model()

    def _get_instruction_activity_factor(self, instruction: Instruction) -> float:
        """Get activity factor based on instruction type."""
        activity_factors = {
            InstructionType.ARITHMETIC: 0.8,
            InstructionType.LOGICAL: 0.6,
            InstructionType.FLOATING_POINT: 0.9,
            InstructionType.LOAD: 0.4,
            InstructionType.STORE: 0.5,
            InstructionType.BRANCH: 0.3,
            InstructionType.JUMP: 0.2,
            InstructionType.NOP: 0.0,
        }

        return activity_factors.get(instruction.instruction_type, 0.5)

    def get_energy_per_instruction(self) -> float:
        """Calculate Energy Per Instruction (EPI) in pJ."""
        if self.instructions_executed == 0:
            return 0.0

        total_energy = sum(comp.get_total_energy() for comp in self.components.values())
        return total_energy / self.instructions_executed

    def get_power_breakdown(self) -> dict[str, float]:
        """Get power breakdown by component."""
        breakdown = {}
        total_power = 0.0

        for name, component in self.components.items():
            power = component.get_average_power()
            breakdown[name] = power
            total_power += power

        # Convert to percentages
        if total_power > 0:
            for name in list(breakdown.keys()):  # Create a copy of keys
                breakdown[f"{name}_percent"] = (breakdown[name] / total_power) * 100

        breakdown["total_power_mW"] = total_power
        return breakdown

    def get_comprehensive_stats(self) -> dict[str, Any]:
        """Get comprehensive power and energy statistics."""
        stats = {
            "total_cycles": self.current_cycle,
            "instructions_executed": self.instructions_executed,
            "energy_per_instruction_pJ": self.get_energy_per_instruction(),
            "current_temperature_C": self.current_temperature,
            "power_breakdown": self.get_power_breakdown(),
            "component_stats": {},
        }

        # Add per-component statistics
        for name, component in self.components.items():
            stats["component_stats"][name] = component.get_stats()

        # Add efficiency metrics
        total_energy = sum(comp.get_total_energy() for comp in self.components.values())
        average_power = sum(
            comp.get_average_power() for comp in self.components.values()
        )
        peak_power = (
            max(comp.get_average_power() for comp in self.components.values())
            if self.components
            else 0
        )

        stats.update(
            {
                "total_energy_pJ": total_energy,
                "total_energy_mJ": total_energy / 1e9,  # Convert pJ to mJ
                "average_power_mW": average_power,
                "peak_power_mW": peak_power,
                "power_efficiency_MIPS_per_W": (
                    self.instructions_executed / max(1, self.current_cycle)
                )
                * 1000
                / max(1, average_power),
            }
        )

        return stats

    def reset_stats(self) -> None:
        """Reset all power statistics."""
        self.current_cycle = 0
        self.instructions_executed = 0
        self.total_energy_consumed = 0.0
        self.current_temperature = self.ambient_temperature

        for component in self.components.values():
            component.activity_events.clear()
            component.total_cycles = 0
            component.active_cycles = 0
            component.dynamic_energy = 0.0
            component.static_energy = 0.0
            component.state_cycles = dict.fromkeys(PowerState, 0)
