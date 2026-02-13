from typing import Optional, Dict, Any, List
import time
import uuid
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Body, HTTPException, status
from pydantic import BaseModel, Field

from app.agent.graph import agent_graph

load_dotenv()

# -------- Models --------
class AgentConfig(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = 0.7

class CreateSessionRequest(BaseModel):
    agent_config: Optional[AgentConfig] = None

class MessageRequest(BaseModel):
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# -------- App --------
app = FastAPI()
START_TIME = time.time()

# Use ONE store for sessions
sessions: Dict[str, Dict[str, Any]] = {}


# -------- Routes --------
@app.get("/")
def home():
    return {"message": "Cyndx LangGraph API running"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime_seconds": int(time.time() - START_TIME),
        "checks": {"llm_provider": "ok", "checkpoint_store": "ok"},
    }

@app.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_session(req: CreateSessionRequest = Body(default={})):
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat() + "Z"

    agent_cfg = req.agent_config or AgentConfig()

    sessions[session_id] = {
        "session_id": session_id,
        "created_at": now,
        "status": "active",
        "agent_config": agent_cfg.model_dump(),
        "messages": [],
    }

    return {
        "session_id": session_id,
        "created_at": now,
        "status": "active",
        "agent_config": agent_cfg.model_dump(),
    }

@app.get("/sessions/{session_id}/history")
def get_session_history(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "message_count": len(session["messages"]),
        "messages": session["messages"],
    }
from fastapi import HTTPException

@app.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
        del sessions[session_id]
        return

@app.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, payload: MessageRequest):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    user_text = payload.content
    start_time = time.time()

    # Store user message
    user_msg = {
        "message_id": f"msg_{uuid.uuid4().hex[:10]}",
        "role": "user",
        "content": user_text,
        "metadata": payload.metadata,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    session["messages"].append(user_msg)

    # Build LangGraph state (use full conversation so it has context)
    state = {
        "session_id": session_id,
        "messages": [{"role": m["role"], "content": m["content"]} for m in session["messages"]],
        "user_input": user_text,
        "response": "",
        "next_node": "planner",
    }

    # Call LangGraph (VALID because we're inside async endpoint)
    result = await agent_graph.ainvoke(state)

    # Extract assistant reply
    assistant_text = ""
    msgs = result.get("messages", [])
    for m in reversed(msgs):
        if m.get("role") == "assistant" and m.get("content"):
            assistant_text = m["content"].strip()
            break
    if not assistant_text:
        assistant_text = (result.get("response") or "").strip()

    # Store assistant message
    assistant_msg = {
        "message_id": f"msg_{uuid.uuid4().hex[:10]}",
        "role": "assistant",
        "content": assistant_text,
        "metadata": {},
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    session["messages"].append(assistant_msg)

    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "message_id": assistant_msg["message_id"],
        "session_id": session_id,
        "role": "assistant",
        "content": assistant_text,
        "tool_calls": [],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "llm_calls": 1,
        },
        "latency_ms": latency_ms,
        "created_at": assistant_msg["created_at"],
    }
