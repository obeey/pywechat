import os
import sys
import time
import json
import requests
import pyautogui
from pywinauto import Desktop
from pyweixin import GlobalConfig, Navigator
from pyweixin.WinSettings import SystemSettings

# Configuration
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

def open_chat_robust(friend: str):
    """Robust chat opening logic."""
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

def send_one(main_window, text: str):
    """Sends a message using the most robust method."""
    input_edit = main_window.child_window(auto_id="chat_input_field", control_type="Edit")
    if not input_edit.exists(timeout=1):
        raise RuntimeError("未找到聊天输入框。")
    
    clear_edit(input_edit)
    input_edit.click_input()
    SystemSettings.copy_text_to_clipboard(text)
    pyautogui.hotkey("ctrl", "v", _pause=False)
    time.sleep(GlobalConfig.send_delay)
    
    # Find send button flexibly
    send_btn = None
    for btn in main_window.descendants(control_type="Button"):
        title = btn.window_text().strip()
        if title in {"Send", "发送"}:
            send_btn = btn
            break
    if not send_btn:
        # Fallback to enter key
        pyautogui.press('enter')
    else:
        send_btn.click_input()
    time.sleep(0.3)

def my_reply_callback(newMessage: str):
    """Custom callback for '长风' using vLLM API."""
    print(f"Received message: {newMessage}")
    
    api_url = "https://vllm.codingstack.xyz:61721/v1/chat/completions"
    api_key = "e6uIhWd+HVJSOYaN"
    model = "gemma4"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant replying to '长风' on WeChat. Keep responses concise and natural."},
            {"role": "user", "content": newMessage}
        ],
        "temperature": 0.7
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        reply = result['choices'][0]['message']['content'].strip()
        return reply
    except Exception as e:
        print(f"API Error: {e}")
        return None

def monitor_and_reply(friend_name: str):
    configure()
    print(f"Starting custom monitor for {friend_name}...")
    main_window = open_chat_robust(friend_name)
    
    time.sleep(1.0) # Give the UI time to render the chat area
    print(f"Monitoring {friend_name} using bubble-detection mode...")

    last_runtime_id = None
    # We will search for message bubbles directly instead of relying on a 'List' container
    # because the UI tree on this machine does not expose the chat history as a standard List.
    
    print("Monitoring... Press Ctrl+C to stop.")
    try:
        # Identify the input field to define the "forbidden zone" at the bottom
        try:
            input_field = main_window.child_window(auto_id="chat_input_field", control_type="Edit")
            input_top = input_field.rectangle().top
        except:
            input_top = main_rect.bottom * 0.8 # Fallback

        while True:
            # Find all elements with text in the right-hand side of the window (the chat area)
            main_rect = main_window.rectangle()
            chat_area_left = main_rect.left + main_rect.width() * 0.3
            
            all_text_elements = []
            for desc in main_window.descendants():
                try:
                    text = desc.window_text()
                    if text:
                        rect = desc.rectangle()
                        # 1. Must be in the chat area (right side)
                        # 2. Must be ABOVE the input field (to avoid picking up input hints)
                        if rect.left > chat_area_left and rect.bottom < input_top:
                            all_text_elements.append(desc)
                except:
                    continue
            
            if all_text_elements:
                # Sort elements by their bottom position to find the most recent message
                # Most recent messages are at the bottom of the chat window
                all_text_elements.sort(key=lambda x: x.rectangle().bottom)
                last_item = all_text_elements[-1]
                
                try:
                    current_runtime_id = last_item.element_info.runtime_id
                except Exception:
                    current_runtime_id = last_item.window_text() + str(last_item.rectangle().top)

                if current_runtime_id != last_runtime_id:
                    msg_text = last_item.window_text()
                    item_rect = last_item.rectangle()
                    
                    # Debug info to help identify why detection might fail
                    # print(f"Detected element: '{msg_text}' at {item_rect}")

                    # Further refine: If it's too far right, it's likely our own message
                    # Users messages are typically aligned to the right side of the chat area
                    is_right_aligned = item_rect.left > (main_rect.left + main_rect.width() * 0.6)
                    
                    if is_right_aligned:
                        # print(f"Ignoring my own message: {msg_text}")
                        pass
                    else:
                        # Ensure we aren't picking up timestamps, system messages, or UI hints
                        # Added "Voice input" and "Hold" to filter out WeChat input area hints
                        forbidden_keywords = ["撤回", " transferred", "发送了", "Voice input", "Hold Ctrl", "Ctrl+Win"]
                        if len(msg_text) > 0 and not any(kw in msg_text for kw in forbidden_keywords):
                            print(f"New message detected: {msg_text}")
                            reply = my_reply_callback(msg_text)
                            if reply:
                                print(f"Replying to: {msg_text} -> {reply}")
                                send_one(main_window, reply)
                                time.sleep(1.0)
                    
                    last_runtime_id = current_runtime_id
            
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user.")

def main():
    try:
        monitor_and_reply("长风")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()