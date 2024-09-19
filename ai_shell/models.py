from typing import List, Optional

from pydantic import BaseModel, Field


class CommandPlan(BaseModel):
    plan: str = Field(description="Describe how you plan to achieve the goal in plain english")
    directory: str = Field(description="the absolute path in which the command should be executed")
    command: str = Field(
        description="the shell command to be executed to achieve the goal. The command should return 0 if it worked.")
    check_command: str = Field(description="Another shell command. It will be executed after 'command' "
                                           + "has been successfully executed. This command must be used to check if "
                                           + "'command' has actually achieved its goal.")
    used_commands: List[str] = Field(
        description="A list of all the different commands, without arguments that must be available for the command to work. ",
        examples=[["ls", "cat", "grep", "apt-get"], ["ping"]])


class AiResponse(BaseModel):
    command_options: List[CommandPlan] = Field(description=
                                               "A list of different approaches to solve the goal. The best ones should come first.")

    task_completed: bool = Field(description="""
    Set this to `true`, if you confirmed that you have completed the task and no further actions are necessary.
    If this is `true`, command_options should be empty. This field is not optional. 
    """)


class Iteration(BaseModel):
    command_plan: CommandPlan = Field(description="The CommandPlan that was executed.")
    userinput: Optional[str] = Field(default=None, description=
    "The input the user gave after seeing the command and plan. "
    + "Empty string means the user was ok with the command. null means no user input was given. "
    + "Another string means the user did not want to execute the command. "
    + "The string is the reason why. It is to be considered as an amendment or extension of the original goal.")
    missing_commands: Optional[List[str]] = Field(default=None, description=
    "Commands that where not available and the shell. For that reason, the command was not executed.")
    shell_output: Optional[str] = Field(default=None, description=
    "If the command of the CommandPlan was executed, this contains the stdout, stderr and result code.")
    check_shell_output: Optional[str] = Field(default=None, description=
    "If the check_command of the CommandPlan was executed, this contains the stdout, stderr and result code.")
