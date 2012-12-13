
import unittest

class TestBlah(unittest.TestCase):
    def test_haha(self):
        self.fail('failing test!')


    def test_ruhroh(self):
        self.assertEqual(3, 3)
