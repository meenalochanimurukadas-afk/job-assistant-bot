import os
import smtplib
from email.message import EmailMessage


# ============================================================
# GMAIL CONFIGURATION
# ============================================================

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

SENDER_EMAIL = os.getenv("JOB_BOT_SENDER_EMAIL")
SENDER_APP_PASSWORD = os.getenv("JOB_BOT_APP_PASSWORD")


# ============================================================
# SEND EMAIL
# ============================================================

def send_email(
    candidate_email,
    job_title,
    company,
    resume_path,
    cover_letter_path,
    email_subject=None,
    email_body=None
):
    """
    Send the customized resume and cover letter by email.

    IMPORTANT:
    This function only sends when app.py explicitly calls it
    after the user has approved the application.

    The approval logic is handled in app.py.
    """

    # --------------------------------------------------------
    # Check sender email
    # --------------------------------------------------------

    if not SENDER_EMAIL:

        print(
            "\nSender email is not configured."
        )

        print(
            "Please set JOB_BOT_SENDER_EMAIL."
        )

        return False

    # --------------------------------------------------------
    # Check Gmail App Password
    # --------------------------------------------------------

    if not SENDER_APP_PASSWORD:

        print(
            "\nGmail App Password is not configured."
        )

        print(
            "Please set JOB_BOT_APP_PASSWORD."
        )

        return False

    # --------------------------------------------------------
    # Check recipient
    # --------------------------------------------------------

    if not candidate_email:

        print(
            "\nRecipient email is empty."
        )

        return False

    # --------------------------------------------------------
    # Check resume
    # --------------------------------------------------------

    if not os.path.exists(resume_path):

        print(
            f"\nResume file not found: {resume_path}"
        )

        return False

    # --------------------------------------------------------
    # Check cover letter
    # --------------------------------------------------------

    if not os.path.exists(cover_letter_path):

        print(
            f"\nCover letter file not found: "
            f"{cover_letter_path}"
        )

        return False

    # --------------------------------------------------------
    # Default subject
    # --------------------------------------------------------

    if not email_subject:

        email_subject = (
            f"Application for {job_title} - {company}"
        )

    # --------------------------------------------------------
    # Default body
    # --------------------------------------------------------

    if not email_body:

        email_body = f"""Dear Hiring Team,

Please find attached my resume and cover letter
for the {job_title} position at {company}.

Thank you for your consideration.

Best regards,
Candidate
"""

    try:

        # ====================================================
        # CREATE EMAIL
        # ====================================================

        message = EmailMessage()

        message["From"] = SENDER_EMAIL
        message["To"] = candidate_email
        message["Subject"] = email_subject

        message.set_content(
            email_body
        )

        # ====================================================
        # ATTACH RESUME
        # ====================================================

        with open(
            resume_path,
            "rb"
        ) as file:

            resume_data = file.read()

        message.add_attachment(
            resume_data,
            maintype="application",
            subtype=(
                "vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            filename=os.path.basename(
                resume_path
            )
        )

        # ====================================================
        # ATTACH COVER LETTER
        # ====================================================

        with open(
            cover_letter_path,
            "rb"
        ) as file:

            cover_letter_data = file.read()

        message.add_attachment(
            cover_letter_data,
            maintype="application",
            subtype=(
                "vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            filename=os.path.basename(
                cover_letter_path
            )
        )

        # ====================================================
        # CONNECT TO GMAIL
        # ====================================================

        print(
            "\nConnecting to Gmail..."
        )

        with smtplib.SMTP_SSL(
            SMTP_SERVER,
            SMTP_PORT
        ) as server:

            server.login(
                SENDER_EMAIL,
                SENDER_APP_PASSWORD
            )

            server.send_message(
                message
            )

        # ====================================================
        # SUCCESS
        # ====================================================

        print(
            "\n=========================================="
        )

        print(
            "EMAIL SENT SUCCESSFULLY"
        )

        print(
            "=========================================="
        )

        print(
            f"\nSent to       : {candidate_email}"
        )

        print(
            f"Subject       : {email_subject}"
        )

        print(
            f"Resume        : "
            f"{os.path.basename(resume_path)}"
        )

        print(
            f"Cover Letter  : "
            f"{os.path.basename(cover_letter_path)}"
        )

        return True

    except Exception as error:

        # ====================================================
        # ERROR
        # ====================================================

        print(
            "\n=========================================="
        )

        print(
            "EMAIL ERROR"
        )

        print(
            "=========================================="
        )

        print(
            error
        )

        return False


# ============================================================
# DIRECT TEST
# ============================================================
#
# IMPORTANT:
# Do not run this file directly for testing right now.
#
# The main application will call send_email() only after
# the user explicitly types YES.
#
# ============================================================

if __name__ == "__main__":

    print(
        "\nemail_sender.py is ready."
    )

    print(
        "Run app.py to test the complete workflow."
    )