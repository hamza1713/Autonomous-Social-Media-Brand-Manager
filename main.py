"""
Module 7 — CLI Entry Point
Run a campaign directly from the terminal:
  python main.py --brief "Launch our new Eclipse Espresso blend" --platforms Instagram LinkedIn
"""

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Add project root to path so all imports resolve
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import GOOGLE_API_KEY
from crew import SocialMediaCrew, CampaignConfig


console = Console()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Autonomous Social Media Brand Manager — CLI"
    )
    parser.add_argument(
        "--brief",
        type=str,
        required=True,
        help="Campaign brief, e.g. 'Launch our new cold brew for summer'",
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        default=["Instagram", "LinkedIn"],
        choices=["Instagram", "LinkedIn", "X (Twitter)", "Facebook"],
        help="Target platforms (default: Instagram LinkedIn)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not GOOGLE_API_KEY:
        console.print(
            "[bold red]Error:[/bold red] GOOGLE_API_KEY not set. "
            "Create a .env file with GOOGLE_API_KEY=AIza... in the project root."
        )
        sys.exit(1)

    config = CampaignConfig(
        campaign_brief=args.brief,
        platforms=args.platforms,
    )

    console.print(Panel.fit(
        f"[bold]Campaign Brief[/bold]: {config.campaign_brief}\n"
        f"[bold]Platforms[/bold]    : {', '.join(config.platforms)}",
        title="Nova Brew Social Media Manager",
        border_style="blue",
    ))
    console.print("\n[dim]Starting 5-agent crew...[/dim]\n")

    crew_runner = SocialMediaCrew()
    result = crew_runner.run(config)

    sections = [
        ("Strategy Plan",         result.strategy),
        ("Generated Posts",       result.posts),
        ("Brand-Reviewed Posts",  result.reviewed_posts),
        ("Engagement Replies",    result.engagement_replies),
        ("Performance Report",    result.performance_report),
    ]

    for title, content in sections:
        console.print(Panel(Markdown(content), title=title, border_style="green"))

    console.print(f"\n[green]✓ Results saved to outputs/[/green]")


if __name__ == "__main__":
    main()
