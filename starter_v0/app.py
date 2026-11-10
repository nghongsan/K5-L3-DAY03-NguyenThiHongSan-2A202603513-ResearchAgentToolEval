"""Streamlit UI for the Research Agent — "Mochi" pastel theme.

Run from starter_v0/ (so .streamlit/config.toml is picked up):
    streamlit run app.py
Then expose it for other teams:
    cloudflared tunnel --url http://localhost:8501

Reuses the exact multi-round tool loop from chat.py, so the UI behaves like the CLI
and every session is logged to transcripts/*.transcript.json.
"""
from __future__ import annotations

import html
import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import ARTIFACTS_DIR, ROOT, now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

PROVIDER = os.getenv("APP_PROVIDER", "openai")
VERSION = os.getenv("APP_VERSION", "v3")
MODEL = os.getenv("APP_MODEL") or None
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4

BOT_AVATAR = "🐰"
USER_AVATAR = "🌸"

# Icon + short Vietnamese label for every tool (used in chips and tool-call bubbles).
TOOL_STYLE = {
    "clarify": ("💭", "hỏi lại"),
    "timeline": ("🐦", "tweet của 1 người"),
    "social_search": ("💬", "tweet theo chủ đề"),
    "lookup": ("🔎", "tìm tin trên web"),
    "fetch": ("🔗", "đọc 1 đường link"),
    "format": ("🎀", "gói thành bản tin"),
    "send": ("💌", "gửi Telegram"),
    "policy": ("📜", "policy công ty"),
    "papers": ("📄", "tìm paper arXiv"),
    "paper_text": ("📖", "đọc paper arXiv"),
    "wiki": ("📚", "Wikipedia"),
    "hn_search": ("🧡", "Hacker News"),
    "github_repo": ("🐙", "GitHub repo"),
    "rss": ("📰", "đọc RSS feed"),
}

# (emoji, question, tool it needs or None)
SAMPLE_QUESTIONS = [
    ("📚", "Transformer trong machine learning là gì? Tra Wikipedia giúp mình.", None),
    ("🧡", "Dân dev trên Hacker News đang bàn gì về AI agents? Lấy 3 bài nổi bật nhất", None),
    ("🐙", "Repo pytorch/pytorch có bao nhiêu sao, license gì?", None),
    ("📰", "Đọc 3 bài mới nhất từ feed https://hnrss.org/frontpage", None),
    ("📜", "Theo policy công ty, đăng bản tin lên Telegram có cần xác nhận trước không?", None),
    ("🔎", "Tin tức AI hôm nay có gì nổi bật?", "lookup"),
    ("🐦", "Lấy 3 tweet mới nhất của Andrej Karpathy", "timeline"),
    ("💌", "Đăng bản tin AI hôm nay lên Telegram giúp mình", "send"),
]

st.set_page_config(page_title="Mochi Research", page_icon="🐰", layout="wide", initial_sidebar_state="auto")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700;800&family=Nunito:wght@400;600;700;800&display=swap');

:root{
  --pink:#ff7eb3; --pink-deep:#e8508f; --pink-soft:#ffe3ee; --pink-mist:#fff4f8;
  --lav:#c9b6ff; --lav-soft:#efe8ff; --mint:#bdf0dc; --peach:#ffd9c2;
  --ink:#5b3a4f; --ink-soft:#9a7489; --white:#ffffff;
  --shadow:0 10px 30px -12px rgba(232,80,143,.35);
}

