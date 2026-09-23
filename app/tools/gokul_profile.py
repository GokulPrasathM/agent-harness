"""Custom tools for Gokul Prasath's personal AI agent.

Provides full transparency into Gokul's background, education, projects,
skills, GitHub live activity, and pre-seeds a relational database for
interactive SQL queries.
"""

from __future__ import annotations

import httpx
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.tools.database import _get_connection
from app.tools.registry import registry

log = get_logger("gokul-tools")

# --- Profile Data ---

GOKUL_BIO = {
    "name": "Gokul Prasath M",
    "role": "GenAI Engineer & AI/Data Science Student",
    "location": "India",
    "education": {
        "degree": "B.Tech in Artificial Intelligence & Data Science",
        "institution": "Dr. Mahalingam College of Engineering and Technology, Pollachi",
        "period": "2022 – Present",
    },
    "tagline": "Passionate GenAI engineer building intelligent, scalable AI applications.",
    "fun_fact": "I think I am funny 😄",
    "email": "beastgokul4@gmail.com",
    "links": {
        "github": "https://github.com/GokulPrasathM",
        "linkedin": "https://linkedin.com/in/gokul-prasathm",
        "huggingface": "https://huggingface.co/BeastGokul",
        "kaggle": "https://kaggle.com/beastgokul",
        "leetcode": "https://leetcode.com/beastgokul4",
        "hackerrank": "https://hackerrank.com/beastgokul4",
        "portfolio": "https://github.com/GokulPrasathM/portfolio",
    },
    "key_achievements": [
        "11 trophies & 45+ badges on Microsoft Learn",
        "26+ specialized certifications in AI, ML, and Data Science",
        "IBM Certified: AI Fundamentals, Data Fundamentals, Big Data",
        "Accenture iAspire Gold level winner",
        "10+ AI/ML awards at collegiate competitions",
        "Creator of Nika-1.5B (fine-tuned DeepSeek model on Hugging Face)",
        "Creator of the S2 dataset with 897K structured entries on Hugging Face",
    ],
    "experience": [
        {
            "role": "Software Development & Analysis Intern",
            "company": "CIBIE, Pollachi",
            "period": "Jun – Jul 2024",
            "highlights": [
                "Database schema design and ERP module development",
                "SQL-based data analysis and automated reporting",
                "Entity-Relationship (ER) diagrams for database planning",
            ],
        }
    ],
}

GOKUL_PROJECTS = [
    {
        "title": "Nika-1.5B: Domain-Focused LLM",
        "category": "llm",
        "tech_stack": "DeepSeek R1, S1 Dataset, PEFT/LoRA, PyTorch, Hugging Face",
        "description": "Fine-tuned DeepSeek R1 1.5B on the S1 dataset for high-accuracy domain-specific Q&A.",
        "link": "https://huggingface.co/BeastGokul/Nika-1.5B",
    },
    {
        "title": "S2 Dataset for LLM Training",
        "category": "dataset",
        "tech_stack": "Python, Web Scraping, Data Processing, Hugging Face Datasets",
        "description": "Scraped and structured 897K entries for fine-tuning LLMs with domain alignment.",
        "link": "https://huggingface.co/datasets/BeastGokul/s2",
    },
    {
        "title": "RAG Chatbot using Gemma-2B",
        "category": "rag",
        "tech_stack": "Gemma-2B, LangChain, ChromaDB, Hugging Face, Python",
        "description": "Domain-specific Retrieval Augmented Generation chatbot using LangChain and ChromaDB.",
        "link": "https://www.kaggle.com/code/beastgokul/rag-using-gemma-2-2b-it-langchain-and-chromadb",
    },
    {
        "title": "Structured Data Generator via Gemini 1.5",
        "category": "llm",
        "tech_stack": "Gemini 1.5 API, Prompt Engineering, JSON Schema, Python",
        "description": "Converts complex unstructured text into structured datasets leveraging Gemini's large context window.",
        "link": "https://www.kaggle.com/code/beastgokul/structured-data-generator-using-gemini",
    },
    {
        "title": "Formula 1 Driver Position Prediction",
        "category": "ml",
        "tech_stack": "Python, Scikit-learn, Pandas, Ensemble Models",
        "description": "ML predictor for Formula 1 race outcomes using historical lap times, grid positions, and weather conditions.",
        "link": "https://github.com/GokulPrasathM/Formula-1-Driver-Position-Prediction",
    },
    {
        "title": "Kinyarwanda-ASR",
        "category": "speech",
        "tech_stack": "PyTorch, Hugging Face Transformers, Audio Processing",
        "description": "Automatic speech recognition (ASR) research and model development for the Kinyarwanda language.",
        "link": "https://github.com/GokulPrasathM/Kinyarwanda-ASR",
    },
    {
        "title": "Bio-Medical Llama-3-8B Finetuned",
        "category": "llm",
        "tech_stack": "Llama 3 8B, QLoRA, Bio-Medical Corpus, Unsloth/Transformers",
        "description": "Fine-tuned Llama 3 on biomedical literature for clinical and scientific Q&A.",
        "link": "https://github.com/GokulPrasathM/Bio-Medical-Llama-3-8B-Finetuned",
    },
    {
        "title": "Cricket Match Outcome Predictor",
        "category": "ml",
        "tech_stack": "Python, Scikit-learn, IPL Ball-by-ball Dataset",
        "description": "Predictive model for IPL cricket match winners based on ball-by-ball and match-level metrics.",
        "link": "https://github.com/GokulPrasathM/Cricket-Match-Outcome-Predictor",
    },
    {
        "title": "Agent Harness",
        "category": "agent",
        "tech_stack": "Python, LiteLLM, Pydantic, FastAPI, SQLite, Docker, GitHub Actions",
        "description": "Production-grade forkable AI agent template based on 'Agent = Model + Harness Engineering'.",
        "link": "https://github.com/GokulPrasathM/agent-harness",
    },
]


