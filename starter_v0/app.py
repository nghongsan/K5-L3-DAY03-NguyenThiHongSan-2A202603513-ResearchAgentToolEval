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
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from tools.send.tool import send_telegram
from versioning import artifact_version_dict, build_artifact_version

APP_NAME = "Dori Research"
PROVIDER = os.getenv("APP_PROVIDER", "openai")
VERSION = os.getenv("APP_VERSION", "v3")
MODEL = os.getenv("APP_MODEL") or None
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4
TRANSCRIPTS_DIR = ROOT / "transcripts"
TOOLS_DIR = ROOT / "tools"

ASSETS_DIR = ROOT / "assets"
BOT_AVATAR = str(ASSETS_DIR / "dori-avatar.png")
USER_AVATAR = "🙂"

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

st.set_page_config(page_title=APP_NAME, page_icon=str(ROOT / "assets" / "dori-icon.png"), layout="wide", initial_sidebar_state="auto")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700;800&family=Nunito:wght@400;600;700;800&display=swap');

/* Palette sampled from the Dori mascot: periwinkle beret/book, navy outline, blush cheeks, star yellow. */
:root{
  --blue:#7d93dc; --blue-deep:#5b6fbf; --blue-soft:#e6ebfb; --blue-mist:#f6f8ff; --sky:#cdd8fa;
  --navy:#3d4673; --navy-soft:#727ba4; --blush:#f2a7b0; --blush-soft:#fdeef0;
  --sun:#f5cf62; --sun-soft:#fff6dc; --white:#ffffff;
  --shadow:0 10px 30px -14px rgba(91,111,191,.35);
}

html, body, .stApp, .stMarkdown, button, input, textarea { font-family:'Nunito', system-ui, sans-serif !important; }
.stApp{
  color:var(--navy);
  background:
    radial-gradient(circle at 8% 12%, rgba(125,147,220,.13) 0 130px, transparent 131px),
    radial-gradient(circle at 93% 6%, rgba(205,216,250,.45) 0 170px, transparent 171px),
    radial-gradient(circle at 96% 90%, rgba(245,207,98,.16) 0 140px, transparent 141px),
    radial-gradient(rgba(125,147,220,.10) 1.5px, transparent 1.6px) 0 0/24px 24px,
    linear-gradient(180deg, var(--blue-mist), #fbfcff);
}
header[data-testid="stHeader"]{background:transparent}
.block-container{padding-top:1.4rem; max-width:960px}

/* ---------- hero ---------- */
.dori-hero{
  position:relative; overflow:hidden; border-radius:26px; padding:20px 28px 20px 20px;
  background:linear-gradient(120deg, #ffffff 0%, #eef2ff 45%, #e2e9fd 100%);
  box-shadow:var(--shadow); border:2px solid var(--sky);
  display:flex; gap:18px; align-items:center; margin-bottom:22px;
}
.dori-hero .logo{width:118px; height:118px; flex:none; border-radius:28px; background:var(--white);
  box-shadow:0 8px 18px -10px rgba(91,111,191,.55); animation:bob 3.6s ease-in-out infinite}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-5px)}}
