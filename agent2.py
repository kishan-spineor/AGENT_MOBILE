# === LLM + Agent Setup ===

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Union
from vault import add_account, get_account, update_account, delete_account
from langchain.prompts import PromptTemplate
from langchain.agents import tool, create_react_agent, AgentExecutor
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain import hub
from langchain_community.llms import LlamaCpp
import sys
import json
from dotenv import load_dotenv
import os
load_dotenv()
os.environ["LLAMA_CPP_LOG_LEVEL"] = "ERROR"
sys.stderr = open(os.devnull, 'w')
app = FastAPI()

# === Step 1: Define Tools ===

@tool
def get_password(input: Union[str, dict]):
    """
    Retrieve password for a given platform and username.
    Input must include: platform, username.
    """
    if isinstance(input, str):
        input = json.loads(input)

    platform = input.get("platform")
    username = input.get("username")

    if not platform or not username:
        return " Please provide both platform and username."

    return get_account(platform, username)


@tool
def add_password(input: Union[str, dict]):
    """
    Add a new password entry to the vault.
    Required fields: platform, username, password.
    """
    if isinstance(input, str):
        input = json.loads(input)

    platform = input.get("platform")
    username = input.get("username")
    password = input.get("password")

    if not platform or not username or not password:
        return "Please provide platform, username, and password."

    return add_account(platform, username, password)


@tool
def update_password(input: Union[str, dict]):
    """
    Update password for a given platform and username.
    Required fields: platform, username, password.
    """
    if isinstance(input, str):
        input = json.loads(input)

    platform = input.get("platform")
    username = input.get("username")
    password = input.get("password")

    if not platform or not username or not password:
        return "Please provide platform, username, and the new password."

    return update_account(platform, username, password)


@tool
def delete_password(input: Union[str, dict]):
    """
    Delete a password entry from the vault.
    Required fields: platform, username.
    """
    if isinstance(input, str):
        input = json.loads(input)

    platform = input.get("platform")
    username = input.get("username")

    if not platform:
        return "Please specify which platform account to delete."
    if not username:
        return "Please specify the username to delete."

    return delete_account(platform, username)


# === Step 2: Register Tools ===
tools = [get_password, add_password, update_password, delete_password]


# === Step 3: Initialize LLM ===
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")

llm2 = LlamaCpp(
    model_path="tinyllama-1.1b-chat-v1.0.Q3_K_L.gguf",
    n_ctx=2000,
    n_threads=4,
    temperature=0.0,

)


from langchain.prompts import PromptTemplate

custom_prompt = PromptTemplate.from_template("""
You are a helpful assistant that uses tools to answer questions.

You have access to the following tools:
{tools}

Use the following format:

Question: the question you must answer

Thought: think step-by-step about what to do
Action: the action to take, must be one of [{tool_names}]
Action Input: the JSON input to the action

Then observe the result and continue if needed.

When you are ready to answer, respond with:

Thought: I now know the final answer
Final Answer: the final answer to the original question

Begin!

Question: {input}
{agent_scratchpad}
""")



# === Step 4: Setup Agent ===
prompt_react = hub.pull("hwchase17/react")


agent = create_react_agent(
    llm=llm2,
    tools=tools,
    prompt=custom_prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=False,
    output_key="response"
)



# === Step 5: Define API ===
class UserInput(BaseModel):
    text: str

@app.post("/agent")
def ask_agent(user_input: UserInput):
    response = agent_executor.invoke({"input": user_input.text})
    # response = agent_executor.run(user_input)
    return {"response": response}

@app.post("/verify")
def home(id:int):
    print("hello")
    return {"id":id}

#uvicorn main:app --reload