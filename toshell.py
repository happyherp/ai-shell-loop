from openai import OpenAI
from typing import Optional
import subprocess, getpass
import sys, json, os, copy
from describe import describe
from util import * 
from pydantic import BaseModel, Field

MODEL = "gpt-4o-2024-08-06"

class ResponseContent(BaseModel):
    plan:str = Field(description="Describe how you plan to achieve the goal in plain english")
    directory:str = Field(description="the absolute path in which the command should be executed")
    command:Optional[str] = Field(description="the shell to be executed to achieve the goal")
    taskCompleted:bool = Field(description="""
    Set this to `True`, if you confirmed that you have completed the task and no further actions are necessary.
    If this is true, command should be `None`.
    """)

class Iteration(BaseModel):
    ai:ResponseContent
    userinput:str
    shellOutput:Optional[str] = None


def fromIterations():

    maxIterationsInHistory = 15

    content = ""
    if len(iterations) > maxIterationsInHistory:
        content += (len(iterations)-maxIterationsInHistory) + " iterations skipped.\n "
    
    content += "Previous iterations:[\n"
    for i in iterations[-maxIterationsInHistory:]:
        small = copy.deepcopy(i)
        small.shellOutput = reduceShelloutput(small.shellOutput)
        content += small.model_dump_json()+"\n"    
    content += "]"

    return [systemMsg("You are a helpful assistant."), userMsg(mainPrompt), userMsg(content)]

def reduceShelloutput(text):
    if not text: return text
    maxSize = 80*10
    extraChars = len(text) - maxSize
    if extraChars > 0:
        return text[:maxSize//2]+ "<< {0} chars skipped>>".format(extraChars)+text[-maxSize//2:]
    else: 
        return text
        

goal = sys.argv[1]


mainPrompt="""
Your goal is:  {goal}. You are connected to a terminal. You 
can pass commends to the shell to achieve the goal.
You will get both the stdout and stderr streams back as a response. Use this to interact with the shell, to achieve your goal. 
Once you see by the response, that you are done, respong with taskCompleted=True to indicate that you are finished. 
Do not try to use any interactive editors, like nano.

Current Directory: {current_directory}
Username: {username}

{schema}

The content of "command" will be sent to the shell and you will receive the stdout and stderr. 

""".format(goal=goal, schema=describe(ResponseContent), current_directory=os.getcwd(),
    username = getpass.getuser())

messages=[systemMsg("You are a helpful assistant."), userMsg(mainPrompt)]

total_tokens = 0
iterations = []

client = createClient()


while True:
    #print("messages: ", fromIterations())
    response = client.chat.completions.create(model=MODEL, messages=fromIterations(), 
        response_format={ "type": "json_object" }
    )
    total_tokens += response.usage.total_tokens
    print("Tokens: ", response.usage.total_tokens, "Total: ", total_tokens)
    obj = ResponseContent.model_validate_json(response.choices[0].message.content)
    print("PLAN>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
    print(obj.plan)
    command = obj.command
    #print("Command raw", command)
    messages.append(assistantMsg(response.choices[0].message.content))
    if (obj.taskCompleted): break
    command = "cd "+obj.directory+ " && " + command
    print("COMMAND>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> in", obj.directory)
    print(command)
    responseContent=None
    userinput = input("continue?(no, new command)")
    if userinput == "no": break
    if userinput != "":
        messages.append(userMsg("Your last command was cancelled by the user. He says: "+userinput))
    else:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

        output = result.stdout
        errors = result.stderr

        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<OUTPUT:\n", output)
        
        responseContent = "Return Code: "+str(result.returncode)
        responseContent += "\nstdout:\n"+output+"\n"
        if errors and errors != "":
            print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Errors:\n", errors)
            responseContent += "stderr:\n"+errors+"\n "
        messages.append(userMsg(responseContent))
    iterations.append(Iteration(ai=obj, userinput=userinput, shellOutput=responseContent))


print("Loop finished. ")

