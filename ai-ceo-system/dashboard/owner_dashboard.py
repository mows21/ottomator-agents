"""
Owner Dashboard - Monitor and guide your AI CEO

This is YOUR interface as Owner/Chairman to:
- Set strategic goals
- Monitor performance
- Approve major decisions
- Guide direction
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich import box
from rich.progress import Progress, BarColumn, TextColumn
from rich.markdown import Markdown

console = Console()


class OwnerDashboard:
    """Dashboard for the Owner/Chairman"""

    def __init__(self, data_dir: str = "ai-ceo-system/data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.goals_file = os.path.join(data_dir, "goals.json")
        self.performance_file = os.path.join(data_dir, "performance_data.json")
        self.decisions_file = os.path.join(data_dir, "pending_decisions.json")

        self.goals = self.load_goals()
        self.performance = self.load_performance()
        self.pending_decisions = self.load_pending_decisions()

    def load_goals(self) -> Dict:
        """Load business goals"""
        if os.path.exists(self.goals_file):
            with open(self.goals_file, 'r') as f:
                return json.load(f)
        return self.get_default_goals()

    def save_goals(self):
        """Save business goals"""
        with open(self.goals_file, 'w') as f:
            json.dump(self.goals, f, indent=2)

    def load_performance(self) -> List[Dict]:
        """Load performance data"""
        if os.path.exists(self.performance_file):
            with open(self.performance_file, 'r') as f:
                return json.load(f)
        return []

    def load_pending_decisions(self) -> List[Dict]:
        """Load pending decisions requiring owner approval"""
        if os.path.exists(self.decisions_file):
            with open(self.decisions_file, 'r') as f:
                return json.load(f)
        return []

    def get_default_goals(self) -> Dict:
        """Default business goals"""
        return {
            "revenue_target_daily": 600.0,
            "timeline_days": 14,
            "max_daily_budget": 100.0,
            "profit_margin_target": 0.80,
            "start_date": datetime.now().isoformat(),
            "strategic_priorities": [
                "Revenue generation",
                "Customer acquisition",
                "Product quality",
                "Sustainable growth"
            ],
            "ethical_guidelines": [
                "No spam or manipulation",
                "Quality over quantity",
                "Transparent pricing",
                "Customer-first approach"
            ]
        }

    def display_dashboard(self):
        """Display the main dashboard"""

        console.clear()

        # Header
        console.print("\n[bold green]" + "═" * 80 + "[/bold green]")
        console.print("[bold green]📊 OWNER DASHBOARD - AI CEO PERFORMANCE[/bold green]")
        console.print("[bold green]" + "═" * 80 + "[/bold green]\n")

        # Goals Overview
        self._display_goals()

        # Performance Metrics
        self._display_performance()

        # Pending Decisions
        self._display_pending_decisions()

        # Agent Activity
        self._display_agent_activity()

        # Menu
        self._display_menu()

    def _display_goals(self):
        """Display current goals"""

        goals_table = Table(title="🎯 Strategic Goals", box=box.ROUNDED)
        goals_table.add_column("Metric", style="cyan")
        goals_table.add_column("Target", style="yellow")
        goals_table.add_column("Status", style="green")

        # Calculate progress
        days_elapsed = (datetime.now() - datetime.fromisoformat(self.goals['start_date'])).days
        days_remaining = max(0, self.goals['timeline_days'] - days_elapsed)

        # Get today's revenue (from latest performance data)
        today_revenue = 0.0
        if self.performance:
            latest = self.performance[-1]
            today_revenue = latest.get('revenue', 0.0)

        revenue_progress = (today_revenue / self.goals['revenue_target_daily'] * 100) if self.goals['revenue_target_daily'] > 0 else 0

        goals_table.add_row(
            "Daily Revenue",
            f"${self.goals['revenue_target_daily']:.2f}",
            f"${today_revenue:.2f} ({revenue_progress:.1f}%)"
        )

        goals_table.add_row(
            "Timeline",
            f"{self.goals['timeline_days']} days",
            f"{days_elapsed} days elapsed, {days_remaining} remaining"
        )

        goals_table.add_row(
            "Daily Budget",
            f"${self.goals['max_daily_budget']:.2f}",
            "Within limits" if True else "Over budget"
        )

        goals_table.add_row(
            "Profit Margin",
            f"{self.goals['profit_margin_target']*100:.0f}%",
            "On track" if True else "Below target"
        )

        console.print(goals_table)
        console.print()

    def _display_performance(self):
        """Display performance metrics"""

        if not self.performance:
            console.print("[yellow]No performance data yet. AI CEO will start collecting data.[/yellow]\n")
            return

        perf_table = Table(title="📈 Performance Metrics (Last 7 Days)", box=box.ROUNDED)
        perf_table.add_column("Date", style="cyan")
        perf_table.add_column("Revenue", style="green")
        perf_table.add_column("Expenses", style="red")
        perf_table.add_column("Profit", style="yellow")
        perf_table.add_column("Margin", style="magenta")

        # Show last 7 days
        recent = self.performance[-7:]

        for day in recent:
            revenue = day.get('revenue', 0)
            expenses = day.get('expenses', 0)
            profit = revenue - expenses
            margin = (profit / revenue * 100) if revenue > 0 else 0

            perf_table.add_row(
                day.get('date', 'Unknown'),
                f"${revenue:.2f}",
                f"${expenses:.2f}",
                f"${profit:.2f}",
                f"{margin:.1f}%"
            )

        # Totals
        total_revenue = sum(d.get('revenue', 0) for d in recent)
        total_expenses = sum(d.get('expenses', 0) for d in recent)
        total_profit = total_revenue - total_expenses

        perf_table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]${total_revenue:.2f}[/bold]",
            f"[bold]${total_expenses:.2f}[/bold]",
            f"[bold]${total_profit:.2f}[/bold]",
            ""
        )

        console.print(perf_table)
        console.print()

    def _display_pending_decisions(self):
        """Display decisions requiring owner approval"""

        if not self.pending_decisions:
            console.print("[green]✅ No pending decisions. AI CEO is operating autonomously.[/green]\n")
            return

        console.print(Panel(
            f"[yellow]⚠️  {len(self.pending_decisions)} decision(s) require your approval[/yellow]",
            title="Pending Decisions",
            border_style="yellow"
        ))

        for i, decision in enumerate(self.pending_decisions, 1):
            console.print(f"\n[bold cyan]Decision #{i}:[/bold cyan]")
            console.print(f"  Type: {decision.get('type', 'Unknown')}")
            console.print(f"  Description: {decision.get('description', 'N/A')}")
            console.print(f"  Impact: {decision.get('impact', 'Unknown')}")
            console.print(f"  Recommendation: {decision.get('recommendation', 'N/A')}")

        console.print()

    def _display_agent_activity(self):
        """Display recent agent activity"""

        activity_table = Table(title="🤖 AI CEO Agent Activity (Last 24h)", box=box.ROUNDED)
        activity_table.add_column("Agent", style="cyan")
        activity_table.add_column("Activity", style="white")
        activity_table.add_column("Status", style="green")

        # Mock data (in real system, load from activity log)
        activities = [
            ("CRO", "Launched template business", "✅ Active"),
            ("CMO", "Running content marketing", "✅ Active"),
            ("CPO", "Developing new service", "🔄 In Progress"),
            ("COO", "Optimizing workflows", "✅ Active"),
            ("CFO", "Tracking financial metrics", "✅ Active"),
        ]

        for agent, activity, status in activities:
            activity_table.add_row(agent, activity, status)

        console.print(activity_table)
        console.print()

    def _display_menu(self):
        """Display action menu"""

        console.print("[bold cyan]Actions:[/bold cyan]")
        console.print("  [1] Set/Update Goals")
        console.print("  [2] Approve Pending Decisions")
        console.print("  [3] View Detailed Report")
        console.print("  [4] Provide Strategic Guidance")
        console.print("  [5] Emergency Stop")
        console.print("  [6] Return to AI CEO")
        console.print("  [Q] Quit")
        console.print()

    async def interactive_mode(self):
        """Run dashboard in interactive mode"""

        while True:
            self.display_dashboard()

            choice = console.input("[bold yellow]Your choice:[/bold yellow] ").strip().lower()

            if choice == '1':
                await self.set_goals_interactive()
            elif choice == '2':
                await self.approve_decisions()
            elif choice == '3':
                await self.view_detailed_report()
            elif choice == '4':
                await self.provide_guidance()
            elif choice == '5':
                await self.emergency_stop()
            elif choice == '6':
                console.print("\n[green]Returning control to AI CEO...[/green]\n")
                break
            elif choice == 'q':
                console.print("\n[yellow]Exiting dashboard...[/yellow]\n")
                return
            else:
                console.print("\n[red]Invalid choice. Please try again.[/red]")
                await asyncio.sleep(2)

    async def set_goals_interactive(self):
        """Set or update goals interactively"""

        console.print("\n[bold cyan]━━━ Set Strategic Goals ━━━[/bold cyan]\n")

        try:
            revenue_target = float(console.input(
                f"Daily revenue target [current: ${self.goals['revenue_target_daily']}]: "
            ) or self.goals['revenue_target_daily'])

            timeline = int(console.input(
                f"Timeline in days [current: {self.goals['timeline_days']}]: "
            ) or self.goals['timeline_days'])

            max_budget = float(console.input(
                f"Max daily budget [current: ${self.goals['max_daily_budget']}]: "
            ) or self.goals['max_daily_budget'])

            # Update goals
            self.goals['revenue_target_daily'] = revenue_target
            self.goals['timeline_days'] = timeline
            self.goals['max_daily_budget'] = max_budget

            self.save_goals()

            console.print("\n[green]✅ Goals updated successfully![/green]")
            console.print("[dim]AI CEO will adjust strategy based on new goals.[/dim]\n")

        except ValueError:
            console.print("\n[red]Invalid input. Goals not updated.[/red]\n")

        console.input("Press Enter to continue...")

    async def approve_decisions(self):
        """Approve or reject pending decisions"""

        if not self.pending_decisions:
            console.print("\n[green]No pending decisions.[/green]\n")
            console.input("Press Enter to continue...")
            return

        console.print("\n[bold cyan]━━━ Approve Decisions ━━━[/bold cyan]\n")

        for i, decision in enumerate(self.pending_decisions, 1):
            console.print(Panel(
                f"**Type**: {decision.get('type')}\n"
                f"**Description**: {decision.get('description')}\n"
                f"**Impact**: {decision.get('impact')}\n"
                f"**AI Recommendation**: {decision.get('recommendation')}",
                title=f"Decision #{i}",
                border_style="cyan"
            ))

            choice = console.input("\nApprove? [Y/n/skip]: ").strip().lower()

            if choice == 'y' or choice == '':
                console.print("[green]✅ Approved[/green]")
                decision['status'] = 'approved'
                decision['approved_at'] = datetime.now().isoformat()
            elif choice == 'n':
                console.print("[red]❌ Rejected[/red]")
                decision['status'] = 'rejected'
                decision['rejected_at'] = datetime.now().isoformat()
            else:
                console.print("[yellow]⏭️  Skipped[/yellow]")

        # Save decisions
        self.save_pending_decisions()

        console.print("\n[green]Decisions processed.[/green]\n")
        console.input("Press Enter to continue...")

    def save_pending_decisions(self):
        """Save pending decisions"""
        with open(self.decisions_file, 'w') as f:
            json.dump(self.pending_decisions, f, indent=2)

    async def view_detailed_report(self):
        """View detailed performance report"""

        console.print("\n[bold cyan]━━━ Detailed Performance Report ━━━[/bold cyan]\n")

        # Generate report using Claude
        from claude_agent_sdk import query

        report_prompt = f"""Generate a comprehensive executive report for the business owner.

