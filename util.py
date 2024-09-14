import os
from openai import OpenAI
import shutil

def createClient():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir,  './openai.key')

    with open(file_path, 'r') as file:
        api_key = file.read().strip()

    return OpenAI(api_key=api_key)
    

def systemMsg(content): return msg("system", content)
def userMsg(content): return msg("user", content)
def assistantMsg(content):  return msg("assistant", content)
def msg(role, content):  return {"role": role, "content": content}



def ensure_empty_directory(path):
    # Check if the directory exists
    if os.path.exists(path):
        # If it exists, remove it and all its contents
        shutil.rmtree(path)

    # Recreate the directory as empty
    os.makedirs(path)