import logging
import copy
import json
import getpass
from typing import TYPE_CHECKING

from openai import OpenAI

from .models import AiResponse, Iteration
from .util import *
from .describe import describe

if TYPE_CHECKING:
    from .aishell import AiShell


class Ai:
    """Communicates with the AI"""

    maxIterationsInHistory = 15

    def __init__(self, ai_shell: 'AiShell'):
        self.ai_shell = ai_shell
        self.total_tokens = 0
        self.client = OpenAI()

    def call(self) -> AiResponse:
        response = self.client.chat.completions.create(
            model="gpt-4-1106-preview", messages=self.build_messages(), response_format={"type": "json_object"}
        )
        self.total_tokens += response.usage.total_tokens
        logging.info(f"Tokens: {response.usage.total_tokens}, Total: {self.total_tokens}")
        content = response.choices[0].message.content
        logging.debug("Response content: " + content)
        return AiResponse.model_validate_json(content)

    def build_messages(self):
        messages = [
            system_msg(self.build_prompt()),
            user_msg(self.ai_shell.goal),
            user_msg(get_folder_content()),
            user_msg(self.ai_shell.shell.get_command_availability())
        ]
        if len(self.ai_shell.iterations) > 0:
            messages.append(user_msg(self.summarize_iterations()))
            last_iteration = self.ai_shell.iterations[-1]
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
        if len(self.ai_shell.iterations) > Ai.maxIterationsInHistory:
            content += str(len(self.ai_shell.iterations) - Ai.maxIterationsInHistory) + " iterations skipped.\n "

        content += "Previous iterations:\n'''json\n[\n"
        for i in self.ai_shell.iterations[-Ai.maxIterationsInHistory:]:
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
