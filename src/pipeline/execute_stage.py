from utils.functional_unit import FunctionalUnit

class ExecuteStage:
    def __init__(self, num_functional_units):
        self.functional_units = [
            FunctionalUnit(i, supported_opcodes=["ADD", "SUB", "MUL", "DIV"]) 
            for i in range(num_functional_units)
        ]

    def execute(self, ready_instructions, register_file):
        executed_instructions = []

        for instruction in ready_instructions:
            functional_unit = self.find_free_functional_unit(instruction.opcode)

            if functional_unit is not None:
                result = functional_unit.execute(instruction, register_file)
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