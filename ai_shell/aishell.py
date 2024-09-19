#!/usr/bin/env python3

import logging
import copy
import getpass
import json
import subprocess
import sys
from typing import List

from openai import OpenAI

from .describe import describe
from .util import *
from .models import CommandPlan, AiResponse, Iteration
from .logger import setup_logging

# Initialize logging
log_file = setup_logging()
print(f"Logging initialized. Log file: {log_file}")

class AiShell:
    iterations: list[Iteration]
    maxIterationsInHistory = 15

    def __init__(self, goal: str, user_input_source=lambda:input("continue?(no, new command)")):
        logging.info(f"Initializing AiShell with goal: {goal}")
        self.goal = goal
        self.user_input_source = user_input_source
        self.total_tokens = 0
        self.iterations = []
        self.client = OpenAI()
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
        ai_response = self.call_ai()
        if ai_response.task_completed:
            print("AI completed its task.")
            return False
        if not ai_response.command_options:
            print("Ai did not provide a single command.")
            return False
        self.check_commands_availability(ai_response.command_options)
        for command_plan in ai_response.command_options:
            self.print_command(command_plan)
            missing_commands = self.unavailable_commands & set(command_plan.used_commands)
            if missing_commands:
                print("Missing commands:", missing_commands)
                self.iterations.append(Iteration(command_plan=command_plan, missing_commands=missing_commands))
                continue
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

    def call_ai(self) -> AiResponse:
        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview", messages=self.build_messages(), response_format={"type": "json_object"}
        )
        self.total_tokens += response.usage.total_tokens
        print("Tokens: ", response.usage.total_tokens, "Total: ", self.total_tokens)
        return AiResponse.model_validate_json(response.choices[0].message.content)

    def build_messages(self):
        messages = [
            system_msg(self.build_prompt()),
            user_msg(self.goal),
            user_msg(get_folder_content()),
            user_msg(self.get_command_availability())
        ]
        if len(self.iterations) > 0:
            messages.append(user_msg(self.summarize_iterations()))
            last_iteration = self.iterations[-1]
            if last_iteration.userinput and last_iteration.userinput != "":
                messages.append(user_msg(
                    "Your last command was cancelled by the user with the following message: "
                    + last_iteration.userinput))
        logging.debug(f"messages: {messages}")
        return messages

    def build_prompt(self):
        return """
You are an helpful assistant that achieves goals for the user.  You are connected to a terminal. You 
can pass commands to the shell to achieve the goal.
You will get both the stdout and stderr streams back as a response. Use this to interact with the shell, to achieve your goal. 
Once you have confirmed, that you are done, respond with task_completed=true to indicate that you are finished. 
In order to confirm that you have to achieved your goal, you must execute an additional command in 'check_command' to check if 
whatever the goal is, was actually done. This will often require using cat, which, and similar commands. 
Do not assume that you are done, just because the command finished without errors.
Do not try to use any interactive editors, like nano.
You can use sudo if you need it. 
The value of 'userinput' of previous iterations is to be followed. It takes precedence over the original goal. 
If multiple 'userinput' contradict each other, the last one is to be followed. 

Current Directory: {current_directory}
Username: {username}

Use the following json-schema for your answers:

{schema}

The content of "command" will be sent to the shell and you will receive the stdout and stderr. 
If the return code of the command is 0, the content of "check_command" will also be executed and you will receive the stdout and stderr. 

""".format(schema=describe(AiResponse), current_directory=os.getcwd(),
           username=getpass.getuser())

    def summarize_iterations(self):
        content = "These are the commands that have previously been executed as json. \n"
        content += "They have the following schema: \n"
        iteration_schema = Iteration.model_json_schema()
        # Modify Iteration schema to reference CommandPlan via $ref
        # The schema of CommandPlan is already part of the system prompt.
        iteration_schema['properties']['command_plan'] = {"$ref": "#/definitions/CommandPlan"}
        del iteration_schema["$defs"]["CommandPlan"]
        content += codeblock(json.dumps(iteration_schema, indent=0)) + "\n"
        if len(self.iterations) > AiShell.maxIterationsInHistory:
            content += str(len(self.iterations) - AiShell.maxIterationsInHistory) + " iterations skipped.\n "

        content += "Previous iterations:\n'''json\n[\n"
        for i in self.iterations[-AiShell.maxIterationsInHistory:]:
            small = copy.deepcopy(i)
            small.shell_output = self.reduce_shell_output(small.shell_output)
            content += small.model_dump_json(indent=0) + ",\n"
        content += "]\n'''\n"
        return content

    def reduce_shell_output(self, text):
        if not text: return text
        max_size = 80 * 10
        extra_chars = len(text) - max_size
        if extra_chars > 0:
            return text[:max_size // 2] + "<< {0} chars skipped>>".format(extra_chars) + text[-max_size // 2:]
        else:
            return text

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
