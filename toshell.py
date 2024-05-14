from openai import OpenAI
import subprocess

END = "I AM DONE!"

with open("openai.key", 'r') as file:
    api_key = file.read()

client = OpenAI(api_key=api_key)
import os


goal = "Check if there are any git changes, and if there are, commit them. Then push."

messages=[{"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "You are connected to a linux shell. Your whole response will be passed into it. You will get both the stdout and stderr streams back as a response. Once you see by the response, that you are done, respond with `"+END+"` to indicate that you are finished. Your goal is:  "+goal}]

while True:
    response = client.chat.completions.create(model="gpt-4o", messages=messages)
    command = response.choices[0].message.content
    print("Command raw", command)
    if (END == command): break
    command = command.lstrip("```sh").rstrip("```")
    print("clean", command)
    messages.append({"role": "assistant", "content": response.choices[0].message.content})

    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

    # Get the standard output (stdout)
    output = result.stdout
    # Get the standard error (stderr), if needed
    errors = result.stderr

    print("output:", output)
    print("Errors:", errors)

    messages.append({"role":"user", "content":
        "Output: "+output+"\\nErrors"+errors+"\\n Enter next command:"})


print("Loop finished. ")