# --- Seed Database Helper ---

def seed_gokul_db() -> str:
    """Populates local SQLite database with Gokul's data for interactive SQL querying."""
    conn = _get_connection()
    try:
        # Projects table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                tech_stack TEXT NOT NULL,
                description TEXT NOT NULL,
                link TEXT NOT NULL
            )
        """)

        # Skills table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                skill_name TEXT NOT NULL
            )
        """)

        # Achievements table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL
            )
        """)

        # Insert projects if table is empty
        cur = conn.execute("SELECT COUNT(*) FROM projects")
        if cur.fetchone()[0] == 0:
            for p in GOKUL_PROJECTS:
                conn.execute(
                    "INSERT INTO projects (title, category, tech_stack, description, link) VALUES (?, ?, ?, ?, ?)",
                    (p["title"], p["category"], p["tech_stack"], p["description"], p["link"])
                )

        # Insert skills if empty
        cur_skills = conn.execute("SELECT COUNT(*) FROM skills")
        if cur_skills.fetchone()[0] == 0:
            skills_data = [
                ("Languages", "Python"), ("Languages", "Java"), ("Languages", "C++"), ("Languages", "SQL"),
                ("AI & ML", "PyTorch"), ("AI & ML", "TensorFlow"), ("AI & ML", "Hugging Face"), ("AI & ML", "Transformers"),
                ("GenAI", "LangChain"), ("GenAI", "RAG"), ("GenAI", "PEFT / LoRA Fine-Tuning"), ("GenAI", "Prompt Engineering"),
                ("Backend & Tools", "FastAPI"), ("Backend & Tools", "REST APIs"), ("Backend & Tools", "ChromaDB"), ("Backend & Tools", "Git & Docker"),
                ("Cloud & Analytics", "Microsoft Azure"), ("Cloud & Analytics", "Power BI"), ("Cloud & Analytics", "Tableau")
            ]
            for cat, name in skills_data:
                conn.execute("INSERT INTO skills (category, skill_name) VALUES (?, ?)", (cat, name))

        # Insert achievements if empty
        cur_ach = conn.execute("SELECT COUNT(*) FROM achievements")
        if cur_ach.fetchone()[0] == 0:
            for ach in GOKUL_BIO["key_achievements"]:
                conn.execute("INSERT INTO achievements (title) VALUES (?)", (ach,))

        conn.commit()
        return "Database successfully populated with Gokul's projects, skills, and achievements."
    finally:
        conn.close()


# Automatically initialize the database tables on import
try:
    seed_gokul_db()
except Exception as e:
    log.warning("failed_to_seed_gokul_db", error=str(e))


# --- Tool 1: Get Bio & Transparency Info ---

class EmptyInput(BaseModel):
    """No arguments required."""


@registry.register(
    name="get_gokul_bio",
    description="Retrieve Gokul Prasath's complete biography, academic background, contact links, achievements, and transparency summary.",
    args_model=EmptyInput,
)
def get_gokul_bio() -> str:
    """Return formatted biography and profile details."""
    bio = GOKUL_BIO
    lines = [
        f"👤 {bio['name']} ({bio['role']})",
        f"📍 Location: {bio['location']}",
        f"🎓 Education: {bio['education']['degree']} at {bio['education']['institution']} {bio['education']['period']}",
        f"💡 About: {bio['tagline']}",
        f"😄 Fun fact: {bio['fun_fact']}",
        f"✉️ Contact: {bio['email']}",
        "\n🔗 Online Presence:",
    ]
    for platform, url in bio["links"].items():
        lines.append(f"  - {platform.capitalize()}: {url}")

    lines.append("\n🏆 Key Achievements & Certifications:")
    for ach in bio["key_achievements"]:
        lines.append(f"  - {ach}")

    lines.append("\n💼 Experience:")
    for exp in bio["experience"]:
        lines.append(f"  - {exp['role']} @ {exp['company']} {exp['period']}")
        for h in exp["highlights"]:
            lines.append(f"    • {h}")

    return "\n".join(lines)


# --- Tool 2: Search & Explore Projects ---

class ProjectsInput(BaseModel):
    category: str = Field(
        default="all",
        description="Filter projects by category: 'llm', 'rag', 'ml', 'dataset', 'speech', 'agent', or 'all'"
    )


@registry.register(
    name="get_gokul_projects",
    description="List and filter Gokul Prasath's featured AI/ML projects, datasets, and models with links.",
    args_model=ProjectsInput,
)
def get_gokul_projects(category: str = "all") -> str:
    """Return Gokul's projects filtered by category."""
    cat_lower = category.lower().strip()
    filtered = [
        p for p in GOKUL_PROJECTS
        if cat_lower in ("all", "") or p["category"].lower() == cat_lower
    ]

    if not filtered:
        return f"No projects found under category '{category}'. Available categories: all, llm, rag, ml, dataset, speech, agent."

    lines = [f"Found {len(filtered)} project(s) [Category: {category}]:\n"]
    for i, p in enumerate(filtered, 1):
        lines.append(f"{i}. 🚀 {p['title']}")
        lines.append(f"   Category: {p['category'].upper()}")
        lines.append(f"   Tech Stack: {p['tech_stack']}")
        lines.append(f"   Summary: {p['description']}")
        lines.append(f"   Link: {p['link']}\n")

    return "\n".join(lines)


