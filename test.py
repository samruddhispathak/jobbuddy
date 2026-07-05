from groq import Groq

client = Groq(api_key="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")

response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
    messages=[
        {"role": "user", "content": "Say hello in 3 languages"}
    ]
)

print(response.choices[0].message.content)