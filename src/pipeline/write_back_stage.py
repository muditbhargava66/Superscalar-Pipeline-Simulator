from utils.instruction import Instruction

class WriteBackStage:
    def __init__(self, register_file):
        self.register_file = register_file

    def write_back(self, memory_results):
        for instruction, result in memory_results:
            if instruction.has_destination_register():
                # Write the result back to the destination register
                destination_register = instruction.get_destination_register()
                self.register_file.write_register(destination_register, result)