# --- Tool 3: Live GitHub Repositories Lookup ---

class GitHubLiveInput(BaseModel):
    limit: int = Field(default=8, ge=1, le=30, description="Maximum number of repositories to fetch")


@registry.register(
    name="get_gokul_github_live",
    description="Query GitHub API directly for Gokul's latest live public repositories, descriptions, stars, and languages.",
    args_model=GitHubLiveInput,
)
async def get_gokul_github_live(limit: int = 8) -> str:
    """Fetch live public repositories directly from GitHub API."""
    url = f"https://api.github.com/users/GokulPrasathM/repos?sort=updated&per_page={limit}"
    headers = {"User-Agent": "GokulAgent/1.0"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            repos = resp.json()

        if not repos:
            return "No public repositories found."

        lines = [f"Live GitHub Repositories for GokulPrasathM ({len(repos)} fetched):\n"]
        for i, r in enumerate(repos, 1):
            name = r.get("name", "Unnamed")
            desc = r.get("description") or "No description provided."
            stars = r.get("stargazers_count", 0)
            forks = r.get("forks_count", 0)
            lang = r.get("language") or "N/A"
            html_url = r.get("html_url", "")

            lines.append(f"{i}. 📦 {name} [{lang}] (⭐ {stars} | 🍴 {forks})")
            lines.append(f"   {desc}")
            lines.append(f"   URL: {html_url}\n")

        return "\n".join(lines)

    except Exception as e:
        log.warning("github_api_failed", error=str(e))
        return f"Could not fetch live GitHub repos: {e}. Check https://github.com/GokulPrasathM directly."
