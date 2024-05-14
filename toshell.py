from openai import OpenAI

client = OpenAI(api_key='your_api_key_here')
import os


def execute_shell_command_from_gpt(prompt):
    response = client.chat.completions.create(model="gpt-4.0-turbo",
    messages=[{"role": "system", "content": "You are a helpful assistant."},
              {"role": "user", "content": prompt}])
    command = response.choices[0].message.content
    os.system(command)

execute_shell_command_from_gpt("Show me the current directory contents")
