from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Dict

app = FastAPI(title="Sherly Multi-User API")

# Simple user session store
user_sessions: Dict[str, Dict] = {}

class User(BaseModel):
    username: str
    token: str

def get_current_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="token"))):
    if token not in user_sessions:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user_sessions[token]

@app.get("/status")
def read_status(current_user: Dict = Depends(get_current_user)):
    return {"status": "online", "user": current_user["username"]}

@app.post("/command")
def execute_command(command: str, current_user: Dict = Depends(get_current_user)):
    # Here we would route the command with session-isolated memory
    return {"result": f"Executed for {current_user['username']}", "command": command}

def start_multi_user_api(port: int = 8080):
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
