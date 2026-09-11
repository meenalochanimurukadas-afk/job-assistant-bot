import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlsplit, urlunsplit


# ============================================================
# READ CONFIGURATION
# ============================================================

def read_config(filename):

    config = {}

    with open(filename, "r", encoding="utf-8") as file:

        for line in file:

            line = line.strip()

            if (
                line
                and "=" in line
                and not line.startswith("#")
            ):

                key, value = line.split("=", 1)

                config[key.strip()] = value.strip()

    return config


config = read_config("config.txt")


# ============================================================
# CONFIGURATION
# ============================================================

roles = config.get("ROLES", "")

locations = config.get(
    "LOCATIONS",
    "India"
)

base_skill = config.get(
    "BASE_SKILL",
    "Java"
)


role_list = [
    role.strip()
    for role in roles.split(",")
    if role.strip()
]


# ============================================================
# SEARCH TERMS
# BASE SKILL + ALL CONFIGURED ROLES
# ============================================================

search_terms = []

seen_terms = set()

for term in [base_skill] + role_list:

    if term.lower() not in seen_terms:

        search_terms.append(term)

        seen_terms.add(
            term.lower()
        )


print()
print("Search terms:")
for term in search_terms:
    print("-", term)


# ============================================================
# REQUEST SETTINGS
# ============================================================

headers = {

    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    ),

    "Accept-Language": "en-US,en;q=0.9",

    "Accept": (
        "text/html,"
        "application/xhtml+xml,"
        "application/xml;q=0.9,"
        "image/avif,"
        "image/webp,"
        "*/*;q=0.8"
    ),

    "Connection": "keep-alive"
}


session = requests.Session()

session.headers.update(headers)


# ============================================================
# CANONICAL JOB LINK
# ============================================================

def canonicalize_job_link(url):

    if not url:
        return ""

    url = url.strip()

    parts = urlsplit(url)

    canonical_url = urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            "",
            ""
        )
    )

    return canonical_url


# ============================================================
# SCRAPE JOBS
# ============================================================

all_jobs = []

seen_links = set()


for search_term in search_terms:

    print()
    print("===================================")
    print("Searching for:", search_term)
    print("===================================")

    search_url = (
        "https://www.linkedin.com/jobs/search/"
        "?keywords="
        + quote(search_term)
        + "&location="
        + quote(locations)
    )

    try:

        response = session.get(
            search_url,
            timeout=20
        )

        print(
            "Status Code:",
            response.status_code
        )

        if response.status_code == 429:

            print(
                "LinkedIn rate limited the search request."
            )

            time.sleep(10)

            continue

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        job_cards = soup.find_all(
            "div",
            class_="base-card"
        )

        print(
            "Jobs found:",
            len(job_cards)
        )

        for job in job_cards:

            title = job.find(
                "h3",
                class_="base-search-card__title"
            )

            company = job.find(
                "h4",
                class_="base-search-card__subtitle"
            )

            link = job.find(
                "a",
                class_="base-card__full-link"
            )

            if not (
                title
                and company
                and link
            ):
                continue

            job_title = title.get_text(
                strip=True
            )

            company_name = company.get_text(
                strip=True
            )

            original_link = link.get(
                "href"
            )

            job_link = canonicalize_job_link(
                original_link
            )

            if not job_link:
                continue

            # Remove duplicate jobs

            if job_link in seen_links:
                continue

            seen_links.add(job_link)

            all_jobs.append(
                {
                    "title": job_title,
                    "company": company_name,
                    "link": job_link
                }
            )

    except requests.RequestException as error:

        print(
            "Error while searching for jobs:",
            error
        )


# ============================================================
# MAKE JOBS AVAILABLE TO APP.PY
# ============================================================

jobs = all_jobs


# ============================================================
# FINAL JOB LIST
# ============================================================

print()
print()
print("===================================")
print(
    "TOTAL UNIQUE JOBS:",
    len(jobs)
)
print("===================================")


for job in jobs:

    print()
    print("-----------------------------")

    print(
        "Title:",
        job["title"]
    )

    print(
        "Company:",
        job["company"]
    )

    print(
        "Link:",
        job["link"]
    )


# ============================================================
# GET JOB DESCRIPTION
# ============================================================

def get_job_description(job_link):

    max_attempts = 3

    for attempt in range(
        1,
        max_attempts + 1
    ):

        try:

            print(
                "\nFetching job description..."
            )

            response = session.get(
                job_link,
                timeout=20
            )

            print(
                "Detail Status Code:",
                response.status_code
            )

            # ------------------------------------------------
            # RATE LIMIT
            # ------------------------------------------------

            if response.status_code == 429:

                wait_time = 10 * attempt

                print(
                    "LinkedIn rate limit detected."
                )

                print(
                    f"Waiting {wait_time} seconds before retry..."
                )

                time.sleep(
                    wait_time
                )

                continue

            # ------------------------------------------------
            # OTHER HTTP ERRORS
            # ------------------------------------------------

            if response.status_code != 200:

                print(
                    "Unable to retrieve job page."
                )

                return ""

            # ------------------------------------------------
            # PARSE PAGE
            # ------------------------------------------------

            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )

            # ------------------------------------------------
            # DESCRIPTION SELECTORS
            # ------------------------------------------------

            selectors = [

                "div.show-more-less-html__markup",

                "div.description__text",

                "section.description",

                "div.jobs-description",

                "div.jobs-description__content",

                "article.jobs-description__container",

                "div[data-job-description]",

                "main"
            ]

            description = None

            for selector in selectors:

                description = soup.select_one(
                    selector
                )

                if description:

                    text = description.get_text(
                        " ",
                        strip=True
                    )

                    if len(text) >= 100:

                        return text

            # ------------------------------------------------
            # FALLBACK: META DESCRIPTION
            # ------------------------------------------------

            meta_description = soup.find(
                "meta",
                attrs={
                    "name": "description"
                }
            )

            if meta_description:

                content = meta_description.get(
                    "content",
                    ""
                ).strip()

                if len(content) >= 100:

                    return content

            # ------------------------------------------------
            # FALLBACK: OG DESCRIPTION
            # ------------------------------------------------

            og_description = soup.find(
                "meta",
                attrs={
                    "property": "og:description"
                }
            )

            if og_description:

                content = og_description.get(
                    "content",
                    ""
                ).strip()

                if len(content) >= 100:

                    return content

            print(
                "No usable job description found."
            )

            return ""

        except requests.RequestException as error:

            print(
                "Error while fetching description:",
                error
            )

            if attempt < max_attempts:

                time.sleep(
                    5 * attempt
                )

            else:

                return ""

    return ""