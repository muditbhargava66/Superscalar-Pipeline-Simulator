"""
Decode Stage Implementation

This module implements the decode stage of the pipeline, which decodes
fetched instructions and reads operands from the register file.
"""

from __future__ import annotations

import logging
from typing import Union

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


class DecodeStage:
    """
    Decode stage of the pipeline.
    
    Responsible for:
    - Decoding instruction format
    - Reading source operands from register file
    - Detecting data hazards
    - Register renaming (if implemented)
    """

    def __init__(self, register_file: RegisterFile) -> None:
        """
        Initialize the decode stage.
        
        Args:
            register_file: Reference to the register file
        """
        if not isinstance(register_file, RegisterFile):
            raise TypeError("register_file must be an instance of RegisterFile")

        self.register_file = register_file
        self.decoded_count = 0
        self.stall_cycles = 0

        logging.debug("Initialized Decode Stage")

    def decode(self, instructions: List[Instruction]) -> List[Instruction]:
        """
        Decode a list of fetched instructions.
        
        Args:
            instructions: List of fetched instructions
            
        Returns:
            List of decoded instructions with operands resolved
        """
        decoded_instructions = []

        for instruction in instructions:
            if instruction is None:
                continue

            try:
                # Decode the instruction format
                decoded_instruction = self.decode_instruction(instruction)

                # Read operand values from register file
                self.read_operands(decoded_instruction)

                # Check for hazards
                if self.check_hazards(decoded_instruction, decoded_instructions):
                    # Stall if hazard detected
                    self.stall_cycles += 1
                    logging.debug(f"Hazard detected for {decoded_instruction}, stalling")
                    break  # Stop decoding further instructions this cycle

                decoded_instructions.append(decoded_instruction)
                self.decoded_count += 1

            except Exception as e:
                logging.error(f"Error decoding instruction {instruction}: {e}")
                continue

        return decoded_instructions

    def decode_instruction(self, instruction: Instruction) -> Instruction:
        """
        Decode instruction format and identify operands.
        
        Args:
            instruction: Instruction to decode
            
        Returns:
            Decoded instruction with fields populated
        """
        # The instruction object already has most fields populated
        # Here we ensure proper format and add any missing information

        # Ensure destination is properly set for instructions that write
        if instruction.has_destination_register() and not instruction.destination:
            # For R-type and I-type instructions, first operand is typically destination
            if len(instruction.operands) > 0 and instruction.opcode.upper() not in ["SW", "SB", "SH"]:
                instruction.destination = instruction.operands[0]

        # Log decoded instruction
        logging.debug(f"Decoded: {instruction}")

        return instruction

    def read_operands(self, instruction: Instruction) -> None:
        """
        Read source operand values from the register file.
        
        This modifies the instruction's operand values in place.
        
        Args:
            instruction: Instruction whose operands to read
        """
        # Get list of source registers
        source_registers = instruction.get_source_registers()

        # Create a mapping of register names to values
        register_values = {}
        for reg in source_registers:
            if self.is_register(reg):
                try:
                    value = self.register_file.read_register(reg)
                    register_values[reg] = value
                except Exception as e:
                    logging.error(f"Error reading register {reg}: {e}")
                    register_values[reg] = 0  # Default value

        # Store register values for later use
        instruction.register_values = register_values

        # For debugging, log register reads
        if register_values:
            logging.debug(f"Read registers for {instruction.opcode}: {register_values}")

    def is_register(self, operand: Union[str, int]) -> bool:
        """
        Check if an operand is a register reference.
        
        Args:
            operand: Operand to check
            
        Returns:
            True if operand is a register, False otherwise
        """
        if not isinstance(operand, str):
            return False

        # Common MIPS register formats
        # $0-$31, $zero, $at, $v0-$v1, $a0-$a3, $t0-$t9, $s0-$s7, $gp, $sp, $fp, $ra
        if operand.startswith('$'):
            # Check numeric registers ($0-$31)
            if operand[1:].isdigit():
                reg_num = int(operand[1:])
                return 0 <= reg_num < self.register_file.num_registers

            # Check named registers
            named_registers = {
                '$zero': 0, '$at': 1,
                '$v0': 2, '$v1': 3,
                '$a0': 4, '$a1': 5, '$a2': 6, '$a3': 7,
                '$t0': 8, '$t1': 9, '$t2': 10, '$t3': 11,
                '$t4': 12, '$t5': 13, '$t6': 14, '$t7': 15,
                '$s0': 16, '$s1': 17, '$s2': 18, '$s3': 19,
                '$s4': 20, '$s5': 21, '$s6': 22, '$s7': 23,
                '$t8': 24, '$t9': 25,
                '$k0': 26, '$k1': 27,
                '$gp': 28, '$sp': 29, '$fp': 30, '$ra': 31
            }
            return operand in named_registers

        # Alternative format: r0-r31
        if operand.startswith('r') and operand[1:].isdigit():
            reg_num = int(operand[1:])
            return 0 <= reg_num < self.register_file.num_registers

        return False

    def check_hazards(self, instruction: Instruction,
                     previous_instructions: List[Instruction]) -> bool:
        """
        Check for data hazards with previously decoded instructions.
        
        Args:
            instruction: Current instruction being decoded
            previous_instructions: Instructions decoded earlier in this cycle
            
        Returns:
            True if hazard detected, False otherwise
        """
        # Get source registers for current instruction
        source_registers = instruction.get_source_registers()

        # Check against destination registers of previous instructions
        for prev_inst in previous_instructions:
            if prev_inst.has_destination_register():
                dest_reg = prev_inst.get_destination_register()
                if dest_reg in source_registers:
                    # RAW hazard detected
                    logging.debug(f"RAW hazard: {instruction.opcode} depends on {prev_inst.opcode}")
                    return True

        # Check for WAW hazards
        if instruction.has_destination_register():
            dest_reg = instruction.get_destination_register()
            for prev_inst in previous_instructions:
                if prev_inst.has_destination_register():
                    if prev_inst.get_destination_register() == dest_reg:
                        # WAW hazard detected
                        logging.debug(f"WAW hazard: both {instruction.opcode} and {prev_inst.opcode} write to {dest_reg}")
                        return True

        return False

    def get_statistics(self) -> dict:
        """Get decode stage statistics."""
        return {
            'decoded_instructions': self.decoded_count,
            'stall_cycles': self.stall_cycles,
            'decode_efficiency': (self.decoded_count / (self.decoded_count + self.stall_cycles) * 100)
                               if (self.decoded_count + self.stall_cycles) > 0 else 0
        }

    def reset(self) -> None:
        """Reset decode stage statistics."""
        self.decoded_count = 0
        self.stall_cycles = 0
