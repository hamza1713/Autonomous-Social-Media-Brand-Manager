"""
Module 3a — Brand Knowledge Tool
Reads brand guideline files and returns relevant sections.
Uses simple keyword search (no vector DB needed for FYP; easy to upgrade to FAISS).
"""

from pathlib import Path
from crewai.tools import BaseTool
from pydantic import Field
from config.settings import BRAND_GUIDELINES_DIR


class BrandKnowledgeTool(BaseTool):
    """Search the loaded brand guidelines for relevant sections."""

    name: str = "brand_knowledge_search"
    description: str = (
        "Search the brand guidelines document for information about tone, "
        "voice, target audience, products, hashtags, or content strategy. "
        "Input: a keyword or topic (e.g. 'tone', 'hashtags', 'products')."
    )
    guidelines_path: Path = Field(default=BRAND_GUIDELINES_DIR / "sample_brand.txt")

    def _run(self, query: str) -> str:
        """Return paragraphs/sections that match the query keyword."""
        if not self.guidelines_path.exists():
            return "Error: brand guidelines file not found."

        content = self.guidelines_path.read_text(encoding="utf-8")
        query_lower = query.lower()

        # Split into sections by ## headings
        sections: list[str] = []
        current: list[str] = []
        for line in content.splitlines():
            if line.startswith("## ") and current:
                sections.append("\n".join(current))
                current = [line]
            else:
                current.append(line)
        if current:
            sections.append("\n".join(current))

        # Return any section whose text contains the query keyword
        matched = [s for s in sections if query_lower in s.lower()]
        if not matched:
            # Fallback: return full document
            return content
        return "\n\n---\n\n".join(matched)


class BrandGuidelinesLoaderTool(BaseTool):
    """Load the full brand guidelines document."""

    name: str = "load_brand_guidelines"
    description: str = (
        "Load and return the complete brand guidelines document. "
        "Use this when you need full context about the brand."
    )
    guidelines_path: Path = Field(default=BRAND_GUIDELINES_DIR / "sample_brand.txt")

    def _run(self, _: str = "") -> str:
        if not self.guidelines_path.exists():
            return "Error: brand guidelines file not found."
        return self.guidelines_path.read_text(encoding="utf-8")
