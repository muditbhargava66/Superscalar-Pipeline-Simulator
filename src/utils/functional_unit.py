class FunctionalUnit:
    def __init__(self, id):
        self.id = id
        self.busy = False
        self.remaining_cycles = 0

    def is_free(self):
        return not self.busy

    def can_execute(self, opcode):
        # Check if the functional unit can execute the given opcode
        # Replace this with your actual logic based on the functional unit's capabilities
        return True

    def execute(self, instruction):
        # Execute the instruction on the functional unit
        # Replace this with your actual execution logic based on the instruction's opcode and operands
        result = instruction.operands[0] + instruction.operands[1]
        self.busy = True
        self.remaining_cycles = self.get_execution_latency(instruction.opcode)
        return result

    def update(self):
        if self.busy:
            self.remaining_cycles -= 1
            if self.remaining_cycles == 0:
                self.busy = False

    def get_execution_latency(self, opcode):
        # Return the execution latency for the given opcode
        # Replace this with your actual latency values based on the opcode
        return 1