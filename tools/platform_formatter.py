"""
Module 3d — Platform Formatter Tool
Validates and trims content to meet platform-specific constraints
(character limits, hashtag count, etc.) before posting.
"""

import json
from crewai.tools import BaseTool
from config.settings import PLATFORM_LIMITS


class PlatformFormatterTool(BaseTool):
    """Validate and trim a post to meet platform-specific rules."""

    name: str = "platform_formatter"
    description: str = (
        "Validate and reformat social media content to comply with "
        "platform-specific character limits and hashtag rules. "
        "Input JSON: {\"platform\": \"Instagram\", \"caption\": \"...\", \"hashtags\": [...]}. "
        "Returns a formatted, compliant version of the content."
    )

    def _run(self, payload: str) -> str:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return "Error: input must be valid JSON."

        platform = data.get("platform", "")
        caption: str = data.get("caption", "")
        hashtags: list[str] = data.get("hashtags", [])

        if platform not in PLATFORM_LIMITS:
            return (
                f"Unknown platform '{platform}'. "
                f"Supported: {list(PLATFORM_LIMITS.keys())}"
            )

        limits = PLATFORM_LIMITS[platform]
        max_chars: int = limits["max_caption_chars"]
        best_hashtags: int = limits["best_hashtags"]
        max_hashtags: int = limits["max_hashtags"]

        issues: list[str] = []

        # Trim hashtags
        if len(hashtags) > max_hashtags:
            hashtags = hashtags[:max_hashtags]
            issues.append(f"Hashtags trimmed to {max_hashtags} (platform maximum).")
        if len(hashtags) > best_hashtags:
            issues.append(
                f"Tip: {platform} performs best with {best_hashtags} hashtags "
                f"(you have {len(hashtags)})."
            )

        # Ensure hashtags have #
        hashtags = [h if h.startswith("#") else f"#{h}" for h in hashtags]
        hashtag_block = " ".join(hashtags)

        # Full text = caption + hashtags
        full_text = f"{caption}\n\n{hashtag_block}" if hashtag_block else caption
        if len(full_text) > max_chars:
            # Trim caption to fit
            overflow = len(full_text) - max_chars
            caption = caption[: max(0, len(caption) - overflow - 3)] + "..."
            full_text = f"{caption}\n\n{hashtag_block}" if hashtag_block else caption
            issues.append(
                f"Caption trimmed by {overflow} chars to fit {platform}'s {max_chars}-char limit."
            )

        status = "✓ Compliant" if not any("trimmed" in i for i in issues) else "⚠ Adjusted"
        issue_text = "\n".join(issues) if issues else "No issues found."

        return (
            f"Status   : {status}\n"
            f"Platform : {platform}\n"
            f"Issues   : {issue_text}\n\n"
            f"--- Formatted Post ---\n{full_text}"
        )