@media (prefers-reduced-motion: reduce){.dori-hero .logo{animation:none}}
.dori-hero h1{font-family:'Baloo 2','Nunito',sans-serif !important; font-weight:800; font-size:2.3rem; margin:0; line-height:1.05; color:var(--navy); padding:0}
.dori-hero h1 span{color:var(--blue-deep)}
.dori-hero p{margin:6px 0 0; font-size:1rem; color:#4c5583; max-width:62ch; line-height:1.5}
.dori-hero .sparkle{position:absolute; font-size:18px; color:var(--blue); opacity:.75}
.dori-hero .s1{top:12px; right:22px} .dori-hero .s2{bottom:14px; right:90px; color:var(--sun); font-size:20px; opacity:.95}
.pill-row{display:flex; flex-wrap:wrap; gap:6px; margin-top:12px}
.pill{background:var(--white); border:1.5px solid var(--sky); border-radius:999px; padding:3px 11px; font-size:.8rem; font-weight:700; color:var(--blue-deep)}
.dori-hero.compact{padding:10px 20px 10px 12px; gap:12px; margin-bottom:16px; border-radius:20px}
.dori-hero.compact .logo{width:52px; height:52px; border-radius:16px; animation:none}
.dori-hero.compact h1{font-size:1.45rem}
.dori-hero.compact p{margin-top:0; font-size:.88rem}
.dori-hero.compact .s2{display:none}
@media (max-width: 640px){
  .dori-hero{flex-direction:column; align-items:flex-start; gap:10px; padding:18px}
  .dori-hero .logo{width:84px; height:84px; border-radius:22px}
  .dori-hero h1{font-size:1.85rem}
  .dori-hero.compact{flex-direction:row; align-items:center}
}

/* ---------- welcome ---------- */
.welcome-title{font-family:'Baloo 2',sans-serif !important; font-weight:700; font-size:1.25rem; color:var(--navy); margin:0}
.welcome-sub{color:var(--navy-soft); margin:2px 0 12px}

/* ---------- buttons ---------- */
.stButton button{
  border-radius:16px !important; border:2px solid var(--blue-soft) !important;
  background:var(--white) !important; color:var(--navy) !important; font-weight:700 !important;
  box-shadow:0 4px 14px -10px rgba(91,111,191,.5); transition:transform .15s, border-color .15s, background .15s;
}
.stButton button:hover{transform:translateY(-1px); border-color:var(--blue) !important; background:var(--blue-mist) !important}
.stButton button:focus-visible{outline:3px solid var(--sun) !important; outline-offset:2px}
.stButton button[kind="primary"]{background:var(--blue) !important; border-color:var(--blue) !important; color:var(--white) !important}
.stButton button[kind="primary"]:hover{background:var(--blue-deep) !important; border-color:var(--blue-deep) !important}

.st-key-samples .stButton button{
  width:100%; min-height:4.6rem; padding:.75rem 1rem !important;
  justify-content:flex-start !important; align-items:center !important; text-align:left !important;
}
.st-key-samples .stButton button > div, .st-key-samples .stButton [data-testid="stMarkdownContainer"]{width:100%; justify-content:flex-start !important}
.st-key-samples .stButton p{white-space:normal !important; text-align:left !important; line-height:1.4 !important; margin:0}

.st-key-history .stButton button{
  width:100%; min-height:0; padding:.45rem .75rem !important; border-radius:12px !important;
  border-width:1.5px !important; box-shadow:none; justify-content:flex-start !important; font-weight:600 !important;
}
.st-key-history .stButton button > div, .st-key-history [data-testid="stMarkdownContainer"]{width:100%; justify-content:flex-start !important; min-width:0}
.st-key-history .stButton p{white-space:nowrap !important; overflow:hidden !important; text-overflow:ellipsis !important; text-align:left !important; margin:0; font-size:.88rem}
.st-key-history .stButton button[kind="primary"]{background:var(--white) !important; color:var(--navy) !important; border-color:var(--blue) !important; box-shadow:inset 3px 0 0 var(--blue)}

/* ---------- chat ---------- */
[data-testid="stChatMessage"]{
  background:var(--white); border-radius:22px; padding:14px 18px; margin-bottom:12px;
  border:2px solid var(--blue-soft); box-shadow:0 8px 22px -18px rgba(91,111,191,.6);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarCustom"] img){background:var(--white)}
[data-testid="stChatMessage"]:not(:has(img)){background:var(--blue-soft); border-color:var(--sky)}
[data-testid="stChatMessageAvatarCustom"]{background:var(--sun-soft) !important; border-radius:50% !important}
[data-testid="stChatMessage"] img{border-radius:50%}
[data-testid="stChatInput"]{border-radius:20px !important; border:2px solid var(--blue) !important; background:var(--white) !important; box-shadow:var(--shadow)}
[data-testid="stBottom"] > div{background:transparent !important}
[data-testid="stBottomBlockContainer"]{background:linear-gradient(180deg, transparent, var(--blue-mist) 45%) !important}
.awaiting{display:inline-flex; align-items:center; gap:6px; background:var(--blush-soft); color:#9a4a59; border-radius:999px;
  padding:2px 10px; font-size:.78rem; font-weight:800; margin-bottom:6px}
.stApp a{color:var(--blue-deep)}

/* tool-call rows */
[data-testid="stExpander"] details{border-radius:14px !important; border:1.5px dashed var(--sky) !important; background:var(--blue-mist) !important}
[data-testid="stExpander"] summary{font-weight:700; color:var(--blue-deep) !important}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#f4f7ff,#eceffd) !important; border-right:2px solid var(--white)}
.side-brand{display:flex; align-items:center; gap:10px; margin:0 0 2px}
.side-brand img{width:42px; height:42px; border-radius:12px; background:var(--white); box-shadow:0 4px 10px -6px rgba(91,111,191,.6)}
.side-brand b{font-family:'Baloo 2',sans-serif !important; font-weight:800; font-size:1.4rem; color:var(--navy); line-height:1.1}
.side-title{font-family:'Baloo 2',sans-serif !important; font-weight:700; font-size:1.02rem; color:var(--navy); margin:14px 0 6px}
.chips{display:flex; flex-wrap:wrap; gap:6px; margin:4px 0 6px}
.chip{background:var(--white); border:1.5px solid var(--blue-soft); border-radius:999px; padding:3px 10px; font-size:.78rem; font-weight:700; color:var(--navy)}
.chip.new{border-color:var(--sun); background:var(--sun-soft)}
.chip.off{background:transparent; border-style:dashed; color:var(--navy-soft)}
.tiny{font-size:.8rem; color:var(--navy-soft)}
.empty-history{font-size:.85rem; color:var(--navy-soft); background:rgba(255,255,255,.7); border-radius:12px; padding:8px 10px}
[data-testid="stSidebar"] [data-testid="stExpander"] details{background:rgba(255,255,255,.7) !important; border-style:solid !important; border-color:var(--blue-soft) !important}
[data-testid="stSidebar"] [data-testid="stExpander"] summary{color:var(--navy) !important}
.stSpinner > div{color:var(--blue-deep) !important; font-weight:700}

/* ---------- send confirmation card ---------- */
.st-key-sendcard{background:var(--sun-soft); border:2px solid var(--sun); border-radius:22px; padding:16px 18px 6px; margin:4px 0 14px;
  box-shadow:0 10px 24px -18px rgba(160,122,18,.7)}
.send-title{font-family:'Baloo 2',sans-serif !important; font-weight:700; font-size:1.08rem; color:var(--navy); margin:0}
.st-key-sendcard textarea{background:var(--white) !important; border-radius:14px !important}
</style>
"""


# ---------------------------------------------------------------- runtime

@st.cache_data
def image_uri(name: str) -> str:
    """Inline a file from assets/ as a data URI so it works through the tunnel without static serving."""
    import base64
    return "data:image/png;base64," + base64.b64encode((ASSETS_DIR / name).read_bytes()).decode()


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


# ---------------------------------------------------------------- UI-level send confirmation

def ui_gated_send(text: str = "", confirmed: bool = False) -> dict:
    """Replaces the `send` tool inside the UI. The model can only prepare a draft: nothing is
    posted to Telegram until the user presses "Xác nhận gửi" on the confirmation card."""
    if not (confirmed is True or (isinstance(confirmed, str) and confirmed.strip().lower() == "true")):
        return send_telegram(text=text, confirmed=False)  # same needs_confirmation answer as the real tool
    if not (text or "").strip():
        return {"tool": "send_telegram", "error": "ValueError", "message": "Nội dung bản tin đang trống."}
    st.session_state.pending_send = {"text": text, "created_at": datetime.now().strftime("%H%M%S%f")}
    return {
        "tool": "send_telegram",
        "status": "awaiting_ui_confirmation",
        "message": ("CHƯA GỬI. Một thẻ bản nháp vừa hiện ngay bên dưới câu trả lời của bạn trong khung chat Dori. "
                    "Tin chỉ được đăng khi người dùng bấm nút 'Xác nhận gửi' trên thẻ đó (không phải trong ứng dụng Telegram). "
                    "Hãy nói ngắn gọn rằng bản nháp đã sẵn sàng ở bên dưới để người dùng kiểm tra, chỉnh sửa và bấm 'Xác nhận gửi'. "
                    "Không nói rằng tin đã được gửi."),
    }


TOOL_FUNCTIONS["send"] = ui_gated_send  # chat.py looks tools up in this dict at call time


def record_ui_action(action: dict, chat_text: str) -> None:
    """Show the outcome in the chat and attach it to the latest turn of the transcript."""
    st.session_state.display.append({"role": "assistant", "content": chat_text})
    st.session_state.history.append({"role": "assistant", "content": chat_text})
    transcript = st.session_state.transcript
    if transcript["turns"]:
        transcript["turns"][-1].setdefault("ui_actions", []).append({"at": now_iso(), "chat_text": chat_text, **action})
        write_transcript(st.session_state.transcript_path, transcript)
    st.session_state.pending_send = None


def render_send_card(pending: dict) -> None:
    with st.container(key="sendcard"):
        st.markdown('<p class="send-title">💌 Bản tin đang chờ bạn xác nhận</p>'
                    '<p class="tiny">Tin chỉ được đăng lên Telegram khi bạn bấm “Xác nhận gửi”. '
                    'Bạn có thể chỉnh sửa nội dung trước khi gửi.</p>', unsafe_allow_html=True)
        draft = st.text_area("Nội dung bản tin", value=pending["text"], height=180,
                             key=f"draft_{pending['created_at']}", label_visibility="collapsed")
        col_ok, col_cancel = st.columns(2)
        if col_ok.button("Xác nhận gửi", type="primary", use_container_width=True, key="send_ok"):
            result = send_telegram(text=draft, confirmed=True)
            if result.get("status") == "sent":
                chat_text = "✅ Đã đăng bản tin lên Telegram."
            else:
                chat_text = f"Gửi không thành công: `{result.get('error')}: {result.get('message')}`"
            record_ui_action({"action": "send_confirmed", "text": draft, "edited": draft != pending["text"],
                              "result": result}, chat_text)
            st.rerun()
        if col_cancel.button("Hủy, không gửi", use_container_width=True, key="send_cancel"):
            record_ui_action({"action": "send_cancelled", "text": pending["text"]}, "Đã hủy. Bản tin không được gửi.")
            st.rerun()


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
    st.session_state.pending_send = None
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
        for action in turn.get("ui_actions", []):
            display.append({"role": "assistant", "content": action.get("chat_text", "")})
            history.append({"role": "assistant", "content": action.get("chat_text", "")})
    st.session_state.display = display
    st.session_state.pending_send = None
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
    st.markdown(f'<div class="side-brand"><img src="{image_uri("dori-avatar.png")}" alt="Dori"><div><b>{APP_NAME}</b><br>'
                '<span class="tiny">Trợ lý nghiên cứu tiếng Việt</span></div></div>', unsafe_allow_html=True)
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
    st.markdown('<span class="tiny">Viền vàng: công cụ do nhóm phát triển</span>', unsafe_allow_html=True)
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
    f'<div class="{hero_class}"><img class="logo" src="{image_uri("dori.png")}" alt="Linh vật Dori">'
    f'<div><h1>Dori <span>Research</span></h1>{hero_body}</div>'
    '<span class="sparkle s1">✦</span><span class="sparkle s2">✦</span></div>',
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

if st.session_state.get("pending_send"):
    render_send_card(st.session_state.pending_send)

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
