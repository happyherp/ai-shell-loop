from unittest import TestCase
from aishell import execute_goal
from util import ensure_empty_directory
import os


class Test(TestCase):

    def setUp(self):
        ensure_empty_directory("build/test-output")

    def test_execute_goal(self):
        filename = "build/test-output/output.txt"
        self.assertFalse(os.path.isfile(filename))
        execute_goal(f"Write the text 'Hello World' into the file '{filename}'", user_input_source=lambda: "")
        self.assertTrue(os.path.isfile(filename))
        with open(filename, "r") as file:
            self.assertEqual('Hello World', file.read().strip())




