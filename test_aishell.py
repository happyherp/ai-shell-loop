from unittest import TestCase
from ai_shell.aishell import AiShell
from ai_shell.shell import Shell
from ai_shell.models import CommandPlan
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

        # first command should be something like "echo 'Hello World' > build/test-output/output.txt"
        self.assertTrue(aishell.run_once())
        self.assertTrue("Hello World" in aishell.iterations[-1].command_plan.command)
        self.assertTrue(os.path.isfile(filename))
        with open(filename, "r") as file:
            self.assertEqual('Hello World', file.read().strip())
        self.assertTrue("output.txt" in aishell.iterations[-1].command_plan.check_command)

        #next call the ai confirms that the job is done.
        self.assertFalse(aishell.run_once())


    def test_user_command(self):
        filename = "build/test-output/output.txt"
        self.assertFalse(os.path.isfile(filename))

        user_input_iterator = iter([
            f"Instead of 'Original Goal', write the text 'Hello World' into the file '{filename}'.",
            "", "", ""])

        aishell = AiShell(
            f"Write the text 'Original goal'  into the file '{filename}'",
            user_input_source=lambda: next(user_input_iterator))

        self.assertEqual(
            [True, True, False],
            [ aishell.run_once(), aishell.run_once(), aishell.run_once()])

        self.assertTrue(os.path.isfile(filename))
        with open(filename, "r") as file:
            self.assertEqual('Hello World', file.read().strip())

    def test_check_commands_availability(self):
        """Should be moved to test for shell only."""
        shell = Shell()
        shell.check_commands_availability([CommandPlan(
            used_commands = ["ls", "cat", "this-command-does-not-exist"],
            command="irrelevant", directory=".", plan="any plan", check_command = "does not matter"
        )])

        self.assertEqual({"ls", "cat"}, shell.available_commands)
        self.assertEqual({"this-command-does-not-exist"}, shell.unavailable_commands)