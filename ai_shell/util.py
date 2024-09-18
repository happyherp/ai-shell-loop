import os
import shutil

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
    code_block_delimiter = "```"
    while code_block_delimiter in code:
        # enlarge delimiter if the current one is already in the code.
        code_block_delimiter += "`"
    return f"{code_block_delimiter}\n{code}{code_block_delimiter}"

def get_folder_content() -> str:
    """Returns a string listing files and directories with type indicator (file or directory)."""
    current_directory = os.getcwd()
    items = os.listdir(current_directory)

    result = f"Files in the current directory({current_directory}): \n"
    character_limit = 2000

    for item in items:
        full_path = os.path.join(current_directory, item)
        if os.path.isfile(full_path):
            entry = f"{item} [File]\n"
        elif os.path.isdir(full_path):
            entry = f"{item} [Directory]\n"
        else: continue

        # Check if adding this entry would exceed the character limit
        if len(result) + len(entry) > character_limit:
            result += "... Extra files skipped.\n"
            break

        result += entry

    return result