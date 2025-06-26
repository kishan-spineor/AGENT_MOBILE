# === main.py ===
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFacePipeline
import json
from dotenv import load_dotenv
from vault import add_account, get_account, update_account, delete_account
from langchain_google_genai import ChatGoogleGenerativeAI
load_dotenv()


app = FastAPI()

# === Load Qwen LLM ===
model_id = "Qwen/Qwen3-0.6B"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True)
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=128,do_sample=True,
    temperature=0.8,
    top_k=50,
    top_p=0.95,
    repetition_penalty=1.2)
llm = HuggingFacePipeline(pipeline=pipe)
llm2 = ChatGoogleGenerativeAI(model='gemini-1.5-pro')
intent_prompt = PromptTemplate(
    input_variables=["text"],
    template="""
You are an assistant that converts user input into structured JSON commands.

The format must be:
{{
  "action": "GET" | "ADD" | "UPDATE" | "DELETE",
  "platform": "<platform_name>",
  "username": "<username or null>",
  "password": "<only for ADD/UPDATE or null>"
}}

User input: {text}
JSON:
"""
)

intent_chain = intent_prompt | llm2

# === Input Model ===
class UserInput(BaseModel):
    text: str

# === Natural Language API ===
@app.post("/ask")
def ask_question(user_input: UserInput):
    result = intent_chain.invoke({"text": user_input.text})
    print(result.content)
    try:
        json_start = result.find("{")
        json_data = json.loads(result[json_start:])

        action = json_data.get("action")
        platform = json_data.get("platform")
        username = json_data.get("username")
        password = json_data.get("password")

        if not platform:
            return {"message": "Which platform are you referring to?"}
        if not username:
            return {"message": f"Which username for {platform}?"}

        if action == "GET":

            return get_account(platform, username)

        elif action == "ADD":
            if not password:
                return {"message": "Missing password for ADD"}
            return add_account(platform, username, password)

        elif action == "UPDATE":
            if not password:
                return {"message": "Missing new password for UPDATE"}
            return update_account(platform, username, password)

        elif action == "DELETE":
            return delete_account(platform, username)

        else:
            return {"message": f"Unknown action '{action}'"}

    except Exception as e:
        return {"error": "Failed to parse or process request", "details": str(e)}


#uvicorn main:app --port 8080 --reload