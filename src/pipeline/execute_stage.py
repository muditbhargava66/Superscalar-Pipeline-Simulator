from utils.instruction import Instruction
from utils.functional_unit import FunctionalUnit

class ExecuteStage:
    def __init__(self, num_functional_units):
        self.functional_units = [FunctionalUnit(i) for i in range(num_functional_units)]

    def execute(self, ready_instructions):
        executed_instructions = []

        for instruction in ready_instructions:
            # Find a free functional unit
            functional_unit = self.find_free_functional_unit(instruction.opcode)

            if functional_unit is not None:
                # Execute the instruction on the functional unit
                result = functional_unit.execute(instruction)
                executed_instructions.append((instruction, result))
            else:
                # No free functional unit available, stall the pipeline
                break

        return executed_instructions

    def find_free_functional_unit(self, opcode):
        for functional_unit in self.functional_units:
            if functional_unit.is_free() and functional_unit.can_execute(opcode):
                return functional_unit
        return None

    def update_functional_units(self):
        for functional_unit in self.functional_units:
            functional_unit.update()