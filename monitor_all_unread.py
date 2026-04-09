import os
import re
import shutil
import subprocess
import time
import html
import json
from urllib.parse import quote_plus

import pyautogui
import requests
from pywinauto import Desktop
from pyweixin import GlobalConfig
from pyweixin.WinSettings import SystemSettings


REPLY_TARGETS = {
    "长风": {
        "kind": "friend",
        "style": "像熟人聊天，简短自然，不要客服腔。",
    },
    "鼎点视讯2026发财群！": {
        "kind": "group",
        "style": "群聊里发言要克制自然，像群成员正常接话，不要过长。",
    },
    "国庆羽球": {
        "kind": "group",
        "style": "语气轻松一点，像球友群里接话，优先简短直接。",
    },
}

REALTIME_PATTERNS = [
    r"目前",
    r"现在",
    r"最新",
    r"实时",
    r"今天",
    r"刚刚",
    r"新闻",
    r"政策",
    r"局势",
    r"形势",
    r"战争",
    r"冲突",
    r"股价",
    r"汇率",
    r"价格",
    r"天气",
    r"赛程",
    r"特朗普",
    r"trump",
    r"伊朗",
    r"中国",
    r"美国",
]

BROWSER_SESSION = "wechat-research"
CDP_URL = "http://127.0.0.1:9222"
BROWSER_USE_EXE = os.getenv("BROWSER_USE_EXE", r"C:\Users\Nico\.browser-use-env\Scripts\browser-use.exe")
BROWSER_PROFILE = os.getenv("BROWSER_USE_PROFILE", "Default")
BROWSER_USE_HOME_DIR = ".browser-use-home5"
BROWSER_USE_CONFIG_DIR = ".browser-use-config5"
SELF_MENTION_ALIASES = {
    alias.strip()
    for alias in os.getenv("WECHAT_SELF_ALIASES", "Nico,尼科,我").split(",")
    if alias.strip()
}


def configure():
    GlobalConfig.close_weixin = False
    GlobalConfig.is_maximize = False
    GlobalConfig.search_pages = 5
    GlobalConfig.send_delay = 0.2
    GlobalConfig.clear = True
    pyautogui.FAILSAFE = False


def get_main_window():
    window = Desktop(backend="uia").window(class_name="mmui::MainWindow")
    if not window.exists(timeout=5):
        raise RuntimeError("未找到 PC 微信主窗口，请先确保微信已打开并已登录。")
    window.set_focus()
    return window


def clear_edit(edit):
    try:
        edit.set_text("")
        return
    except Exception:
        pass

    edit.click_input()
    edit.type_keys("^a{BACKSPACE}", set_foreground=True)


def focus_wechat_window(main_window):
    try:
        if hasattr(main_window, "restore"):
            main_window.restore()
    except Exception:
        pass
    try:
        main_window.set_focus()
        time.sleep(0.2)
    except Exception as e:
        print(f"  -> Warning: could not focus WeChat window: {e}")


def _find_send_button(main_window):
    exact_titles = {
        "Send",
        "发送",
        "发送(S)",
        "Send (Enter)",
        "发送(Enter)",
    }
    exclude_keywords = {"sticker", "emoji", "emoticon", "表情", "贴纸"}

    # First pass: exact title match only.
    for btn in main_window.descendants(control_type="Button"):
        title = (btn.window_text() or "").strip()
        if title in exact_titles:
            return btn

    # Second pass: contains send/发送 but explicitly excludes sticker/emoji buttons.
    for btn in main_window.descendants(control_type="Button"):
        title = (btn.window_text() or "").strip()
        lowered = title.lower()
        if not title:
            continue
        if any(word in lowered for word in exclude_keywords) or any(word in title for word in exclude_keywords):
            continue
        if ("send" in lowered) or ("发送" in title):
            return btn
    return None


def send_one(main_window, text: str, session_item=None):
    for attempt in range(1, 4):
        try:
            focus_wechat_window(main_window)
            if session_item is not None:
                try:
                    session_item.click_input()
                    time.sleep(0.25)
                except Exception:
                    pass

            input_edit = main_window.child_window(auto_id="chat_input_field", control_type="Edit")
            if not input_edit.exists(timeout=1):
                raise RuntimeError("未找到聊天输入框。")

            clear_edit(input_edit)
            input_edit.click_input()
            SystemSettings.copy_text_to_clipboard(text)
            pyautogui.hotkey("ctrl", "v", _pause=False)
            time.sleep(GlobalConfig.send_delay)

            send_btn = _find_send_button(main_window)
            if send_btn:
                send_btn.click_input()
            else:
                # Fallback shortcut when send button title is unavailable in current UI language/layout.
                pyautogui.hotkey("ctrl", "enter", _pause=False)
            time.sleep(0.35)
            return True
        except Exception as e:
            print(f"  -> Send attempt {attempt} failed: {e}")
            time.sleep(0.4)
    return False


