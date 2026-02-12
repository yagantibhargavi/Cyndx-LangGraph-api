from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from fastapi import status
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

from fastapi import FastAPI, Body
from app.agent.graph import agent_graph

class AgentConfig(BaseModel):
    model: str = "gpt-4o-mini"
    temperature: float = 0.7

class CreateSessionRequest(BaseModel):
    agent_config: Optional[AgentConfig] = None

class MessageRequest(BaseModel):
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


app = FastAPI()

import time

START_TIME = time.time()

@app.get("/")
def home():
    return {"message": "Cyndx LangGraph API running"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime_seconds": int(time.time() - START_TIME),
        "checks": {
            "llm_provider": "ok",
            "checkpoint_store": "ok"
        }
    }
import uuid
from datetime import datetime

sessions = {}

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
from fastapi import HTTPException

@app.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, payload: MessageRequest):
    if session_id not in sessions:
        return {"error": "Session not found"}

    user_text = payload.content
    start_time = time.time()

    # Build LangGraph state
    state = {
        "session_id": session_id,
        "messages": [{"role": "user", "content": user_text}],
        "user_input": user_text,
        "response": "",
        "next_node": "planner",
    }

    # Call LangGraph
    result = await agent_graph.ainvoke(state)

    # Extract assistant reply from messages
    assistant_text = ""
    msgs = result.get("messages", [])

    for m in reversed(msgs):
        if m.get("role") == "assistant" and m.get("content"):
            assistant_text = m["content"].strip()
            break

    # fallback
    if not assistant_text:
        assistant_text = (result.get("response") or "").strip()

    # Generate message_id
    message_id = f"msg_{uuid.uuid4().hex[:10]}"
    latency_ms = int((time.time() - start_time) * 1000)

    return {
        "message_id": message_id,
        "session_id": session_id,
        "role": "assistant",
        "content": assistant_text,
        "tool_calls": [],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "llm_calls": 1
        },
        "latency_ms": latency_ms,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
