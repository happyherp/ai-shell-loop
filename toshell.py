from openai import OpenAI
import subprocess
import sys, json, os
from describe import describe

END = "I AM DONE!"

script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir,  './openai.key')

with open(file_path, 'r') as file:
    api_key = file.read()

client = OpenAI(api_key=api_key)


goal = sys.argv[1]

from pydantic import BaseModel, Field

class ResponseContent(BaseModel):
    plan:str = Field(description="Describe how you plan to achieve the goal in plain english")
    directory:str = Field(description="the absolute path in which the command should be executed")
    command:str = Field(description="the shell to be executed to achieve the goal")

mainPrompt="""
Your goal is:  {goal}. You are connected to a linux shell. You 
can pass commends to the shell to achieve the goal.
You will get both the stdout and stderr streams back as a response. Use this to interact with the shell, to achieve your goal. 
Once you see by the response, that you are done, respond with the command `{end}` to indicate that you are finished. 
Do not try to use any interactive editors, like nano.

{schema}

The content of "command" will be sent to the shell and you will receive the stdout and stderr. 

""".format(goal=goal, end=END, schema=describe(ResponseContent))

messages=[{"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": mainPrompt}]
print(messages)          
total_tokens = 0
while True:
    response = client.chat.completions.create(model="gpt-4o", messages=messages, 
        response_format={ "type": "json_object" }
    )
    total_tokens += response.usage.total_tokens
    print("Tokens: ", response.usage.total_tokens, "Total: ", total_tokens)
    obj = ResponseContent.parse_raw(response.choices[0].message.content)
    print("PLAN>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
    print(obj.plan)
    command = obj.command
    #print("Command raw", command)
    messages.append({"role": "assistant", "content": response.choices[0].message.content})
    if (END == command): break
    command = "cd "+obj.directory+ " && " + command
    print("COMMAND>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> in", obj.directory)
    print(command)
    userinput = input("continue?(no, new command)")
    if userinput == "no": break
    if userinput != "":
        messages.append({"role":"user", "content":"Your last command was cancelled by the user. He says: "+userinput})
    else:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

        output = result.stdout
        errors = result.stderr

        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<OUTPUT:\n", output)
        
        responseContent = "Return Code: "+str(result.returncode)
        responseContent += "\nstdout:\n"+output+"\n"
        if errors != "":
            print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Errors:\n", errors)
            responseContent += "stderr:\n"+errors+"\n "
        messages.append({"role":"user", "content": responseContent})


print("Loop finished. ")

