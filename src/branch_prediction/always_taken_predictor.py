class AlwaysTakenPredictor:
    def __init__(self):
        pass

    def predict(self, branch_instruction):
        # Always predict that the branch will be taken
        return True

    def update(self, branch_instruction, actual_outcome):
        # No need to update the predictor since it always predicts taken
        pass