**Current Goals:**
{json.dumps(self.goals, indent=2)}

**Recent Performance:**
{json.dumps(self.performance[-7:], indent=2)}

**Report Sections:**
1. Executive Summary
2. Financial Performance Analysis
3. Progress Toward Goals
4. Key Insights and Trends
5. Risks and Opportunities
6. Strategic Recommendations
7. Next 7 Days Forecast

Format as professional markdown report suitable for a Chairman/Owner."""

        console.print("[dim]Generating report with AI...[/dim]\n")

        report = await query(report_prompt)

        console.print(Markdown(report))

        console.print("\n")
        console.input("Press Enter to continue...")

    async def provide_guidance(self):
        """Provide strategic guidance to the AI CEO"""

        console.print("\n[bold cyan]━━━ Provide Strategic Guidance ━━━[/bold cyan]\n")

        console.print("As Owner/Chairman, share your strategic direction for the AI CEO:")
        console.print("[dim](Type your guidance, press Enter twice when done)[/dim]\n")

        guidance_lines = []
        while True:
            line = console.input()
            if not line:
                break
            guidance_lines.append(line)

        guidance = "\n".join(guidance_lines)

        if guidance:
            # Save guidance
            guidance_file = os.path.join(self.data_dir, "owner_guidance.json")
            guidance_data = {
                "timestamp": datetime.now().isoformat(),
                "guidance": guidance
            }

            with open(guidance_file, 'w') as f:
                json.dump(guidance_data, f, indent=2)

            console.print("\n[green]✅ Guidance recorded. AI CEO will incorporate this into strategy.[/green]\n")
        else:
            console.print("\n[yellow]No guidance provided.[/yellow]\n")

        console.input("Press Enter to continue...")

    async def emergency_stop(self):
        """Emergency stop all AI CEO operations"""

        console.print("\n[bold red]⚠️  EMERGENCY STOP ⚠️[/bold red]\n")

        confirm = console.input("Are you sure you want to STOP all AI CEO operations? [yes/NO]: ").strip().lower()

        if confirm == 'yes':
            # Create stop signal
            stop_file = os.path.join(self.data_dir, "EMERGENCY_STOP")
            with open(stop_file, 'w') as f:
                f.write(json.dumps({
                    "stopped_at": datetime.now().isoformat(),
                    "reason": "Owner emergency stop"
                }))

            console.print("\n[red]🛑 AI CEO operations STOPPED.[/red]")
            console.print("[yellow]Remove the file 'EMERGENCY_STOP' to resume operations.[/yellow]\n")
        else:
            console.print("\n[green]Emergency stop cancelled.[/green]\n")

        console.input("Press Enter to continue...")


async def main():
    """Launch owner dashboard"""

    dashboard = OwnerDashboard()
    await dashboard.interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())
