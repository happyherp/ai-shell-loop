import logging
import getpass
import subprocess
from typing import List

from .models import CommandPlan
from .util import *


class Shell:
    """Communicates with the Shell"""

    maxIterationsInHistory = 15

    def __init__(self):
        self.available_commands = set()
        self.unavailable_commands = set()
        self.sudo_password = None

    def get_command_availability(self):
        return "confirmed available commands: {}\n unavailable commands: {}".format(
                self.available_commands, self.unavailable_commands)

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