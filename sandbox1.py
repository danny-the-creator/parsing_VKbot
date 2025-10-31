from langchain_ollama import OllamaLLM

chat_model = OllamaLLM(model="llama3.1")

PROMPT = """I don't understand the following expression: <<{expression}>>. Please explain me what does it mean in easy way with some examples"""

print(chat_model.invoke(PROMPT.format(expression="Skibidi Toilet")))