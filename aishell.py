#!/usr/bin/env python3
from typing import Optional
import subprocess, getpass
import sys, copy
from describe import describe
from util import *
from pydantic import BaseModel, Field

MODEL = "gpt-4o-2024-08-06"


def user_input_from_console(): return input("continue?(no, new command)")


class ResponseContent(BaseModel):
    plan: str = Field(description="Describe how you plan to achieve the goal in plain english")
    directory: str = Field(description="the absolute path in which the command should be executed")
    command: Optional[str] = Field(description="the shell command to be executed to achieve the goal. Set this to null if you are done.")
    task_completed: bool = Field(description="""
    Set this to `true`, if you confirmed that you have completed the task and no further actions are necessary.
    If this is `true`, command should be `null`. This field is not optional. 
    """)


class Iteration(BaseModel):
    ai: ResponseContent
    userinput: str
    shell_output: Optional[str] = None


class AiShell:
    maxIterationsInHistory = 15

    def __init__(self, main_prompt: str, user_input_source=user_input_from_console):
        self.main_prompt = main_prompt
        self.user_input_source = user_input_source
        self.total_tokens = 0
        self.total_tokens = 0
        self.iterations = []
        self.client = create_client()

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
            system_msg("You are a helpful assistant."),
            user_msg(self.main_prompt),
            user_msg(self.get_folder_content())
        ]
        if len(self.iterations) > 0:
            messages.append(user_msg(self.summarize_iterations()))
            last_iteration = self.iterations[-1]
            if last_iteration.userinput != "":
                messages.append(user_msg(
                    "Your last command was cancelled by the user with the following message: "
                    + last_iteration.userinput))
        return messages

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
        print("PLAN>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
        print(ai_response.plan)
        command = ai_response.command
        # print("Command raw", command)
        if ai_response.task_completed: return False
        print("COMMAND>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> in", ai_response.directory)
        print(command)
        userinput = self.user_input_source()
        if userinput == "no":
            return False
        if userinput != "":
            # do not execute shell command. Userinput will be presented to ai on next run.
            self.iterations.append(Iteration(ai=ai_response, userinput=userinput, shell_output=None))
        else:
            shell_output = self.execute_shell_command("cd " + ai_response.directory + " && " + command)
            self.iterations.append(Iteration(ai=ai_response, userinput=userinput, shell_output=shell_output))
        return True

    def loop(self):

        while self.run_once():
            pass
        print("Loop finished. ")

    def call_ai(self):
        response = self.client.chat.completions.create(
            model=MODEL, messages=self.build_messages(), response_format={"type": "json_object"}
        )
        self.total_tokens += response.usage.total_tokens
        print("Tokens: ", response.usage.total_tokens, "Total: ", self.total_tokens)
        return ResponseContent.model_validate_json(response.choices[0].message.content)

    def execute_shell_command(self, command):
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

        output = result.stdout
        errors = result.stderr

        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<OUTPUT:\n", output)

        shell_output = "Return Code: " + str(result.returncode)
        shell_output += "\nstdout:\n" + output + "\n"
        if errors and errors != "":
            print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Errors:\n", errors)
            shell_output += "stderr:\n" + errors + "\n "
        return shell_output

    def get_folder_content(self):
        """Returns a string listing files and directories with type indicator (file or directory)."""
        current_directory = os.getcwd()
        items = os.listdir(current_directory)

        result = "Files in the current directory: \n"
        for item in items:
            full_path = os.path.join(current_directory, item)
            if os.path.isfile(full_path):
                result += f"{item} [File]\n"
            elif os.path.isdir(full_path):
                result += f"{item} [Directory]\n"

        return result

def execute_goal(goal: str, user_input_source=user_input_from_console):
    prompt = """
    Your goal is:  {goal}. You are connected to a terminal. You 
    can pass commands to the shell to achieve the goal.
    You will get both the stdout and stderr streams back as a response. Use this to interact with the shell, to achieve your goal. 
    Once you have confirmed, that you are done, respond with task_completed=true to indicate that you are finished. 
    Do not try to use any interactive editors, like nano.
    The value of 'userinput' of previous iterations if to be followed. It takes precedence over the original goal. 
    If multiple 'userinput' contradict each other, the last one is to be followed. 
    
    Current Directory: {current_directory}
    Username: {username}
    
    {schema}
    
    The content of "command" will be sent to the shell and you will receive the stdout and stderr. 
    
    """.format(goal=goal, schema=describe(ResponseContent), current_directory=os.getcwd(),
               username=getpass.getuser())

    aishell = AiShell(prompt, user_input_source)
    aishell.loop()


if __name__ == "__main__":
    goal = sys.argv[1]
    execute_goal(goal)