def parse_session_preview(full_text: str):
    lines = [line.strip() for line in full_text.splitlines() if line.strip()]
    if len(lines) < 2:
        return None

    session_name = lines[0]
    unread_match = re.match(r"^\[(\d+)\](.*)$", lines[1])
    if not unread_match:
        return None

    unread_count = unread_match.group(1)
    second_line_rest = unread_match.group(2).strip()

    session_info = {
        "name": session_name,
        "unread_count": unread_count,
        "is_group": False,
        "sender_name": None,
        "message": "",
        "time": None,
        "is_muted": False,
        "raw_text": full_text,
    }

    if ":" in second_line_rest:
        sender_name, message = second_line_rest.split(":", 1)
        session_info["is_group"] = True
        session_info["sender_name"] = sender_name.strip() or None
        session_info["message"] = message.strip()
        if len(lines) >= 3:
            session_info["time"] = lines[2]
        if len(lines) >= 4 and lines[3] == "Mute Notifications":
            session_info["is_muted"] = True
        return session_info

    if len(lines) >= 3:
        session_info["message"] = lines[2]
    if len(lines) >= 4:
        session_info["time"] = lines[3]
    return session_info


def get_last_message(main_window):
    try:
        input_field = main_window.child_window(auto_id="chat_input_field", control_type="Edit")
        input_top = input_field.rectangle().top
    except Exception:
        main_rect = main_window.rectangle()
        input_top = main_rect.bottom * 0.8

    main_rect = main_window.rectangle()
    chat_area_left = main_rect.left + main_rect.width() * 0.3
    all_text_elements = []

    for desc in main_window.descendants():
        try:
            text = desc.window_text()
            if text:
                rect = desc.rectangle()
                if rect.left > chat_area_left and rect.bottom < input_top:
                    all_text_elements.append(desc)
        except Exception:
            continue

    if not all_text_elements:
        return None

    all_text_elements.sort(key=lambda x: x.rectangle().bottom)

    for item in reversed(all_text_elements):
        item_rect = item.rectangle()
        is_right_aligned = item_rect.left > (main_rect.left + main_rect.width() * 0.6)
        msg_text = item.window_text()
        forbidden_keywords = ["撤回", " transferred", "发送了", "Voice input", "Hold Ctrl", "Ctrl+Win"]
        if not is_right_aligned and msg_text and not any(kw in msg_text for kw in forbidden_keywords):
            return msg_text

    return None


def build_session_dedup_key(session_info):
    return (
        session_info["name"],
        session_info["sender_name"] or "",
        session_info["message"] or "",
        session_info["time"] or "",
        session_info["unread_count"] or "",
    )


def should_reply(session_name: str):
    return session_name in REPLY_TARGETS


def extract_group_mentions(message: str):
    # WeChat group mention often appears like "@张三 消息内容" (includes thin space U+2005).
    mentions = re.findall(r"@([^\s\u2005\u00A0]+)", message or "")
    return [m.strip() for m in mentions if m.strip()]


def should_engage_group_message(session_info, message: str):
    if not session_info.get("is_group"):
        return True
    mentions = extract_group_mentions(message)
    if not mentions:
        return True

    lowered_mentions = {m.lower() for m in mentions}
    if any(token in lowered_mentions for token in {"all", "所有人"}):
        return True
    self_aliases_lower = {alias.lower() for alias in SELF_MENTION_ALIASES}
    if any(m in self_aliases_lower for m in lowered_mentions):
        return True
    return False


def needs_realtime_lookup(message: str):
    lowered = message.lower()
    return any(re.search(pattern, lowered, re.IGNORECASE) for pattern in REALTIME_PATTERNS)


