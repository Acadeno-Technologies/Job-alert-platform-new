from dotenv import load_dotenv
load_dotenv()

import json
import os
import smtplib
import random
import sqlite3
import pandas as pd

from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ==========================================================
# LOAD STUDENTS
# ==========================================================

def load_students():

    # GitHub Actions
    email_to = os.getenv("EMAIL_TO")
    student_names = os.getenv("STUDENT_NAMES")

    if email_to and student_names:

        emails = [
            e.strip()
            for e in email_to.split(",")
            if e.strip()
        ]

        names = [
            n.strip().title()
            for n in student_names.split(",")
            if n.strip()
        ]

        print("Using GitHub Secrets")

        return names, emails

    # Local SQLite Database

    print("Using SQLite Database")

    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, email
        FROM students
        ORDER BY id
    """)

    rows = cursor.fetchall()

    conn.close()

    names = [row[0].strip().title() if row[0] else "" for row in rows]
    emails = [row[1].strip() for row in rows if row[1]]

    # Fallback to EMAIL_USER if no recipient found
    if not emails and os.getenv("EMAIL_USER"):
        fallback_email = os.getenv("EMAIL_USER").strip()
        names = ["Test Recipient"]
        emails = [fallback_email]

    return names, emails


# ==========================================================
# ENV VARIABLES
# ==========================================================

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

if EMAIL_USER:
    EMAIL_USER = EMAIL_USER.strip()

if EMAIL_PASS:
    EMAIL_PASS = EMAIL_PASS.replace(" ", "").strip()

USER_NAME, EMAIL_TO = load_students()

print("=" * 60)
print("Sender Email :", EMAIL_USER)
print("Recipients   :", EMAIL_TO)
print("Names        :", USER_NAME)
print("=" * 60)

if not EMAIL_USER or not EMAIL_PASS:
    print("⚠️ WARNING: EMAIL_USER or EMAIL_PASS missing in .env file.")
    print("To send real emails, create a .env file with your Gmail credentials.")

# ==========================================================
# RANDOM QUOTE
# ==========================================================

quote = "Success is not final, failure is not fatal: it is the courage to continue that counts."
quote_file = "scraper/career_quotes_unique.xlsx"
if os.path.exists(quote_file):
    try:
        quotes_df = pd.read_excel(quote_file)
        if "Quote" in quotes_df.columns:
            quote_list = quotes_df["Quote"].dropna().tolist()
            if quote_list:
                quote = random.choice(quote_list)
    except Exception as e:
        print("Note: Could not load quotes file, using default quote:", e)

# ==========================================================
# LOAD JOBS
# ==========================================================

jobs = []
jobs_file = "scraper/jobs.json"
if not os.path.exists(jobs_file):
    jobs_file = "jobs.json"

if os.path.exists(jobs_file):
    try:
        with open(jobs_file, "r", encoding="utf-8") as f:
            jobs = json.load(f)
    except Exception as e:
        print("Note: Error loading jobs.json:", e)

today = datetime.now().strftime("%d %B %Y")

# ==========================================================
# JOB PRIORITIZATION & CLASSIFICATION
# ==========================================================

def classify_job(job):
    title = job.get("title", "").lower()

    # 1. HR & Talent Management Roles
    hr_kw = ["hr ", "hr/", "hr-", "human resource", "recruiter", "talent acquisition", "hrbp", "payroll"]
    if any(kw in title for kw in hr_kw) or title.startswith("hr"):
        return 6  # HR & Talent Management

    # 2. AI & Data Science Roles
    ai_kw = ["ai", "ml", "machine learning", "data science", "data engineer", "data analyst", "power bi", "deep learning", "nlp", "sensing & ai"]
    if any(kw in title for kw in ai_kw):
        return 5  # AI & Data Science Role

    # Explicit Non-IT exclusion keywords
    non_it_exclusions = [
        "psychology", "research", "biology", "medical", "counselor", "teaching", "trainer", 
        "bpo", "voice", "data entry", "operator", "business development", "sales", "hr ", 
        "recruiter", "accountant", "telecaller", "content writer", "marketing", "supply chain",
        "video editing", "designer", "graphic", "finance", "legal", "nurse"
    ]

    is_excluded_from_it = any(ex in title for ex in non_it_exclusions)

    fresher_kw = ["fresher", "intern", "trainee", "junior", "jr.", "jr ", "entry", "walkin", "walk-in", "0-1", "0 to 1", "0-2", "0 to 2", "graduate", "beginner"]
    it_kw = [
        "developer", "engineer", "software", "python", "react", "angular", "frontend", "backend",
        "fullstack", "full stack", "qa", "quality analyst", "web", "node", "ui/ux", "plsql", "code", "tech", "cyber", "cloud",
        "java", "c++", "php", "testing", "tester", "android", "ios", "devops", "database", ".net", "dot net", "system engineer", "it support", "technical support"
    ]

    is_fresher = any(kw in title for kw in fresher_kw)
    is_it = any(kw in title for kw in it_kw) and not is_excluded_from_it

    if is_fresher and is_it:
        return 1  # IT Fresher / Entry Level
    elif is_it:
        return 2  # Software & IT Role
    elif is_fresher:
        return 3  # Non-IT Entry Level
    else:
        return 4  # General Roles


# ==========================================================
# LINK CLEANER & 404 PREVENTER
# ==========================================================

import urllib.parse
import requests

def get_clean_working_url(job):
    link = job.get("link", "").strip()
    title = job.get("title", "").strip()
    clean_title = title.split("\n")[0].strip()
    encoded_title = urllib.parse.quote_plus(clean_title)

    if "technopark" in link or "technopark" in title.lower():
        return f"https://www.technopark.in/job-search?q={encoded_title}"
    elif "cyberparks" in link or "cyberpark" in title.lower():
        return "https://cyberparks.in/careers/"
    elif "smartcity" in link or "smartcity" in title.lower():
        return "https://smartcity-kochi.in/careers/"
    else:
        return "https://infopark.in/company-jobs"


# ==========================================================
# BUILD JOB CARDS
# ==========================================================

cards = ""

if jobs:
    hr_jobs = [j for j in jobs if classify_job(j) == 6]
    ai_data_jobs = [j for j in jobs if classify_job(j) == 5]
    fresher_it_jobs = [j for j in jobs if classify_job(j) == 1]
    general_it_jobs = [j for j in jobs if classify_job(j) == 2]
    fresher_other_jobs = [j for j in jobs if classify_job(j) == 3]
    other_jobs = [j for j in jobs if classify_job(j) == 4]

    random.shuffle(hr_jobs)
    random.shuffle(ai_data_jobs)
    random.shuffle(fresher_it_jobs)
    random.shuffle(general_it_jobs)
    random.shuffle(fresher_other_jobs)
    random.shuffle(other_jobs)

    top_it_list = list(hr_jobs + ai_data_jobs + fresher_it_jobs + general_it_jobs)[:14]

    down_area_pool = [j for j in jobs if j not in top_it_list]
    random.shuffle(down_area_pool)
    general_list = list(down_area_pool[:8])

    portal_url = os.getenv("PORTAL_URL", "http://127.0.0.1:5000/user")
    search_filter_bar = ""

    def render_job_card(job):
        title = job.get("title", "Job Opening").strip()
        link = get_clean_working_url(job)
        cat = classify_job(job)

        badge_html = ""
        if cat == 6:
            badge_html = '<span style="background:#fef3c7;color:#92400e;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:700;display:inline-block;margin-bottom:8px;">👔 HR & Talent Management</span>'
        elif cat == 5:
            badge_html = '<span style="background:#fae8ff;color:#86198f;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:700;display:inline-block;margin-bottom:8px;">🤖 AI & Data Science</span>'
        elif cat == 1:
            badge_html = '<span style="background:#e0e7ff;color:#4338ca;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:700;display:inline-block;margin-bottom:8px;">🎓 IT Fresher / Entry Level</span>'
        elif cat == 2:
            badge_html = '<span style="background:#dbeafe;color:#1e40af;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:700;display:inline-block;margin-bottom:8px;">💻 Software & IT Role</span>'
        elif cat == 3:
            badge_html = '<span style="background:#fef3c7;color:#92400e;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600;display:inline-block;margin-bottom:8px;">🌟 General Entry Level</span>'
        else:
            badge_html = '<span style="background:#f3f4f6;color:#374151;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:600;display:inline-block;margin-bottom:8px;">📌 General Position</span>'

        return f"""
        <div style="
            border:1px solid #e2e8f0;
            border-radius:12px;
            padding:16px;
            margin-bottom:15px;
            background:#ffffff;
            box-shadow:0 1px 3px rgba(0,0,0,0.05);
            box-sizing:border-box;
        ">
            {badge_html}
            <h3 style="color:#5f2cff;margin-top:4px;margin-bottom:12px;font-size:16px;line-height:1.4;">{title}</h3>
            <a href="{link}" target="_blank" style="background:#5f2cff;color:white;padding:9px 18px;border-radius:8px;text-decoration:none;display:inline-block;font-weight:700;font-size:13px;">Apply Now ↗</a>
        </div>
        """

    # 1. AI & Data Science Section (Top Priority)
    if ai_data_jobs:
        cards += '<h3 style="color:#86198f;margin-top:25px;margin-bottom:15px;border-left:4px solid #c084fc;padding-left:10px;font-size:16px;">🤖 AI, ML & Data Science Openings</h3>'
        for j in ai_data_jobs:
            cards += render_job_card(j)

    # 2. Software & IT Roles Section
    if general_it_jobs:
        cards += '<h3 style="color:#1e40af;margin-top:30px;margin-bottom:15px;border-left:4px solid #3b82f6;padding-left:10px;font-size:16px;">💻 Software & IT Roles</h3>'
        for j in general_it_jobs:
            cards += render_job_card(j)

    # 3. IT Fresher Section
    if fresher_it_jobs:
        cards += '<h3 style="color:#3730a3;margin-top:30px;margin-bottom:15px;border-left:4px solid #6366f1;padding-left:10px;font-size:16px;">🎓 IT Fresher & Entry Level Openings</h3>'
        for j in fresher_it_jobs:
            cards += render_job_card(j)

    # 4. HR & Talent Management Section (Below Tech)
    if hr_jobs:
        cards += '<h3 style="color:#b45309;margin-top:30px;margin-bottom:15px;border-left:4px solid #f59e0b;padding-left:10px;font-size:16px;">👔 HR & Talent Management Openings</h3>'
        for j in hr_jobs:
            cards += render_job_card(j)

    # 5. Non-IT & General Roles Section
    if general_list:
        cards += '<h3 style="color:#92400e;margin-top:30px;margin-bottom:15px;border-left:4px solid #f59e0b;padding-left:10px;font-size:16px;">🌐 Non-IT & General Positions</h3>'
        for j in general_list:
            cards += render_job_card(j)
else:
    search_filter_bar = ""
    cards = "<p style='color:#666;'>No active job postings found today. Please check back soon!</p>"

# ==========================================================
# EMAIL TEMPLATE
# ==========================================================

html_template = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;background:#f4f6fb;margin:0;padding:12px;">

<!-- Hidden Email Inbox Preheader Snippet -->
<div style="display:none;font-size:1px;color:#f4f6fb;line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;mso-hide:all;">
Explore today's verified IT job openings & search roles on Acadeno Technologies.
</div>

<div style="max-width:640px;
margin:auto;
background:white;
padding:24px 18px;
border-radius:16px;
box-shadow:0 4px 15px rgba(0,0,0,0.05);
box-sizing:border-box;">

<h1 style="color:#5f2cff;font-size:22px;margin-top:0;">
Acadeno Technologies
</h1>

<p style="font-size:15px;color:#1e293b;">
Dear <b>{{USER_NAME}}</b>,
</p>

<p style="font-style:italic;color:#475569;font-size:13px;line-height:1.4;">"{quote}"</p>

<h3 style="color:#1e1b4b;font-size:16px;margin-bottom:6px;">
Today's Verified IT Opportunities
</h3>

<p style="color:#64748b;font-size:13px;margin-top:0;">
Date : <b>{today}</b>
</p>

{search_filter_bar}

{cards}

<p style="margin-top:28px;font-size:14px;color:#334155;">
Best Wishes,<br>
<b style="color:#5f2cff;">Acadeno Technologies</b>
</p>

</div>

</body>

</html>
"""

