import json
import re
import requests

from scraper import jobs, get_job_description
from resume_generator import customize_resume
from cover_letter_generator import customize_cover_letter
from email_sender import send_email


# ============================================================
# READ CONFIGURATION
# ============================================================

def read_config(filename="config.txt"):
    config = {}

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if line and "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()

    return config


config = read_config()


# ============================================================
# CONFIGURATION
# ============================================================

BASE_SKILL = config.get("BASE_SKILL", "Java")
CANDIDATE_SKILL_DESCRIPTION = config.get(
    "CANDIDATE_SKILL_DESCRIPTION",
    ""
)
ROLES = config.get("ROLES", "")
LOCATIONS = config.get("LOCATIONS", "Bangalore, Hyderabad")
EXPERIENCE = config.get("EXPERIENCE", "4 years")
CONFIDENCE_THRESHOLD = float(
    config.get("CONFIDENCE_THRESHOLD", "85")
)
GOOGLE_SHEET_URL = config.get("GOOGLE_SHEET_URL", "")
CANDIDATE_EMAIL = config.get("CANDIDATE_EMAIL", "")
SEND_EMAIL = config.get("SEND_EMAIL", "false").lower() == "true"


# ============================================================
# LM STUDIO SETTINGS
# ============================================================

LM_STUDIO_URL = "http://localhost:1234/api/v1/chat"
LM_MODEL = "google/gemma-4-e4b"


# ============================================================
# AI REQUEST
# ============================================================

def ask_ai(prompt):
    payload = {
        "model": LM_MODEL,
        "input": prompt,
        "temperature": 0,
        "max_output_tokens": 250,
        "reasoning": "off",
        "store": False
    }

    response = requests.post(
        LM_STUDIO_URL,
        json=payload,
        timeout=300
    )

    response.raise_for_status()

    data = response.json()

    output = data.get("output", [])

    if not output:
        return ""

    parts = []

    for item in output:
        if isinstance(item, dict):
            content = item.get("content", "")

            if isinstance(content, str):
                parts.append(content)

    return "\n".join(parts).strip()


# ============================================================
# NUMBER EXTRACTION
# ============================================================

def extract_number(text, key):
    pattern = rf"{key}\s*[:=]\s*(\d{{1,3}})"
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return None

    value = int(match.group(1))

    return max(0, min(100, value))


# ============================================================
# SCORE NORMALIZATION
# ============================================================

def normalize_component(value):
    if value is None:
        return 0

    return max(0, min(100, float(value)))


# ============================================================
# AI JOB EVALUATION
# ============================================================

