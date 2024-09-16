import os
from openai import OpenAI
import shutil


def create_client():
    return OpenAI()


def system_msg(content):
    return msg("system", content)


def user_msg(content):
    return msg("user", content)


def assistant_msg(content):
    return msg("assistant", content)


def msg(role, content):
    return {"role": role, "content": content}


def ensure_empty_directory(path):
    # Check if the directory exists
    if os.path.exists(path):
        # If it exists, remove it and all its contents
        shutil.rmtree(path)

    # Recreate the directory as empty
    os.makedirs(path)


def codeblock(code: str):
    return "```\n" + code + "\n```\n"
