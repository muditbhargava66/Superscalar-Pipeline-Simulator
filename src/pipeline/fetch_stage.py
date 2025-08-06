# Handle imports for both package and direct execution
try:
    from ..cache.cache import InstructionCache
    from ..utils.instruction import Instruction
except (ImportError, ValueError):
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from utils.instruction import Instruction
import logging


class FetchStage:
    def __init__(self, instruction_cache, branch_predictor, memory):
        self.instruction_cache = instruction_cache
        self.branch_predictor = branch_predictor
        self.memory = memory
        self.pc = 0

    def load_program(self, program_file):
        try:
            with open(program_file) as file:
                instructions = file.readlines()

            for i, instruction_str in enumerate(instructions):
                instruction_data = self.parse_instruction_data(instruction_str)
                if instruction_data is not None:
                    self.instruction_cache.add_instruction(i * 4, instruction_data)
        except FileNotFoundError:
            logging.error(f"Program file '{program_file}' not found.")
            raise

    def fetch(self):
        instructions = []

        for _ in range(self.instruction_cache.fetch_bandwidth):
            if self.pc >= self.memory.size:
                break

            if self.instruction_cache.has_instruction(self.pc):
                instruction_data = self.instruction_cache.get_instruction(self.pc)
                if isinstance(instruction_data, dict):
                    instruction = self.parse_instruction(instruction_data)
                    if instruction is not None:
                        instructions.append(instruction)
                        predicted_pc = self.branch_predictor.predict(instruction)
                        if predicted_pc is not None:
                            self.pc = predicted_pc
                        else:
                            self.pc += 4
                    else:
                        logging.warning(f"Skipping invalid instruction data at PC: {self.pc}")
                        self.pc += 4
                else:
                    logging.warning(f"Instruction data is not a dictionary at PC: {self.pc}")
                    self.pc += 4
            else:
                logging.debug(f"Instruction cache miss at PC: {self.pc}")
                self.pc += 4

        return instructions

    def parse_instruction_data(self, instruction_str):
        if not instruction_str.strip():
            return None

        if instruction_str.strip().startswith('.') or ':' in instruction_str:
            return None

        parts = instruction_str.strip().split()
        if not parts:
            return None
        opcode = parts[0]
        operands = parts[1:]

        instruction_dict = {
            'opcode': opcode,
            'operands': operands
        }

        return instruction_dict

    def parse_instruction(self, instruction_data):
        if instruction_data is None:
            logging.error("Instruction data is None")
            return None

        if not isinstance(instruction_data, dict):
            logging.error("Instruction data is not a dictionary")
            return None

        opcode = instruction_data.get('opcode')
        operands = instruction_data.get('operands', [])

        if opcode is None:
            logging.error("Invalid instruction data format")
            return None

        instruction = Instruction(self.pc, opcode, operands)
        return instruction

    def update_pc(self, new_pc):
        self.pc = new_pc

    def get_pc(self):
        return self.pc

class MemoryAccessError(Exception):
    pass

class InstructionCacheMissError(Exception):
    pass

class InstructionParseError(Exception):
    pass

class InstructionCacheError(Exception):
    pass

class InstructionDataError(Exception):
    pass
