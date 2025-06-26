from fastapi import FastAPI
from pydantic import BaseModel
from tinydb import TinyDB, Query
from cryptography.fernet import Fernet
from datetime import datetime
import os

# ----------------------------
# FastAPI App
# ----------------------------
app = FastAPI(title="Secure Vault API")
db = TinyDB("vault.json")
Vault = Query()

# ----------------------------
# Encryption Key Handling
# ----------------------------
if not os.path.exists("vault.key"):
    with open("vault.key", "wb") as f:
        f.write(Fernet.generate_key())

with open("vault.key", "rb") as f:
    key = f.read()

fernet = Fernet(key)

# ----------------------------
# Helper Functions
# ----------------------------
def encrypt(text: str) -> str:
    return fernet.encrypt(text.encode()).decode()

def decrypt(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()

def current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ----------------------------
# Pydantic Models
# ----------------------------
class VaultEntry(BaseModel):
    platform: str
    username: str
    password: str

class VaultQuery(BaseModel):
    platform: str
    username: str

class VaultUpdate(BaseModel):
    platform: str
    username: str
    new_password: str

# ----------------------------
# API Endpoints
# ----------------------------

@app.post("/vault/add")
def add_account(entry: VaultEntry):
    if db.search((Vault.platform == entry.platform) & (Vault.username == entry.username)):
        return {"message": "Account already exists"}
    db.insert({
        "platform": entry.platform,
        "username": entry.username,
        "password": encrypt(entry.password),
        "timestamp": current_time()
    })
    return {"message": "Account added"}

@app.post("/vault/get")
def get_account(query: VaultQuery):
    result = db.search((Vault.platform == query.platform) & (Vault.username == query.username))
    if not result:
        return {"message": "Account not found"}
    record = result[0]
    return {
        "platform": record["platform"],
        "username": record["username"],
        "password": decrypt(record["password"]),
        "timestamp": record["timestamp"]
    }

@app.put("/vault/update")
def update_account(update: VaultUpdate):
    if not db.search((Vault.platform == update.platform) & (Vault.username == update.username)):
        return {"message": "Account not found"}
    db.update({
        "password": encrypt(update.new_password),
        "timestamp": current_time()
    }, (Vault.platform == update.platform) & (Vault.username == update.username))
    return {"message": "Password updated"}

@app.delete("/vault/delete")
def delete_account(query: VaultQuery):
    if not db.search((Vault.platform == query.platform) & (Vault.username == query.username)):
        return {"message": "Account not found"}
    db.remove((Vault.platform == query.platform) & (Vault.username == query.username))
    return {"message": "Account deleted"}

@app.get("/vault/list")
def list_accounts():
    records = db.all()
    return [
        {
            "platform": r["platform"],
            "username": r["username"],
            "timestamp": r["timestamp"]
        }
        for r in records
    ]
