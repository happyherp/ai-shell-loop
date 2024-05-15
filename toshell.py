from openai import OpenAI
import subprocess
import sys, json, os

END = "I AM DONE!"

with open("openai.key", 'r') as file:
    api_key = file.read()

client = OpenAI(api_key=api_key)


goal = sys.argv[1]

messages=[{"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": """Your goal is:  {goal}. You are connected to a linux shell. Your whole response will be passed into it. 
          You will get both the stdout and stderr streams back as a response. Use this, to interact with the shell, like a human would, to achieve your goal. 
          Once you see by the response, that you are done, respond with the command `{end}` to indicate that you are finished. 
          Do not try to use any interactive editors, like nano.
          Respond in a json format: 
          ```
          {{
            "plan": "<Describe how you plan to achieve the goal in plain english>",
            "directory": "<the absolute path in which the command should be executed>"
            "command": "echo Hello World"
          }}
          ```
          
          The content of "command" will be sent to the shell and you will receive the stdout and stderr. 
          
          """.format(goal=goal, end=END)}]
while True:
    response = client.chat.completions.create(model="gpt-4o", messages=messages, 
        response_format={ "type": "json_object" }
    )
    obj = json.loads(response.choices[0].message.content)
    print("PLAN>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
    print(obj["plan"])
    command = obj["command"]
    #print("Command raw", command)
    command = "cd "+obj["directory"]+ " && " + command
    print("COMMAND>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> in", obj["directory"])
    print(command)
    messages.append({"role": "assistant", "content": response.choices[0].message.content})
    if (END == command): break

    if input("continue?(no)") == "no": break

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

    output = result.stdout
    errors = result.stderr

    print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<OUTPUT:\n", output)
    
    responseContent = "stdout:\n"+output+"\n"
    if errors != "":
        print("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<Errors:\n", errors)
        responseContent += "stderr:\n"+errors+"\n "

    messages.append({"role":"user", "content": responseContent})


print("Loop finished. ")