def evaluate_job(job_title, company, job_description):

    prompt = f"""
You are evaluating ONE job for ONE candidate.

Candidate target:
- Base skill: {BASE_SKILL}
- Target roles: {ROLES}
- Target locations: {LOCATIONS}
- Candidate experience: {EXPERIENCE}
- Candidate skills:
{CANDIDATE_SKILL_DESCRIPTION}

Job title:
{job_title}

Company:
{company}

Job description:
{job_description}

Evaluate the job using these four dimensions.

1. ROLE = 0 to 100
How closely does the job title and actual role match the candidate's target roles and Java career direction?

2. SKILL = 0 to 100
How strongly do the required/preferred technical skills in the job description match the candidate's skills?
Do not reward a skill just because the word Java appears. Consider the actual technical requirements.

3. EXPERIENCE = 0 to 100
Compare the job's required experience with the candidate's {EXPERIENCE}.
If the job requires substantially more experience, reduce this score.
If experience is suitable or the job is entry/flexible, score it higher.

4. DESCRIPTION = 0 to 100
How strongly does the complete job description semantically fit the candidate profile?
Consider responsibilities, technologies, architecture, databases, testing, tools and development work.

IMPORTANT:
- Use the complete job description, not only the title.
- A strong Java/software-development match should be capable of receiving a score above 85.
- Do not artificially cap good matches at 85.
- Give different scores when the jobs have different levels of fit.
- Do not use only fixed values such as 50, 60, 75 or 85.
- The final score will be calculated by the program as:
  ROLE 25% + SKILL 50% + EXPERIENCE 15% + DESCRIPTION 10%.

Return ONLY these six lines and nothing else:

ROLE=<0-100>
SKILL=<0-100>
EXPERIENCE=<0-100>
DESCRIPTION=<0-100>
TOTAL=<0-100>
COMMENT=<one short reason for the score>
"""

    print()
    print("AI evaluating:", job_title)

    try:
        ai_text = ask_ai(prompt)

        role_score = extract_number(ai_text, "ROLE")
        skill_score = extract_number(ai_text, "SKILL")
        experience_score = extract_number(ai_text, "EXPERIENCE")
        description_score = extract_number(ai_text, "DESCRIPTION")

        if (
            role_score is None
            or skill_score is None
            or experience_score is None
            or description_score is None
        ):
            print("AI returned an unexpected format:")
            print(ai_text)
            return {
                "confidence": 0,
                "comments": "AI evaluation format could not be parsed."
            }

        total = (
            normalize_component(role_score) * 0.25
            + normalize_component(skill_score) * 0.50
            + normalize_component(experience_score) * 0.15
            + normalize_component(description_score) * 0.10
        )

        total = round(total, 1)

        comment_match = re.search(
            r"COMMENT\s*=\s*(.+)",
            ai_text,
            re.IGNORECASE
        )

        if comment_match:
            comment = comment_match.group(1).strip()
        else:
            comment = (
                f"Role {role_score}, skills {skill_score}, "
                f"experience {experience_score}, description "
                f"match {description_score}."
            )

        print(
            f"  Role: {role_score} | "
            f"Skills: {skill_score} | "
            f"Experience: {experience_score} | "
            f"Description: {description_score}"
        )
        print("  Final confidence:", total)
        print("  Comment:", comment)

        return {
            "confidence": total,
            "comments": comment
        }

    except Exception as error:
        print("AI evaluation error:", error)

        return {
            "confidence": 0,
            "comments": "AI evaluation failed."
        }


# ============================================================
# GOOGLE SHEET UPDATE
# ============================================================

def update_google_sheet(results):

    if not GOOGLE_SHEET_URL:
        print()
        print("GOOGLE_SHEET_URL is missing in config.txt")
        return

    payload = {
        "jobs": results
    }

    print()
    print("=" * 60)
    print("UPDATING GOOGLE SHEET")
    print("=" * 60)

    try:
        response = requests.post(
            GOOGLE_SHEET_URL,
            json=payload,
            timeout=60
        )

        print("Google Sheet HTTP status:", response.status_code)
        print("Google Sheet response:", response.text)

    except Exception as error:
        print("Google Sheet update error:", error)


# ============================================================
# PART 2 - DOCUMENT GENERATION
# ============================================================

def generate_documents_for_high_confidence_jobs(high_confidence):

    generated_jobs = []

    if not high_confidence:
        print("\nNo jobs crossed the confidence threshold.")
        return generated_jobs

    print()
    print("=" * 60)
    print("PART 2 - RESUME AND COVER LETTER GENERATION")
    print("=" * 60)

    for index, job in enumerate(high_confidence, start=1):
        title = job["title"]
        company = job["company"]
        description = job.get("description", "")

        print()
        print("=" * 60)
        print(f"GENERATING DOCUMENTS {index} OF {len(high_confidence)}")
        print("=" * 60)
        print("Title:", title)
        print("Company:", company)
        print("Confidence:", job["confidence"])

        if not description:
            print("Skipping: job description is unavailable.")
            continue

        try:
            resume_path = customize_resume(title, company, description)
            cover_letter_path = customize_cover_letter(title, company, description)

            generated_jobs.append({
                "job": job,
                "resume_path": resume_path,
                "cover_letter_path": cover_letter_path
            })

            print("\nDocuments generated successfully.")
            print("Resume:", resume_path)
            print("Cover Letter:", cover_letter_path)

        except Exception as error:
            print("\nDocument generation failed:")
            print(error)

    return generated_jobs


# ============================================================
# HUMAN REVIEW + OPTIONAL EMAIL
# ============================================================