# ==========================================================
# SEND EMAIL
# ==========================================================

def send_all_emails():
    if not EMAIL_USER or not EMAIL_PASS:
        print("\n❌ Error: Cannot send email because EMAIL_USER or EMAIL_PASS is missing in .env!")
        print("Please create a .env file with:")
        print("EMAIL_USER=your_email@gmail.com")
        print("EMAIL_PASS=your_app_password")
        return

    if not EMAIL_TO:
        print("\n❌ Error: No recipients found to send emails.")
        return

    print(f"\nConnecting to Gmail SMTP as '{EMAIL_USER}' (App Password length: {len(EMAIL_PASS)} chars)...")

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        print("Login Successful!\n")
    except smtplib.SMTPAuthenticationError as auth_err:
        print("\n" + "!" * 70)
        print("❌ GMAIL SMTP AUTHENTICATION FAILED (Error 535 / BadCredentials)")
        print("!" * 70)
        print(f"User Attempted: '{EMAIL_USER}'")
        print("\nCommon Causes & Solutions:")
        print(" 1. 2-Step Verification is OFF:")
        print("    Google requires 2-Step Verification to be ON to generate App Passwords.")
        print("    Enable it here: https://myaccount.google.com/signinoptions/two-step-verification")
        print("\n 2. App Password needs to be re-generated:")
        print("    Generate a new 16-character App Password specifically for this email at:")
        print("    https://myaccount.google.com/apppasswords")
        print("\n 3. Email mismatch:")
        print(f"    Ensure '{EMAIL_USER}' is the EXACT Google account where the App Password was created.")
        print("!" * 70 + "\n")
        return

    for email, name in zip(EMAIL_TO, USER_NAME):
        formatted_name = name.strip().title() if name else "Subscriber"

        html = html_template.replace(
            "{USER_NAME}",
            formatted_name
        )

        plain_text = f"Dear {formatted_name},\n\nHere are today's verified IT opportunities from Acadeno Technologies ({today}).\n\nPlease view the HTML version of this email or visit our portal at http://127.0.0.1:5000/user to apply."

        msg = MIMEMultipart("alternative")

        msg["Subject"] = f"Today's Verified IT Openings - {today}"
        msg["From"] = f"Acadeno Careers <{EMAIL_USER}>"
        msg["To"] = email
        msg["Reply-To"] = EMAIL_USER
        msg["X-Mailer"] = "Acadeno Job Alert Platform"

        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html, "html"))

        server.send_message(msg)
        print(f"✓ Email sent to {formatted_name} ({email})")

    server.quit()

    print("\n========================================")
    print("All Student Emails Sent Successfully")
    print("========================================")

if __name__ == "__main__":
    send_all_emails()