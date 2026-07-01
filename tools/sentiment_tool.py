"""
Module 3b — Sentiment & Text Analysis Tool
Uses VADER (rule-based, no API key needed) to classify text sentiment
and extract basic engagement signals from user comments.
"""

import json
from typing import Any, Union
from crewai.tools import BaseTool
from pydantic import field_validator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


_analyzer = SentimentIntensityAnalyzer()


def _classify(compound: float) -> str:
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


class SentimentAnalysisTool(BaseTool):
    """Analyse sentiment of social media text or a list of comments."""

    name: str = "sentiment_analysis"
    description: str = (
        "Analyse the sentiment of a piece of text or a JSON list of comment strings. "
        "Returns a sentiment label (positive / neutral / negative) and a confidence score. "
        "Input: a single string or a JSON array of strings."
    )

    @field_validator("*", mode="before")
    @classmethod
    def _coerce_list_to_str(cls, v: Any) -> Any:
        """If the agent passes a Python list, convert it to a JSON string."""
        if isinstance(v, list):
            return json.dumps(v)
        return v

    def _run(self, text: Union[str, list]) -> str:
        # Handle if a list sneaks through anyway
        if isinstance(text, list):
            items: list[str] = text
        else:
            # Accept a single string or a JSON array
            try:
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    items = parsed
                else:
                    items = [text]
            except (json.JSONDecodeError, ValueError):
                items = [text]

        results = []
        for item in items:
            scores = _analyzer.polarity_scores(str(item))
            label = _classify(scores["compound"])
            results.append({
                "text": str(item)[:120],          # Truncate for readability
                "sentiment": label,
                "compound": round(scores["compound"], 3),
            })

        if len(results) == 1:
            r = results[0]
            return (
                f"Sentiment: {r['sentiment']} (compound score: {r['compound']})\n"
                f"Text: {r['text']}"
            )

        # Multiple items — summarise
        counts = {"positive": 0, "neutral": 0, "negative": 0}
        for r in results:
            counts[r["sentiment"]] += 1
        summary = (
            f"Analysed {len(results)} texts — "
            f"positive: {counts['positive']}, "
            f"neutral: {counts['neutral']}, "
            f"negative: {counts['negative']}\n\n"
        )
        details = "\n".join(
            f"[{r['sentiment']}] {r['text']}" for r in results
        )
        return summary + details
