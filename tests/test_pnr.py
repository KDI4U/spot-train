import unittest
from train_status.routes.pnr_routes import pnr_test
from train_status.parsers.pnr_parser import parse_pnr_response


class TestPNRRoutes(unittest.TestCase):

    def test_pnr_test_endpoint(self):
        res = pnr_test()
        self.assertTrue(res["success"])
        self.assertEqual(res["message"], "PNR API working")

    def test_pnr_parser_invalid_data(self):
        with self.assertRaises(ValueError):
            parse_pnr_response("invalid_string_instead_of_dict")


if __name__ == "__main__":
    unittest.main()
