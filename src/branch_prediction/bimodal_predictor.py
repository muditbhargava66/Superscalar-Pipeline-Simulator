class BimodalPredictor:
    def __init__(self, num_entries):
        self.num_entries = num_entries
        self.counters = [2] * num_entries

    def predict(self, branch_instruction):
        # Extract the branch address from the instruction
        branch_address = branch_instruction.address

        # Calculate the index into the counters table
        index = self.get_index(branch_address)

        # Make a prediction based on the saturating counter value
        prediction = self.counters[index] >= 2

        return prediction

    def update(self, branch_instruction, actual_outcome):
        # Extract the branch address from the instruction
        branch_address = branch_instruction.address

        # Calculate the index into the counters table
        index = self.get_index(branch_address)

        # Update the saturating counter based on the actual outcome
        if actual_outcome:
            self.counters[index] = min(3, self.counters[index] + 1)
        else:
            self.counters[index] = max(0, self.counters[index] - 1)

    def get_index(self, branch_address):
        # Mask the branch address to fit within the number of entries in the counters table
        index = branch_address % self.num_entries

        return index