def get_browser_use_env():
    env = os.environ.copy()
    env["BROWSER_USE_HOME"] = os.path.join(os.getcwd(), BROWSER_USE_HOME_DIR)
    env["BROWSER_USE_CONFIG_DIR"] = os.path.join(os.getcwd(), BROWSER_USE_CONFIG_DIR)
    env["PYTHONUTF8"] = "1"
    return env


def cleanup_browser_use_runtime():
    for dirname in (BROWSER_USE_HOME_DIR, BROWSER_USE_CONFIG_DIR):
        path = os.path.join(os.getcwd(), dirname)
        try:
            shutil.rmtree(path, ignore_errors=True)
        except Exception:
            pass


def run_browser_use_command(args, timeout=120, allow_failure=False):
    command = [BROWSER_USE_EXE] + args
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        timeout=timeout,
        env=get_browser_use_env(),
    )
    stdout = (result.stdout or "").strip()
    stderr = (result.stderr or "").strip()

    if result.returncode != 0 and not allow_failure:
        detail = stderr or stdout or f"browser-use failed: {' '.join(command)}"
        raise RuntimeError(detail)

    return {
        "code": result.returncode,
        "stdout": stdout,
        "stderr": stderr,
    }


def close_browser_use_session():
    result = run_browser_use_command(
        ["--session", BROWSER_SESSION, "close"],
        timeout=20,
        allow_failure=True,
    )
    if result["code"] == 0:
        print("  -> Closed stale browser-use session before retry.")


def close_all_chrome_processes():
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "chrome.exe"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        time.sleep(1.0)
        print("  -> Closed running Chrome processes for clean profile startup.")
    except Exception as e:
        print(f"  -> Failed to close Chrome processes: {e}")


def open_research_page_with_cdp(query_url: str):
    print("  -> Trying browser-use via existing Chrome CDP...")
    close_browser_use_session()
    result = run_browser_use_command(
        ["--cdp-url", CDP_URL, "--session", BROWSER_SESSION, "open", query_url],
        timeout=60,
        allow_failure=True,
    )
    if result["code"] == 0:
        print("  -> Opened research page through existing Chrome CDP.")
        return True

    detail = result["stderr"] or result["stdout"] or "unknown open failure"
    print(f"  -> browser-use cdp open failed: {detail}")
    return False


def open_research_page_with_profile(query_url: str):
    result = run_browser_use_command(
        [
            "--session",
            BROWSER_SESSION,
            "--profile",
            BROWSER_PROFILE,
            "--headed",
            "open",
            query_url,
        ],
        timeout=80,
        allow_failure=True,
    )
    if result["code"] == 0:
        print(f"  -> Opened research page with browser profile: {BROWSER_PROFILE}.")
        return True

    detail = result["stderr"] or result["stdout"] or "unknown profile open failure"
    print(f"  -> browser-use profile open failed: {detail}")
    return False


def parse_browser_use_json(stdout_text: str):
    if not stdout_text:
        return None
    text = stdout_text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        try:
            return json.loads(text[first : last + 1])
        except Exception:
            return None
    return None


def get_browser_page_title():
    result = run_browser_use_command(
        ["--session", BROWSER_SESSION, "get", "title"],
        timeout=25,
        allow_failure=True,
    )
    if result["code"] != 0:
        return None
    title_text = (result["stdout"] or "").strip()
    title_text = re.sub(r"^\s*title\s*:\s*", "", title_text, flags=re.IGNORECASE).strip()
    return title_text or None


def get_browser_page_html():
    result = run_browser_use_command(
        ["--json", "--session", BROWSER_SESSION, "get", "html"],
        timeout=60,
        allow_failure=True,
    )
    if result["code"] != 0:
        detail = result["stderr"] or result["stdout"] or "unknown get html failure"
        print(f"  -> browser-use get html failed: {detail}")
        return None

    payload = parse_browser_use_json(result["stdout"])
    if isinstance(payload, dict):
        if isinstance(payload.get("html"), str):
            return payload["html"]
        if isinstance(payload.get("data"), dict) and isinstance(payload["data"].get("html"), str):
            return payload["data"]["html"]
        if isinstance(payload.get("result"), dict) and isinstance(payload["result"].get("html"), str):
            return payload["result"]["html"]

    # Extremely defensive: some versions may return raw HTML instead of structured JSON.
    text = (result["stdout"] or "").strip()
    if "<html" in text.lower():
        return text
    print("  -> browser-use returned non-JSON html payload.")
    return None


