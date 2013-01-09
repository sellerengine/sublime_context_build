
import unittest

class TestBlah(unittest.TestCase):
    def test_haha(self):
        import time
        time.sleep(2)
        self.fail('failing test!')


    def test_ruhroh(self):
        self.assertEqual(3, 3)
