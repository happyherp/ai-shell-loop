from openai import OpenAI
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageToolCall
client = OpenAI()


tokens = [
    47991,#great,
    4869,11458,#however
    ]
    
tools = [
  {
    "type": "function",
    "function": {
      "name": "send_email",
      "description": "Sent an plain text email to a single person",
      "parameters": {
        "type": "object",
        "properties": {
          "recipient": {
            "type": "string",
            "description": "The email address of the recipient. For example karls@gmail.com",
          },
          "subject": {
            "type": "string",
            "description": "subject line",
          },  
          "body": {
            "type": "string",
            "description": "The main body of the email as plain text.",
          }
        },
        "required": ["recipient"],
      },
    }
  },
  {
    "type": "function",
    "function": {
      "name": "notify",
      "description": "Causes a message to be sent to you later. You can use this, to communicate with the user or perform actions at a later point in time",
      "parameters": {
        "type": "object",
        "properties": {
          "message": {
            "type": "string",
            "description": "Any content. Might be used to transmit information about the thing that is supposed to be done later. ",
          },
          "time": {
            "type": "string",
            "description": "The time at which you want to be notified. In ISO 1691",
          }
        },
        "required": ["time"],
      },
    }
  }  
]


completion = client.chat.completions.create(
  model="gpt-4",
  messages=[
    {"role": "system", "content": open("prompts/default.txt", 'r').read()},
    {"role": "user", "content": """
    Sent an email congratulating my aunt to her 53. Birthday, which is on the 24.12.2024. She likes cats. 
    Her email is steffi@gmail.com. 
    Sent it on her birthday. Not today. 
    """},
    ChatCompletionMessage(content="blub", role='assistant',
        tool_calls=[ChatCompletionMessageToolCall(
            id='call_9MEpHPZYqdxibA0dD8WQ533M', function={
                "arguments":'{\n  "message": "Send birthday email to aunt",\n  "time": "2024-12-24T08:00:00Z"\n}', 
                "name":'notify'}, type='function')]),
    {"role": "tool", "content": "Send birthday email to aunt", "name":"notify",
        "tool_call_id" : "call_9MEpHPZYqdxibA0dD8WQ533M"} ],
  #logit_bias=dict.fromkeys(tokens, 25),
  tools=tools,
  temperature=1.0
)

print(completion.choices[0].message)
