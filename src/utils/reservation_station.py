class ReservationStation:
    def __init__(self, id):
        self.id = id
        self.instruction = None
        self.operands = []
        self.busy = False

    def is_free(self):
        return not self.busy

    def issue(self, instruction):
        self.instruction = instruction
        self.operands = [None] * len(instruction.operands)
        self.busy = True

    def update(self, executed_instructions):
        for executed_instruction in executed_instructions:
            for i, operand in enumerate(self.operands):
                if operand is None and executed_instruction.destination == self.instruction.operands[i]:
                    self.operands[i] = executed_instruction.result

    def get_ready_instruction(self):
        if self.busy and all(operand is not None for operand in self.operands):
            ready_instruction = self.instruction
            self.instruction = None
            self.operands = []
            self.busy = False
            return ready_instruction
        return None