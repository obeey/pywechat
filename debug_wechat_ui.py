import pyautogui
from pywinauto import Desktop
from pyweixin import GlobalConfig

def debug_ui():
    print("Searching for WeChat main window...")
    try:
        window = Desktop(backend="uia").window(class_name="mmui::MainWindow")
        if not window.exists(timeout=5):
            print("Could not find WeChat main window.")
            return
        window.set_focus()
        print("Main window found and focused.")

        print("\n--- Scanning for all 'List' controls ---")
        lists = window.descendants(control_type="List")
        print(f"Found {len(lists)} List controls.\n")

        for i, lst in enumerate(lists):
            info = lst.element_info
            title = info.name
            aid = info.automation_id
            try:
                items = lst.children(control_type="ListItem")
                count = len(items)
            except:
                count = "Error"
            
            print(f"List [{i}]:")
            print(f"  Title: {title}")
            print(f"  AutomationID: {aid}")
            print(f"  ListItem Count: {count}")
            print("-" * 30)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    debug_ui()