html, body, .stApp, [class*="css"], .stMarkdown, button, input, textarea {
  font-family:'Nunito', system-ui, sans-serif !important; color:var(--ink);
}
.stApp{
  background:
    radial-gradient(circle at 12% 18%, rgba(255,126,179,.18) 0 120px, transparent 121px),
    radial-gradient(circle at 88% 8%, rgba(201,182,255,.25) 0 160px, transparent 161px),
    radial-gradient(circle at 92% 85%, rgba(189,240,220,.30) 0 140px, transparent 141px),
    radial-gradient(rgba(255,126,179,.10) 1.5px, transparent 1.6px) 0 0/22px 22px,
    linear-gradient(180deg, var(--pink-mist), #fbf6ff);
}
header[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:1.6rem; max-width:980px}

/* ---------- hero ---------- */
.mochi-hero{
  position:relative; overflow:hidden; border-radius:28px; padding:26px 28px 24px;
  background:linear-gradient(120deg, #ffc2da 0%, #f6c9ff 55%, #c9e9ff 100%);
  box-shadow:var(--shadow); border:3px solid var(--white);
  display:flex; gap:20px; align-items:center; margin-bottom:18px;
}
.mochi-hero .bunny{
  font-size:64px; line-height:1; flex:none; filter:drop-shadow(0 6px 8px rgba(232,80,143,.25));
  animation:bob 3.2s ease-in-out infinite;
}
@keyframes bob{0%,100%{transform:translateY(0) rotate(-3deg)}50%{transform:translateY(-6px) rotate(3deg)}}
@media (prefers-reduced-motion: reduce){.mochi-hero .bunny{animation:none}}
@media (max-width: 640px){
  .mochi-hero{flex-direction:column; align-items:flex-start; gap:8px; padding:20px 18px}
  .mochi-hero .bunny{font-size:48px}
  .mochi-hero h1{font-size:1.9rem !important}
}
.mochi-hero h1{
  font-family:'Baloo 2', 'Nunito', sans-serif !important; font-weight:800; font-size:2.35rem;
  margin:0; line-height:1.05; color:#7a2e5a; letter-spacing:.2px;
}
.mochi-hero p{margin:6px 0 0; font-size:1.02rem; color:#6b3f5c; max-width:60ch}
.mochi-hero .sparkle{position:absolute; font-size:22px; opacity:.85}
.mochi-hero .s1{top:12px; right:24px} .mochi-hero .s2{bottom:12px; right:120px; font-size:16px}
.mochi-hero .s3{top:46px; right:84px; font-size:14px}
.pill-row{display:flex; flex-wrap:wrap; gap:6px; margin-top:12px}
.pill{background:rgba(255,255,255,.75); border-radius:999px; padding:3px 11px; font-size:.82rem; font-weight:700; color:#8a3a68}

/* ---------- welcome ---------- */
.welcome-title{font-family:'Baloo 2',sans-serif !important; font-weight:700; font-size:1.3rem; color:#8a3a68; margin:4px 0 2px}
.welcome-sub{color:var(--ink-soft); margin:0 0 10px}

/* ---------- buttons (sample cards + sidebar) ---------- */
.stButton > button{
  border-radius:18px !important; border:2px solid var(--pink-soft) !important;
  background:var(--white) !important; color:var(--ink) !important; font-weight:700 !important;
  padding:.65rem .9rem !important; text-align:left !important; justify-content:flex-start !important;
  box-shadow:0 4px 14px -8px rgba(232,80,143,.45); transition:transform .15s, border-color .15s, background .15s;
  white-space:normal !important; line-height:1.35 !important; min-height:3.2rem;
}
.stButton > button p, .stButton > button div{
  white-space:normal !important; overflow:visible !important; text-overflow:clip !important; text-align:left !important;
}
.stButton > button:hover{transform:translateY(-2px); border-color:var(--pink) !important; background:var(--pink-mist) !important}
.stButton > button:focus-visible{outline:3px solid var(--lav) !important}

/* ---------- chat ---------- */
[data-testid="stChatMessage"]{
  background:var(--white); border-radius:24px; padding:14px 18px; margin-bottom:12px;
  border:2px solid var(--pink-soft); box-shadow:0 8px 22px -16px rgba(232,80,143,.6);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarCustom"]:not(:empty)) {}
[data-testid="stChatMessageAvatarCustom"], [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"]{
  background:var(--pink-soft) !important; border-radius:50% !important;
}
[data-testid="stChatInput"]{border-radius:22px !important; border:2px solid var(--pink) !important; background:var(--white) !important; box-shadow:var(--shadow)}
[data-testid="stChatInput"] textarea{color:var(--ink) !important}
[data-testid="stBottom"] > div{background:transparent !important}
[data-testid="stBottomBlockContainer"]{background:linear-gradient(180deg, transparent, var(--pink-mist) 40%) !important}

/* tool-call bubbles */
[data-testid="stExpander"] details{
  border-radius:16px !important; border:1.5px dashed var(--lav) !important; background:var(--lav-soft) !important;
}
[data-testid="stExpander"] summary{font-weight:700; color:#5c4596 !important}
.tool-err [data-testid="stExpander"] details{border-color:var(--peach) !important; background:#fff1e8 !important}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#ffe9f2,#f3ecff) !important; border-right:2px solid var(--white)}
[data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3{font-family:'Baloo 2',sans-serif !important; color:#8a3a68 !important}
.chips{display:flex; flex-wrap:wrap; gap:6px; margin:4px 0 8px}
.chip{background:var(--white); border:1.5px solid var(--pink-soft); border-radius:999px; padding:3px 10px; font-size:.8rem; font-weight:700; color:var(--ink)}
.chip.off{background:transparent; border-style:dashed; color:var(--ink-soft); text-decoration:line-through}
.chip.new{border-color:var(--mint); background:#effcf6}
.version-tag{display:inline-block; font-size:.75rem; font-weight:800; background:var(--white); color:#8a3a68; border-radius:999px; padding:2px 10px; border:1.5px solid var(--pink-soft)}
.tiny{font-size:.8rem; color:var(--ink-soft)}
.stSpinner > div{color:#8a3a68 !important; font-weight:700}
</style>
"""

TOOLS_DIR = ROOT / "tools"
NEW_TOOLS = {"wiki", "hn_search", "github_repo", "rss"}


def missing_env(tool_name: str) -> list[str]:
    """Env vars listed in tools/<name>/TOOL.md `requires_env` that are unset or empty."""
    doc = TOOLS_DIR / tool_name / "TOOL.md"
    if not doc.exists():
        return []
    for line in doc.read_text(encoding="utf-8").splitlines():
        if line.startswith("requires_env:"):
            names = line.split(":", 1)[1].strip().strip("[]")
            return [n.strip() for n in names.split(",") if n.strip() and not os.getenv(n.strip())]
    return []


@st.cache_resource
def load_runtime() -> dict:
    prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    all_declarations = load_tool_declarations(tools_path)
    # Demo mode: hide tools whose API keys are not configured, so the agent never calls them.
    disabled = {d["name"]: missing_env(d["name"]) for d in all_declarations}
    disabled = {name: envs for name, envs in disabled.items() if envs}
    declarations = [d for d in all_declarations if d["name"] not in disabled]
    system_prompt = prompt_path.read_text(encoding="utf-8")
    if disabled:
        system_prompt += (
            "\n\n## Demo mode\nCác tool sau KHÔNG khả dụng trong bản demo này (chưa cấu hình API key): "
            + ", ".join(sorted(disabled))
            + ". Nếu người dùng yêu cầu chức năng của chúng, hãy nói rõ là bản demo chưa hỗ trợ và gợi ý việc khác.\n"
        )
    return {
        "system_prompt": system_prompt,
        "disabled": disabled,
        "all_declarations": all_declarations,
        "declarations": declarations,
        "tools": to_openai_tools(declarations),
        "provider": make_provider(PROVIDER),
        "artifact": build_artifact_version(VERSION, prompt_path, tools_path),
    }


def new_transcript(runtime: dict) -> tuple[Path, dict]:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(VERSION), safe_slug(PROVIDER), "ui", stamp])
    path = ROOT / "transcripts" / f"{transcript_id}.transcript.json"
    data = {
        "transcript_id": transcript_id,
        **artifact_version_dict(runtime["artifact"]),
        "provider": PROVIDER,
        "model": MODEL or getattr(runtime["provider"], "default_model", None),
        "system_prompt": str(ARTIFACTS_DIR / "system_prompt.md"),
        "tools": str(ARTIFACTS_DIR / "tools.yaml"),
        "interface": "streamlit",
        "history_window": HISTORY_WINDOW,
        "max_tool_rounds": MAX_TOOL_ROUNDS,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    return path, data


def reset_session(runtime: dict) -> None:
    st.session_state.history = []
    st.session_state.display = []
    st.session_state.transcript_path, st.session_state.transcript = new_transcript(runtime)


def tool_label(name: str, args: dict, failed: bool) -> str:
    icon, label = TOOL_STYLE.get(name, ("✨", name))
    arg_text = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in args.items())
    if len(arg_text) > 90:
        arg_text = arg_text[:87] + "…"
    status = " · 🥺 lỗi" if failed else ""
    return f"{icon} {label} · `{name}`({arg_text}){status}"


def render_tool_events(rounds: list[dict]) -> None:
    for record in rounds:
        for event in record.get("tool_results", []):
            result = event.get("result", {})
            failed = isinstance(result, dict) and "error" in result
            with st.expander(tool_label(event["tool"], event.get("args", {}), failed), expanded=False):
                st.json(result)


def chips_html(names: list[str], css: str = "") -> str:
    parts = []
    for name in names:
        icon, label = TOOL_STYLE.get(name, ("✨", name))
        extra = " new" if name in NEW_TOOLS and not css else ""
        parts.append(f'<span class="chip{extra}{css}" title="{html.escape(name)}">{icon} {html.escape(label)}</span>')
    return '<div class="chips">' + "".join(parts) + "</div>"


runtime = load_runtime()
if "display" not in st.session_state:
    reset_session(runtime)

st.markdown(CSS, unsafe_allow_html=True)

# ---------------- sidebar ----------------
with st.sidebar:
    st.markdown("## 🐰 Mochi Research")
    model_name = MODEL or getattr(runtime["provider"], "default_model", "")
    st.markdown(
        f'<span class="version-tag">✨ {html.escape(runtime["artifact"].artifact_version)}</span> '
        f'<span class="tiny">· {html.escape(PROVIDER)} / {html.escape(model_name)}</span>',
        unsafe_allow_html=True,
    )
    st.markdown("### 🧺 Túi đồ nghề")
    st.markdown(chips_html([d["name"] for d in runtime["declarations"]]), unsafe_allow_html=True)
    st.markdown('<span class="tiny">🌿 viền xanh = tool nhóm tự viết</span>', unsafe_allow_html=True)
    if runtime["disabled"]:
        st.markdown("### 💤 Đang ngủ (thiếu key)")
        st.markdown(chips_html(sorted(runtime["disabled"]), css=" off"), unsafe_allow_html=True)
        st.markdown(
            '<span class="tiny">Điền key vào <code>.env</code> rồi chạy lại app để đánh thức nha.</span>',
            unsafe_allow_html=True,
        )
    st.markdown("### 💗 Mochi hứa")
    st.markdown(
        "- Thiếu thông tin thì **hỏi lại**, không đoán bừa\n"
        "- **Xin phép** trước khi gửi Telegram\n"
        "- Ngoài chuyện research thì từ chối nhẹ nhàng"
    )
    if st.button("🧹 Trò chuyện mới", use_container_width=True):
        reset_session(runtime)
        st.rerun()

# ---------------- hero ----------------
st.markdown(
    """
<div class="mochi-hero">
  <div class="bunny">🐰</div>
  <div>
    <h1>Mochi Research</h1>
    <p>Cô thỏ nhỏ đi lượm tin giúp bạn: Hacker News, Wikipedia, GitHub, RSS, paper arXiv, policy công ty… rồi gói lại thật xinh 🎀</p>
    <div class="pill-row"><span class="pill">🌷 hỏi lại khi thiếu info</span><span class="pill">💌 xin phép trước khi gửi</span><span class="pill">🧁 tiếng Việt</span></div>
  </div>
  <span class="sparkle s1">✨</span><span class="sparkle s2">💗</span><span class="sparkle s3">⭐</span>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------- welcome cards (empty chat) ----------------
if not st.session_state.display:
    st.markdown('<p class="welcome-title">Hôm nay bạn muốn Mochi tìm gì nè? 🍓</p>'
                '<p class="welcome-sub">Bấm thử một thẻ bên dưới, hoặc gõ câu hỏi ở ô chat.</p>', unsafe_allow_html=True)
    available = [(e, q) for e, q, needs in SAMPLE_QUESTIONS if needs not in runtime["disabled"]]
    cols = st.columns(2)
    for index, (emoji, question) in enumerate(available):
        with cols[index % 2]:
            if st.button(f"{emoji}  {question}", key=f"sample_{index}", use_container_width=True):
                st.session_state.pending = question
                st.rerun()

# ---------------- conversation ----------------
for message in st.session_state.display:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        if message.get("rounds"):
            render_tool_events(message["rounds"])
        st.markdown(message["content"])

user_text = st.chat_input("Nhắn cho Mochi nè… ví dụ: repo pytorch/pytorch có bao nhiêu sao? 🐾") or st.session_state.pop("pending", None)

if user_text:
    st.session_state.display.append({"role": "user", "content": user_text})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(user_text)

    messages = [
        {"role": "system", "content": runtime["system_prompt"]},
        *trim_history(st.session_state.history, HISTORY_WINDOW),
        {"role": "user", "content": user_text},
    ]
    turn = {"turn_index": len(st.session_state.transcript["turns"]) + 1, "started_at": now_iso(), "user": user_text}

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner("Mochi đang nhảy đi tìm giúp bạn… 🐾"):
            try:
                result = run_model_tool_loop(
                    provider=runtime["provider"], messages=messages, tools=runtime["tools"],
                    model=MODEL, max_tool_rounds=MAX_TOOL_ROUNDS,
                )
                answer = result["assistant_text"] or "(Mochi chưa nghĩ ra câu trả lời 🥺)"
                if result["status"] == "waiting_for_user":
                    answer = f"💭 {answer}"
                turn.update(result)
                st.session_state.history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": result["assistant_text"]}]
            except Exception as exc:  # show provider errors instead of crashing the page
                answer = f"🥺 Mochi gặp trục trặc khi gọi model: `{type(exc).__name__}: {exc}`"
                result = {"rounds": []}
                turn.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
        render_tool_events(result.get("rounds", []))
        st.markdown(answer)

    st.session_state.display.append({"role": "assistant", "content": answer, "rounds": result.get("rounds", [])})
    turn["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)
