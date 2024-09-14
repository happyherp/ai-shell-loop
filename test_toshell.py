from unittest import TestCase
from toshell import executeGoal
from util import ensure_empty_directory
import os


class Test(TestCase):

    def setUp(self):
        ensure_empty_directory("build/test-output")

    def test_execute_goal(self):
        filename = "build/test-output/output.txt"
        self.assertFalse(os.path.isfile(filename))
        executeGoal(f"Write the text 'Hello World' into the file '{filename}'", userInputSource=lambda:"")
        self.assertTrue(os.path.isfile(filename))
        self.assertEqual('Hello World', open(filename, "r").read().strip())




