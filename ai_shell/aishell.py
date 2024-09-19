#!/usr/bin/env python3

import logging
import sys

from .models import  Iteration
from .logger import setup_logging
from .ai import Ai
from .shell import Shell

# Initialize logging
log_file = setup_logging()
print(f"Logging initialized. Log file: {log_file}")

class AiShell:
    iterations: list[Iteration]

    def __init__(self, goal: str, user_input_source=lambda:input("continue?(no, new command)")):
        logging.info(f"Initializing AiShell with goal: {goal}")
        self.goal = goal
        self.ai = Ai(self)
        self.shell = Shell()
        self.user_input_source = user_input_source
        self.iterations = []

    def loop(self):
        while self.run_once():
            pass
        print("Loop finished. ")

    def run_once(self):
        """
        Sent the prompt to the AI and process its response.

        Returns:
            bool: True, if there should be another run. If the task is completed or the user cancelled it,
            False is returned instead.
        """
        ai_response = self.ai.call()
        if ai_response.task_completed:
            print("AI completed its task.")
            return False
        if not ai_response.command_options:
            print("Ai did not provide a single command.")
            return False
        self.shell.check_commands_availability(ai_response.command_options)
        for command_plan in ai_response.command_options:
            missing_commands = self.shell.unavailable_commands & set(command_plan.used_commands)
            if missing_commands:
                print("Missing commands:", missing_commands)
                self.iterations.append(Iteration(command_plan=command_plan, missing_commands=missing_commands))
                continue
            self.print_command(command_plan)
            userinput = self.user_input_source()
            if userinput == "no":
                return False
            if userinput != "":
                # do not execute shell command. Userinput will be presented to AI on next run.
                self.iterations.append(Iteration(command_plan=command_plan, userinput=userinput))
            else:
                command_process = self.shell.execute_shell_command(
                    "cd " + command_plan.directory + " && " + command_plan.command)
                self.shell.print_shell_output(command_process)
                output_as_string = self.shell.shell_output_to_string(command_process)
                if command_process.returncode == 0:
                    print("Checking if command was successful: ", command_plan.check_command)
                    check_process = self.shell.execute_shell_command(
                        "cd " + command_plan.directory + " && " + command_plan.check_command)
                    self.shell.print_shell_output(check_process)
                    check_output_as_string = self.shell.shell_output_to_string(check_process)
                    self.iterations.append(
                        Iteration(command_plan=command_plan, userinput=userinput, shell_output=output_as_string,
                                  check_shell_output=check_output_as_string))
                else:
                    self.iterations.append(
                        Iteration(command_plan=command_plan, userinput=userinput, shell_output=output_as_string))
        return True


    def print_command(self, command_plan):
        print("PLAN>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(command_plan.plan)
        print("COMMAND>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> in", command_plan.directory)
        print(command_plan.command)


def main():
    goal = sys.argv[1] if len(sys.argv) > 1 else "No goal provided"
    aishell = AiShell(goal)
    aishell.loop()


if __name__ == "__main__":
    main()
