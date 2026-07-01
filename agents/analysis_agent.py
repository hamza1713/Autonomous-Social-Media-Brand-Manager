"""Module 4e — Analysis Agent (crewai 1.x compatible)"""

from crewai import Agent
from config.settings import get_llm, VERBOSE_LOGGING
from tools import MockFetchMetricsTool, SentimentAnalysisTool


def create_analysis_agent() -> Agent:
    llm=get_llm()
    return Agent(
        role="Social Media Performance Analyst",
        goal=(
            "Analyse engagement metrics, identify which content types perform best, "
            "detect sentiment trends, and produce actionable recommendations for the next cycle."
        ),
        backstory=(
            "You are data-driven: you have cut client budgets by 30% while tripling "
            "engagement by knowing what works. You translate raw metrics into plain-language "
            "insights with prioritised action lists."
        ),
        tools=[
            MockFetchMetricsTool(),
            SentimentAnalysisTool(),
        ],
        llm=llm,
        allow_delegation=False,
        verbose=VERBOSE_LOGGING,
        max_iter=3,
    )
