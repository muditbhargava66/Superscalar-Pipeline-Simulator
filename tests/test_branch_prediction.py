import unittest
from src.branch_prediction import AlwaysTakenPredictor, GsharePredictor, BimodalPredictor
from src.utils import BranchInstruction

class TestBranchPrediction(unittest.TestCase):
    def test_always_taken_predictor(self):
        # Test case for the always taken predictor
        predictor = AlwaysTakenPredictor()
        branch_instruction = BranchInstruction(address=100, condition=True)
        
        # Predict branch outcome
        prediction = predictor.predict(branch_instruction)
        
        # Assert the prediction is always taken
        self.assertTrue(prediction)
        
        # Update predictor with actual outcome
        predictor.update(branch_instruction, True)
        predictor.update(branch_instruction, False)
        
        # Assert the prediction remains taken
        prediction = predictor.predict(branch_instruction)
        self.assertTrue(prediction)
    
    def test_gshare_predictor(self):
        # Test case for the gshare predictor
        predictor = GsharePredictor(num_entries=256, history_length=8)
        branch_instruction1 = BranchInstruction(address=100, condition=True)
        branch_instruction2 = BranchInstruction(address=200, condition=False)
        
        # Predict branch outcomes
        prediction1 = predictor.predict(branch_instruction1)
        prediction2 = predictor.predict(branch_instruction2)
        
        # Assert initial predictions
        self.assertTrue(prediction1)
        self.assertTrue(prediction2)
        
        # Update predictor with actual outcomes
        predictor.update(branch_instruction1, True)
        predictor.update(branch_instruction2, False)
        
        # Predict branch outcomes again
        prediction1 = predictor.predict(branch_instruction1)
        prediction2 = predictor.predict(branch_instruction2)
        
        # Assert updated predictions
        self.assertTrue(prediction1)
        self.assertFalse(prediction2)
    
    def test_bimodal_predictor(self):
        # Test case for the bimodal predictor
        predictor = BimodalPredictor(num_entries=1024)
        branch_instruction1 = BranchInstruction(address=100, condition=True)
        branch_instruction2 = BranchInstruction(address=200, condition=False)
        
        # Predict branch outcomes
        prediction1 = predictor.predict(branch_instruction1)
        prediction2 = predictor.predict(branch_instruction2)
        
        # Assert initial predictions
        self.assertTrue(prediction1)
        self.assertTrue(prediction2)
        
        # Update predictor with actual outcomes
        predictor.update(branch_instruction1, True)
        predictor.update(branch_instruction2, False)
        
        # Predict branch outcomes again
        prediction1 = predictor.predict(branch_instruction1)
        prediction2 = predictor.predict(branch_instruction2)
        
        # Assert updated predictions
        self.assertTrue(prediction1)
        self.assertFalse(prediction2)

if __name__ == '__main__':
    unittest.main()