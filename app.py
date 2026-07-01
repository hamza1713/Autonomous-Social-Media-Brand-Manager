"""
Module 8 — Streamlit UI
Interactive web interface for the Autonomous Social Media Brand Manager.
"""

import sys
import json
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import re
from contextlib import contextmanager

# ── Stdout capture for live agent logs ──────────────────────────────────────
class StreamlitTerminal:
    def __init__(self, container):
        self.container = container
        self.log_text = ""
        self.placeholder = self.container.empty()

    def write(self, text):
        clean_text = re.sub(r'\x1b\[[0-9;]*m', '', text)
        self.log_text += clean_text
        if len(self.log_text) > 10000:
            self.log_text = self.log_text[-10000:]
        self.placeholder.markdown(f"```text\n{self.log_text}\n```")

    def flush(self):
        pass


@contextmanager
def capture_stdout(container):
    original_stdout = sys.stdout
    st_terminal = StreamlitTerminal(container)
    sys.stdout = st_terminal
    try:
        yield
    finally:
        sys.stdout = original_stdout


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Social Media Brand Manager",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config.settings import (
    GOOGLE_API_KEY,
    SUPPORTED_PLATFORMS,
    BRAND_GUIDELINES_DIR,
    OUTPUTS_DIR,
)
from crew import SocialMediaCrew, CampaignConfig


