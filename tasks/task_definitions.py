"""
Module 5 — Task Definitions (Enhanced)
All 5 tasks are upgraded with:
  - Brand context injection (tone, audience, keywords)
  - Forced RAG usage ("use at least 1 phrase from guidelines")
  - Configurable tone_intensity, creativity_level, post_length
  - 2 content variations per post
  - Naturalness guardrails in brand review
  - Observed-trend language in analysis (no fake numbers)
  - Memory references where available
"""

from crewai import Task, Agent


# ── Task 1: Strategy Planning ─────────────────────────────────────────────────

def create_strategy_task(
    strategy_agent: Agent,
    campaign_brief: str,
    platforms: list[str],
    tone_intensity: str = "balanced",
    creativity_level: str = "creative",
    post_length: str = "medium",
) -> Task:
    """
    Strategy Agent loads brand guidelines, then builds a platform/audience-
    specific content plan tailored to the user's configuration.
    """
    platforms_str = ", ".join(platforms)
    length_map = {
        "short": "very concise 1–2 sentence posts",
        "medium": "conversational 3–4 sentence posts",
        "long": "detailed 5–6 sentence posts",
    }
    length_guide = length_map.get(post_length, "conversational 3–4 sentence posts")

    return Task(
        description=(
            f"Campaign brief: '{campaign_brief}'\n"
            f"Target platforms: {platforms_str}\n"
            f"User settings — Tone: {tone_intensity} | Style: {creativity_level} | "
            f"Post length: {length_guide}\n\n"
            "STEP 1 — Load brand context:\n"
            "  Use the brand knowledge tool to extract:\n"
            "  • Brand name and target audience (age, interests, lifestyle)\n"
            "  • Tone & voice rules (what TO do and what to AVOID)\n"
            "  • Key brand keywords, taglines, and example phrases\n\n"
            "STEP 2 — Check memory:\n"
            "  If previous campaign data is available, open with "
            "'Based on previous campaigns...' and use those patterns to improve this strategy.\n\n"
            "STEP 3 — Produce a concise, brand-specific strategy:\n"
            "1. Campaign theme + one-line key message "
            "(must use brand language — not generic phrases).\n"
            "2. Content mix: product% / educational% / community% / promo%.\n"
            "3. Exactly 3 post ideas, each tied to the brand's audience:\n"
            "   Format: title | hook sentence | content type | platform\n"
            f"4. Posting cadence for each platform in {platforms_str} (one line each).\n"
            "5. 2 measurable KPIs relevant to this campaign.\n\n"
            "Be specific to the brand. Avoid generic marketing advice. No padding."
        ),
        expected_output=(
            "Concise markdown strategy:\n"
            "## Theme & Key Message\n"
            "[2 sentences using brand language]\n\n"
            "## Content Mix\n"
            "[one line]\n\n"
            "## 3 Post Ideas\n"
            "1. title | hook | type | platform\n"
            "2. ...\n"
            "3. ...\n\n"
            "## Cadence\n"
            "- [Platform]: [frequency]\n\n"
            "## KPIs\n"
            "1. [KPI]\n"
            "2. [KPI]"
        ),
        agent=strategy_agent,
    )


# ── Task 2: Content Creation ──────────────────────────────────────────────────

