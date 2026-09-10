import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import mailer

print("=" * 70)
print("⏰ ACADENO JOB ALERT PLATFORM - AUTOMATED DAILY EMAIL SCHEDULER")
print("=" * 70)
print("Scheduled Execution Times:")
print("  1. Morning Shift : 10:00 AM (10:00)")
print("  2. Evening Shift : 05:00 PM (17:00)")
print("=" * 70)

def check_and_run():
    last_run_date = ""
    last_run_slot = ""

    while True:
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")

        # Morning Slot: 10:00 AM
        if current_time == "10:00" and (last_run_date != current_date or last_run_slot != "morning"):
            print(f"\n[⏰ 10:00 AM AUTOMATED TRIGGER] Starting morning email alert dispatch at {now.strftime('%d %B %Y %H:%M:%S')}...")
            try:
                mailer.send_all_emails()
                last_run_date = current_date
                last_run_slot = "morning"
                print("✅ Morning email dispatch completed successfully.")
            except Exception as e:
                print("❌ Error in morning email dispatch:", e)

        # Evening Slot: 05:00 PM (17:00)
        elif current_time == "17:00" and (last_run_date != current_date or last_run_slot != "evening"):
            print(f"\n[⏰ 05:00 PM AUTOMATED TRIGGER] Starting evening email alert dispatch at {now.strftime('%d %B %Y %H:%M:%S')}...")
            try:
                mailer.send_all_emails()
                last_run_date = current_date
                last_run_slot = "evening"
                print("✅ Evening email dispatch completed successfully.")
            except Exception as e:
                print("❌ Error in evening email dispatch:", e)

        # Status heartbeat every 30 seconds
        time.sleep(30)

if __name__ == "__main__":
    check_and_run()
