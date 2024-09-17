import os
import subprocess
from ai_shell.util import codeblock

def create_markdown_from_git_files(directory):

    os.chdir(directory)

    git_files = subprocess.check_output(["git", "ls-files"], text=True).splitlines()

    markdown_content = ["# Project files"]

    for filename in git_files:
        if filename == "LICENSE":
            continue
        with open(filename, "r") as file:
            content = file.read()
            markdown_content.append(f"## {filename}")
            markdown_content.append(codeblock(content))

    return "\n".join(markdown_content)

print(create_markdown_from_git_files("."))

