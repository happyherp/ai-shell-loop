from unittest import TestCase
from ai_shell.aishell import execute_goal, AiShell
from ai_shell.util import ensure_empty_directory
import os


class Test(TestCase):

    def setUp(self):
        ensure_empty_directory("build/test-output")

    def test_execute_goal(self):
        filename = "build/test-output/output.txt"
        self.assertFalse(os.path.isfile(filename))
        aishell = AiShell(
            f"Write the text 'Hello World' into the file '{filename}'",
            user_input_source=lambda: "")
        aishell.run_once()
        aishell.run_once()
        self.assertTrue(os.path.isfile(filename))
        with open(filename, "r") as file:
            self.assertEqual('Hello World', file.read().strip())

    def test_user_command(self):
        filename = "build/test-output/output.txt"
        self.assertFalse(os.path.isfile(filename))

        user_input_iterator = iter([
            f"Instead of 'Original Goal', write the text 'Hello World' into the file '{filename}'.",
            "", "", ""])

        aishell = AiShell(
            f"Write the text 'Original goal'  into the file '{filename}'",
            user_input_source=lambda: next(user_input_iterator))
        aishell.run_once()
        aishell.run_once()
        aishell.run_once()

        self.assertTrue(os.path.isfile(filename))
        with open(filename, "r") as file:
            self.assertEqual('Hello World', file.read().strip())
