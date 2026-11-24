import unittest


class TestMarketingDecisionSupportSystem(unittest.TestCase):

    def test_prediction_result_is_valid(self):
        prediction = 1

        self.assertIn(prediction, [0, 1])

    def test_prediction_probability_is_valid(self):
        probability = 0.75

        self.assertGreaterEqual(probability, 0)
        self.assertLessEqual(probability, 1)

    def test_recommendation_is_generated(self):
        recommendation = "Target customer with a promotional offer"

        self.assertIsNotNone(recommendation)
        self.assertNotEqual(recommendation, "")


if __name__ == "__main__":
    unittest.main()