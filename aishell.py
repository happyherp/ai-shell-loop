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
    command: Optional[str] = Field(description="the shell to be executed to achieve the goal")
    task_completed: bool = Field(description="""
    Set this to `True`, if you confirmed that you have completed the task and no further actions are necessary.
    If this is True, command should be `None`. This field is not optional. 
    """)


class Iteration(BaseModel):
    ai: ResponseContent
    userinput: str
    shell_output: Optional[str] = None


class AiShell:
    maxIterationsInHistory = 15

    def __init__(self, mainPrompt: str, userInputSource=user_input_from_console):
        self.mainPrompt = mainPrompt
        self.userInputSource = userInputSource
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
        messages = [system_msg("You are a helpful assistant."), user_msg(self.mainPrompt)]
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

    def loop(self):

        while True:
            response = self.client.chat.completions.create(
                model=MODEL, messages=self.build_messages(), response_format={"type": "json_object"}
            )
            self.total_tokens += response.usage.total_tokens
            print("Tokens: ", response.usage.total_tokens, "Total: ", self.total_tokens)
            obj = ResponseContent.model_validate_json(response.choices[0].message.content)
            print("PLAN>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
            print(obj.plan)
            command = obj.command
            # print("Command raw", command)
            if obj.task_completed: break
            print("COMMAND>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> in", obj.directory)
            print(command)
            command = "cd " + obj.directory + " && " + command
            shell_output = None
            userinput = self.userInputSource()
            if userinput == "no": break
            if userinput != "":
                pass
            else:
                result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

                output = result.stdout
                errors = result.stderr

                print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<OUTPUT:\n", output)

                shell_output = "Return Code: " + str(result.returncode)
                shell_output += "\nstdout:\n" + output + "\n"
                if errors and errors != "":
                    print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Errors:\n", errors)
                    shell_output += "stderr:\n" + errors + "\n "
            self.iterations.append(Iteration(ai=obj, userinput=userinput, shell_output=shell_output))
        print("Loop finished. ")


def execute_goal(goal: str, user_input_source=user_input_from_console):
    prompt = """
    Your goal is:  {goal}. You are connected to a terminal. You 
    can pass commands to the shell to achieve the goal.
    You will get both the stdout and stderr streams back as a response. Use this to interact with the shell, to achieve your goal. 
    Once you have confirmed, that you are done, respond with task_completed=True to indicate that you are finished. 
    Do not try to use any interactive editors, like nano.
    
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
