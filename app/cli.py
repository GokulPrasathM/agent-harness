"""CLI interface — interactive chat and single-shot mode."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Import tools to trigger registration
import app.tools.calculator
import app.tools.database
import app.tools.read_url
import app.tools.web_search  # noqa: F401
from app.agent.loop import run_agent
from app.agent.state import RunStatus
from app.core.config import load_settings
from app.core.logging import setup_logging
from app.tools.registry import registry

cli = typer.Typer(name="agent-forge", help="Production-grade AI agent template.")
cli = typer.Typer(name="agent-harness", help="Production-grade AI agent template.")
console = Console()


def _run_async(coro):
    """Run an async function from sync context."""
    return asyncio.run(coro)


@cli.command()
def chat(
    config: str = typer.Option("agent.yaml", "--config", "-c", help="Path to agent.yaml"),
) -> None:
    """Interactive chat with the agent."""
    settings = load_settings(config)
    cfg = settings.yaml_config
    setup_logging(level=cfg.logging.level, log_file=cfg.logging.log_file)

    console.print(
        Panel(
            f"[bold]{cfg.agent.name}[/bold]\n"
            f"Model: {cfg.agent.model}\n"
            f"Scope: {'enabled' if cfg.scope.enabled else 'disabled'}\n"
            f"Tools: {', '.join(cfg.tools.enabled)}\n\n"
            f"Type 'quit' or 'exit' to stop.",
            title="🔨 Agent Forge",
            title="🪢 Agent Harness",
            border_style="blue",
        )
    )

    while True:
        try:
            user_input = console.input("\n[bold green]You:[/bold green] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n👋 Goodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            console.print("👋 Goodbye!")
            break

        with console.status("Thinking...", spinner="dots"):
            result = _run_async(run_agent(user_input, settings, registry))

        # Display result
        if result.status == RunStatus.SCOPE_REJECTED:
            console.print(f"\n[bold yellow]⚠ {result.output}[/bold yellow]")
        elif result.status == RunStatus.SUCCESS:
            console.print(f"\n[bold blue]Agent:[/bold blue] {result.output}")
        else:
            console.print(f"\n[bold red]⚠ [{result.status.value}][/bold red] {result.output}")

        # Show stats
        console.print(
            f"[dim]  ↳ {result.iterations} turns | "
            f"${result.total_cost_usd:.4f} | "
            f"{result.duration_seconds:.1f}s[/dim]"
        )


@cli.command()
def run(
    message: str = typer.Argument(help="Message to send to the agent"),
    config: str = typer.Option("agent.yaml", "--config", "-c", help="Path to agent.yaml"),
) -> None:
    """Run a single query and exit."""
    settings = load_settings(config)
    cfg = settings.yaml_config
    setup_logging(level=cfg.logging.level, log_file=cfg.logging.log_file)

    result = _run_async(run_agent(message, settings, registry))

    console.print(result.output)
    console.print(
        f"\n[dim]Status: {result.status.value} | "
        f"{result.iterations} turns | "
        f"${result.total_cost_usd:.4f} | "
        f"{result.duration_seconds:.1f}s[/dim]"
    )


@cli.command()
def tools(
    config: str = typer.Option("agent.yaml", "--config", "-c", help="Path to agent.yaml"),
) -> None:
    """List available tools."""
    settings = load_settings(config)
    enabled = settings.yaml_config.tools.enabled

    table = Table(title="Available Tools")
    table.add_column("Name", style="bold")
    table.add_column("Description")
    table.add_column("Enabled", justify="center")

    for tool in registry.list_tools():
        is_enabled = "✅" if tool["name"] in enabled else "❌"
        table.add_row(tool["name"], tool["description"], is_enabled)

    console.print(table)


@cli.command(name="config")
def show_config(
    config: str = typer.Option("agent.yaml", "--config", "-c", help="Path to agent.yaml"),
) -> None:
    """Show current configuration."""
    settings = load_settings(config)
    cfg = settings.yaml_config

    console.print(Panel(
        f"Name: {cfg.agent.name}\n"
        f"Model: {cfg.agent.model}\n"
        f"Fallback: {cfg.agent.fallback_model}\n"
        f"\nScope: {'enabled' if cfg.scope.enabled else 'disabled'}\n"
        f"Scope Description: {cfg.scope.description}\n"
        f"\nMax Iterations: {cfg.limits.max_iterations}\n"
        f"Max Cost: ${cfg.limits.max_cost_usd}\n"
        f"Timeout: {cfg.limits.timeout_seconds}s\n"
        f"\nTools: {', '.join(cfg.tools.enabled)}\n"
        f"Log Level: {cfg.logging.level}",
        title="⚙️ Configuration",
        border_style="cyan",
    ))


def main() -> None:
    """Entry point."""
    cli()


if __name__ == "__main__":
    main()
