import os
import sys
import time
import pyautogui
from pywinauto import Desktop
from pyweixin import GlobalConfig
from pyweixin.WinSettings import SystemSettings

# Configuration
def configure():
    GlobalConfig.close_weixin = False
    GlobalConfig.is_maximize = False
    GlobalConfig.search_pages = 5
    GlobalConfig.send_delay = 0.2
    pyautogui.FAILSAFE = False

def get_main_window():
    window = Desktop(backend="uia").window(class_name="mmui::MainWindow")
    if not window.exists(timeout=5):
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

def clear_edit(edit):
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
    time.sleep(1.0)

    search_list = main_window.child_window(auto_id="search_list", control_type="List")
    if not search_list.exists(timeout=2):
        clear_edit(search)
        raise RuntimeError(f"未出现搜索结果列表，无法打开聊天: {friend}")

    items = search_list.children(control_type="ListItem")
    normalized = []
    for item in items:
        text = item.window_text().strip()
        if text in {"", "Favorites", "Contacts", "Group Chats", "Service Accounts", "Official Accounts", "Recent Used", "Most Frequently Used", "功能", "最近使用", "联系人", "群聊", "服务号", "公众号", "搜索"}:
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
        raise RuntimeError(f"未找到联系人或群聊: {friend}")

    exact[0].click_input()
    time.sleep(0.5)
    clear_edit(search)
    return main_window

def get_chat_input(main_window):
    input_edit = main_window.child_window(auto_id="chat_input_field", control_type="Edit")
    if not input_edit.exists(timeout=2):
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

def send_one(main_window, text: str):
    input_edit = get_chat_input(main_window)
    clear_edit(input_edit)
    input_edit.click_input()
    SystemSettings.copy_text_to_clipboard(text)
    pyautogui.hotkey("ctrl", "v", _pause=False)
    time.sleep(GlobalConfig.send_delay)
    get_send_button(main_window).click_input()
    time.sleep(0.5)

def main():
    configure()
    friend_name = "长风"
    report_path = os.path.join(os.getcwd(), "iran_war_latest_report_20260409.txt")
    
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        print(f"Reading report from: {report_path}")
        print(f"Opening chat with {friend_name}...")
        main_window = open_chat(friend_name)
        
        # Split long message into chunks
        max_length = 400
        chunks = [content[i:i + max_length] for i in range(0, len(content), max_length)]
        
        print(f"Sending {len(chunks)} chunks of message...")
        for i, chunk in enumerate(chunks):
            print(f"Sending chunk {i+1}/{len(chunks)}...")
            send_one(main_window, chunk)
            
        print(f"Successfully sent the latest report to {friend_name}!")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()