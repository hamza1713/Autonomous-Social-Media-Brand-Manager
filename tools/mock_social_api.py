"""
Module 3c — Mock Social Media API Tool
Simulates posting, fetching comments, and fetching metrics without
real platform credentials. In production, swap with real API wrappers.
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from crewai.tools import BaseTool
from config.settings import MOCK_METRICS_DIR, OUTPUTS_DIR


class MockPostTool(BaseTool):
    """Simulate posting content to a social media platform."""

    name: str = "mock_post_to_platform"
    description: str = (
        "Simulate posting text content to a social media platform. "
        "Input JSON: {\"platform\": \"Instagram\", \"content\": \"...\", \"hashtags\": [...]}. "
        "Returns a mock post ID and confirmation."
    )

    def _run(self, payload: str) -> str:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return "Error: input must be valid JSON."

        platform = data.get("platform", "Unknown")
        content = data.get("content", "")
        hashtags = data.get("hashtags", [])
        post_id = f"POST_{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now().isoformat()

        # Persist to outputs for the session
        OUTPUTS_DIR.mkdir(exist_ok=True)
        log_path = OUTPUTS_DIR / "posted_content.jsonl"
        with log_path.open("a") as f:
            f.write(json.dumps({
                "post_id": post_id,
                "platform": platform,
                "content": content,
                "hashtags": hashtags,
                "timestamp": timestamp,
                "status": "published",
            }) + "\n")

        return (
            f"[SIMULATED] Post published successfully.\n"
            f"Platform : {platform}\n"
            f"Post ID  : {post_id}\n"
            f"Timestamp: {timestamp}\n"
            f"Preview  : {content[:100]}{'...' if len(content) > 100 else ''}"
        )


class MockFetchCommentsTool(BaseTool):
    """Fetch mock comments/mentions from the metrics dataset."""

    name: str = "mock_fetch_comments"
    description: str = (
        "Fetch recent user comments or mentions for a platform from the mock dataset. "
        "Input: platform name (e.g. 'Instagram'). "
        "Returns a list of comments with sentiment labels."
    )
    metrics_path: Path = MOCK_METRICS_DIR / "sample_metrics.json"

    def _run(self, platform: str) -> str:
        if not self.metrics_path.exists():
            return "Error: metrics file not found."
        data = json.loads(self.metrics_path.read_text())
        comments = [
            c for c in data.get("top_comments_sample", [])
            if platform.lower() in c["platform"].lower()
        ]
        if not comments:
            return f"No comments found for platform: {platform}"
        lines = [f"[{c['sentiment'].upper()}] {c['text']}" for c in comments]
        return f"Recent comments on {platform}:\n" + "\n".join(lines)


class MockFetchMetricsTool(BaseTool):
    """Fetch simulated engagement metrics for analysis."""

    name: str = "mock_fetch_metrics"
    description: str = (
        "Retrieve simulated 30-day engagement metrics (likes, comments, shares, "
        "engagement rate) and content insights for a platform. "
        "Input: platform name or 'all' for all platforms."
    )
    metrics_path: Path = MOCK_METRICS_DIR / "sample_metrics.json"

    def _run(self, platform: str) -> str:
        if not self.metrics_path.exists():
            return "Error: metrics file not found."
        data = json.loads(self.metrics_path.read_text())
        summary = data.get("platform_summary", {})
        insights = data.get("content_insights", [])

        if platform.lower() == "all":
            result = json.dumps(summary, indent=2)
        else:
            matched = {k: v for k, v in summary.items() if platform.lower() in k.lower()}
            result = json.dumps(matched, indent=2) if matched else f"No data for {platform}"

        insights_text = "\n".join(f"- {i}" for i in insights)
        return f"Metrics:\n{result}\n\nGeneral Insights:\n{insights_text}"