def strip_html_tags(text: str):
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def research_via_http_search(question: str):
    search_url = f"https://www.bing.com/search?q={quote_plus(question)}&setlang=zh-Hans"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(search_url, headers=headers, timeout=20)
        response.raise_for_status()
        html_text = response.text

        matches = re.findall(
            r'(?is)<li class="b_algo".*?<h2.*?>(.*?)</h2>.*?(?:<p>(.*?)</p>|<div class="b_caption".*?<p>(.*?)</p>)',
            html_text,
        )

        summaries = []
        for match in matches[:5]:
            title = strip_html_tags(match[0] or "")
            snippet = strip_html_tags(match[1] or match[2] or "")
            if title or snippet:
                summaries.append(f"{title}: {snippet}".strip(": "))

        if summaries:
            return " | ".join(summaries[:3])
    except Exception as e:
        print(f"  -> HTTP search fallback failed: {e}")

    return None


def summarize_search_html(question: str, html_text: str, page_title: str | None = None):
    matches = re.findall(
        r'(?is)<li[^>]*class="[^"]*b_algo[^"]*"[^>]*>.*?<h2[^>]*>(.*?)</h2>.*?(?:<p[^>]*>(.*?)</p>|<div[^>]*class="[^"]*b_caption[^"]*"[^>]*>.*?<p[^>]*>(.*?)</p>)',
        html_text,
    )
    snippets = []
    for match in matches[:5]:
        title = strip_html_tags(match[0] or "")
        snippet = strip_html_tags(match[1] or match[2] or "")
        if title or snippet:
            snippets.append(f"{title}: {snippet}".strip(": "))

    if not snippets:
        plain = strip_html_tags(html_text)
        if len(plain) > 320:
            plain = plain[:320] + "..."
        if plain:
            snippets.append(plain)

    if not snippets:
        return None

    header = f"检索问题：{question}"
    if page_title:
        header += f"；页面标题：{page_title}"
    body = " | ".join(snippets[:3])
    return f"{header}。摘要：{body}"


def research_with_browser_use(question: str):
    query_url = f"https://www.bing.com/search?q={quote_plus(question)}&setlang=zh-Hans"
    try:
        print("  -> Realtime query detected, starting browser-use research flow...")
        cleanup_browser_use_runtime()

        opened = open_research_page_with_cdp(query_url)
        if not opened:
            close_browser_use_session()
            print(f"  -> Falling back to launching profile {BROWSER_PROFILE}...")
            opened = open_research_page_with_profile(query_url)

        if not opened:
            close_browser_use_session()
            close_all_chrome_processes()
            opened = open_research_page_with_profile(query_url)

        if not opened:
            print("  -> browser-use unavailable, falling back to direct HTTP search summary.")
            return research_via_http_search(question)

        time.sleep(2.0)
        page_title = get_browser_page_title()
        page_html = get_browser_page_html()
        if page_html:
            summary = summarize_search_html(question, page_html, page_title)
            if summary:
                return summary

        print("  -> browser-use opened page but could not extract summary. Falling back to HTTP search.")
        return research_via_http_search(question)
    except Exception as e:
        print(f"  -> browser-use research failed: {e}")
        print("  -> Falling back to direct HTTP search summary.")
        return research_via_http_search(question)


def build_realtime_failure_reply(session_info, message_for_reply: str):
    if session_info["is_group"]:
        return "这个我得再查一下实时信息，晚点确认清楚了再说。"
    return "这个我得先查一下实时信息，等我确认清楚再跟你说。"


def build_reply_prompt(session_info, message_for_reply: str, research_summary: str | None = None):
    config = REPLY_TARGETS[session_info["name"]]
    chat_kind = "群聊" if session_info["is_group"] else "私聊"
    speaker = session_info["sender_name"] or session_info["name"]

    system_prompt = (
        "你在代替真实用户回复微信消息。\n"
        "只输出一条可以直接发送的中文微信消息，不要解释，不要加引号，不要自称 AI。\n"
        "回复要像真人自然聊天，不要客服腔。\n"
        "默认控制在 1 到 3 句话，除非对方明显需要更完整说明。\n"
        "如果给了实时检索摘要，要优先依据该摘要作答，不要回避问题，不要只说自己没关注。\n"
        f"当前会话类型：{chat_kind}。\n"
        f"当前会话名称：{session_info['name']}。\n"
        f"当前说话人：{speaker}。\n"
        f"附加风格：{config['style']}"
    )

    user_prompt = (
        f"对方最新消息：{message_for_reply}\n"
        f"未读条数：{session_info['unread_count']}\n"
        f"消息时间：{session_info['time'] or '未知'}\n"
    )
    if research_summary:
        user_prompt += f"实时检索摘要：{research_summary}\n"
    user_prompt += "请直接生成一条现在就适合发出去的回复。"

    return system_prompt, user_prompt


