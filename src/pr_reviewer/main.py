"""First call to the Claude API.

Goal: send one message to the model and read its answer,
including how many tokens (and therefore how much money) it used.
"""

import anthropic
from dotenv import load_dotenv

# Read the variables from the .env file into the environment,
# so ANTHROPIC_API_KEY is available without writing it in the code
load_dotenv()

# The client is our "phone line" to the API.
# It finds ANTHROPIC_API_KEY in the environment automatically.
client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-5-5",  # which model answers
    max_tokens=500,  # hard cap on the answer length (cost control)
    messages=[
        # The conversation is a list of messages.
        # Each message has a role ("user" or "assistant") and its content.
        {"role": "user", "content": "Explain what a Pull Request is in one sentence."}
    ],
)

# response.content is a list of blocks. The first block holds the text.
print(response.content[0].text)

print(f"Tokens: {response.usage.input_tokens} in / {response.usage.output_tokens} out.")
