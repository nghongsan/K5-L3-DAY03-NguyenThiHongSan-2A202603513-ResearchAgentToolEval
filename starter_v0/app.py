"""Streamlit UI for the Research Agent — "Dori Research".

Run from starter_v0/ (so .streamlit/config.toml is picked up):
    streamlit run app.py
Then expose it for other teams:
    cloudflared tunnel --url http://localhost:8501

Reuses the exact multi-round tool loop from chat.py, so the UI behaves like the CLI
and every session is logged to transcripts/*.transcript.json.

Conversation history is scoped per browser: each visitor gets a random `sid` in the
URL, and only conversations saved with that `sid` are listed. People sharing the same
tunnel link therefore never see each other's chats.
"""
from __future__ import annotations

import html
import json
import os
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import ARTIFACTS_DIR, ROOT, now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

APP_NAME = "Dori Research"
PROVIDER = os.getenv("APP_PROVIDER", "openai")
VERSION = os.getenv("APP_VERSION", "v3")
MODEL = os.getenv("APP_MODEL") or None
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4
TRANSCRIPTS_DIR = ROOT / "transcripts"
TOOLS_DIR = ROOT / "tools"

BOT_AVATAR = "🐰"
USER_AVATAR = "🌸"

# Icon + short label for every tool (sidebar chips and tool-call rows).
TOOL_STYLE = {
    "clarify": ("💭", "Hỏi lại người dùng"),
    "timeline": ("🐦", "Bài đăng của một tài khoản X"),
    "social_search": ("💬", "Tìm bài đăng trên X"),
    "lookup": ("🔎", "Tìm kiếm trên web"),
    "fetch": ("🔗", "Đọc nội dung trang web"),
    "format": ("🎀", "Trình bày bản tin"),
    "send": ("💌", "Đăng lên Telegram"),
    "policy": ("📜", "Chính sách nội bộ"),
    "papers": ("📄", "Tìm bài báo arXiv"),
    "paper_text": ("📖", "Đọc bài báo arXiv"),
    "wiki": ("📚", "Wikipedia"),
    "hn_search": ("🧡", "Hacker News"),
    "github_repo": ("🐙", "Kho mã GitHub"),
    "rss": ("📰", "Nguồn tin RSS"),
}
NEW_TOOLS = {"wiki", "hn_search", "github_repo", "rss"}

# (emoji, question, tool it needs). Shown on the welcome screen when that tool is enabled.
SAMPLE_QUESTIONS = [
    ("🔎", "Tin tức AI hôm nay có gì nổi bật?", "lookup"),
    ("📚", "Transformer trong machine learning là gì? Tra cứu Wikipedia giúp tôi.", "wiki"),
    ("🧡", "Cộng đồng Hacker News đang thảo luận gì về AI agents? Lấy 3 bài nổi bật nhất.", "hn_search"),
    ("🐙", "Repo pytorch/pytorch có bao nhiêu sao và dùng license gì?", "github_repo"),
    ("🐦", "Lấy 3 bài đăng mới nhất của Andrej Karpathy.", "timeline"),
    ("📜", "Theo chính sách công ty, đăng bản tin lên Telegram có cần xác nhận trước không?", "policy"),
    ("📰", "Đọc 3 bài mới nhất từ nguồn https://hnrss.org/frontpage", "rss"),
    ("📄", "Tìm các bài báo arXiv mới về đánh giá AI agent.", "papers"),
]

st.set_page_config(page_title=APP_NAME, page_icon="🐰", layout="wide", initial_sidebar_state="auto")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Nunito:wght@400;600;700;800&display=swap');

:root{
  --pink:#ff7eb3; --pink-deep:#d94a86; --pink-soft:#ffe3ee; --pink-mist:#fff6f9;
  --lav:#c9b6ff; --lav-soft:#f1ebff; --mint:#bdf0dc; --mint-soft:#effcf6; --peach-soft:#fff1e8;
  --ink:#4f3446; --ink-soft:#8d6c80; --plum:#7a2e5a; --white:#ffffff;
  --shadow:0 10px 30px -14px rgba(217,74,134,.35);
}

