class Scoreboard:
    def __init__(self, num_registers):
        self.num_registers = num_registers
        self.register_status = [False] * num_registers
        self.function_unit_status = {}

    def is_register_available(self, register):
        return not self.register_status[register]

    def is_function_unit_available(self, function_unit):
        return function_unit not in self.function_unit_status

    def allocate_register(self, register):
        self.register_status[register] = True

    def deallocate_register(self, register):
        self.register_status[register] = False

    def allocate_function_unit(self, function_unit, instruction):
        self.function_unit_status[function_unit] = instruction

    def deallocate_function_unit(self, function_unit):
        del self.function_unit_status[function_unit]

    def get_instruction_in_function_unit(self, function_unit):
        return self.function_unit_status.get(function_unit, None)