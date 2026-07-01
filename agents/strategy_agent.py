"""Module 4a — Strategy Agent (crewai 1.x compatible)"""

from crewai import Agent
from config.settings import get_llm, VERBOSE_LOGGING
from tools import BrandGuidelinesLoaderTool, BrandKnowledgeTool, MockFetchMetricsTool


def create_strategy_agent() -> Agent:
    llm = get_llm()
    return Agent(
        role="Social Media Strategy Director",
        goal=(
            "Analyse the brand guidelines and campaign brief to produce a specific, "
            "audience-tailored content strategy. Always ground recommendations in the "
            "brand's actual tone, audience demographics, platform preferences, and past "
            "campaign patterns. Never produce generic advice."
        ),
        backstory=(
            "You are a veteran digital marketing strategist with 12 years of experience "
            "across Instagram, LinkedIn, Twitter, and Facebook. You understand that a "
            "fitness brand targeting 18–30 year-olds needs completely different content "
            "from a B2B SaaS targeting CTOs. You always read the brand guidelines first, "
            "then tailor every recommendation to the specific audience and platform — "
            "because what works on LinkedIn kills engagement on Instagram."
        ),
        tools=[
            BrandGuidelinesLoaderTool(),
            BrandKnowledgeTool(),
            MockFetchMetricsTool(),
        ],
        llm=llm,
        allow_delegation=False,
        verbose=VERBOSE_LOGGING,
        max_iter=3,
    )
