#!/usr/bin/env python3

import logging
import getpass
import subprocess
import sys
from typing import List

from .util import *
from .models import CommandPlan, Iteration
from .logger import setup_logging
from .ai import Ai

# Initialize logging
log_file = setup_logging()
print(f"Logging initialized. Log file: {log_file}")

class AiShell:
    iterations: list[Iteration]

    def __init__(self, goal: str, user_input_source=lambda:input("continue?(no, new command)")):
        logging.info(f"Initializing AiShell with goal: {goal}")
        self.goal = goal
        self.ai = Ai(self)
        self.user_input_source = user_input_source
        self.iterations = []
        self.available_commands = set()
        self.unavailable_commands = set()
        self.sudo_password = None

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
        self.check_commands_availability(ai_response.command_options)
        for command_plan in ai_response.command_options:
            missing_commands = self.unavailable_commands & set(command_plan.used_commands)
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
                command_process = self.execute_shell_command(
                    "cd " + command_plan.directory + " && " + command_plan.command)
                self.print_shell_output(command_process)
                output_as_string = self.shell_output_to_string(command_process)
                if command_process.returncode == 0:
                    print("Checking if command was successful: ", command_plan.check_command)
                    check_process = self.execute_shell_command(
                        "cd " + command_plan.directory + " && " + command_plan.check_command)
                    self.print_shell_output(check_process)
                    check_output_as_string = self.shell_output_to_string(check_process)
                    self.iterations.append(
                        Iteration(command_plan=command_plan, userinput=userinput, shell_output=output_as_string,
                                  check_shell_output=check_output_as_string))
                else:
                    self.iterations.append(
                        Iteration(command_plan=command_plan, userinput=userinput, shell_output=output_as_string))
        return True

    def get_command_availability(self):
        return "confirmed available commands: {}\n unavailable commands: {}".format(
            self.available_commands, self.unavailable_commands)

    def print_command(self, command_plan):
        print("PLAN>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(command_plan.plan)
        print("COMMAND>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> in", command_plan.directory)
        print(command_plan.command)

    def check_commands_availability(self, command_options: List[CommandPlan]):
        """
        Checks if the commands used in the command-options are available on the current machine.
        It will update self.available_commands and self.unavailable_commands accordingly.
        """
        all_used_commands = {cmd for plan in command_options for cmd in plan.used_commands}
        for command in all_used_commands:
            if shutil.which(command) is not None:
                self.available_commands.add(command)
                self.unavailable_commands.discard(command)
            else:
                self.available_commands.discard(command)
                self.unavailable_commands.add(command)

    def execute_shell_command(self, command) -> subprocess.CompletedProcess[str]:
        logging.info(f"Executing shell command: {command}")
        if "sudo" in command:
            if not self.sudo_password:
                self.sudo_password = getpass.getpass("Please enter your sudo password: ")
            command = command.replace("sudo", f"echo {self.sudo_password} | sudo -S")

        completed_process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                           shell=True)
        logging.info(f"Command executed with return code {completed_process.returncode}")
        logging.debug(f"stdout: {completed_process.stdout}")
        logging.debug(f"stderr: {completed_process.stderr}")
        return completed_process

    def print_shell_output(self, completed_process: subprocess.CompletedProcess[str]):
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<stdout:")
        print(completed_process.stdout)
        if completed_process.stderr and completed_process.stderr != "":
            print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Errors:")
            print(completed_process.stderr)

    def shell_output_to_string(self, completed_process: subprocess.CompletedProcess[str]):

        output = completed_process.stdout
        errors = completed_process.stderr
        shell_output = "Return Code: " + str(completed_process.returncode)
        shell_output += "\nstdout:\n" + codeblock(output)
        if errors and errors != "":
            shell_output += "stderr:\n" + codeblock(errors)
        return shell_output


def main():
    goal = sys.argv[1] if len(sys.argv) > 1 else "No goal provided"
    aishell = AiShell(goal)
    aishell.loop()


if __name__ == "__main__":
    main()
