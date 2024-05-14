from openai import OpenAI
import subprocess
import sys

END = "I AM DONE!"

with open("openai.key", 'r') as file:
    api_key = file.read()

client = OpenAI(api_key=api_key)
import os


goal = sys.argv[1]

messages=[{"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": """Your goal is:  {goal}. You are connected to a linux shell. Your whole response will be passed into it. 
          You will get both the stdout and stderr streams back as a response. Use this, to interact with the shell, like a human would, to achieve your goal. 
          Once you see by the response, that you are done, respond with `{end}` to indicate that you are finished. 
          Prefer responding with single commands rather than with a script or series of commands. 
          Do not try to use any interactive editors, like nano.""".format(goal=goal, end=END)}]
print(messages)
while True:
    response = client.chat.completions.create(model="gpt-4o", messages=messages)
    command = response.choices[0].message.content
    #print("Command raw", command)
    if (END == command): break
    command = command.lstrip("```sh\r\n").rstrip("```")
    print("COMMAND>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n", command)
    messages.append({"role": "assistant", "content": response.choices[0].message.content})

    if input("continue?(no)") == "no": break

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

    # Get the standard output (stdout)
    output = result.stdout
    # Get the standard error (stderr), if needed
    errors = result.stderr

    print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<OUTPUT:\n", output)
    
    if errors != "":
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Errors:\n", errors)

    messages.append({"role":"user", "content":
        "Output: "+output+"\\nErrors"+errors+"\\n Enter next command:"})


print("Loop finished. ")