def get_llm_reply(session_info, message_for_reply: str, research_summary: str | None = None):
    print(f"Generating LLM reply for: {message_for_reply}")

    api_url = "https://vllm.codingstack.xyz:61721/v1/chat/completions"
    api_key = "e6uIhWd+HVJSOYaN"
    model = "gemma4"
    system_prompt, user_prompt = build_reply_prompt(session_info, message_for_reply, research_summary)

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.5,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"API Error: {e}")
        return None


def monitor_all_unread():
    configure()
    print("\n--- WeChat Unread Monitor (Targeted Auto Reply) ---")
    main_window = get_main_window()
    processed_previews = set()

    print("Monitoring... Press Ctrl+C to stop.")
    try:
        while True:
            try:
                session_list = main_window.child_window(auto_id="session_list", control_type="List")
                if not session_list.exists(timeout=1):
                    time.sleep(2)
                    continue

                items = session_list.children(control_type="ListItem")
                unread_found = False

                for item in items:
                    full_text = item.window_text()
                    if not full_text:
                        continue

                    session_info = parse_session_preview(full_text)
                    if not session_info:
                        continue

                    session_name = session_info["name"]
                    preview_key = build_session_dedup_key(session_info)
                    if preview_key in processed_previews:
                        continue

                    unread_found = True
                    print(f"!!! DETECTED UNREAD from: {session_name} ({session_info['unread_count']} new messages)")
                    if session_info["is_group"] and session_info["sender_name"]:
                        print(f"  -> Group Sender: {session_info['sender_name']}")
                    if session_info["message"]:
                        print(f"  -> Latest Message: {session_info['message']}")
                    if session_info["time"]:
                        print(f"  -> Time: {session_info['time']}")
                    if session_info["is_muted"]:
                        print("  -> Muted: True")

                    if not should_reply(session_name):
                        print("  -> Ignored: not in reply whitelist.")
                        processed_previews.add(preview_key)
                        continue

                    item.click_input()
                    time.sleep(1.2)

                    message_for_reply = session_info["message"] or get_last_message(main_window)
                    if not message_for_reply:
                        print("  -> Could not parse latest message from session preview.")
                        processed_previews.add(preview_key)
                        continue

                    if not session_info["message"]:
                        print(f"  -> Fallback Last Message: {message_for_reply}")

                    if not should_engage_group_message(session_info, message_for_reply):
                        print("  -> Ignored: group message @ someone else, not directed to me.")
                        processed_previews.add(preview_key)
                        continue

                    reply = None
                    if needs_realtime_lookup(message_for_reply):
                        research_summary = research_with_browser_use(message_for_reply)
                        if research_summary:
                            print(f"  -> Research Summary: {research_summary}")
                            reply = get_llm_reply(session_info, message_for_reply, research_summary)
                        else:
                            reply = build_realtime_failure_reply(session_info, message_for_reply)
                            print(f"  -> Research unavailable, sending cautious fallback: {reply}")
                    else:
                        reply = get_llm_reply(session_info, message_for_reply)

                    if reply:
                        print(f"  -> Sending Reply: {reply}")
                        try:
                            item.click_input()
                            time.sleep(0.4)
                        except Exception:
                            pass
                        send_ok = send_one(main_window, reply, session_item=item)
                        if send_ok:
                            print("  -> Reply sent to WeChat.")
                        else:
                            print("  -> Reply send failed after retries.")
                    else:
                        print("  -> Reply generation failed.")

                    processed_previews.add(preview_key)
                    if len(processed_previews) > 500:
                        processed_previews = set(list(processed_previews)[-200:])

                    time.sleep(0.5)

                if not unread_found:
                    time.sleep(3.0)
                else:
                    time.sleep(1.0)

            except Exception as e:
                print(f"Error during scan loop: {e}")
                time.sleep(2.0)

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")


def main():
    try:
        monitor_all_unread()
    except Exception as e:
        print(f"Critical error: {e}")


if __name__ == "__main__":
    main()
