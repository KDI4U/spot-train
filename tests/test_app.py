import unittest
from app import root, health_check


class TestApp(unittest.TestCase):

    def test_root_endpoint(self):
        root_res = root()
        self.assertTrue(root_res["success"])
        self.assertIn("Spot Train API", root_res["message"])

    def test_health_check(self):
        health_res = health_check()
        self.assertEqual(health_res["status"], "healthy")


if __name__ == "__main__":
    unittest.main()
