import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

import mailer

print("=" * 60)
print("📧 JOB ALERT PLATFORM - EMAIL & RECIPIENT VERIFICATION TEST")
print("=" * 60)

names, emails = mailer.load_students()

print(f"\nTotal Subscribed Students Found in DB: {len(emails)}")

for idx, (name, email) in enumerate(zip(names, emails), start=1):
    print(f"  {idx}. Name: '{name}' | Email: '{email}'")

if not emails:
    print("\n⚠️ No students found in database table 'students'.")
    print("Add a student via http://127.0.0.1:5000/admin-home or insert into SQLite.")
else:
    print("\n✓ Sample Email Preview for first recipient:")
    first_name = names[0]
    first_email = emails[0]
    preview_html = mailer.html_template.replace("{USER_NAME}", first_name)
    
    print(f"  - Subject: Today's Verified IT Openings - {mailer.today}")
    print(f"  - Recipient: {first_email}")
    print(f"  - Greeting Line: Dear {first_name},")
    print(f"  - Total Jobs Selected: {min(20, len(mailer.jobs))}")
    print("\n  Section 1: 🎯 Top IT, Software & Tech Openings (High Priority):")
    if hasattr(mailer, 'top_it_list'):
        for i, j in enumerate(mailer.top_it_list[:6], 1):
            badge = "🎓 IT Fresher" if mailer.classify_job(j) == 1 else "💻 Software & IT Role"
            print(f"    {i}. [{badge}] {j.get('title', '').strip()}")

    print("\n  Section 2: 🌐 Explore All Other Openings (Down Area):")
    if hasattr(mailer, 'general_list'):
        for i, j in enumerate(mailer.general_list[:5], 1):
            print(f"    {i}. [📌 Open Position] {j.get('title', '').strip()}")

print("\n------------------------------------------------------------")
print("To execute a REAL email test to all registered students, run:")
print("  python mailer.py")
print("------------------------------------------------------------")
