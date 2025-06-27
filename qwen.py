from llama_cpp import Llama
import sys
import os
os.environ["LLAMA_CPP_LOG_LEVEL"] = "ERROR"
sys.stderr = open(os.devnull, 'w')

llm = Llama(model_path="tinyllama-1.1b-chat-v1.0.Q3_K_L.gguf", n_ctx=512, n_threads=4,temperature=0.0)

response = llm("Q:tell me about india?\nA:", max_tokens=100)
print(response["choices"][0]["text"])
