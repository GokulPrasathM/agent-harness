"""Minimal FastAPI server for production deployment."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import tools to trigger registration
import app.tools.calculator
import app.tools.database
import app.tools.gokul_profile
import app.tools.read_url
import app.tools.web_search
from app.agent.loop import run_agent
from app.agent.state import RunResult
from app.core.config import load_settings
from app.core.logging import setup_logging
from app.tools.registry import registry

# --- Setup ---
settings = load_settings()
cfg = settings.yaml_config
setup_logging(level=cfg.logging.level, log_file=cfg.logging.log_file)

app = FastAPI(
    title=f"{cfg.agent.name} API",
    description="Production-grade AI agent",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Models ---
class ChatRequest(BaseModel):
    message: str


# --- Routes ---
@app.get("/health")
async def health():
    return {"status": "ok", "agent": cfg.agent.name, "model": cfg.agent.model}


@app.post("/chat", response_model=RunResult)
async def chat(request: ChatRequest):
    return await run_agent(request.message, settings, registry)


@app.get("/tools")
async def list_tools():
    return {"tools": registry.list_tools()}
