import os
import sys
from pywinauto import Desktop

def debug_ui():
    print("Searching for WeChat main window...")
    try:
        window = Desktop(backend="uia").window(class_name="mmui::MainWindow")
        if not window.exists(timeout=5):
            print("WeChat main window not found.")
            return
        window.set_focus()
        print("Window found and focused.")
        
        print("\n--- Listing ALL elements with any text ---")
        count = 0
        for desc in window.descendants():
            try:
                text = desc.window_text()
                if text:
                    class_name = desc.class_name()
                    rect = desc.rectangle()
                    print(f"Class: {class_name} | Text: {text} | Rect: {rect}")
                    count += 1
            except Exception:
                continue
        
        if count == 0:
            print("No elements with text found.")
        else:
            print(f"\nFound {count} elements with text.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_ui()