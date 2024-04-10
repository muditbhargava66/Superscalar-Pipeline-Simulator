class RegisterFile:
    def __init__(self, num_registers):
        self.num_registers = num_registers
        self.registers = [0] * num_registers

    def read_register(self, register_num):
        if 0 <= register_num < self.num_registers:
            return self.registers[register_num]
        else:
            raise ValueError(f"Invalid register number: {register_num}")

    def write_register(self, register_num, value):
        if 0 <= register_num < self.num_registers:
            self.registers[register_num] = value
        else:
            raise ValueError(f"Invalid register number: {register_num}")

    def __str__(self):
        return f"RegisterFile: {self.registers}"