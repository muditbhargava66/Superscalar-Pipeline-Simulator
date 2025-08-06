"""
Reservation Station Implementation

This module implements reservation stations for out-of-order execution
in the superscalar pipeline simulator.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Optional

from .instruction import Instruction


@dataclass
class OperandInfo:
    """Information about an operand in a reservation station."""
    value: Optional[Any] = None
    ready: bool = False
    source_tag: Optional[str] = None  # Which instruction produces this value
    register_name: Optional[str] = None


class ReservationStation:
    """
    Reservation station for holding instructions waiting for operands.
    
    Implements Tomasulo's algorithm for dynamic scheduling.
    """

    def __init__(self, station_id: int) -> None:
        """
        Initialize reservation station.
        
        Args:
            station_id: Unique identifier for this station
        """
        self.id = station_id
        self.instruction: Optional[Instruction] = None
        self.operands: List[OperandInfo] = []
        self.busy = False
        self.ready_for_execution = False

        # Timing information
        self.issue_cycle: Optional[int] = None
        self.ready_cycle: Optional[int] = None

        logging.debug(f"Initialized Reservation Station {station_id}")

    def is_free(self) -> bool:
        """Check if this reservation station is free."""
        return not self.busy

    def issue(self, instruction: Instruction) -> None:
        """
        Issue an instruction to this reservation station.
        
        Args:
            instruction: Instruction to issue
        """
        if self.busy:
            raise RuntimeError(f"Reservation station {self.id} is already busy")

        self.instruction = instruction
        self.busy = True
        self.ready_for_execution = False
        self.issue_cycle = getattr(instruction, 'issue_cycle', 0)

        # Initialize operand information
        self.operands = []
        source_registers = instruction.get_source_registers()

        for reg in source_registers:
            operand_info = OperandInfo(
                register_name=reg,
                ready=False,
                source_tag=None
            )
            self.operands.append(operand_info)

        # Handle immediate operands (always ready)
        for i, operand in enumerate(instruction.operands):
            if not isinstance(operand, str) or not operand.startswith('$'):
                # This is an immediate value
                if i < len(self.operands):
                    self.operands[i].value = operand
                    self.operands[i].ready = True

        logging.debug(f"Issued {instruction} to RS {self.id}")

    def update(self, executed_instructions: List[tuple]) -> None:
        """
        Update operand values based on executed instructions.
        
        Args:
            executed_instructions: List of (instruction, result) tuples
        """
        if not self.busy or not self.instruction:
            return

        # Update operands with results from executed instructions
        for executed_instruction, result in executed_instructions:
            if not executed_instruction or not executed_instruction.has_destination_register():
                continue

            dest_reg = executed_instruction.get_destination_register()

            # Check if any of our operands depend on this result
            for operand_info in self.operands:
                if (not operand_info.ready and
                    operand_info.register_name == dest_reg):
                    operand_info.value = result
                    operand_info.ready = True
                    operand_info.source_tag = str(executed_instruction)

                    logging.debug(f"RS {self.id}: Updated operand {dest_reg} = {result}")

        # Check if instruction is now ready for execution
        self._check_readiness()

    def get_ready_instruction(self, register_file, data_forwarding_unit) -> Optional[Instruction]:
        """
        Get instruction if ready for execution.
        
        Args:
            register_file: Register file to read values from
            data_forwarding_unit: Data forwarding unit for bypassing
            
        Returns:
            Ready instruction or None
        """
        if not self.busy or not self.instruction:
            return None

        # Try to resolve any unready operands
        self._resolve_operands(register_file, data_forwarding_unit)

        # Check if all operands are ready
        if self._all_operands_ready():
            ready_instruction = self.instruction

            # Attach operand values to instruction
            ready_instruction.resolved_operands = {
                operand.register_name: operand.value
                for operand in self.operands
                if operand.register_name
            }

            # Clear the reservation station
            self._clear()

            logging.debug(f"RS {self.id}: Instruction ready for execution: {ready_instruction}")
            return ready_instruction

        return None

    def _resolve_operands(self, register_file, data_forwarding_unit) -> None:
        """
        Try to resolve unready operands from register file or forwarding.
        
        Args:
            register_file: Register file to read from
            data_forwarding_unit: Forwarding unit to check
        """
        for operand_info in self.operands:
            if operand_info.ready or not operand_info.register_name:
                continue

            # Try to get value from data forwarding unit first
            if data_forwarding_unit:
                forwarded_value = data_forwarding_unit.get_operand_value(
                    operand_info.register_name
                )
                if forwarded_value is not None:
                    operand_info.value = forwarded_value
                    operand_info.ready = True
                    operand_info.source_tag = "forwarded"
                    continue

            # Try to read from register file
            try:
                reg_value = register_file.read_register(operand_info.register_name)
                if reg_value is not None:
                    operand_info.value = reg_value
                    operand_info.ready = True
                    operand_info.source_tag = "register_file"
            except Exception as e:
                logging.debug(f"Could not read register {operand_info.register_name}: {e}")

    def _all_operands_ready(self) -> bool:
        """Check if all operands are ready."""
        return all(operand.ready for operand in self.operands)

    def _check_readiness(self) -> None:
        """Check and update readiness status."""
        if self.busy and self.instruction:
            self.ready_for_execution = self._all_operands_ready()
            if self.ready_for_execution and not self.ready_cycle:
                self.ready_cycle = getattr(self, 'current_cycle', 0)

    def _clear(self) -> None:
        """Clear the reservation station."""
        self.instruction = None
        self.operands.clear()
        self.busy = False
        self.ready_for_execution = False
        self.issue_cycle = None
        self.ready_cycle = None

    def reset(self) -> None:
        """Reset the reservation station to initial state."""
        self._clear()
        logging.debug(f"Reset Reservation Station {self.id}")

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the reservation station."""
        return {
            'id': self.id,
            'busy': self.busy,
            'instruction': str(self.instruction) if self.instruction else None,
            'ready_for_execution': self.ready_for_execution,
            'operands_ready': [op.ready for op in self.operands],
            'operand_values': [op.value for op in self.operands],
            'issue_cycle': self.issue_cycle,
            'ready_cycle': self.ready_cycle
        }

    def __repr__(self) -> str:
        """String representation of reservation station."""
        status = "BUSY" if self.busy else "FREE"
        inst_str = str(self.instruction) if self.instruction else "None"
        return f"RS{self.id}[{status}]: {inst_str}"


