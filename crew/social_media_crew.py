"""
Module 6 — Social Media Crew Orchestrator (crewai 1.x compatible)
"""

from __future__ import annotations
import json, os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

from crewai import Crew, Process
from config.settings import MEMORY_ENABLED, VERBOSE_LOGGING, OUTPUTS_DIR
from agents import (
    create_strategy_agent, create_content_agent,
    create_brand_voice_agent, create_engagement_agent, create_analysis_agent,
)
from tasks.task_definitions import (
    create_strategy_task, create_content_task, create_brand_review_task,
    create_engagement_task, create_analysis_task,
)


@dataclass
class CampaignConfig:
    campaign_brief: str
    platforms: list[str] = field(default_factory=lambda: ["Instagram", "LinkedIn"])
    brand_file: str = "sample_brand.txt"
    # ── Configurable generation controls ──────────────────────────────────────
    tone_intensity: str = "balanced"     # subtle | balanced | bold
    creativity_level: str = "creative"  # conservative | creative | experimental
    post_length: str = "medium"         # short | medium | long


@dataclass
class CampaignResult:
    strategy: str
    posts: str
    reviewed_posts: str
    engagement_replies: str
    performance_report: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "strategy": self.strategy,
            "posts": self.posts,
            "reviewed_posts": self.reviewed_posts,
            "engagement_replies": self.engagement_replies,
            "performance_report": self.performance_report,
        }

    def save(self, path: Path | None = None) -> Path:
        OUTPUTS_DIR.mkdir(exist_ok=True)
        out = path or OUTPUTS_DIR / f"campaign_{self.timestamp[:10]}.json"
        out.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return out


class SocialMediaCrew:
    """Builds and runs the full 5-agent crew."""

    def __init__(self, google_api_key: str | None = None) -> None:
        if google_api_key:
            os.environ["GEMINI_API_KEY"] = google_api_key
            os.environ["GOOGLE_API_KEY"] = google_api_key

    def run(
        self,
        config: CampaignConfig,
        on_task_done: Optional[Callable[[int], None]] = None,
    ) -> CampaignResult:
        # Agents
        strategy_agent   = create_strategy_agent()
        content_agent    = create_content_agent()
        brand_agent      = create_brand_voice_agent()
        engagement_agent = create_engagement_agent()
        analysis_agent   = create_analysis_agent()

        # Tasks — pass configurable controls to each task
        strategy_task = create_strategy_task(
            strategy_agent,
            config.campaign_brief,
            config.platforms,
            tone_intensity=config.tone_intensity,
            creativity_level=config.creativity_level,
            post_length=config.post_length,
        )
        content_task = create_content_task(
            content_agent,
            strategy_task,
            config.platforms,
            tone_intensity=config.tone_intensity,
            creativity_level=config.creativity_level,
            post_length=config.post_length,
        )
        review_task = create_brand_review_task(brand_agent, content_task)
        engagement_task = create_engagement_task(
            engagement_agent,
            config.platforms,
            tone_intensity=config.tone_intensity,
        )
        analysis_task = create_analysis_task(analysis_agent, review_task, config.platforms)

        # Crew
        embedder_config = {
            "provider": "google",
            "config": {
                "model": "models/gemini-embedding-2",
                "api_key": os.environ.get("GOOGLE_API_KEY", "")
            }
        }

        # Build task-completion callback to report progress to the UI
        _task_index = [0]

        def _task_callback(task_output) -> None:  # noqa: ANN001
            idx = _task_index[0]
            _task_index[0] += 1
            if on_task_done is not None:
                try:
                    on_task_done(idx)
                except Exception:
                    pass

        crew = Crew(
            agents=[strategy_agent, content_agent, brand_agent, engagement_agent, analysis_agent],
            tasks=[strategy_task, content_task, review_task, engagement_task, analysis_task],
            process=Process.sequential,
            memory=MEMORY_ENABLED,
            verbose=VERBOSE_LOGGING,
            embedder=embedder_config,
            task_callback=_task_callback,
        )

        crew.kickoff(inputs={
            "campaign_brief": config.campaign_brief,
            "platforms": ", ".join(config.platforms),
            "tone_intensity": config.tone_intensity,
            "creativity_level": config.creativity_level,
            "post_length": config.post_length,
        })

        def _out(task_obj) -> str:
            if task_obj.output is None:
                return ""
            return getattr(task_obj.output, "raw", str(task_obj.output))

        result = CampaignResult(
            strategy           = _out(crew.tasks[0]),
            posts              = _out(crew.tasks[1]),
            reviewed_posts     = _out(crew.tasks[2]),
            engagement_replies = _out(crew.tasks[3]),
            performance_report = _out(crew.tasks[4]),
        )
        result.save()
        return result