# ── Custom CSS ───────────────────────────────────────────────────────────────
def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        .main-header {
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(90deg, #6366f1, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0;
        }
        .sub-header {
            color: #6b7280;
            font-size: 1rem;
            margin-top: -0.4rem;
        }
        .metric-card {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
        }
        .status-pill {
            display: inline-block;
            padding: 0.2rem 0.7rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .status-ready { background: #d1fae5; color: #065f46; }
        .status-idle { background: #fef3c7; color: #92400e; }
        .stTabs [data-baseweb="tab"] {
            font-weight: 600;
            padding: 0.5rem 1rem;
        }
        div[data-testid="stExpander"] {
            border: 1px solid #e5e7eb;
            border-radius: 10px;
        }

        /* ── Agent Pipeline Cards ─────────────────────────────────────────────── */
        @keyframes pulse-glow {
            0%   { box-shadow: 0 0 0 0 rgba(99,102,241,0.55); }
            60%  { box-shadow: 0 0 0 10px rgba(99,102,241,0.0); }
            100% { box-shadow: 0 0 0 0 rgba(99,102,241,0.0); }
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes fadeSlideIn {
            from { opacity:0; transform: translateY(8px); }
            to   { opacity:1; transform: translateY(0);   }
        }

        .pipeline-wrap {
            display: flex;
            align-items: center;
            gap: 0;
            justify-content: center;
            padding: 1.4rem 0.5rem;
            animation: fadeSlideIn 0.4s ease;
        }
        .agent-card {
            flex: 1;
            min-width: 0;
            border-radius: 14px;
            padding: 1.1rem 0.8rem;
            text-align: center;
            transition: transform 0.25s ease, box-shadow 0.25s ease;
            position: relative;
        }
        .agent-card .icon  { font-size: 1.9rem; margin-bottom: 0.3rem; }
        .agent-card .label { font-size: 0.78rem; font-weight: 700; letter-spacing: .03em; margin-bottom: 0.25rem; }
        .agent-card .badge {
            display: inline-block;
            padding: 0.18rem 0.65rem;
            border-radius: 999px;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: .04em;
            text-transform: uppercase;
        }
        /* waiting */
        .agent-waiting {
            background: #f8fafc;
            border: 2px dashed #cbd5e1;
            color: #94a3b8;
        }
        .agent-waiting .badge { background: #e2e8f0; color: #64748b; }

        /* running */
        .agent-running {
            background: linear-gradient(135deg, #eef2ff 0%, #fdf4ff 100%);
            border: 2px solid #6366f1;
            color: #3730a3;
            animation: pulse-glow 1.4s infinite;
            transform: translateY(-4px) scale(1.04);
        }
        .agent-running .badge {
            background: linear-gradient(90deg,#6366f1,#a855f7);
            color: #fff;
        }
        .spinner {
            display: inline-block;
            width: 13px; height: 13px;
            border: 2.5px solid #c7d2fe;
            border-top-color: #6366f1;
            border-radius: 50%;
            animation: spin 0.75s linear infinite;
            vertical-align: middle;
            margin-right: 4px;
        }

        /* done */
        .agent-done {
            background: linear-gradient(135deg,#f0fdf4 0%,#ecfdf5 100%);
            border: 2px solid #22c55e;
            color: #15803d;
        }
        .agent-done .badge { background: #dcfce7; color: #166534; }

        /* connector arrow */
        .pipe-arrow {
            font-size: 1.3rem;
            color: #cbd5e1;
            flex-shrink: 0;
            padding: 0 4px;
            user-select: none;
        }
        .pipe-arrow.active { color: #6366f1; }

        /* overall progress bar */
        .prog-bar-wrap {
            background: #e2e8f0;
            border-radius: 999px;
            height: 7px;
            margin: 0.3rem 0 1rem 0;
            overflow: hidden;
        }
        .prog-bar-fill {
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg,#6366f1,#ec4899);
            transition: width 0.5s ease;
        }

        /* logs panel */
        .log-panel {
            background: #0f172a;
            border-radius: 12px;
            padding: 1rem 1.2rem;
            font-family: 'Courier New', monospace;
            font-size: 0.78rem;
            color: #94a3b8;
            max-height: 260px;
            overflow-y: auto;
            line-height: 1.6;
        }
        </style>
    """, unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def load_guidelines_text() -> str:
    path = BRAND_GUIDELINES_DIR / "sample_brand.txt"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def save_custom_guidelines(text: str) -> None:
    BRAND_GUIDELINES_DIR.mkdir(parents=True, exist_ok=True)
    (BRAND_GUIDELINES_DIR / "sample_brand.txt").write_text(text, encoding="utf-8")


def word_count(text: str) -> int:
    return len((text or "").split())


def render_agent_pipeline(done_count: int, running: bool):
    agents = [("🧠", "Strategy"), ("✍️", "Drafting"), ("✅", "Review"), ("💬", "Engagement"), ("📊", "Analysis")]
    html = '<div class="prog-bar-wrap"><div class="prog-bar-fill" style="width: ' + str((done_count / 5) * 100) + '%"></div></div>'
    html += '<div class="pipeline-wrap">'
    for i, (icon, label) in enumerate(agents):
        state = "agent-done" if i < done_count else ("agent-running" if (running and i == done_count) else "agent-waiting")
        spinner = '<span class="spinner"></span>' if (running and i == done_count) else ""
        html += f'''
            <div class="agent-card {state}">
                <div class="icon">{icon}</div>
                <div class="label">{label}</div>
                <div class="badge">{spinner}{"Done" if i < done_count else ("Running" if (running and i == done_count) else "Pending")}</div>
            </div>
        '''
        if i < 4:
            html += f'<div class="pipe-arrow {"active" if i < done_count else ""}">➔</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar() -> tuple[str, list[str], str, str, str]:
    """Renders sidebar and returns (api_key, platforms, tone_intensity, creativity_level, post_length)."""
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")

        # API Key with status indicator
        api_key = st.text_input(
            "Google API Key",
            value=GOOGLE_API_KEY,
            type="password",
            placeholder="AIza...",
            help="Your Google API key. Or set GOOGLE_API_KEY in .env",
        )
        if api_key:
            st.markdown('<span class="status-pill status-ready">🟢 Key configured</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-pill status-idle">🟡 Key required</span>', unsafe_allow_html=True)

        st.divider()

        # Platform selection — multiselect for compactness
        st.markdown("#### 📡 Target Platforms")
        platforms = st.multiselect(
            "Select platforms",
            options=SUPPORTED_PLATFORMS,
            default=[p for p in ["Instagram", "LinkedIn"] if p in SUPPORTED_PLATFORMS],
            label_visibility="collapsed",
        )
        if not platforms:
            st.warning("⚠️ Select at least one platform.")
            platforms = ["Instagram"]
        else:
            st.caption(f"✓ {len(platforms)} platform(s) selected: {', '.join(platforms)}")

        st.divider()

        # Brand guidelines editor
        st.markdown("#### 🏷️ Brand Guidelines")
        with st.expander("Edit brand guidelines", expanded=False):
            st.caption("✏️ Replace the text below with YOUR brand info — name, tone, audience, hashtags.")
            guidelines = st.text_area(
                "Brand guidelines (editable)",
                value=load_guidelines_text(),
                height=260,
                key="guidelines_editor",
                label_visibility="collapsed",
            )
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("💾 Save", use_container_width=True):
                    save_custom_guidelines(guidelines)
                    st.success("✅ Saved!")
            with col_b:
                if st.button("↩️ Reload", use_container_width=True):
                    st.rerun()

        st.divider()

        # Generation Controls
        st.markdown("#### 🎛️ Generation Controls")

        tone_intensity = st.select_slider(
            "Tone Intensity",
            options=["subtle", "balanced", "bold"],
            value="balanced",
            help="subtle = calm & understated | balanced = warm & conversational | bold = energetic & punchy",
        )

        creativity_level = st.radio(
            "Creativity Level",
            options=["conservative", "creative", "experimental"],
            index=1,
            horizontal=True,
            help="conservative = safe proven formats | creative = story-driven | experimental = bold & unconventional",
        )

        post_length = st.select_slider(
            "Post Length",
            options=["short", "medium", "long"],
            value="medium",
            help="short = under 80 words | medium = 80–150 words | long = 150–220 words",
        )

        # Live config summary
        st.divider()
        with st.container():
            st.caption("**Current Config**")
            st.code(
                f"Tone: {tone_intensity}\n"
                f"Style: {creativity_level}\n"
                f"Length: {post_length}\n"
                f"Platforms: {len(platforms)}",
                language="text",
            )

        st.divider()
        st.caption("🚀 Autonomous Social Media Brand Manager · Powered by CrewAI")

    return api_key, platforms, tone_intensity, creativity_level, post_length


# ── Main UI ───────────────────────────────────────────────────────────────────
def render_main(api_key: str, platforms: list[str], tone_intensity: str, creativity_level: str, post_length: str) -> None:
    inject_custom_css()

    # Header
    col_title, col_status = st.columns([4, 1])
    with col_title:
        st.markdown('<p class="main-header">🚀 Autonomous Social Media Brand Manager</p>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Multi-agent AI system · Strategy → Content → Review → Engagement → Analysis</p>', unsafe_allow_html=True)
    with col_status:
        st.metric("Platforms", len(platforms))

    st.write("")

    # ── Campaign Brief Section ───────────────────────────────────────────────
    with st.container(border=True):
        st.markdown("#### 📝 Campaign Brief")
        col1, col2 = st.columns([3, 1])

        with col1:
            brief = st.text_area(
                "Describe your campaign",
                placeholder=(
                    "e.g. Launch our new Eclipse Espresso blend targeting busy professionals. "
                    "Focus on the ritual and energy boost. Run for 2 weeks."
                ),
                height=130,
                key="brief_input",
                label_visibility="collapsed",
            )
            char_count = len(brief)
            st.caption(f"{char_count} characters")

        with col2:
            st.markdown("**💡 Quick examples**")
            examples = [
                "Launch a summer fitness challenge campaign",
                "Promote a new product for developers",
                "Announce a weekend workshop event",
                "Introduce a new subscription service",
            ]

            def set_brief(text: str):
                st.session_state["brief_input"] = text

            for ex in examples:
                st.button(ex, key=f"ex_{ex[:20]}", on_click=set_brief, args=(ex,), use_container_width=True)

        st.write("")
        run_col1, run_col2, _ = st.columns([1, 1, 2])
        with run_col1:
            run_clicked = st.button(
                "▶ Run Campaign",
                type="primary",
                use_container_width=True,
                disabled=(not brief.strip() or not api_key),
            )
        with run_col2:
            if st.session_state.get("last_result") is not None:
                if st.button("🔄 New Campaign", use_container_width=True):
                    for k in ["last_result", "run_timestamp", "_crew_thread",
                               "_shared", "_toasted"]:
                        st.session_state.pop(k, None)
                    st.rerun()

    if not api_key:
        st.error("🔑 Add your Google API key in the sidebar to run a campaign.")
        return

    # ── Kick off the crew in a background thread on first click ─────────────
    if run_clicked and brief.strip():
        import os
        os.environ["GEMINI_API_KEY"] = api_key
        os.environ["GOOGLE_API_KEY"] = api_key

        current_guidelines = st.session_state.get("guidelines_editor", "")
        if current_guidelines.strip():
            save_custom_guidelines(current_guidelines)

        config = CampaignConfig(
            campaign_brief=brief,
            platforms=platforms,
            tone_intensity=tone_intensity,
            creativity_level=creativity_level,
            post_length=post_length,
        )

        # ── Shared plain-dict bus (safe to write from any thread) ────────────
        # The background thread ONLY touches this dict — never st.session_state.
        # The main Streamlit thread reads from it on every rerun.
        shared: dict = {
            "done_count": 0,   # number of tasks finished (0-5)
            "done":       False,
            "error":      None,
            "log":        "",   # raw stdout captured from the thread
            "result":     None,
            "timestamp":  None,
        }
        st.session_state["_shared"]      = shared
        st.session_state["last_result"]  = None
        st.session_state["_toasted"]     = False

        # ── Stdout logger that writes into the shared dict ───────────────────
        class _SharedLog:
            _ANSI = re.compile(r'\x1b\[[0-9;]*m')
            def write(self, txt: str) -> None:
                clean = self._ANSI.sub("", txt)
                shared["log"] = (shared["log"] + clean)[-15000:]
            def flush(self) -> None:
                pass

        def _run_crew() -> None:
            orig_out = sys.stdout
            sys.stdout = _SharedLog()
            try:
                def _on_done(idx: int) -> None:
                    shared["done_count"] = idx + 1

                crew_obj = SocialMediaCrew(google_api_key=api_key)
                result   = crew_obj.run(config, on_task_done=_on_done)

                shared["result"]     = result
                shared["timestamp"]  = datetime.now().isoformat()
                shared["done_count"] = 5
                shared["done"]       = True
            except Exception as exc:
                shared["error"] = str(exc)
                shared["done"]  = True
            finally:
                sys.stdout = orig_out

        t = threading.Thread(target=_run_crew, daemon=True, name="crew-worker")
        t.start()
        st.session_state["_crew_thread"] = t
        st.rerun()

    # ── Live pipeline view while crew is running ───────────────────────────
    shared: dict = st.session_state.get("_shared", {})
    crew_is_alive = (
        st.session_state.get("_crew_thread") is not None
        and not shared.get("done", True)
    )
    crew_error  = shared.get("error")
    crew_done   = shared.get("done", False)
    crew_result = shared.get("result")

    # Promote result into session_state once it arrives (main thread only)
    if crew_result is not None and st.session_state.get("last_result") is None:
        st.session_state["last_result"]  = crew_result
        st.session_state["run_timestamp"] = shared.get("timestamp", "")

    if crew_is_alive or (crew_done and st.session_state.get("last_result") is None and not crew_error):
        done_count = shared.get("done_count", 0)
        render_agent_pipeline(done_count, running=crew_is_alive)

        if crew_error:
            st.error(f"❌ Agent error: {crew_error}")
        elif crew_is_alive:
            log_text = shared.get("log", "")
            with st.expander("📡 Live Agent Logs", expanded=True):
                # Auto-scroll: newest lines at the bottom; use a JS trick via HTML
                escaped = (
                    log_text
                    .replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace("\n", "<br>")
                )
                st.markdown(
                    f"""
                    <div class="log-panel" id="log-scroll">
                        {escaped}
                    </div>
                    <script>
                        var el = document.getElementById('log-scroll');
                        if (el) el.scrollTop = el.scrollHeight;
                    </script>
                    """,
                    unsafe_allow_html=True,
                )
            time.sleep(1.0)
            st.rerun()
        return

    # ── Display results ─────────────────────────────────────────────
    result = st.session_state.get("last_result")
    if result is None:
        st.info("👈 Enter a campaign brief above and click **Run Campaign** to start.")
        return

    # Show completed pipeline (all-green) once results arrive
    render_agent_pipeline(5, running=False)
    if not st.session_state.get("_toasted"):
        st.toast("🎉 All 5 agents completed! Campaign is ready.", icon="✅")
        st.session_state["_toasted"] = True



    tabs = st.tabs([
        "📋 Strategy",
        "✍️ Posts",
        "✅ Reviewed Posts",
        "💬 Engagement",
        "📊 Analysis",
        "💾 Export",
    ])

    with tabs[0]:
        st.markdown("### 📋 Content Strategy Plan")
        st.markdown(result.strategy)

    with tabs[1]:
        st.markdown("### ✍️ Generated Posts (pre-review)")
        st.markdown(result.posts)

    with tabs[2]:
        col_h, col_b = st.columns([3, 1])
        with col_h:
            st.markdown("### ✅ Brand-Reviewed Final Posts")
        with col_b:
            st.download_button(
                "⬇️ Download .txt",
                data=result.reviewed_posts,
                file_name="reviewed_posts.txt",
                use_container_width=True,
            )
        st.markdown(result.reviewed_posts)
        with st.expander("📋 View as plain text (for copying)"):
            st.code(result.reviewed_posts)

    with tabs[3]:
        st.markdown("### 💬 Engagement Replies")
        st.markdown(result.engagement_replies)

    with tabs[4]:
        st.markdown("### 📊 Performance Analysis Report")
        st.markdown(result.performance_report)

    with tabs[5]:
        st.markdown("### 💾 Export Results")
        data = json.dumps(result.to_dict(), indent=2)
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.download_button(
                "⬇️ Download Full Report (JSON)",
                data=data,
                file_name=f"campaign_{result.timestamp[:10]}.json",
                mime="application/json",
                use_container_width=True,
            )
        with col_e2:
            st.download_button(
                "⬇️ Download Posts Only (TXT)",
                data=result.reviewed_posts,
                file_name=f"posts_{result.timestamp[:10]}.txt",
                use_container_width=True,
            )
        with st.expander("View raw JSON"):
            st.json(result.to_dict())




# ── Entry ─────────────────────────────────────────────────────────────────────
def main() -> None:
    api_key, platforms, tone_intensity, creativity_level, post_length = render_sidebar()
    render_main(api_key, platforms, tone_intensity, creativity_level, post_length)


if __name__ == "__main__":
    main()