class ReservationStationPool:
    """
    Pool of reservation stations with management utilities.
    
    Provides higher-level operations for managing multiple reservation stations.
    """

    def __init__(self, num_stations: int) -> None:
        """
        Initialize pool of reservation stations.
        
        Args:
            num_stations: Number of reservation stations to create
        """
        self.stations = [ReservationStation(i) for i in range(num_stations)]
        self.num_stations = num_stations

        # Statistics
        self.total_issues = 0
        self.total_completions = 0

        logging.info(f"Initialized Reservation Station Pool with {num_stations} stations")

    def find_free_station(self) -> Optional[ReservationStation]:
        """Find and return a free reservation station."""
        for station in self.stations:
            if station.is_free():
                return station
        return None

    def issue_instruction(self, instruction: Instruction) -> bool:
        """
        Issue an instruction to a free reservation station.
        
        Args:
            instruction: Instruction to issue
            
        Returns:
            True if successfully issued, False if no free stations
        """
        free_station = self.find_free_station()
        if free_station:
            free_station.issue(instruction)
            self.total_issues += 1
            return True
        return False

    def update_all(self, executed_instructions: List[tuple]) -> None:
        """Update all reservation stations with execution results."""
        for station in self.stations:
            station.update(executed_instructions)

    def get_ready_instructions(self, register_file, data_forwarding_unit) -> List[Instruction]:
        """Get all instructions ready for execution."""
        ready_instructions = []

        for station in self.stations:
            ready_inst = station.get_ready_instruction(register_file, data_forwarding_unit)
            if ready_inst:
                ready_instructions.append(ready_inst)
                self.total_completions += 1

        return ready_instructions

    def get_utilization(self) -> float:
        """Get utilization percentage of reservation stations."""
        busy_count = sum(1 for station in self.stations if station.busy)
        return (busy_count / self.num_stations) * 100

    def get_statistics(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            'total_stations': self.num_stations,
            'busy_stations': sum(1 for s in self.stations if s.busy),
            'utilization': self.get_utilization(),
            'total_issues': self.total_issues,
            'total_completions': self.total_completions,
            'ready_for_execution': sum(1 for s in self.stations if s.ready_for_execution)
        }

    def reset_all(self) -> None:
        """Reset all reservation stations."""
        for station in self.stations:
            station.reset()

        self.total_issues = 0
        self.total_completions = 0

        logging.info("Reset all reservation stations")

    def __repr__(self) -> str:
        """String representation of the pool."""
        busy_count = sum(1 for s in self.stations if s.busy)
        return f"RSPool({busy_count}/{self.num_stations} busy)"
