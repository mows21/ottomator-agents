#!/usr/bin/env python3
"""
Start AI CEO System

Launch your autonomous AI CEO to generate $600/day profit.
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_ceo import AICEO, BusinessGoals
from rich.console import Console
from datetime import datetime

console = Console()

load_dotenv()


def check_prerequisites():
    """Check that all prerequisites are met"""

    console.print("\n[bold cyan]Checking prerequisites...[/bold cyan]\n")

    checks = {
        "Claude Agent SDK": check_claude_sdk(),
        "API Key": check_api_key(),
        "Data Directory": check_data_dir(),
    }

    all_passed = True

    for check_name, (passed, message) in checks.items():
        status = "[green]✅" if passed else "[red]❌"
        console.print(f"{status} {check_name}: {message}[/green]" if passed else f"{status} {check_name}: {message}[/red]")

        if not passed:
            all_passed = False

    console.print()

    if not all_passed:
        console.print("[red]❌ Prerequisites not met. Please fix the issues above.[/red]\n")
        return False

    console.print("[green]✅ All prerequisites met![/green]\n")
    return True


def check_claude_sdk():
    """Check if Claude SDK is installed"""
    try:
        import claude_agent_sdk
        return True, "Installed"
    except ImportError:
        return False, "Not installed. Run: pip install claude-agent-sdk"


def check_api_key():
    """Check if API key is set"""
    key = os.getenv('ANTHROPIC_API_KEY')

    if key:
        return True, "Set"
    else:
        return False, "Not set. Set ANTHROPIC_API_KEY or run: claude auth login"


def check_data_dir():
    """Check if data directory exists"""
    data_dir = "ai-ceo-system/data"
    os.makedirs(data_dir, exist_ok=True)
    return True, f"Ready: {data_dir}"


def display_welcome():
    """Display welcome message"""

    console.print("\n[bold green]" + "═" * 80 + "[/bold green]")
    console.print("[bold green]🚀 AI CEO SYSTEM - AUTONOMOUS REVENUE GENERATION[/bold green]")
    console.print("[bold green]" + "═" * 80 + "[/bold green]\n")

    console.print("[cyan]Welcome, Owner/Chairman![/cyan]\n")

    console.print("This AI CEO will:")
    console.print("  • Manage all executive functions autonomously")
    console.print("  • Generate $600/day profit within 14 days")
    console.print("  • Run 24/7 with periodic strategy cycles")
    console.print("  • Learn and adapt from results")
    console.print("  • Report to you for oversight\n")

    console.print("[yellow]You retain full control:[/yellow]")
    console.print("  • Set strategic goals")
    console.print("  • Monitor performance")
    console.print("  • Approve major decisions")
    console.print("  • Emergency stop anytime\n")


def get_configuration():
    """Get configuration from user"""

    console.print("[bold cyan]Configuration:[/bold cyan]\n")

    # Revenue target
    default_target = 600.0
    target_input = console.input(f"Daily revenue target [$[bold]{default_target}[/bold]]: ").strip()
    revenue_target = float(target_input) if target_input else default_target

    # Timeline
    default_timeline = 14
    timeline_input = console.input(f"Timeline in days [[bold]{default_timeline}[/bold]]: ").strip()
    timeline = int(timeline_input) if timeline_input else default_timeline

    # Budget
    default_budget = 100.0
    budget_input = console.input(f"Max daily budget [$[bold]{default_budget}[/bold]]: ").strip()
    max_budget = float(budget_input) if budget_input else default_budget

    # Demo mode
    console.print()
    demo = console.input("Enable demo mode? (faster cycles for testing) [y/N]: ").strip().lower()
    if demo == 'y':
        os.environ['DEMO_MODE'] = 'true'
        console.print("[yellow]⚡ Demo mode enabled: 30-second cycles[/yellow]")
    else:
        console.print("[dim]Production mode: 6-hour cycles[/dim]")

    console.print()

    return BusinessGoals(
        daily_revenue_target=revenue_target,
        timeline_days=timeline,
        max_daily_budget=max_budget,
        profit_margin_target=0.80,
        start_date=datetime.now()
    )


def confirm_launch():
    """Get confirmation to launch"""

    console.print("\n[bold yellow]⚠️  Ready to launch AI CEO[/bold yellow]\n")

    console.print("The AI CEO will:")
    console.print("  1. Analyze current situation")
    console.print("  2. Execute revenue generation strategies")
    console.print("  3. Run continuous optimization cycles")
    console.print("  4. Report results to you\n")

    console.print("[dim]You can stop anytime with Ctrl+C[/dim]\n")

    confirm = console.input("Launch AI CEO? [Y/n]: ").strip().lower()

    return confirm == 'y' or confirm == ''


async def main():
    """Main entry point"""

    # Display welcome
    display_welcome()

    # Check prerequisites
    if not check_prerequisites():
        return

    # Get configuration
    goals = get_configuration()

    # Confirm launch
    if not confirm_launch():
        console.print("\n[yellow]Launch cancelled.[/yellow]\n")
        return

    console.print("\n[bold green]🚀 Launching AI CEO...[/bold green]\n")

    # Create and start AI CEO
    ceo = AICEO(goals)

    try:
        # Run autonomous mode
        cycle_hours = 6 if os.getenv('DEMO_MODE') != 'true' else 0.5  # 30 minutes in demo

        await ceo.run_autonomous_mode(cycle_interval_hours=cycle_hours)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/yellow]")
        console.print("[yellow]AI CEO paused by Owner[/yellow]")
        console.print("[yellow]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/yellow]\n")

        # Show options
        console.print("[bold cyan]Options:[/bold cyan]")
        console.print("  [1] Resume AI CEO")
        console.print("  [2] Open Owner Dashboard")
        console.print("  [3] Exit completely\n")

        choice = console.input("Your choice: ").strip()

        if choice == '1':
            console.print("\n[green]Resuming AI CEO...[/green]\n")
            await ceo.run_autonomous_mode(cycle_interval_hours=cycle_hours)
        elif choice == '2':
            console.print("\n[cyan]Opening Owner Dashboard...[/cyan]\n")
            from dashboard.owner_dashboard import OwnerDashboard
            dashboard = OwnerDashboard()
            await dashboard.interactive_mode()
        else:
            console.print("\n[yellow]Exiting AI CEO System.[/yellow]\n")

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
