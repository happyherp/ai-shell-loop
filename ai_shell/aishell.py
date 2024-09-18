#!/usr/bin/env python3
import copy
import getpass
import subprocess
import sys
from typing import Optional, List

from openai import OpenAI
from pydantic import BaseModel, Field

from ai_shell.describe import describe
from ai_shell.util import *

MODEL = "gpt-4-1106-preview"


def user_input_from_console(): return input("continue?(no, new command)")



class CommandPlan(BaseModel):
    plan: str = Field(description="Describe how you plan to achieve the goal in plain english")
    directory: str = Field(description="the absolute path in which the command should be executed")
    command: str = Field(
        description="the shell command to be executed to achieve the goal. The command should return 0 if it worked.")
    used_commands: List[str] = Field(
        description="A list of all the different commands, without arguments that must be available for the command to work. ",
        examples=[["ls", "cat", "grep", "apt-get"], ["ping"]])

class AiResponse(BaseModel):

    command_options: List[CommandPlan] = Field(description="""
        A list of different approaches to solve the goal. The best ones should come first.
    """)

    task_completed: bool = Field(description="""
    Set this to `true`, if you confirmed that you have completed the task and no further actions are necessary.
    If this is `true`, command_options should be empty. This field is not optional. 
    """)



class Iteration(BaseModel):
    ai: AiResponse
    userinput: Optional[str] = None
    missing_commands: Optional[List[str]] = None
    shell_output: Optional[str] = None


class AiShell:
    maxIterationsInHistory = 15

    def __init__(self, goal: str, user_input_source=user_input_from_console):
        self.goal = goal
        self.user_input_source = user_input_source
        self.total_tokens = 0
        self.iterations = []
        self.client = OpenAI()
        self.available_commands = set()
        self.unavailable_commands = set()

    def summarize_iterations(self):
        content = ""
        if len(self.iterations) > AiShell.maxIterationsInHistory:
            content += str(len(self.iterations) - AiShell.maxIterationsInHistory) + " iterations skipped.\n "

        content += "Previous iterations:[\n"
        for i in self.iterations[-AiShell.maxIterationsInHistory:]:
            small = copy.deepcopy(i)
            small.shell_output = self.reduce_shelloutput(small.shell_output)
            content += small.model_dump_json() + "\n"
        content += "]"
        return content

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
        return messages

    def build_prompt(self):
        return """
            You are an helpful assistant that achieves goals for the user.  You are connected to a terminal. You 
            can pass commands to the shell to achieve the goal.
            You will get both the stdout and stderr streams back as a response. Use this to interact with the shell, to achieve your goal. 
            Once you have confirmed, that you are done, respond with task_completed=true to indicate that you are finished. 
            Do not try to use any interactive editors, like nano.
            You can use sudo if you need it. 
            The value of 'userinput' of previous iterations is to be followed. It takes precedence over the original goal. 
            If multiple 'userinput' contradict each other, the last one is to be followed. 
            
            Current Directory: {current_directory}
            Username: {username}
            
            Use the following schema for your answers:
            {schema}
            
            The content of "command" will be sent to the shell and you will receive the stdout and stderr. 
            
            """.format(schema=describe(AiResponse), current_directory=os.getcwd(),
                       username=getpass.getuser())


    def reduce_shelloutput(self, text):
        if not text: return text
        maxSize = 80 * 10
        extraChars = len(text) - maxSize
        if extraChars > 0:
            return text[:maxSize // 2] + "<< {0} chars skipped>>".format(extraChars) + text[-maxSize // 2:]
        else:
            return text

    def run_once(self):
        """
        Sent the prompt to the AI and process its response.

        Returns:
            bool: True, if there should be another run. If the task is completed or the user cancelled it,
            False is returned instead.
        """
        ai_response = self.call_ai()
        if not ai_response.command_options:
            print("Ai did not provide a single command. ")
            return False
        all_used_commands = {cmd for plan in ai_response.command_options for cmd in plan.used_commands}
        self.check_commands_availability(all_used_commands)
        if ai_response.task_completed: return False
        for command_plan in ai_response.command_options:
            print("PLAN>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
            print(command_plan.plan)
            command = command_plan.command
            print("COMMAND>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> in", command_plan.directory)
            print(command)

            missing_commands = self.unavailable_commands & set(command_plan.used_commands)
            if missing_commands:
                print("Missing commands:", missing_commands)
                self.iterations.append(Iteration(ai=ai_response, missing_commands = missing_commands))
                continue

            userinput = self.user_input_source()
            if userinput == "no":
                return False
            if userinput != "":
                # do not execute shell command. Userinput will be presented to ai on next run.
                self.iterations.append(Iteration(ai=ai_response, userinput=userinput))
            else:
                completed_process = self.execute_shell_command("cd " + command_plan.directory + " && " + command)
                self.print_shell_output(completed_process)
                output_as_string = self.shell_output_to_string(completed_process)
                self.iterations.append(Iteration(ai=ai_response, userinput=userinput, shell_output=output_as_string))
                if completed_process.returncode == 0: break
        return True

    def loop(self):

        while self.run_once():
            pass
        print("Loop finished. ")

    def call_ai(self) -> AiResponse:
        response = self.client.chat.completions.create(
            model=MODEL, messages=self.build_messages(), response_format={"type": "json_object"}
        )
        self.total_tokens += response.usage.total_tokens
        print("Tokens: ", response.usage.total_tokens, "Total: ", self.total_tokens)
        return AiResponse.model_validate_json(response.choices[0].message.content)

    def execute_shell_command(self, command) ->  subprocess.CompletedProcess[str]:

        if "sudo" in command:
            sudo_password = getpass.getpass("Please enter your sudo password: ")
            command = command.replace("sudo", f"echo {sudo_password} | sudo -S")

        return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)


    def print_shell_output(self, completed_process : subprocess.CompletedProcess[str]):
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<stdout:")
        print(completed_process.stdout)
        if completed_process.stderr and completed_process.stderr  != "":
            print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Errors:")
            print(completed_process.stderr)

    def shell_output_to_string(self, completed_process : subprocess.CompletedProcess[str]):

        output = completed_process.stdout
        errors = completed_process.stderr
        shell_output = "Return Code: " + str(completed_process.returncode)
        shell_output += "\nstdout:\n" + codeblock(output)
        if errors and errors != "":
            shell_output += "stderr:\n" + codeblock(errors)
        return shell_output

    def check_commands_availability(self, commands):
        """
        Given a list of shell commands (without arguments), this function checks if they are available on the current machine.
        It will update self.available_commands and self.unavailable_commands accordingly.

        Args:
            commands (set): Set of shell commands (e.g., ["cat", "bat", "apt-get"]).
        """
        for command in commands:
            # Check if the command is available using shutil.which()
            if shutil.which(command) is not None:
                self.available_commands.add(command)
                self.unavailable_commands.discard(command)
            else:
                self.available_commands.discard(command)
                self.unavailable_commands.add(command)

    def get_command_availability(self):
        return "confirmed available commands: {}\n unavailable commands: {}".format(self.available_commands, self.unavailable_commands)


def execute_goal(goal: str, user_input_source=user_input_from_console):
    aishell = AiShell(goal, user_input_source)
    aishell.loop()


def main():
    goal = sys.argv[1] if len(sys.argv) > 1 else "No goal provided"
    execute_goal(goal)


if __name__ == "__main__":
    main()
