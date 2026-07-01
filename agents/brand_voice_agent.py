"""Module 4c — Brand Voice Agent (crewai 1.x compatible)"""

from crewai import Agent
from config.settings import get_llm, VERBOSE_LOGGING
from tools import BrandGuidelinesLoaderTool, BrandKnowledgeTool, PlatformFormatterTool


def create_brand_voice_agent() -> Agent:
    llm = get_llm()
    return Agent(
        role="Brand Voice Guardian",
        goal=(
            "Review every piece of generated content against brand guidelines. "
            "Ensure consistent tone, correct language, adherence to values, and platform fit. "
            "Return approved or rewritten versions."
        ),
        backstory=(
            "You are the strictest editor the brand has ever worked with — but fair. "
            "You have the brand guidelines memorised. You detect a brand voice violation "
            "in 10 seconds. You don't just flag issues — you fix them."
        ),
        tools=[
            BrandGuidelinesLoaderTool(),
            BrandKnowledgeTool(),
            PlatformFormatterTool(),
        ],
        llm=llm,
        allow_delegation=False,
        verbose=VERBOSE_LOGGING,
        max_iter=3,
    )
