# === LLM + Agent Setup ===

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Union
from vault import add_account, get_account, update_account, delete_account,add_reminder,delete_reminder,get_reminders

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


@tool
def add_reminders(input: Union[str, dict]):
    """
    Add a reminder with title, datetime (YYYY-MM-DD HH:MM), and optional note.
    """
    if isinstance(input, str):
        input = json.loads(input)
    title = input.get("title")
    datetime_val = input.get("datetime")
    note = input.get("note", "")
    if not title or not datetime_val:
        return "Please provide both title and datetime."
    return add_reminder(title, datetime_val, note)

@tool
def list_reminders(_: Union[str, dict]):
    """
    List all saved reminders.
    """
    return get_reminders()

@tool
def delete_reminder_tool(input: Union[str, dict]):
    """
    Delete a reminder by title.
    """
    if isinstance(input, str):
        input = json.loads(input)
    title = input.get("title")
    if not title:
        return "Please provide a reminder title."
    return delete_reminder(title)





# === Step 2: Register Tools ===
tools = [get_password, add_password, update_password,delete_password,delete_reminder_tool,list_reminders,add_reminders]


# === Step 3: Initialize LLM ===
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")

llm2 = LlamaCpp(
    model_path="tinyllama-1.1b-chat-v1.0.Q3_K_L.gguf",
    n_ctx=512,
    n_threads=4,
    temperature=0.7,

)





# === Step 4: Setup Agent ===
prompt_react = hub.pull("hwchase17/react")


agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt_react
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True
)


# === Step 5: Define API ===
class UserInput(BaseModel):
    text: str

@app.post("/agent")
def ask_agent(user_input: UserInput):
    response = agent_executor.invoke({"input": user_input.text})
    # response = agent_executor.run(user_input)
    return {"response": response}

