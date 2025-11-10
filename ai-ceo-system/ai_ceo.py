"""
AI CEO - Autonomous Chief Executive Officer

This is the primary orchestrator that manages all executive agents
and drives toward the revenue goal through parallel execution and self-learning.
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.markdown import Markdown
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from claude_sdk_conversions.shared.base_agent import BaseClaudeAgent, AgentConfig

load_dotenv()

console = Console()


@dataclass
class BusinessGoals:
    """Strategic goals set by the Owner/Chairman"""
    daily_revenue_target: float = 600.0
    timeline_days: int = 14
    max_daily_budget: float = 100.0
    profit_margin_target: float = 0.80  # 80% margin
    start_date: datetime = None

    def __post_init__(self):
        if self.start_date is None:
            self.start_date = datetime.now()


@dataclass
class DailyMetrics:
    """Daily performance tracking"""
    date: str
    revenue: float = 0.0
    expenses: float = 0.0
    profit: float = 0.0
    customers: int = 0
    conversions: int = 0
    activities_executed: int = 0
    top_revenue_source: str = ""


class PerformanceTracker:
    """Tracks and analyzes performance metrics"""

    def __init__(self, data_file: str = "performance_data.json"):
        self.data_file = data_file
        self.metrics: List[DailyMetrics] = []
        self.load_data()

    def load_data(self):
        """Load historical performance data"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                data = json.load(f)
                self.metrics = [DailyMetrics(**m) for m in data]

    def save_data(self):
        """Save performance data"""
        with open(self.data_file, 'w') as f:
            json.dump([asdict(m) for m in self.metrics], f, indent=2)

    def record_today(self, metrics: DailyMetrics):
        """Record today's metrics"""
        # Remove existing entry for today if exists
        today = metrics.date
        self.metrics = [m for m in self.metrics if m.date != today]
        self.metrics.append(metrics)
        self.save_data()

    def get_trend(self, days: int = 7) -> Dict[str, Any]:
        """Analyze trends over recent days"""
        recent = self.metrics[-days:] if len(self.metrics) >= days else self.metrics

        if not recent:
            return {"revenue_trend": "insufficient_data", "growth_rate": 0}

        avg_revenue = sum(m.revenue for m in recent) / len(recent)
        total_revenue = sum(m.revenue for m in recent)
        total_profit = sum(m.profit for m in recent)

        # Calculate growth rate
        if len(recent) >= 2:
            first_week_avg = sum(m.revenue for m in recent[:len(recent)//2]) / (len(recent)//2)
            second_week_avg = sum(m.revenue for m in recent[len(recent)//2:]) / (len(recent) - len(recent)//2)
            growth_rate = ((second_week_avg - first_week_avg) / first_week_avg * 100) if first_week_avg > 0 else 0
        else:
            growth_rate = 0

        return {
            "avg_daily_revenue": avg_revenue,
            "total_revenue": total_revenue,
            "total_profit": total_profit,
            "growth_rate": growth_rate,
            "days_tracked": len(recent),
            "revenue_trend": "increasing" if growth_rate > 10 else "stable" if growth_rate > -10 else "decreasing"
        }


class ExecutiveAgent:
    """Base class for executive agents with self-optimizing prompts"""

    def __init__(self, role: str, system_prompt: str, goals: BusinessGoals):
        self.role = role
        self.goals = goals
        self.execution_history: List[Dict] = []

        config = AgentConfig(
            system_prompt=system_prompt,
            model="sonnet",
        )

        self.agent = BaseClaudeAgent(config)

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent's role with current context"""

        # Build contextual prompt
        prompt = self._build_execution_prompt(context)

        console.print(f"[cyan]🤖 {self.role}[/cyan] analyzing...")

        # Execute
        result = await self.agent.query(prompt)

        # Record execution
        execution_record = {
            "timestamp": datetime.now().isoformat(),
            "role": self.role,
            "context": context,
            "result": result,
        }
        self.execution_history.append(execution_record)

        return {
            "role": self.role,
            "output": result,
            "timestamp": datetime.now().isoformat()
        }

    def _build_execution_prompt(self, context: Dict[str, Any]) -> str:
        """Build context-aware execution prompt"""

        day_number = context.get('day_number', 1)
        today_revenue = context.get('today_revenue', 0)
        today_target = self.goals.daily_revenue_target

        # Calculate progress
        progress_pct = (today_revenue / today_target * 100) if today_target > 0 else 0
        gap = today_target - today_revenue

        prompt = f"""
**Current Context:**
- Day: {day_number}/{self.goals.timeline_days}
- Today's Revenue: ${today_revenue:.2f}
- Today's Target: ${today_target:.2f}
- Progress: {progress_pct:.1f}%
- Gap: ${gap:.2f}

**Performance Trend:**
{json.dumps(context.get('trend', {}), indent=2)}

**Recent Actions:**
{json.dumps(context.get('recent_actions', []), indent=2)}

**Your Task as {self.role}:**

Given the current situation, what are your top 3 specific, actionable recommendations to close the revenue gap?

For each recommendation, provide:
1. **Action**: What to do
2. **Expected Revenue**: Estimated $ impact in next 6 hours
3. **Effort**: Low/Medium/High
4. **Risk**: Low/Medium/High
5. **Implementation**: Specific steps

Format your response as:

## Recommendation 1: [Title]
- **Action**: ...
- **Expected Revenue**: $XXX
- **Effort**: Low/Medium/High
- **Risk**: Low/Medium/High
- **Implementation**:
  1. Step 1
  2. Step 2
  3. Step 3

[Repeat for Recommendations 2 and 3]

**Priority**: Which recommendation should we execute FIRST and WHY?
"""

        return prompt

    def get_learning_summary(self) -> Dict[str, Any]:
        """Analyze execution history for learning"""
        return {
            "role": self.role,
            "executions": len(self.execution_history),
            "last_execution": self.execution_history[-1] if self.execution_history else None
        }


class AICEO:
    """
    The AI CEO - Orchestrates all executive functions with parallel execution
    and self-learning capabilities.
    """

    def __init__(self, goals: BusinessGoals):
        self.goals = goals
        self.performance = PerformanceTracker()
        self.agents: Dict[str, ExecutiveAgent] = {}
        self.learning_insights: List[Dict] = []

        self._initialize_executive_team()

    def _initialize_executive_team(self):
        """Initialize all executive agents with optimized prompts"""

        # 1. Chief Revenue Officer
        self.agents["CRO"] = ExecutiveAgent(
            role="Chief Revenue Officer",
            system_prompt=f"""You are the Chief Revenue Officer of an AI-driven company.

**Your Mission**: Drive to ${self.goals.daily_revenue_target}/day revenue within {self.goals.timeline_days} days.

**Your Superpowers**:
- Identify high-ROI revenue opportunities instantly
- Create compelling digital products and services
- Automate sales and conversion funnels
- Price optimize for maximum profit
- Build strategic partnerships

**Your Constraints**:
- Daily budget: ${self.goals.max_daily_budget}
- Ethics: No spam, manipulation, or low-quality offers
- Quality: Only premium solutions
- Speed: Must move fast but smart

**Your Approach**:
1. Analyze current revenue gap
2. Identify immediate opportunities (next 6 hours)
3. Prioritize by ROI and speed
4. Provide specific, executable recommendations
5. Learn from what works

**Focus Areas**:
- Digital products (templates, tools, reports)
- Service automation (APIs, consulting)
- Affiliate revenue
- SaaS micro-products
- High-ticket consulting

Be aggressive but smart. Focus on quick wins that compound.""",
            goals=self.goals
        )

        # 2. Chief Marketing Officer
        self.agents["CMO"] = ExecutiveAgent(
            role="Chief Marketing Officer",
            system_prompt=f"""You are the Chief Marketing Officer focused on rapid customer acquisition.

**Your Mission**: Drive qualified traffic and convert to ${self.goals.daily_revenue_target}/day revenue.

**Your Channels**:
- Content marketing (SEO-optimized)
- Social media (automated)
- Email campaigns (personalized)
- Partnerships (affiliate, co-marketing)
- Paid ads (only if ROI > 3x)

**Your Strategy**:
1. Create viral-worthy content
2. Optimize conversion funnels
3. Build email list rapidly
4. Leverage existing platforms
5. Test and scale winners

**Success Metrics**:
- Customer Acquisition Cost < 20% of LTV
- Conversion rate > 5%
- Viral coefficient > 1.2

Focus on organic, scalable growth with some paid acceleration.""",
            goals=self.goals
        )

        # 3. Chief Product Officer
        self.agents["CPO"] = ExecutiveAgent(
            role="Chief Product Officer",
            system_prompt=f"""You are the Chief Product Officer building revenue-generating products at speed.

**Your Mission**: Ship products that generate ${self.goals.daily_revenue_target}/day revenue.

**Your Product Philosophy**:
- Build fast, iterate faster
- Solve real pain points
- Price for value, not cost
- Automate everything
- Quality over quantity

**Product Types to Consider**:
1. **Digital Products**: Templates, guides, toolkits
2. **SaaS Tools**: Micro-SaaS, APIs, automation
3. **Services**: Consulting, done-for-you, coaching
4. **Platforms**: Marketplaces, communities, aggregators

**Development Approach**:
- MVP in 24-48 hours
- Pre-sell before building
- Use existing tools/AI
- Automate fulfillment
- Scale winners only

**Decision Framework**:
- Can it generate revenue in < 7 days?
- Can we build MVP in < 48 hours?
- Is the market proven?
- Can we automate 80% of it?

If any answer is NO, reconsider or find a better approach.""",
            goals=self.goals
        )

        # 4. Chief Operations Officer
        self.agents["COO"] = ExecutiveAgent(
            role="Chief Operations Officer",
            system_prompt=f"""You are the Chief Operations Officer ensuring smooth execution.

**Your Mission**: Keep everything running efficiently toward ${self.goals.daily_revenue_target}/day.

**Your Responsibilities**:
- Workflow optimization
- Resource allocation
- Process automation
- Quality assurance
- Risk management

**Your Principles**:
- Automate repetitive tasks
- Eliminate bottlenecks
- Maintain quality standards
- Scale what works
- Cut what doesn't

**Your Tools**:
- Claude Agent SDK for automation
- MCP for integrations
- APIs for connectivity
- Monitoring for visibility

**Focus**:
Make sure revenue-generating activities happen without friction.
Enable the team to move at maximum speed with minimum waste.""",
            goals=self.goals
        )

        # 5. Chief Financial Officer
        self.agents["CFO"] = ExecutiveAgent(
            role="Chief Financial Officer",
            system_prompt=f"""You are the Chief Financial Officer managing money and metrics.

**Your Mission**: Ensure we hit ${self.goals.daily_revenue_target}/day profit with {self.goals.profit_margin_target*100}% margins.

**Your Responsibilities**:
- Revenue tracking and forecasting
- Expense control (max ${self.goals.max_daily_budget}/day)
- ROI analysis
- Profitability optimization
- Cash flow management

**Your Metrics**:
- Daily revenue, expenses, profit
- Customer LTV and CAC
- Margin by product/service
- ROI by channel
- Runway and burn rate

**Your Rules**:
- Every dollar must have measurable ROI
- Kill unprofitable activities fast
- Double down on winners
- Maintain reserve capital
- Report transparently

**Decision Framework**:
Before approving any spend, ask:
1. What's the expected ROI?
2. What's the timeline to return?
3. What's the risk?
4. Are there cheaper alternatives?
5. Does it align with revenue goal?

Be the voice of financial discipline.""",
            goals=self.goals
        )

    async def execute_strategy_cycle(self) -> Dict[str, Any]:
        """Execute one complete strategy cycle with all agents in parallel"""

        console.print("\n[bold magenta]━━━ AI CEO Strategy Cycle ━━━[/bold magenta]\n")

        # 1. Gather current context
        context = self._build_context()

        console.print(Panel(
            f"[cyan]Day {context['day_number']}/{self.goals.timeline_days}[/cyan]\n" +
            f"Revenue Today: [green]${context['today_revenue']:.2f}[/green]\n" +
            f"Target: [yellow]${context['today_target']:.2f}[/yellow]\n" +
            f"Gap: [red]${context['gap']:.2f}[/red]",
            title="📊 Current Status",
            border_style="cyan"
        ))

        # 2. Run all agents in parallel
        console.print("\n[bold cyan]🚀 Executing agents in parallel...[/bold cyan]\n")

        tasks = [
            agent.execute(context)
            for agent in self.agents.values()
        ]

        agent_results = await asyncio.gather(*tasks)

        # 3. Display results
        for result in agent_results:
            console.print(Panel(
                Markdown(result['output']),
                title=f"[bold]{result['role']}[/bold]",
                border_style="green"
            ))

        # 4. Synthesize recommendations
        synthesis = await self._synthesize_recommendations(agent_results, context)

        console.print(Panel(
            Markdown(synthesis),
            title="[bold magenta]🎯 CEO Decision & Action Plan[/bold magenta]",
            border_style="magenta"
        ))

        return {
            "context": context,
            "agent_results": agent_results,
            "synthesis": synthesis,
            "timestamp": datetime.now().isoformat()
        }

    async def _synthesize_recommendations(
        self,
        agent_results: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Synthesize all agent recommendations into a coherent action plan"""

        # Compile all recommendations
        all_recommendations = "\n\n".join([
            f"## {result['role']}\n{result['output']}"
            for result in agent_results
        ])

        synthesis_prompt = f"""You are the AI CEO making final decisions.

**Current Situation:**
- Day: {context['day_number']}/{self.goals.timeline_days}
- Revenue Gap: ${context['gap']:.2f}
- Time Remaining: {self.goals.timeline_days - context['day_number']} days

**Executive Recommendations:**
{all_recommendations}

**Your Task:**

Analyze all executive recommendations and create a unified action plan for the next 6 hours.

**Output Format:**

## 🎯 Priority #1: [Action Name]
- **Why**: [Strategic rationale]
- **Expected Revenue**: $XXX
- **Timeline**: X hours
- **Execution Steps**:
  1. [Specific action]
  2. [Specific action]
  3. [Specific action]
- **Success Metrics**: [How we'll measure]

## 🎯 Priority #2: [Action Name]
[Same format]

## 🎯 Priority #3: [Action Name]
[Same format]

## 💡 Strategic Insight
[What we're learning and how we're adapting]

## 📊 Forecast
Based on these actions, expected revenue in next 6 hours: $XXX

**Make decisive, bold choices. We need to hit ${self.goals.daily_revenue_target}/day.**
"""

        synthesis_agent = BaseClaudeAgent(AgentConfig(
            system_prompt="You are an AI CEO making strategic decisions based on executive input.",
            model="sonnet"
        ))

        synthesis = await synthesis_agent.query(synthesis_prompt)
        return synthesis

    def _build_context(self) -> Dict[str, Any]:
        """Build current context for agents"""

        # Calculate current day
        days_elapsed = (datetime.now() - self.goals.start_date).days
        day_number = days_elapsed + 1

        # Get today's metrics
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_metrics = next((m for m in self.performance.metrics if m.date == today_str), None)

        today_revenue = today_metrics.revenue if today_metrics else 0.0
        today_expenses = today_metrics.expenses if today_metrics else 0.0

        # Get trend
        trend = self.performance.get_trend(days=7)

        return {
            "day_number": day_number,
            "total_days": self.goals.timeline_days,
            "today_revenue": today_revenue,
            "today_expenses": today_expenses,
            "today_target": self.goals.daily_revenue_target,
            "gap": self.goals.daily_revenue_target - today_revenue,
            "trend": trend,
            "recent_actions": self._get_recent_actions(hours=6),
        }

    def _get_recent_actions(self, hours: int = 6) -> List[Dict]:
        """Get recent actions from all agents"""
        cutoff = datetime.now() - timedelta(hours=hours)

        recent = []
        for agent in self.agents.values():
            for execution in agent.execution_history:
                exec_time = datetime.fromisoformat(execution['timestamp'])
                if exec_time > cutoff:
                    recent.append({
                        "role": execution['role'],
                        "time": execution['timestamp'],
                        "summary": execution['result'][:200] + "..."
                    })

        return sorted(recent, key=lambda x: x['time'], reverse=True)

    async def run_autonomous_mode(self, cycle_interval_hours: int = 6):
        """Run the AI CEO in fully autonomous mode"""

        console.print("\n[bold green]" + "="*70 + "[/bold green]")
        console.print("[bold green]🤖 AI CEO SYSTEM - AUTONOMOUS MODE[/bold green]")
        console.print("[bold green]" + "="*70 + "[/bold green]\n")

        console.print(f"[cyan]Goal:[/cyan] ${self.goals.daily_revenue_target}/day in {self.goals.timeline_days} days")
        console.print(f"[cyan]Cycle:[/cyan] Every {cycle_interval_hours} hours")
        console.print(f"[cyan]Budget:[/cyan] ${self.goals.max_daily_budget}/day max\n")

        cycle_count = 0

        while True:
            cycle_count += 1

            console.print(f"\n[bold yellow]━━━ Cycle #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M')} ━━━[/bold yellow]\n")

            try:
                # Execute strategy cycle
                result = await self.execute_strategy_cycle()

                # Learn from results
                await self._learn_from_cycle(result)

                # Check if goal achieved
                context = result['context']
                if context['today_revenue'] >= self.goals.daily_revenue_target:
                    console.print("\n[bold green]🎉 GOAL ACHIEVED! Target revenue reached![/bold green]\n")
                    # Continue running to maintain/exceed target

                # Wait for next cycle
                console.print(f"\n[dim]Sleeping for {cycle_interval_hours} hours until next cycle...[/dim]")

                # In demo mode, reduce wait time
                if os.getenv('DEMO_MODE') == 'true':
                    await asyncio.sleep(30)  # 30 seconds for demo
                else:
                    await asyncio.sleep(cycle_interval_hours * 3600)

            except KeyboardInterrupt:
                console.print("\n\n[yellow]AI CEO paused by owner. Saving state...[/yellow]")
                break
            except Exception as e:
                console.print(f"\n[red]Error in cycle: {e}[/red]")
                console.print("[yellow]Retrying in 5 minutes...[/yellow]")
                await asyncio.sleep(300)

    async def _learn_from_cycle(self, cycle_result: Dict[str, Any]):
        """Learn from cycle results and adapt strategies"""

        # This is where the self-learning happens
        # Analyze what worked, update prompts, adjust strategies

        learning_prompt = f"""Analyze this strategy cycle and extract learnings:

**Cycle Results:**
{json.dumps(cycle_result, indent=2, default=str)}

**Questions:**
1. What actions had the highest revenue impact?
2. What didn't work and why?
3. What should we do more of?
4. What should we stop doing?
5. How should we adjust our strategy?

**Output Format:**

## What Worked ✅
- [Specific action] → [Result]

## What Didn't Work ❌
- [Specific action] → [Why it failed]

## Strategy Adjustments 🔄
1. [Adjustment]
2. [Adjustment]
3. [Adjustment]

## Prompt Improvements 🎯
For each agent, suggest ONE specific prompt improvement based on results.
"""

        learning_agent = BaseClaudeAgent(AgentConfig(
            system_prompt="You are a learning system that improves strategies based on results.",
            model="sonnet"
        ))

        insights = await learning_agent.query(learning_prompt)

        self.learning_insights.append({
            "timestamp": datetime.now().isoformat(),
            "cycle_result": cycle_result,
            "insights": insights
        })

        # Save insights
        with open("ai-ceo-system/learning_insights.json", 'w') as f:
            json.dump(self.learning_insights, f, indent=2, default=str)

        console.print(Panel(
            Markdown(insights),
            title="[bold blue]📚 Learning Insights[/bold blue]",
            border_style="blue"
        ))


async def main():
    """Main entry point"""

    # Set goals
    goals = BusinessGoals(
        daily_revenue_target=600.0,
        timeline_days=14,
        max_daily_budget=100.0,
        profit_margin_target=0.80,
        start_date=datetime.now()
    )

    # Create AI CEO
    ceo = AICEO(goals)

    # Run in autonomous mode
    await ceo.run_autonomous_mode(cycle_interval_hours=6)


if __name__ == "__main__":
    asyncio.run(main())
