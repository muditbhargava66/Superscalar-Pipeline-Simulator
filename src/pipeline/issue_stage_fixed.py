"""
Fixed Issue Stage Implementation

This module implements the issue stage of the pipeline with proper
import paths and enhanced hazard detection.
"""

import logging
from typing import Optional

from ..utils.instruction import Instruction
from ..utils.reservation_station import ReservationStation


class IssueStage:
    """
    Issue stage of the superscalar pipeline.
    
    Responsible for:
    - Dispatching instructions to reservation stations
    - Checking for structural and data hazards
    - Managing instruction dependencies
    """

    def __init__(self, num_reservation_stations: int, register_file,
                 data_forwarding_unit, execution_units: dict):
        """
        Initialize the issue stage.
        
        Args:
            num_reservation_stations: Number of reservation stations
            register_file: Reference to register file
            data_forwarding_unit: Reference to data forwarding unit
            execution_units: Dictionary of available execution units
        """
        self.reservation_stations = [
            ReservationStation(i) for i in range(num_reservation_stations)
        ]
        self.register_file = register_file
        self.data_forwarding_unit = data_forwarding_unit
        self.execution_units = execution_units

        # Performance counters
        self.issued_count = 0
        self.stall_count = 0
        self.structural_hazards = 0
        self.data_hazards = 0

        logging.debug(f"Initialized Issue Stage with {num_reservation_stations} reservation stations")

    def issue(self, decoded_instructions: List[Instruction]) -> List[Instruction]:
        """
        Issue instructions to reservation stations.
        
        Args:
            decoded_instructions: List of decoded instructions
            
        Returns:
            List of successfully issued instructions
        """
        issued_instructions = []

        for instruction in decoded_instructions:
            # Check for structural hazards
            if not self._check_structural_hazards(instruction):
                self.structural_hazards += 1
                logging.debug(f"Structural hazard for {instruction}")
                break

            # Find a free reservation station
            reservation_station = self.find_free_reservation_station()

            if reservation_station is not None and self.is_instruction_ready(instruction):
                # Issue the instruction to the reservation station
                reservation_station.issue(instruction)
                issued_instructions.append(instruction)
                self.issued_count += 1

                logging.debug(f"Issued {instruction} to RS {reservation_station.id}")
            else:
                # No free reservation station available or instruction not ready
                self.stall_count += 1
                if reservation_station is None:
                    logging.debug(f"No free reservation station for {instruction}")
                else:
                    logging.debug(f"Instruction not ready: {instruction}")
                break

        return issued_instructions

    def find_free_reservation_station(self) -> Optional[ReservationStation]:
        """Find a free reservation station."""
        for reservation_station in self.reservation_stations:
            if reservation_station.is_free():
                return reservation_station
        return None

    def update_reservation_stations(self, executed_instructions: List[Instruction]) -> None:
        """Update reservation stations with executed instruction results."""
        for reservation_station in self.reservation_stations:
            reservation_station.update(executed_instructions)

    def get_ready_instructions(self) -> List[Instruction]:
        """Get instructions ready for execution."""
        ready_instructions = []
        for reservation_station in self.reservation_stations:
            ready_instruction = reservation_station.get_ready_instruction(
                self.register_file, self.data_forwarding_unit
            )
            if ready_instruction is not None:
                ready_instructions.append(ready_instruction)
        return ready_instructions

    def is_instruction_ready(self, instruction: Instruction) -> bool:
        """
        Check if instruction is ready for issue.
        
        Args:
            instruction: Instruction to check
            
        Returns:
            True if instruction is ready, False otherwise
        """
        try:
            # Check if the operands are available
            operands_ready = all(
                self.is_operand_ready(operand)
                for operand in instruction.get_source_operands()
            )

            if not operands_ready:
                self.data_hazards += 1
                return False

            # Check for additional hazards
            return self._check_additional_hazards(instruction)

        except Exception as e:
            logging.error(f"Error checking instruction readiness: {e}")
            return False

    def is_operand_ready(self, operand) -> bool:
        """
        Check if a specific operand is ready.
        
        Args:
            operand: Operand to check (register number or immediate)
            
        Returns:
            True if operand is ready, False otherwise
        """
        try:
            # Handle immediate values
            if isinstance(operand, int) and operand < 0:
                return True  # Immediate value, always ready

            # Handle register operands
            if isinstance(operand, int | str):
                # Check register file
                register_value = self.register_file.read_register(operand)
                if register_value is not None:
                    return True

                # Check data forwarding unit
                operand_value = self.data_forwarding_unit.get_operand_value(operand)
                if operand_value is not None:
                    return True

                return False

            # Unknown operand type, assume ready
            return True

        except Exception as e:
            logging.error(f"Error checking operand readiness: {e}")
            return False

    def _check_structural_hazards(self, instruction: Instruction) -> bool:
        """
        Check for structural hazards.
        
        Args:
            instruction: Instruction to check
            
        Returns:
            True if no structural hazard, False otherwise
        """
        try:
            # Get required execution unit type
            unit_type = instruction.get_execution_unit_type()

            # Check if execution unit is available
            if unit_type in self.execution_units:
                available_units = self.execution_units[unit_type].get('count', 1)
                used_units = sum(
                    1 for rs in self.reservation_stations
                    if not rs.is_free() and rs.instruction.get_execution_unit_type() == unit_type
                )

                return used_units < available_units

            # Unknown unit type, assume available
            return True

        except Exception as e:
            logging.error(f"Error checking structural hazards: {e}")
            return True

    def _check_additional_hazards(self, instruction: Instruction) -> bool:
        """
        Check for additional hazards (WAW, WAR, etc.).
        
        Args:
            instruction: Instruction to check
            
        Returns:
            True if no additional hazards, False otherwise
        """
        # This is a simplified implementation
        # In a real processor, you would check for:
        # - Write-after-write (WAW) hazards
        # - Write-after-read (WAR) hazards
        # - Control hazards

        return True

    def get_statistics(self) -> dict:
        """Get issue stage statistics."""
        total_attempts = self.issued_count + self.stall_count

        return {
            'instructions_issued': self.issued_count,
            'pipeline_stalls': self.stall_count,
            'structural_hazards': self.structural_hazards,
            'data_hazards': self.data_hazards,
            'issue_rate': (self.issued_count / max(1, total_attempts)) * 100,
            'reservation_station_utilization': self._get_rs_utilization()
        }

    def _get_rs_utilization(self) -> float:
        """Calculate reservation station utilization."""
        if not self.reservation_stations:
            return 0.0

        occupied = sum(1 for rs in self.reservation_stations if not rs.is_free())
        return (occupied / len(self.reservation_stations)) * 100

    def reset(self) -> None:
        """Reset issue stage state."""
        for rs in self.reservation_stations:
            rs.reset()

        self.issued_count = 0
        self.stall_count = 0
        self.structural_hazards = 0
        self.data_hazards = 0

        logging.info("Issue stage reset")
