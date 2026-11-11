import unittest
from fastapi import HTTPException
from train_status.routes.train_routes import spot_train, train_test


class TestTrainRoutes(unittest.TestCase):

    def test_train_test_endpoint(self):
        res = train_test()
        self.assertTrue(res["success"])
        self.assertEqual(res["message"], "Train API working")

    def test_spot_train_invalid_train_number(self):
        with self.assertRaises(HTTPException) as ctx:
            spot_train(train_no="ABC12", journey_date="11-11-2026")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("digits only", ctx.exception.detail)

    def test_spot_train_invalid_date_format(self):
        with self.assertRaises(HTTPException) as ctx:
            spot_train(train_no="12345", journey_date="2026/11/11")
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Invalid journey_date", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
