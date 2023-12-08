from openai import OpenAI
client = OpenAI()


tokens = [
    47991,#great,
    4869,11458,#however
    ]


completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": open("prompts/default.txt", 'r').read()},
    {"role": "user", "content": "What makes a breakfast great?"}, ],
  logit_bias=dict.fromkeys(tokens, 25)
)

print(completion.choices[0].message.content)
