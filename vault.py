# === vault.py ===
from tinydb import TinyDB, Query
from cryptography.fernet import Fernet
from datetime import datetime
import os

# Database & Query object
db = TinyDB("vault.json")
Vault = Query()

# Encryption setup
if not os.path.exists("vault.key"):
    with open("vault.key", "wb") as f:
        f.write(Fernet.generate_key())
with open("vault.key", "rb") as f:
    fernet = Fernet(f.read())

def encrypt(text):
    return fernet.encrypt(text.encode()).decode()

def decrypt(token):
    return fernet.decrypt(token.encode()).decode()

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# CRUD operations
def add_account(platform: str, username: str, password: str):
    """Add a new account with encrypted password."""
    if db.search((Vault.platform == platform) & (Vault.username == username)):
        return {"message": "Account already exists"}
    db.insert({
        "platform": platform.lower(),
        "username": username.lower(),
        "password": encrypt(password),
        "timestamp": now()
    })
    return {"message": "Account added"}

def get_account(platform: str, username: str):
    """Retrieve and decrypt password for given platform and username."""
    result = db.search((Vault.platform == platform.lower()) & (Vault.username == username.lower()))
    if not result:
        return {"message": "Account not found"}
    record = result[0]
    return {
        "platform": record["platform"],
        "username": record["username"],
        "password": decrypt(record["password"]),
        "timestamp": record["timestamp"]
    }

def update_account(platform: str, username: str, new_password: str):
    """Update password for an existing account."""
    if not db.search((Vault.platform == platform.lower()) & (Vault.username == username.lower())):
        return {"message": "Account not found"}
    db.update({
        "password": encrypt(new_password),
        "timestamp": now()
    }, (Vault.platform == platform.lower()) & (Vault.username == username.lower()))
    return {"message": "Password updated"}

def delete_account(platform: str, username: str):
    """Delete account based on platform and username."""
    if not db.search((Vault.platform == platform.lower()) & (Vault.username == username.lower())):
        return {"message": "Account not found"}
    db.remove((Vault.platform == platform.lower()) & (Vault.username == username.lower()))
    return {"message": "Account deleted"}

def add_reminder(title, datetime, name="", note="", repeat="none"):
    db.insert({
        "type": "reminder",
        "name": name.lower(),
        "title": title,
        "datetime": datetime,
        "note": note,
        "repeat": repeat
    })
    return "Reminder added."




def get_reminders(name: str = None):
    Reminder = Query()
    if name:
        return db.search((Reminder.type == "reminder") & (Reminder.name == name.lower()))
    return db.search(Reminder.type == "reminder")


def delete_reminder(title):
    result = db.remove((Query().type == "reminder") & (Query().title == title))
    return "Deleted" if result else "Reminder not found."