html, body, .stApp, .stMarkdown, button, input, textarea { font-family:'Nunito', system-ui, sans-serif !important; }
.stApp{
  color:var(--ink);
  background:
    radial-gradient(circle at 10% 14%, rgba(255,126,179,.14) 0 120px, transparent 121px),
    radial-gradient(circle at 92% 6%, rgba(201,182,255,.22) 0 170px, transparent 171px),
    radial-gradient(circle at 95% 88%, rgba(189,240,220,.28) 0 150px, transparent 151px),
    radial-gradient(rgba(255,126,179,.09) 1.5px, transparent 1.6px) 0 0/22px 22px,
    linear-gradient(180deg, var(--pink-mist), #fbf7ff);
}
header[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:1.4rem; max-width:960px}

/* ---------- hero ---------- */
.dori-hero{
  position:relative; overflow:hidden; border-radius:26px; padding:24px 28px;
  background:linear-gradient(120deg, #ffcadf 0%, #f3d1ff 55%, #d3ecff 100%);
  box-shadow:var(--shadow); border:3px solid var(--white);
  display:flex; gap:20px; align-items:center; margin-bottom:22px;
}
.dori-hero .bunny{font-size:60px; line-height:1; flex:none; filter:drop-shadow(0 6px 8px rgba(217,74,134,.22)); animation:bob 3.4s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0) rotate(-3deg)}50%{transform:translateY(-5px) rotate(3deg)}}
@media (prefers-reduced-motion: reduce){.dori-hero .bunny{animation:none}}
.dori-hero h1{font-family:'Baloo 2','Nunito',sans-serif !important; font-weight:800; font-size:2.3rem; margin:0; line-height:1.05; color:var(--plum); padding:0}
.dori-hero p{margin:6px 0 0; font-size:1rem; color:#5e3a52; max-width:62ch; line-height:1.5}
.dori-hero .sparkle{position:absolute; font-size:20px; opacity:.8}
.dori-hero .s1{top:12px; right:22px} .dori-hero .s2{bottom:14px; right:96px; font-size:15px}
.dori-hero.compact{padding:12px 20px; gap:14px; margin-bottom:16px; border-radius:20px}
.dori-hero.compact .bunny{font-size:34px}
.dori-hero.compact h1{font-size:1.45rem}
.dori-hero.compact p{margin-top:0; font-size:.88rem}
.dori-hero.compact .s2{display:none}
.pill-row{display:flex; flex-wrap:wrap; gap:6px; margin-top:12px}
.pill{background:rgba(255,255,255,.78); border-radius:999px; padding:3px 11px; font-size:.8rem; font-weight:700; color:var(--plum)}
@media (max-width: 640px){
  .dori-hero{flex-direction:column; align-items:flex-start; gap:8px; padding:20px 18px}
  .dori-hero .bunny{font-size:46px}
  .dori-hero h1{font-size:1.85rem}
}

/* ---------- welcome ---------- */
.welcome-title{font-family:'Baloo 2',sans-serif !important; font-weight:700; font-size:1.25rem; color:var(--plum); margin:0}
.welcome-sub{color:var(--ink-soft); margin:2px 0 12px}

/* ---------- buttons: base ---------- */
.stButton button{
  border-radius:16px !important; border:2px solid var(--pink-soft) !important;
  background:var(--white) !important; color:var(--ink) !important; font-weight:700 !important;
  box-shadow:0 4px 14px -9px rgba(217,74,134,.45); transition:transform .15s, border-color .15s, background .15s;
}
.stButton button:hover{transform:translateY(-1px); border-color:var(--pink) !important; background:var(--pink-mist) !important}
.stButton button:focus-visible{outline:3px solid var(--lav) !important; outline-offset:2px}
.stButton button[kind="primary"]{background:var(--pink) !important; border-color:var(--pink) !important; color:var(--white) !important}
.stButton button[kind="primary"]:hover{background:var(--pink-deep) !important; border-color:var(--pink-deep) !important}

/* sample cards: left-aligned, equal height */
.st-key-samples .stButton button{
  width:100%; min-height:4.6rem; padding:.75rem 1rem !important;
  justify-content:flex-start !important; align-items:center !important; text-align:left !important;
}
.st-key-samples .stButton button > div, .st-key-samples .stButton [data-testid="stMarkdownContainer"]{width:100%; justify-content:flex-start !important}
.st-key-samples .stButton p{white-space:normal !important; text-align:left !important; line-height:1.4 !important; margin:0}

/* history list: compact, left aligned, ellipsis */
.st-key-history .stButton button{
  width:100%; min-height:0; padding:.45rem .75rem !important; border-radius:12px !important;
  border-width:1.5px !important; box-shadow:none; justify-content:flex-start !important; font-weight:600 !important;
}
.st-key-history .stButton button > div, .st-key-history [data-testid="stMarkdownContainer"]{width:100%; justify-content:flex-start !important; min-width:0}
.st-key-history .stButton p{white-space:nowrap !important; overflow:hidden !important; text-overflow:ellipsis !important; text-align:left !important; margin:0; font-size:.88rem}
.st-key-history .stButton button[kind="primary"]{background:var(--white) !important; color:var(--plum) !important; border-color:var(--pink) !important; box-shadow:inset 3px 0 0 var(--pink)}

/* ---------- chat ---------- */
[data-testid="stChatMessage"]{
  background:var(--white); border-radius:22px; padding:14px 18px; margin-bottom:12px;
  border:2px solid var(--pink-soft); box-shadow:0 8px 22px -18px rgba(217,74,134,.6);
}
[data-testid="stChatMessageAvatarCustom"]{background:var(--pink-soft) !important; border-radius:50% !important}
[data-testid="stChatInput"]{border-radius:20px !important; border:2px solid var(--pink) !important; background:var(--white) !important; box-shadow:var(--shadow)}
[data-testid="stBottom"] > div{background:transparent !important}
[data-testid="stBottomBlockContainer"]{background:linear-gradient(180deg, transparent, var(--pink-mist) 45%) !important}
.awaiting{display:inline-flex; align-items:center; gap:6px; background:var(--lav-soft); color:#5c4596; border-radius:999px;
  padding:2px 10px; font-size:.78rem; font-weight:800; margin-bottom:6px}

/* tool-call rows */
[data-testid="stExpander"] details{border-radius:14px !important; border:1.5px dashed var(--lav) !important; background:var(--lav-soft) !important}
[data-testid="stExpander"] summary{font-weight:700; color:#5c4596 !important}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#ffedf4,#f4eeff) !important; border-right:2px solid var(--white)}
.side-brand{font-family:'Baloo 2',sans-serif !important; font-weight:800; font-size:1.45rem; color:var(--plum); margin:0 0 2px}
.side-title{font-family:'Baloo 2',sans-serif !important; font-weight:700; font-size:1.02rem; color:var(--plum); margin:14px 0 6px}
.chips{display:flex; flex-wrap:wrap; gap:6px; margin:4px 0 6px}
.chip{background:var(--white); border:1.5px solid var(--pink-soft); border-radius:999px; padding:3px 10px; font-size:.78rem; font-weight:700; color:var(--ink)}
.chip.new{border-color:var(--mint); background:var(--mint-soft)}
.chip.off{background:transparent; border-style:dashed; color:var(--ink-soft)}
.tiny{font-size:.8rem; color:var(--ink-soft)}
.empty-history{font-size:.85rem; color:var(--ink-soft); background:rgba(255,255,255,.6); border-radius:12px; padding:8px 10px}
[data-testid="stSidebar"] [data-testid="stExpander"] details{background:rgba(255,255,255,.6) !important; border-style:solid !important; border-color:var(--pink-soft) !important}
[data-testid="stSidebar"] [data-testid="stExpander"] summary{color:var(--plum) !important}
.stSpinner > div{color:var(--plum) !important; font-weight:700}
</style>
"""


# ---------------------------------------------------------------- runtime

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
        "declarations": declarations,
        "tools": to_openai_tools(declarations),
        "provider": make_provider(PROVIDER),
        "artifact": build_artifact_version(VERSION, prompt_path, tools_path),
    }


# ---------------------------------------------------------------- per-browser session id

def client_id() -> str:
    sid = st.query_params.get("sid", "")
    if not (isinstance(sid, str) and sid.isalnum() and 8 <= len(sid) <= 32):
        sid = uuid.uuid4().hex[:16]
        st.query_params["sid"] = sid
    return sid


# ---------------------------------------------------------------- transcripts & history

def new_transcript(runtime: dict, sid: str) -> tuple[Path, dict]:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(VERSION), safe_slug(PROVIDER), "ui", stamp])
    data = {
        "transcript_id": transcript_id,
        **artifact_version_dict(runtime["artifact"]),
        "provider": PROVIDER,
        "model": MODEL or getattr(runtime["provider"], "default_model", None),
        "system_prompt": str(ARTIFACTS_DIR / "system_prompt.md"),
        "tools": str(ARTIFACTS_DIR / "tools.yaml"),
        "interface": "streamlit",
        "client_id": sid,
        "title": "",
        "history_window": HISTORY_WINDOW,
        "max_tool_rounds": MAX_TOOL_ROUNDS,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    return TRANSCRIPTS_DIR / f"{transcript_id}.transcript.json", data


def list_history(sid: str) -> list[dict]:
    items = []
    for path in TRANSCRIPTS_DIR.glob("*_ui_*.transcript.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if data.get("client_id") != sid or not data.get("turns"):
            continue
        title = data.get("title") or data["turns"][0].get("user", "")
        items.append({"path": path, "title": title, "updated_at": data.get("updated_at", "")})
    return sorted(items, key=lambda item: item["updated_at"], reverse=True)


def assistant_display(turn: dict) -> tuple[str, bool]:
    if turn.get("status") == "provider_error":
        return f"Không thể kết nối tới mô hình: `{turn.get('error', '')}`", False
    text = turn.get("assistant_text") or "Dori chưa có câu trả lời cho yêu cầu này."
    return text, turn.get("status") == "waiting_for_user"


def start_new_conversation(runtime: dict, sid: str) -> None:
    st.session_state.history = []
    st.session_state.display = []
    st.session_state.transcript_path, st.session_state.transcript = new_transcript(runtime, sid)


def open_conversation(path: Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    display, history = [], []
    for turn in data.get("turns", []):
        display.append({"role": "user", "content": turn.get("user", "")})
        text, awaiting = assistant_display(turn)
        display.append({"role": "assistant", "content": text, "rounds": turn.get("rounds", []), "awaiting": awaiting})
        if turn.get("status") != "provider_error":
            history += [{"role": "user", "content": turn.get("user", "")}, {"role": "assistant", "content": turn.get("assistant_text") or ""}]
    st.session_state.display = display
    st.session_state.history = history
    st.session_state.transcript_path = path
    st.session_state.transcript = data


# ---------------------------------------------------------------- rendering helpers

def tool_label(name: str, args: dict, failed: bool) -> str:
    icon, label = TOOL_STYLE.get(name, ("✨", name))
    arg_text = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in args.items())
    if len(arg_text) > 80:
        arg_text = arg_text[:77] + "…"
    return f"{icon} {label} · `{name}`({arg_text})" + (" · lỗi" if failed else "")


def render_tool_events(rounds: list[dict]) -> None:
    for record in rounds:
        for event in record.get("tool_results", []):
            if event["tool"] == "clarify":
                continue  # the question itself is shown as the reply, with the "cần thêm thông tin" badge
            result = event.get("result", {})
            failed = isinstance(result, dict) and "error" in result
            with st.expander(tool_label(event["tool"], event.get("args", {}), failed), expanded=False):
                st.json(result)


def render_message(message: dict) -> None:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        if message.get("rounds"):
            render_tool_events(message["rounds"])
        if message.get("awaiting"):
            st.markdown('<span class="awaiting">💭 Dori cần thêm thông tin từ bạn</span>', unsafe_allow_html=True)
        st.markdown(message["content"])


def chips_html(names: list[str], extra_class: str = "") -> str:
    parts = []
    for name in names:
        icon, label = TOOL_STYLE.get(name, ("✨", name))
        cls = "chip" + extra_class + (" new" if name in NEW_TOOLS and not extra_class else "")
        parts.append(f'<span class="{cls}" title="{html.escape(name)}">{icon} {html.escape(label)}</span>')
    return '<div class="chips">' + "".join(parts) + "</div>"


# ---------------------------------------------------------------- page

runtime = load_runtime()
sid = client_id()
if "display" not in st.session_state:
    start_new_conversation(runtime, sid)

st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown(f'<p class="side-brand">🐰 {APP_NAME}</p><span class="tiny">Trợ lý nghiên cứu tiếng Việt</span>', unsafe_allow_html=True)
    if st.button("＋ Cuộc trò chuyện mới", type="primary", use_container_width=True):
        start_new_conversation(runtime, sid)
        st.rerun()

    st.markdown('<p class="side-title">Lịch sử trò chuyện</p>', unsafe_allow_html=True)
    history_items = list_history(sid)
    with st.container(key="history"):
        if not history_items:
            st.markdown('<div class="empty-history">Các cuộc trò chuyện của bạn sẽ được lưu tại đây.</div>', unsafe_allow_html=True)
        for index, item in enumerate(history_items[:20]):
            is_current = item["path"] == st.session_state.transcript_path
            title = item["title"] if len(item["title"]) <= 60 else item["title"][:57] + "…"
            if st.button(title, key=f"hist_{index}", type="primary" if is_current else "secondary",
                         use_container_width=True, help=item["title"]):
                if not is_current:
                    open_conversation(item["path"])
                    st.rerun()

    st.markdown('<p class="side-title">Công cụ khả dụng</p>', unsafe_allow_html=True)
    st.markdown(chips_html([d["name"] for d in runtime["declarations"]]), unsafe_allow_html=True)
    st.markdown('<span class="tiny">Viền xanh: công cụ do nhóm phát triển</span>', unsafe_allow_html=True)
    if runtime["disabled"]:
        with st.expander(f"Chưa kích hoạt ({len(runtime['disabled'])})"):
            st.markdown(chips_html(sorted(runtime["disabled"]), extra_class=" off"), unsafe_allow_html=True)
            st.markdown('<span class="tiny">Cần bổ sung API key trong <code>.env</code> và khởi động lại ứng dụng.</span>',
                        unsafe_allow_html=True)

    with st.expander("Nguyên tắc hoạt động"):
        st.markdown(
            "- Khi yêu cầu thiếu thông tin (tài khoản, đường dẫn, tên repo), Dori sẽ hỏi lại thay vì tự suy đoán.\n"
            "- Mọi thao tác đăng tải ra bên ngoài đều cần bạn xác nhận trước.\n"
            "- Dori chỉ hỗ trợ các yêu cầu nghiên cứu, tra cứu thông tin."
        )
    with st.expander("Thông tin phiên bản"):
        model_name = MODEL or getattr(runtime["provider"], "default_model", "")
        st.markdown(f"Phiên bản `{runtime['artifact'].artifact_version}`  \nMô hình `{PROVIDER} / {model_name}`")

if st.session_state.display:
    # Compact header while a conversation is open, so messages get the space.
    hero_body = '<p>Trợ lý nghiên cứu tiếng Việt · tra cứu có dẫn nguồn</p>'
    hero_class = "dori-hero compact"
else:
    hero_body = (
        "<p>Trợ lý nghiên cứu giúp bạn tra cứu và tổng hợp thông tin từ web, mạng xã hội X, Hacker News, Wikipedia, "
        "GitHub, nguồn RSS, bài báo arXiv và chính sách nội bộ, kèm đường dẫn tới nguồn gốc.</p>"
        '<div class="pill-row"><span class="pill">Hỏi lại khi thiếu thông tin</span>'
        '<span class="pill">Xác nhận trước khi đăng tải</span><span class="pill">Dẫn nguồn rõ ràng</span></div>'
    )
    hero_class = "dori-hero"
st.markdown(
    f'<div class="{hero_class}"><div class="bunny">🐰</div><div><h1>{APP_NAME}</h1>{hero_body}</div>'
    '<span class="sparkle s1">✨</span><span class="sparkle s2">💗</span></div>',
    unsafe_allow_html=True,
)

if not st.session_state.display:
    st.markdown('<p class="welcome-title">Bạn muốn tìm hiểu điều gì hôm nay?</p>'
                '<p class="welcome-sub">Chọn một câu hỏi gợi ý bên dưới hoặc nhập yêu cầu của bạn.</p>', unsafe_allow_html=True)
    available = [(e, q) for e, q, needs in SAMPLE_QUESTIONS if needs not in runtime["disabled"]]
    available = available[: max(2, len(available) - len(available) % 2)][:6]  # even count, at most 6
    with st.container(key="samples"):
        cols = st.columns(2)
        for index, (emoji, question) in enumerate(available):
            with cols[index % 2]:
                if st.button(f"{emoji}  {question}", key=f"sample_{index}", use_container_width=True):
                    st.session_state.pending = question
                    st.rerun()

for message in st.session_state.display:
    render_message(message)

user_text = st.chat_input("Nhập yêu cầu tra cứu, ví dụ: repo pytorch/pytorch có bao nhiêu sao?") or st.session_state.pop("pending", None)

if user_text:
    user_message = {"role": "user", "content": user_text}
    st.session_state.display.append(user_message)
    render_message(user_message)

    messages = [
        {"role": "system", "content": runtime["system_prompt"]},
        *trim_history(st.session_state.history, HISTORY_WINDOW),
        {"role": "user", "content": user_text},
    ]
    transcript = st.session_state.transcript
    if not transcript.get("title"):
        transcript["title"] = user_text
    turn = {"turn_index": len(transcript["turns"]) + 1, "started_at": now_iso(), "user": user_text}

    with st.spinner("Dori đang tra cứu…"):
        try:
            result = run_model_tool_loop(
                provider=runtime["provider"], messages=messages, tools=runtime["tools"],
                model=MODEL, max_tool_rounds=MAX_TOOL_ROUNDS,
            )
            turn.update(result)
            st.session_state.history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": result["assistant_text"]}]
        except Exception as exc:  # show provider errors instead of crashing the page
            turn.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})

    text, awaiting = assistant_display(turn)
    assistant_message = {"role": "assistant", "content": text, "rounds": turn.get("rounds", []), "awaiting": awaiting}
    st.session_state.display.append(assistant_message)
    render_message(assistant_message)

    turn["ended_at"] = now_iso()
    transcript["turns"].append(turn)
    write_transcript(st.session_state.transcript_path, transcript)
    st.rerun()  # refresh the sidebar history list
