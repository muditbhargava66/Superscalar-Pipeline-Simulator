class GsharePredictor:
    def __init__(self, num_entries, history_length):
        self.num_entries = num_entries
        self.history_length = history_length
        self.history_register = 0
        self.pattern_history_table = [2] * num_entries

    def predict(self, branch_instruction):
        # Extract the branch address from the instruction
        branch_address = branch_instruction.address

        # Calculate the index into the pattern history table
        index = self.get_index(branch_address)

        # Make a prediction based on the saturating counter value
        prediction = self.pattern_history_table[index] >= 2

        return prediction

    def update(self, branch_instruction, actual_outcome):
        # Extract the branch address from the instruction
        branch_address = branch_instruction.address

        # Calculate the index into the pattern history table
        index = self.get_index(branch_address)

        # Update the saturating counter based on the actual outcome
        if actual_outcome:
            self.pattern_history_table[index] = min(3, self.pattern_history_table[index] + 1)
        else:
            self.pattern_history_table[index] = max(0, self.pattern_history_table[index] - 1)

        # Update the global history register
        self.history_register = ((self.history_register << 1) | actual_outcome) & ((1 << self.history_length) - 1)

    def get_index(self, branch_address):
        # Combine the branch address and global history register using XOR
        index = branch_address ^ self.history_register

        # Mask the index to fit within the number of entries in the pattern history table
        index = index % self.num_entries

        return index