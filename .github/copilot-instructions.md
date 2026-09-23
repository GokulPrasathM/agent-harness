# Agent Forge — AI Assistant Context
# Agent Harness — AI Assistant Context

This file helps AI coding assistants (GitHub Copilot, Cursor, Cody, etc.) understand this project.
This file helps AI coding assistants (GitHub Copilot, Cursor, Cody, Antigravity, etc.) understand this project.

## What is this?

Agent Forge is a production-grade, forkable AI agent template. It's NOT a framework — it's a starter kit.
**Agent Harness** is a production-grade, forkable AI agent template based on the principle:
> **Agent = Model + Harness Engineering**

It's NOT a heavy framework — it's a minimal, robust starter kit.
The core agent loop is ~150 lines of Python. Users fork, configure via `agent.yaml`, and deploy.

## Architecture

```
agent.yaml (config)  →  Scope Guardrail  →  Agent Loop (ReAct)  →  Final Answer
                              ↓                    ↓
                         Reject if              Tool calls
                         off-scope              (calculator, web_search, read_url)
                         off-scope              (calculator, web_search, read_url,
                                                 sql_query, sql_execute, sql_describe)
```

## Key Files

- `agent.yaml` — ALL agent configuration (identity, model, scope, limits, tools)
- `.env` — API keys (NEVER commit this file)
- `agent.yaml` — ALL agent configuration (identity, model, scope, limits, tools, database)
- `.env` — API keys & database connection (NEVER commit this file)
- `app/agent/loop.py` — The core ReAct loop. This is the heart of the agent.
- `app/agent/guardrail.py` — Scope boundary checker (rejects off-topic inputs)
- `app/agent/state.py` — Pydantic models: RunResult, ScopeResult, RunStatus
- `app/agent/prompts.py` — System prompt builder
- `app/tools/registry.py` — Tool registration system (@tool decorator)
- `app/tools/*.py` — Built-in tools (calculator, web_search, read_url)
- `app/tools/calculator.py` — Built-in: safe math evaluation
- `app/tools/web_search.py` — Built-in: web search (Tavily + DuckDuckGo)
- `app/tools/read_url.py` — Built-in: fetch URL content
- `app/tools/database.py` — Built-in: SQL database management (SQLite default)
- `app/tools/_template.py` — Copy-paste template for new tools
- `app/core/config.py` — Loads .env + agent.yaml into typed Settings
- `app/core/cost.py` — Cost tracking with budget circuit breaker
- `app/core/logging.py` — Structlog setup
- `app/cli.py` — Local CLI (chat, run, tools, config commands)
- `app/server.py` — FastAPI server for production deployment

## How to Add a New Tool

1. Copy `app/tools/_template.py` to `app/tools/my_tool.py`
2. Define a Pydantic input model for your tool's arguments
3. Implement the function with `@registry.register(name, description, args_model)`
4. Import it in `app/cli.py` and `app/server.py` (add `import app.tools.my_tool`)
5. Add the tool name to `tools.enabled` in `agent.yaml`

## How to Change the Model

Edit `agent.model` in `agent.yaml`. Uses LiteLLM format:
- OpenAI: `openai/gpt-4o`, `openai/gpt-4o-mini`
- Anthropic: `anthropic/claude-3-5-sonnet-20241022`
- Gemini: `gemini/gemini-2.0-flash`
- Local (Ollama): `ollama/llama3.1`

## How to Enable Strict Scope

Set `scope.enabled: true` in `agent.yaml` and describe what the agent should respond to.

## How to Configure the Database

Default: local SQLite file (`agent_forge.db`) — zero config needed.
Default: local SQLite file (`agent_harness.db`) — zero config needed.

```yaml
# agent.yaml
database:
  path: "agent_forge.db"     # Change the SQLite file path
  path: "agent_harness.db"     # Change the SQLite file path
```

For external databases, set `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

Database tools available:
- `sql_query` — Read-only SELECT queries
- `sql_execute` — Write queries (CREATE, INSERT, UPDATE, DELETE)
- `sql_describe` — List all tables with schemas

## Code Conventions

- ALL data models use Pydantic v2
- Async-first (use `async def` for tools that do I/O)
- Tool errors are returned as strings to the LLM (never crash the loop)
- Config is loaded once at startup, passed through as `Settings`
- Logging uses structlog (JSON format for files, colored for console)
- Database uses stdlib sqlite3 (zero external deps)

## Anti-Patterns (DON'T do these)

- ❌ Never put API keys in code — use `.env`
- ❌ Never use `eval()` — use the safe AST-based calculator
- ❌ Never skip Pydantic validation for tool inputs
- ❌ Never let tool errors crash the agent loop — always catch and return error strings
- ❌ Never remove the iteration/cost/timeout circuit breakers
- ❌ Never commit `.env` or `*.db` to git

## Common Tasks

- **Run locally**: `uv run agent-harness chat` (or `uv run python -m app.cli chat`)
- **Single query**: `uv run agent-harness run "What is 2+2?"`
- **Deploy**: Push to ANY branch → GitHub Action auto-deploys
- **Add a tool**: Copy `_template.py`, implement, register, import
- **Change scope**: Edit `scope` section in `agent.yaml`
- **Change database**: Edit `database.path` in `agent.yaml` or set `DATABASE_URL` in `.env`

---

## Helping Prompts for AI Assistants

If you're new to this project, try asking your AI assistant these questions:

### Getting Started
- "Explain the architecture of this project"
- "What does agent.yaml configure?"
- "How does the agent loop work in loop.py?"

### Building Features
- "Help me add a new tool that sends emails"
- "How do I make the agent only answer coding questions?"
- "Help me add a custom system prompt for a customer support bot"
- "How do I connect this to a Postgres database?"

### Database Tasks
- "Help me create a schema for a user management system"
- "How do I add a tool that queries my database?"
- "Show me how to use sql_execute to create a users table"

### Debugging
- "Why isn't my tool being called by the agent?"
- "How do I see the full conversation history?"
- "Why is the agent hitting the cost limit?"

### Deployment
- "Help me deploy this to Railway"
- "How do I set up the GitHub Action for auto-deploy?"
- "What secrets do I need to set in GitHub?"