def create_content_task(
    content_agent: Agent,
    strategy_task: Task,
    platforms: list[str],
    tone_intensity: str = "balanced",
    creativity_level: str = "creative",
    post_length: str = "medium",
) -> Task:
    """
    Content Agent injects brand context from RAG, writes 2 variations per post,
    and personalizes for the target audience.
    """
    platforms_str = ", ".join(platforms)
    length_map = {
        "short": "under 80 words",
        "medium": "80–150 words",
        "long": "150–220 words",
    }
    length_guide = length_map.get(post_length, "80–150 words")

    tone_guide = {
        "subtle": "understated, calm, professional — let the content speak quietly",
        "balanced": "warm, friendly, conversational — relatable but polished",
        "bold": "energetic, punchy, attention-grabbing — every word earns its place",
    }.get(tone_intensity, "warm, friendly, conversational")

    creativity_guide = {
        "conservative": "safe proven formats, clear direct CTAs, minimal risk",
        "creative": "engaging story-driven hooks, personality, surprising angles",
        "experimental": "unexpected metaphors, bold pattern-interrupts, challenge conventions",
    }.get(creativity_level, "engaging story-driven hooks, personality, surprising angles")

    return Task(
        description=(
            f"Platforms: {platforms_str}\n"
            f"Caption length: {length_guide} | Tone: {tone_guide} | Style: {creativity_guide}\n\n"
            "STEP 1 — Load brand context (REQUIRED):\n"
            "  Use the brand knowledge tool to retrieve:\n"
            "  • Brand tone rules and voice guidelines\n"
            "  • Target audience description (age, interests, mindset)\n"
            "  • Brand keywords, taglines, and example phrases\n"
            "  You MUST include at least 1 phrase or keyword from the brand guidelines "
            "in every caption. Label it with [brand voice] in your thinking.\n\n"
            "STEP 2 — Audience personalization:\n"
            "  Read the audience description. Adjust language accordingly:\n"
            "  • Young adults (18–30): energetic, relatable, emoji-friendly\n"
            "  • Professionals (25–45): aspirational, grounded, value-focused\n"
            "  • Developers/tech: precise, clever, jargon-aware but not over-technical\n\n"
            "STEP 3 — Write 2 VARIATIONS for each of the 3 post ideas from the strategy:\n"
            "  Variation A — Closer to the brand's established voice (safe, on-brand)\n"
            "  Variation B — A more creative/experimental angle (fresh perspective)\n\n"
            "For each variation:\n"
            "  - Platform name\n"
            "  - Caption: hook + body + CTA\n"
            f"  - Length: {length_guide}\n"
            "  - 3–5 hashtags (platform-appropriate)\n\n"
            "No placeholder text. Every post must feel human and brand-specific. "
            "Do not start every caption with 'Introducing' or 'Are you ready'."
        ),
        expected_output=(
            "3 posts, each with 2 variations:\n\n"
            "--- POST 1 ---\n"
            "Variation A | Platform: X\n"
            "Caption: [hook + body + CTA]\n"
            "Hashtags: #tag1 #tag2 #tag3\n\n"
            "Variation B | Platform: X\n"
            "Caption: [hook + body + CTA]\n"
            "Hashtags: #tag1 #tag2 #tag3\n\n"
            "--- POST 2 --- [same format]\n"
            "--- POST 3 --- [same format]"
        ),
        agent=content_agent,
        context=[strategy_task],
    )


# ── Task 3: Brand Voice Review ────────────────────────────────────────────────

def create_brand_review_task(
    brand_voice_agent: Agent,
    content_task: Task,
) -> Task:
    """
    Brand Voice Agent runs 5 quality checks on all 6 variations,
    labels each APPROVED or REVISED, and outputs a feedback summary.
    """
    return Task(
        description=(
            "Load the brand guidelines first. Then review all post variations.\n\n"
            "For EACH variation, run all 5 checks:\n"
            "1. TONE MATCH: Does the tone match the brand voice rules exactly? "
            "Is the intensity appropriate for the brand?\n"
            "2. NATURALNESS: Does it sound like a real human wrote it? "
            "Flag any awkward phrasing, robotic structures, or unnatural word choices "
            "(e.g. 'second-degree nature', 'leverage synergies').\n"
            "3. GUARDRAILS: Check for: all-caps words (except brand name), competitor mentions, "
            "inappropriate content, excessive exclamation marks (max 1 per post).\n"
            "4. AUDIENCE FIT: Is the vocabulary, register, and tone right for the stated audience?\n"
            "5. HASHTAG CHECK: Correct count for the platform? Relevant to the content?\n\n"
            "Label each: APPROVED (passes all checks) or REVISED (at least one check failed).\n"
            "For REVISED: write one line describing what was wrong, then the corrected final version.\n\n"
            "After all reviews, write a FEEDBACK SUMMARY with 2–3 bullet points listing "
            "recurring issues across the variations — this is the feedback loop for the content team.\n\n"
            "STOP CONDITION — CRITICAL:\n"
            "Your output MUST end immediately after the FEEDBACK SUMMARY section. "
            "Do NOT write comments, replies, engagement content, analysis, or anything "
            "beyond the 6 reviewed posts and the feedback summary. If a post from the "
            "content task appears truncated or incomplete, note this in the FEEDBACK "
            "SUMMARY as an issue — do not attempt to continue or complete it yourself, "
            "and do not fabricate additional content of any kind."
        ),
        expected_output=(
            "For each of the 6 variations:\n"
            "POST [n][A/B] — APPROVED\n"
            "Final: [caption] | Hashtags: [...]\n\n"
            "OR:\n"
            "POST [n][A/B] — REVISED\n"
            "Issue: [one-line description of the problem]\n"
            "Final: [corrected caption] | Hashtags: [...]\n\n"
            "ENDS WITH (and nothing after):\n"
            "## FEEDBACK SUMMARY\n"
            "• [Recurring issue 1]\n"
            "• [Recurring issue 2]\n"
            "• [Recurring issue 3 if applicable]"
        ),
        agent=brand_voice_agent,
        context=[content_task],
    )


# ── Task 4: Engagement Replies ────────────────────────────────────────────────

