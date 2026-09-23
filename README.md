# 🤖 Gokul AI — Personal Persona & Sandbox Agent

> **"Agent = Model + Harness Engineering"** — Customized as an interactive persona and playground agent for **Gokul Prasath M**.

This branch runs **Gokul AI**: an interactive agent anyone can chat with to explore Gokul's actual projects (Nika-1.5B, S2 dataset, RAG chatbot), education, skills, achievements, or play around with tools and SQL database queries. Built using the [Agent Harness](https://github.com/GokulPrasathM/agent-harness) template.

---

## ⚡ Quick Start

```bash
# 1. Clone
git clone https://github.com/GokulPrasathM/agent-harness.git
cd agent-harness

# 2. Install (requires Python 3.11+ and uv)
pip install uv
uv sync

# 3. Configure
cp .env.example .env
# Edit .env -> add your API key (e.g. OPENAI_API_KEY=sk-...)
# Edit agent.yaml -> customize identity, scope, model, tools

# 4. Chat
uv run agent-harness chat
# Or: uv run python -m app.cli chat
```

---

## 💡 What You Get

- **Config-driven agent** — Change identity, model, tools, database, and limits in `agent.yaml`
- **Scope guardrail** — Agent only responds to topics you define (toggle on/off in config)
- **Multi-provider** — OpenAI, Anthropic, Gemini, Ollama, OpenRouter via LiteLLM
- **Built-in tools** — Calculator, web search, URL reader, and SQL database management
- **Database built-in** — Local SQLite by default (`agent_harness.db`), swap to Postgres/MySQL via `DATABASE_URL`
- **Production safeguards** — Cost tracking, budget limits, retries with backoff, timeouts
- **Structured logging** — JSON logs for production monitoring, colored for development
- **One-push deploy** — Push to `deploy` branch -> GitHub Actions -> Railway/Render/Fly.io
- **AI-assisted DX** — Includes `.github/copilot-instructions.md` for Copilot, Cursor, Cody, etc.

---

## 🏛️ Architecture

```
agent.yaml          ->  Scope Guardrail  ->  Agent Loop (ReAct)  ->  Response
(your config)            (strict mode)      (bounded, safe)       (typed)
```

The core agent loop is ~150 lines in [`app/agent/loop.py`](app/agent/loop.py). Read it. Understand it. Own it.

---

## 🖥️ CLI Commands

| Command | Description |
|:---|:---|
| `uv run agent-harness chat` | Interactive chat session |
| `uv run agent-harness run "query"` | Single-shot query |
| `uv run agent-harness tools` | List available tools and their status |
| `uv run agent-harness config` | Inspect active configuration |

---

## 🗄️ Database

Agent Harness includes a built-in SQL database tool. The agent can create tables, insert data, run queries, and inspect schemas — all through natural conversation.

### Default: Local SQLite (zero config)

Works out of the box. Data is stored in `agent_harness.db`.

```yaml
# agent.yaml
database:
  path: "agent_harness.db"
```

### External Database

Set `DATABASE_URL` in `.env` for Postgres, MySQL, etc:

```bash
# .env
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### Database Tools

| Tool | What it does |
|:---|:---|
| `sql_query` | Read-only SELECT queries |
| `sql_execute` | Write operations (CREATE, INSERT, UPDATE, DELETE) |
| `sql_describe` | List all tables with schemas and row counts |

---

## 🛠️ Adding a Custom Tool

1. Copy [`app/tools/_template.py`](app/tools/_template.py) -> `app/tools/my_tool.py`
2. Define input schema using a Pydantic model
3. Implement function with `@registry.register()`
4. Import in `app/cli.py` and `app/server.py`
5. Add to `tools.enabled` in `agent.yaml`

---

## 🛡️ Strict Scope Mode

Keep your agent strictly bounded to its designated domain and reject off-topic questions before wasting tokens:

```yaml
# agent.yaml
scope:
  enabled: true
  description: "Customer support for Acme Corp products"
  rejection_message: "I can only help with Acme Corp product questions."
