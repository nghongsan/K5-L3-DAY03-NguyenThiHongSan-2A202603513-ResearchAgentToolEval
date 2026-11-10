"""Streamlit UI for the Research Agent.

Run from starter_v0/:
    streamlit run app.py
Then expose it for other teams:
    cloudflared tunnel --url http://localhost:8501

Reuses the exact multi-round tool loop from chat.py, so the UI behaves like the CLI
and every session is logged to transcripts/*.transcript.json.
"""
from __future__ import annotations

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
VERSION = os.getenv("APP_VERSION", "v6")
MODEL = os.getenv("APP_MODEL") or None
HISTORY_WINDOW = 5
MAX_TOOL_ROUNDS = 4

SAMPLE_QUESTIONS = [
    "Tin tức AI hôm nay có gì nổi bật?",
    "Lấy 3 tweet mới nhất của Andrej Karpathy",
    "Transformer trong machine learning là gì? Tra Wikipedia giúp mình.",
    "Dân dev trên Hacker News đang bàn gì về Rust? Lấy bài mới nhất.",
    "Repo langchain-ai/langchain có bao nhiêu sao, license gì?",
    "Theo policy công ty, đăng bản tin lên Telegram có cần xác nhận trước không?",
    "Đăng bản tin AI hôm nay lên Telegram giúp mình",
]

st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")


@st.cache_resource
def load_runtime() -> dict:
    prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    declarations = load_tool_declarations(tools_path)
    return {
        "system_prompt": prompt_path.read_text(encoding="utf-8"),
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


def render_tool_events(rounds: list[dict]) -> None:
    for record in rounds:
        for event in record.get("tool_results", []):
            result = event.get("result", {})
            failed = isinstance(result, dict) and "error" in result
            label = f"{'⚠️' if failed else '🔧'} {event['tool']}({json.dumps(event.get('args', {}), ensure_ascii=False)})"
            with st.expander(label, expanded=False):
                st.json(result)


runtime = load_runtime()
if "display" not in st.session_state:
    reset_session(runtime)

with st.sidebar:
    st.header("Research Agent")
    st.caption(f"`{runtime['artifact'].artifact_version}` · {PROVIDER} / {MODEL or getattr(runtime['provider'], 'default_model', '')}")
    st.markdown(
        "Tìm tin trên web, tweet theo tài khoản hoặc chủ đề, đọc URL/feed/paper arXiv, tra Wikipedia, "
        "Hacker News, GitHub repo và policy nội bộ. Hỏi lại khi thiếu thông tin; luôn xin xác nhận trước khi gửi Telegram."
    )
    st.subheader("Thử nhanh")
    for question in SAMPLE_QUESTIONS:
        if st.button(question, use_container_width=True):
            st.session_state.pending = question
    st.subheader("Tool")
    for item in runtime["declarations"]:
        st.markdown(f"- **{item['name']}**: {item['description'].split('.')[0]}.")
    if st.button("Cuộc trò chuyện mới", type="secondary"):
        reset_session(runtime)
        st.rerun()

st.title("🔎 Research Agent")

for message in st.session_state.display:
    with st.chat_message(message["role"]):
        if message.get("rounds"):
            render_tool_events(message["rounds"])
        st.markdown(message["content"])

user_text = st.chat_input("Hỏi agent… (ví dụ: tin AI hôm nay)") or st.session_state.pop("pending", None)

if user_text:
    st.session_state.display.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    messages = [
        {"role": "system", "content": runtime["system_prompt"]},
        *trim_history(st.session_state.history, HISTORY_WINDOW),
        {"role": "user", "content": user_text},
    ]
    turn = {"turn_index": len(st.session_state.transcript["turns"]) + 1, "started_at": now_iso(), "user": user_text}

    with st.chat_message("assistant"):
        with st.spinner("Agent đang xử lý…"):
            try:
                result = run_model_tool_loop(
                    provider=runtime["provider"], messages=messages, tools=runtime["tools"],
                    model=MODEL, max_tool_rounds=MAX_TOOL_ROUNDS,
                )
                answer = result["assistant_text"] or "(không có câu trả lời)"
                if result["status"] == "waiting_for_user":
                    answer = f"❓ {answer}"
                turn.update(result)
                st.session_state.history += [{"role": "user", "content": user_text}, {"role": "assistant", "content": result["assistant_text"]}]
            except Exception as exc:  # show provider errors instead of crashing the page
                answer = f"Lỗi khi gọi model: `{type(exc).__name__}: {exc}`"
                result = {"rounds": []}
                turn.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
        render_tool_events(result.get("rounds", []))
        st.markdown(answer)

    st.session_state.display.append({"role": "assistant", "content": answer, "rounds": result.get("rounds", [])})
    turn["ended_at"] = now_iso()
    st.session_state.transcript["turns"].append(turn)
    write_transcript(st.session_state.transcript_path, st.session_state.transcript)
