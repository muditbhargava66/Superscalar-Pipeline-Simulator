class Scoreboard:
    def __init__(self, num_registers):
        self.num_registers = num_registers
        self.register_status = [False] * num_registers
        self.function_unit_status = {}

    def is_register_available(self, register):
        if 0 <= register < self.num_registers:
            return not self.register_status[register]
        else:
            raise ValueError(f"Invalid register number: {register}")

    def is_function_unit_available(self, function_unit):
        return function_unit not in self.function_unit_status

    def allocate_register(self, register):
        if 0 <= register < self.num_registers:
            self.register_status[register] = True
        else:
            raise ValueError(f"Invalid register number: {register}")

    def deallocate_register(self, register):
        if 0 <= register < self.num_registers:
            self.register_status[register] = False
        else:
            raise ValueError(f"Invalid register number: {register}")

    def allocate_function_unit(self, function_unit, instruction):
        self.function_unit_status[function_unit] = instruction

    def deallocate_function_unit(self, function_unit):
        if function_unit in self.function_unit_status:
            del self.function_unit_status[function_unit]

    def get_instruction_in_function_unit(self, function_unit):
        return self.function_unit_status.get(function_unit, None)