```

---

## 🚀 Deploy to Production

```bash
git checkout -b deploy
git push origin deploy
# GitHub Action builds Docker image and deploys
```

Configure your deploy target in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) (Railway, Render, or Fly.io).

Set API keys as repository secrets in GitHub -> **Settings -> Secrets and variables -> Actions**.

---

## 🤖 For AI-Assisted Developers (Copilot, Cursor, Cody, etc.)

This repo includes [`.github/copilot-instructions.md`](.github/copilot-instructions.md) which gives your AI coding assistant full project context. When you open this repo, your assistant already knows:

- How the architecture works
- How to add tools
- How to change models and config
- Code conventions and anti-patterns to avoid

**Try asking your assistant:**
- "Explain the agent loop in loop.py"
- "Help me add a tool that sends emails"
- "How do I connect to Postgres instead of SQLite?"
- "Help me set up strict scope for a customer support bot"

---

## 📖 For Developers Without AI Assistants

No AI coding assistant? No problem. Here is your roadmap:

### 1. Understand the Config
Open [`agent.yaml`](agent.yaml) — this is the single file that controls your agent's identity, model, scope, tools, database, and limits.

### 2. Understand the Core Loop
Read [`app/agent/loop.py`](app/agent/loop.py) — ~150 lines of Python that runs the agent:
1. Check scope guardrail -> reject if off-topic
2. Call LLM with system prompt + user message + tool schemas
3. If LLM requests tools -> execute them -> append results -> loop
4. If LLM gives final answer -> return

### 3. Understand Tools
Read [`app/tools/calculator.py`](app/tools/calculator.py) — simple, clear tool pattern:
1. Define a Pydantic model for inputs
2. Write a function
3. Decorate with `@registry.register(name, description, args_model)`

### 4. Prompts to Paste Into ChatGPT / Claude

**Understanding the project:**
> I'm working on a Python project called Agent Harness. It's an AI agent template with a ReAct loop in `app/agent/loop.py`, tool registration via Pydantic decorators, YAML config, and SQLite database tools. Help me understand [your question here].

**Adding a feature:**
> I have a Python AI agent template that uses a @registry.register decorator to add tools. Each tool has a Pydantic input model and an async function. Help me create a new tool that [describe what you want].

**Debugging:**
> My AI agent template uses LiteLLM to call LLMs and has a bounded ReAct loop with max_iterations, cost tracking, and tool execution. The agent is [describe the problem]. Here's the relevant code: [paste code].

---

## 📁 Project Structure

```
agent-harness/
├── agent.yaml              # Agent configuration
├── .env.example            # API key template
├── app/
│   ├── cli.py              # CLI interface
│   ├── server.py           # FastAPI server
│   ├── agent/
│   │   ├── loop.py         # Core agent loop (~150 lines)
│   │   ├── guardrail.py    # Scope enforcement
│   │   ├── state.py        # Typed models
│   │   └── prompts.py      # Prompt builder
│   ├── tools/
│   │   ├── registry.py     # Tool system
│   │   ├── calculator.py   # Built-in: math
│   │   ├── web_search.py   # Built-in: search
│   │   ├── read_url.py     # Built-in: fetch URLs
│   │   ├── database.py     # Built-in: SQL database
│   │   └── _template.py    # Copy to add tools
│   └── core/
│       ├── config.py       # Config loader
│       ├── logging.py      # Structured logging
│       └── cost.py         # Cost tracking
├── Dockerfile              # Production container
└── .github/
    ├── copilot-instructions.md  # AI assistant context
    └── workflows/deploy.yml     # CI/CD pipeline
```

---

## 🧰 Tech Stack

| Component | Choice |
|:---|:---|
| LLM Client | LiteLLM (100+ providers) |
| Validation | Pydantic v2 |
| CLI | Typer + Rich |
| API | FastAPI + Uvicorn |
| Database | SQLite (stdlib, zero deps) |
| Retries | Tenacity |
| Logging | structlog |
| HTTP | httpx |
| Deploy | Docker + GitHub Actions |

---

## 📄 License

MIT — fork it, ship it, make it yours.