def review_and_send(generated_jobs):

    if not generated_jobs:
        return

    print()
    print("=" * 60)
    print("HUMAN REVIEW / EMAIL")
    print("=" * 60)

    if not SEND_EMAIL:
        print("SEND_EMAIL=false")
        print("Email sending is disabled.")
        print("Please review the generated documents manually.")
        print("No email will be sent.")
        return

    if not CANDIDATE_EMAIL:
        print("CANDIDATE_EMAIL is missing in config.txt.")
        print("Documents were generated, but no email was sent.")
        return

    print("Email sending is enabled.")
    print("Each job requires explicit human approval.")

    for item in generated_jobs:
        job = item["job"]

        print()
        print("=" * 60)
        print("REVIEW BEFORE EMAIL")
        print("=" * 60)
        print("Job:", job["title"])
        print("Company:", job["company"])
        print("Confidence:", job["confidence"])
        print("Resume:", item["resume_path"])
        print("Cover Letter:", item["cover_letter_path"])

        approval = input(
            "After reviewing both files, type YES to send them to your email, or NO to skip: "
        ).strip().upper()

        if approval != "YES":
            print("Email skipped for this job.")
            continue

        print("Human approval received. Sending email...")

        send_email(
            CANDIDATE_EMAIL,
            job["title"],
            job["company"],
            item["resume_path"],
            item["cover_letter_path"]
        )


# ============================================================
# MAIN
# ============================================================

print()
print("=" * 60)
print("JOB ASSISTANT BOT - COMPLETE WORKFLOW")
print("=" * 60)

print("Jobs received from scraper:", len(jobs))
print("Confidence threshold:", CONFIDENCE_THRESHOLD)
print("Target locations:", LOCATIONS)
print("Candidate experience:", EXPERIENCE)

results = []


# ============================================================
# PROCESS EACH JOB
# ============================================================

for index, job in enumerate(jobs, start=1):

    print()
    print("=" * 60)
    print(f"PROCESSING JOB {index} OF {len(jobs)}")
    print("=" * 60)

    title = job.get("title", "")
    company = job.get("company", "")
    link = job.get("link", "")

    print("Title:", title)
    print("Company:", company)

    description = get_job_description(link)

    if not description:
        print("No usable job description found.")

        results.append({
            "title": title,
            "company": company,
            "link": link,
            "confidence": 0,
            "comments": "Job description could not be retrieved."
        })

        continue

    evaluation = evaluate_job(
        title,
        company,
        description
    )

    results.append({
        "title": title,
        "company": company,
        "link": link,
        "confidence": evaluation["confidence"],
        "comments": evaluation["comments"],
        "description": description
    })


# ============================================================
# SORT RESULTS
# ============================================================

results.sort(
    key=lambda job: float(job["confidence"]),
    reverse=True
)


print()
print("=" * 60)
print("ALL JOBS - SORTED BY CONFIDENCE")
print("=" * 60)

for job in results:
    print(
        f'{float(job["confidence"]):5.1f} | '
        f'{job["title"]} | '
        f'{job["company"]}'
    )


# ============================================================
# PART 2 ELIGIBILITY CHECK
# STRICTLY GREATER THAN 85
# ============================================================

high_confidence = [
    job
    for job in results
    if float(job["confidence"]) > CONFIDENCE_THRESHOLD
]


print()
print("=" * 60)
print("PART 2 ELIGIBILITY TEST")
print("=" * 60)

print(
    f"Jobs with confidence > {CONFIDENCE_THRESHOLD}: "
    f"{len(high_confidence)}"
)

for job in high_confidence:
    print(
        f'{float(job["confidence"]):5.1f} | '
        f'{job["title"]} | '
        f'{job["company"]}'
    )


# ============================================================
# UPDATE GOOGLE SHEET
# ============================================================

update_google_sheet(results)


# ============================================================
# PART 2 - GENERATE DOCUMENTS FOR JOBS ABOVE 85
# ============================================================

generated_jobs = generate_documents_for_high_confidence_jobs(high_confidence)

review_and_send(generated_jobs)


print()
print("=" * 60)
print("JOB ASSISTANT BOT COMPLETED")
print("=" * 60)
print()
