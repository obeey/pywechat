import os
import sys

# Add the current directory to sys.path so we can import send_to_wechat
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from send_to_wechat import send_to_wechat

def main():
    report_path = os.path.join(os.getcwd(), "iran_war_final_report_20260407.txt")
    # If the file is not in CWD, try the root project dir
    if not os.path.exists(report_path):
        # The file was written to the root directory c:\Users\Nico\Documents\Projects\digital-employees
        report_path = r"c:\Users\Nico\Documents\Projects\digital-employees\iran_war_final_report_20260407.txt"

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        print(f"Reading report from: {report_path}")
        print(f"Sending to '长风'...")
        
        if send_to_wechat("长风", content):
            print("Successfully sent the report to 长风!")
        else:
            print("Failed to send the report.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()