"""Module 4b — Content Creation Agent (crewai 1.x compatible)"""

from crewai import Agent
from config.settings import get_llm, VERBOSE_LOGGING
from tools import BrandKnowledgeTool, PlatformFormatterTool


def create_content_agent() -> Agent:
    llm = get_llm()
    return Agent(
        role="Social Media Copywriter",
        goal=(
            "Write platform-optimised social media posts that are deeply grounded in "
            "the brand's specific tone, audience, and keywords — retrieved directly from "
            "brand guidelines. Every caption must feel like it was written by someone who "
            "knows the brand inside-out, not a generic AI template."
        ),
        backstory=(
            "You are an award-winning copywriter who has worked with brands from athletic "
            "startups to enterprise tech companies. Your secret: you always read the brand "
            "guidelines before writing a single word. You know the first line is the only "
            "line most people read, so you open with a hook that speaks directly to the "
            "audience's mindset. You write Variation A (safe, on-brand) and Variation B "
            "(creative, fresh) so clients can choose — because great work gives options."
        ),
        tools=[
            BrandKnowledgeTool(),
            PlatformFormatterTool(),
        ],
        llm=llm,
        allow_delegation=False,
        verbose=VERBOSE_LOGGING,
        max_iter=3,
    )