def create_engagement_task(
    engagement_agent: Agent,
    platforms: list[str],
    tone_intensity: str = "balanced",
) -> Task:
    """
    Engagement Agent fetches comments, analyses sentiment, and writes
    personalized, context-aware brand replies.
    """
    platforms_str = ", ".join(platforms)
    tone_guide = {
        "subtle": "calm, measured, professional",
        "balanced": "warm, friendly, and genuinely helpful",
        "bold": "enthusiastic, energetic, and memorable",
    }.get(tone_intensity, "warm, friendly, and genuinely helpful")

    return Task(
        description=(
            f"Fetch recent comments from: {platforms_str}.\n\n"
            "STEP 1 — Load brand context:\n"
            "  Use brand knowledge tool — get brand name, audience, tone rules, "
            "and any key product/service names.\n\n"
            "STEP 2 — For each comment:\n"
            f"  a. Run sentiment_analysis to classify: positive / neutral / negative.\n"
            f"  b. Write a reply using the brand's {tone_guide} tone.\n"
            "     Rules for each sentiment:\n"
            "     • POSITIVE: Thank them by echoing something specific from their comment "
            "('Love that you noticed X!'). Add a brand-relevant value (product tip, fact).\n"
            "     • NEUTRAL/QUESTION: Give a specific, helpful answer using brand knowledge. "
            "Don't say 'Great question!' — just answer it directly.\n"
            "     • NEGATIVE: Acknowledge sincerely ('You're right that...'). "
            "Don't be defensive. Offer a clear next step (DM, support, refund).\n"
            "  c. Length: under 150 characters for Instagram/Twitter; up to 250 for LinkedIn.\n"
            "  d. Never use generic openers like 'Thanks for your comment!' or "
            "'We appreciate your feedback!'\n\n"
            "Based on previous memory: if similar comments have appeared before, "
            "reference that pattern to improve this reply."
        ),
        expected_output=(
            "Comment-reply pairs:\n\n"
            "COMMENT [platform | sentiment]: [original comment text]\n"
            "REPLY: [personalized, brand-specific reply]\n\n"
            "Repeat for all comments fetched."
        ),
        agent=engagement_agent,
    )


# ── Task 5: Performance Analysis ─────────────────────────────────────────────

def create_analysis_task(
    analysis_agent: Agent,
    brand_review_task: Task,
    platforms: list[str],
) -> Task:
    platforms_str = ", ".join(platforms)

    return Task(
        description=(
            f"Target platforms for THIS campaign: {platforms_str}\n"
            f"CRITICAL: Only analyze and report on these platform(s): {platforms_str}. "
            f"Do not mention, fetch, or invent data for any other platform "
            f"(e.g. if a platform is not in the list above, never reference it).\n\n"
            f"Fetch engagement metrics using the metrics tool, filtering to "
            f"{platforms_str} only. If the tool returns data for other platforms, "
            "ignore it.\n\n"
            "CRITICAL RULE — Language accuracy:\n"
            "Do NOT state specific percentages as hard facts. "
            "Always use qualified language:\n"
            "  ✅ 'estimated higher engagement based on observed patterns'\n"
            "  ✅ 'data suggests video content outperforms static posts'\n"
            "  ✅ 'an observed trend toward higher comment rates on question-based posts'\n"
            "  ❌ '38% more engagement' (never fabricate specific numbers)\n"
            "  ❌ '78% of users preferred...' (never invent statistics)\n\n"
            "CRITICAL RULE — Recommendation quality:\n"
            "Before writing each recommendation, ask yourself: 'Is this already stated "
            "in the campaign strategy or KPIs?' If yes, do not repeat it as a new finding. "
            "Instead, either CONFIRM it with data support "
            "(e.g. 'The question-CTA approach in the strategy is validated by observed "
            "comment trends — maintain it') OR surface a genuinely new insight the "
            "strategy did not already cover. Every recommendation must add new value, "
            "not restate the plan.\n\n"
            "If memory contains previous campaign data, open with "
            "'Based on previous campaigns, ...' to show continuity.\n\n"
            "Report structure (be concise, no padding):\n"
            f"1. Top content type for EACH of {platforms_str} — 1 sentence each using "
            "observed-trend language. Do not include platforms outside this list.\n"
            "2. Sentiment summary from the brand-reviewed posts — one line.\n"
            "3. Two actionable recommendations — each must follow this format:\n"
            "   WHY: [what the data suggests] → DO THIS: [specific action]\n"
            "   At least one must be a genuinely new insight not present in the strategy.\n"
        ),
        expected_output=(
            "## Top Content Trends\n"
            f"- [Platform from {platforms_str}]: [observed trend, not a fake number]\n\n"
            "## Sentiment Summary\n"
            "[one line]\n\n"
            "## Recommendations\n"
            "1. WHY: [data-backed reason] → DO THIS: [specific action]\n"
            "2. WHY: [data-backed reason] → DO THIS: [specific action]\n\n"
            "Note: At least one recommendation must surface a new insight beyond "
            "what the campaign strategy already specifies."
        ),
        agent=analysis_agent,
        context=[brand_review_task],
    )