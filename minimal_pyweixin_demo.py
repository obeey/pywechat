"""
Minimal runnable demo for PC WeChat 4.1+.

This script avoids the repo's language-specific UI mapping for `send`,
so it can work on English or Chinese WeChat UI.

Examples:
    python minimal_pyweixin_demo.py
    python minimal_pyweixin_demo.py send --friend n2o_n2o --message 你好
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime

import pyautogui
from pywinauto import Desktop

from pyweixin import GlobalConfig
from pyweixin.WinSettings import SystemSettings


DEFAULT_FRIEND = "File Transfer"
SEARCH_RESULT_IGNORE = {
    "",
    "Favorites",
    "Contacts",
    "Group Chats",
    "Service Accounts",
    "Official Accounts",
    "Recent Used",
    "Most Frequently Used",
    "Internet search results",
    "功能",
    "最近使用",
    "联系人",
    "群聊",
    "服务号",
    "公众号",
    "最常使用",
    "搜索",
}


def configure() -> None:
    GlobalConfig.close_weixin = False
    GlobalConfig.is_maximize = False
    GlobalConfig.search_pages = 5
    GlobalConfig.send_delay = 0.2
    GlobalConfig.clear = True
    pyautogui.FAILSAFE = False


def get_main_window():
    window = Desktop(backend="uia").window(class_name="mmui::MainWindow")
    if not window.exists(timeout=2):
        raise RuntimeError("未找到 PC 微信主窗口，请先确保微信已打开并已登录。")
    window.set_focus()
    return window


def get_search_edit(main_window):
    edits = [
        edit
        for edit in main_window.descendants(control_type="Edit")
        if getattr(edit.element_info, "automation_id", "") != "chat_input_field"
    ]
    if not edits:
        raise RuntimeError("未找到微信顶部搜索框。")
    return edits[0]


def clear_edit(edit) -> None:
    try:
        edit.set_text("")
        return
    except Exception:
        pass
    edit.click_input()
    edit.type_keys("^a{BACKSPACE}", set_foreground=True)


def open_chat(friend: str):
    main_window = get_main_window()

    try:
        session_list = main_window.child_window(auto_id="session_list", control_type="List")
        if session_list.exists(timeout=1):
            exact_session = session_list.child_window(
                auto_id=f"session_item_{friend}",
                control_type="ListItem",
            )
            if exact_session.exists(timeout=0.5):
                exact_session.click_input()
                return main_window
    except Exception:
        pass

    search = get_search_edit(main_window)
    clear_edit(search)
    search.set_text(friend)
    time.sleep(0.8)

    search_list = main_window.child_window(auto_id="search_list", control_type="List")
    if not search_list.exists(timeout=1):
        clear_edit(search)
        raise RuntimeError(f"未出现搜索结果列表，无法打开聊天: {friend}")

    items = search_list.children(control_type="ListItem")
    normalized = []
    for item in items:
        text = item.window_text().strip()
        if text in SEARCH_RESULT_IGNORE:
            continue
        normalized.append((text, item))

    exact = [item for text, item in normalized if text == friend]
    if not exact:
        exact = [item for text, item in normalized if text.splitlines()[0] == friend]
    if not exact:
        exact = [
            item
            for text, item in normalized
            if friend.lower() == text.lower() or friend.lower() == text.splitlines()[0].lower()
        ]
    if not exact:
        clear_edit(search)
        choices = [text for text, _ in normalized[:10]]
        raise RuntimeError(
            f"未找到联系人或群聊: {friend}。当前前 10 个候选结果: {choices}"
        )

    exact[0].click_input()
    time.sleep(0.5)
    clear_edit(search)
    return main_window


def get_chat_input(main_window):
    input_edit = main_window.child_window(auto_id="chat_input_field", control_type="Edit")
    if not input_edit.exists(timeout=1):
        raise RuntimeError("未找到聊天输入框。")
    return input_edit


def get_send_button(main_window):
    candidates = []
    for button in main_window.descendants(control_type="Button"):
        title = button.window_text().strip()
        class_name = button.class_name()
        if title in {"Send", "发送"}:
            return button
        if class_name == "mmui::XOutlineButton":
            candidates.append(button)
    if candidates:
        return candidates[0]
    raise RuntimeError("未找到发送按钮。")


def send_one(main_window, text: str) -> None:
    input_edit = get_chat_input(main_window)
    clear_edit(input_edit)
    input_edit.click_input()
    SystemSettings.copy_text_to_clipboard(text)
    pyautogui.hotkey("ctrl", "v", _pause=False)
    time.sleep(GlobalConfig.send_delay)
    get_send_button(main_window).click_input()
    time.sleep(0.3)


def send_demo(friend: str, message: str) -> None:
    main_window = open_chat(friend)
    payload = [
        message,
        f"sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "this is a minimal automation demo message.",
    ]
    for item in payload:
        send_one(main_window, item)
    print(f"已向 [{friend}] 发送 {len(payload)} 条消息。")


def unsupported(command: str) -> int:
    print(
        f"{command} 暂未在这个脚本里启用。"
        "原因是仓库当前的监听/自动回复实现依赖中文 UI 映射，"
        "而你机器上的微信 UI 暴露为英文控件名。"
    )
    print("当前已适配并验证修复方向的是 send。")
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PC 微信 4.1+ 最小可运行示例。默认执行 send。"
    )
    subparsers = parser.add_subparsers(dest="command")

    send_parser = subparsers.add_parser("send", help="发送测试消息")
    send_parser.add_argument("--friend", default=DEFAULT_FRIEND, help="好友或群聊名称")
    send_parser.add_argument(
        "--message",
        default="你好，这是一条最小示例消息。",
        help="第一条发送内容",
    )

    listen_parser = subparsers.add_parser("listen", help="预留命令")
    listen_parser.add_argument("--friend", default=DEFAULT_FRIEND)
    listen_parser.add_argument("--duration", default="30s")

    reply_parser = subparsers.add_parser("reply", help="预留命令")
    reply_parser.add_argument("--friend", default=DEFAULT_FRIEND)
    reply_parser.add_argument("--duration", default="1min")

    return parser


def main(argv: list[str] | None = None) -> int:
    configure()
    parser = build_parser()
    args = parser.parse_args(argv)

    command = args.command or "send"
    if command == "send":
        send_demo(friend=args.friend, message=args.message)
        return 0
    if command == "listen":
        return unsupported("listen")
    if command == "reply":
        return unsupported("reply")

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
