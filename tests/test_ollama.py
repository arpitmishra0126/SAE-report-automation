from ollama import chat

response = chat(
    model="qwen3:8b",
    messages=[
        {
            "role": "user",
            "content": "Say Hello in one sentence."
        }
    ],
)

print(response["message"]["content"])