import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Configure these with your own sending email + app password ---
# For Gmail: enable 2FA, then generate an "App Password" (not your normal password)
# Google Account -> Security -> 2-Step Verification -> App Passwords
SENDER_EMAIL = "arhamazeem318@gmail.com"
SENDER_APP_PASSWORD = "fycv ktrk lydu pwav"
ADMIN_EMAIL = "wisamahmed851@gmail.com"  # where alerts get sent
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587


def send_email(to_email, subject, body):
    """Sends a plain-text email. Returns (success: bool, message: str)."""
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # upgrades to a secure encrypted connection
        server.login(SENDER_EMAIL, SENDER_APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        server.quit()

        return True, "Email sent successfully."
    except Exception as e:
        return False, f"Email failed: {str(e)}"


def build_alert_email_body(consecutive_flagged, low_attendance_flagged):
    """Formats the flagged students into a readable email body."""
    lines = ["AI Attendance Manager - Irregular Attendance Alert", ""]

    if consecutive_flagged:
        lines.append("--- Students with Consecutive Absences ---")
        for s in consecutive_flagged:
            lines.append(f"- {s['name']} ({s['student_id']}): {s['consecutive_absences']} days absent in a row")
        lines.append("")

    if low_attendance_flagged:
        lines.append("--- Students Below Attendance Threshold ---")
        for s in low_attendance_flagged:
            lines.append(f"- {s['name']} ({s['student_id']}): {s['attendance_percentage']}% attendance "
                         f"({s['days_present']}/{s['total_days']} days)")
        lines.append("")

    lines.append("Please review these students in the AI Attendance Manager Reports page.")
    return "\n".join(lines)


def run_irregularity_check(db_manager, consecutive_threshold=3, percentage_threshold=75):
    """
    Checks both criteria, sends ONE consolidated email if anything is flagged.
    Returns (alert_sent: bool, message: str, flagged_count: int)
    """
    consecutive_flagged = db_manager.get_consecutive_absent_students(consecutive_threshold)
    low_attendance_flagged = db_manager.get_low_attendance_students(percentage_threshold)

    # avoid double-listing a student who trips both criteria in the count, but keep both sections informative
    if not consecutive_flagged and not low_attendance_flagged:
        return False, "No irregular attendance detected. No email sent.", 0

    body = build_alert_email_body(consecutive_flagged, low_attendance_flagged)
    subject = "Irregular Attendance Alert - Action Needed"

    success, msg = send_email(ADMIN_EMAIL, subject, body)

    flagged_ids = {s["student_id"] for s in consecutive_flagged} | {s["student_id"] for s in low_attendance_flagged}

    if success:
        return True, f"Alert email sent for {len(flagged_ids)} student(s).", len(flagged_ids)
    else:
        return False, msg, 0
    