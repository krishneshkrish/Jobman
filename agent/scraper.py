# agent/scraper.py — Job discovery from Naukri, LinkedIn, Indeed, Remotive, Jobicy

import feedparser
import requests
import json
import os
import time
from config import JOB_KEYWORDS, KEYWORDS_POWER_PLATFORM, KEYWORDS_AI

CACHE_FILE = "data/applied_jobs.json"

def load_seen_jobs():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}

def save_seen_jobs(seen):
    with open(CACHE_FILE, "w") as f:
        json.dump(seen, f, indent=2)

# ── Source 1: Naukri RSS (India's #1 job board) ────────
def fetch_naukri_jobs():
    jobs = []
    # Naukri exposes job listings via their search URLs
    # We use their JSON API endpoint (unofficial but stable)
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "systemId": "109",
        "appid": "109",
    }

    keywords_to_search = KEYWORDS_POWER_PLATFORM[:4] + KEYWORDS_AI[:4]

    for keyword in keywords_to_search:
        url = (
            f"https://www.naukri.com/jobapi/v3/search"
            f"?noOfResults=10"
            f"&urlType=search_by_keyword"
            f"&searchType=adv"
            f"&keyword={keyword.replace(' ', '%20')}"
            f"&location=india"
            f"&experience=0"
            f"&experience=1"
            f"&jobAge=7"
        )
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                continue
            data = res.json()
            job_list = data.get("jobDetails", [])
            for job in job_list:
                jobs.append({
                    "id": f"naukri_{job.get('jobId', '')}",
                    "title": job.get("title", ""),
                    "company": job.get("companyName", "Unknown"),
                    "location": ", ".join(job.get("placeholders", [{}])[0].get("label", "India").split(",")[:2]) if job.get("placeholders") else "India",
                    "description": job.get("jobDescription", "") or job.get("jobDesc", ""),
                    "url": f"https://www.naukri.com{job.get('jdURL', '')}",
                    "apply_type": "link",
                    "source": "Naukri",
                    "posted": job.get("createdDate", ""),
                    "experience": job.get("experienceText", "0-2 years"),
                })
            time.sleep(1)  # polite delay
        except Exception as e:
            print(f"[Naukri] Error for '{keyword}': {e}")

    print(f"[Scraper] fetch_naukri_jobs: {len(jobs)} jobs found")
    return jobs

# ── Source 2: LinkedIn Jobs (public RSS feed) ──────────
def fetch_linkedin_jobs():
    jobs = []
    keywords_to_search = KEYWORDS_POWER_PLATFORM[:3] + KEYWORDS_AI[:3]

    for keyword in keywords_to_search:
        kw = keyword.replace(" ", "%20")
        # LinkedIn public job search (no login required for listing)
        url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
            f"?keywords={kw}"
            f"&location=India"
            f"&f_TPR=r604800"   # last 7 days
            f"&f_E=1,2"         # entry + associate level
            f"&start=0"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                continue

            # LinkedIn returns HTML cards, parse job IDs from them
            from html.parser import HTMLParser

            class LinkedInParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.jobs = []
                    self.current_job = {}
                    self.capture = None

                def handle_starttag(self, tag, attrs):
                    attrs = dict(attrs)
                    if tag == "div" and "data-entity-urn" in attrs:
                        urn = attrs["data-entity-urn"]
                        job_id = urn.split(":")[-1]
                        self.current_job = {"id": f"linkedin_{job_id}", "job_id": job_id}
                    if tag == "a" and "href" in attrs and "/jobs/view/" in attrs["href"]:
                        self.current_job["url"] = attrs["href"].split("?")[0]
                        self.capture = "title"
                    if tag == "h3":
                        self.capture = "title"
                    if tag == "h4":
                        self.capture = "company"

                def handle_data(self, data):
                    data = data.strip()
                    if not data:
                        return
                    if self.capture == "title" and "title" not in self.current_job:
                        self.current_job["title"] = data
                        self.capture = None
                    elif self.capture == "company" and "company" not in self.current_job:
                        self.current_job["company"] = data
                        self.capture = None

                def handle_endtag(self, tag):
                    if tag == "li" and self.current_job.get("title"):
                        self.jobs.append(self.current_job.copy())
                        self.current_job = {}

            parser = LinkedInParser()
            parser.feed(res.text)

            for j in parser.jobs:
                if not j.get("url"):
                    j["url"] = f"https://www.linkedin.com/jobs/view/{j.get('job_id', '')}"
                jobs.append({
                    "id": j["id"],
                    "title": j.get("title", keyword),
                    "company": j.get("company", "Unknown"),
                    "location": "India",
                    "description": f"LinkedIn job for {keyword}. Visit URL for full description.",
                    "url": j.get("url", ""),
                    "apply_type": "easy_apply_linkedin",
                    "source": "LinkedIn",
                    "posted": "",
                    "experience": "0-2 years",
                })
            time.sleep(1.5)
        except Exception as e:
            print(f"[LinkedIn] Error for '{keyword}': {e}")

    print(f"[Scraper] fetch_linkedin_jobs: {len(jobs)} jobs found")
    return jobs

# ── Source 3: Indeed India (RSS) ───────────────────────
def fetch_indeed_jobs():
    jobs = []
    keywords_to_search = KEYWORDS_POWER_PLATFORM[:3] + KEYWORDS_AI[:3]

    for keyword in keywords_to_search:
        kw = keyword.replace(" ", "+")
        url = f"https://in.indeed.com/rss?q={kw}&l=India&fromage=7&sort=date"
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            feed = feedparser.parse(url, request_headers=headers)
            for entry in feed.entries[:8]:
                jobs.append({
                    "id": f"indeed_{abs(hash(entry.link))}",
                    "title": entry.title,
                    "company": entry.get("source", {}).get("value", "Unknown"),
                    "location": "India",
                    "description": entry.get("summary", ""),
                    "url": entry.link,
                    "apply_type": "link",
                    "source": "Indeed",
                    "posted": entry.get("published", ""),
                    "experience": "0-2 years",
                })
            time.sleep(1)
        except Exception as e:
            print(f"[Indeed] Error for '{keyword}': {e}")

    print(f"[Scraper] fetch_indeed_jobs: {len(jobs)} jobs found")
    return jobs

# ── Source 4: Remotive (keep for remote roles) ─────────
def fetch_remotive_jobs():
    jobs = []
    # Only search AI/tech keywords on Remotive — it's remote-first
    for keyword in KEYWORDS_AI[:3]:
        url = f"https://remotive.com/api/remote-jobs?search={keyword.replace(' ', '%20')}&limit=8"
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            for job in data.get("jobs", []):
                jobs.append({
                    "id": f"remotive_{job['id']}",
                    "title": job["title"],
                    "company": job["company_name"],
                    "location": job.get("candidate_required_location", "Remote"),
                    "description": job.get("description", ""),
                    "url": job["url"],
                    "apply_type": "link",
                    "source": "Remotive",
                    "posted": job.get("publication_date", ""),
                    "experience": "any",
                })
        except Exception as e:
            print(f"[Remotive] Error: {e}")

    print(f"[Scraper] fetch_remotive_jobs: {len(jobs)} jobs found")
    return jobs

# ── Main scraper ───────────────────────────────────────
def scrape_all_jobs():
    print("[Scraper] Starting job discovery...")
    seen = load_seen_jobs()
    all_jobs = []

    sources = [
        fetch_naukri_jobs,
        fetch_linkedin_jobs,
        fetch_indeed_jobs,
        fetch_remotive_jobs,
    ]

    for fetch_fn in sources:
        try:
            jobs = fetch_fn()
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[Scraper] {fetch_fn.__name__} failed: {e}")

    # Deduplicate by ID
    seen_ids = set()
    unique_jobs = []
    for job in all_jobs:
        if job["id"] not in seen_ids and job["id"] not in seen:
            seen_ids.add(job["id"])
            unique_jobs.append(job)

    print(f"[Scraper] {len(unique_jobs)} new jobs (filtered {len(all_jobs) - len(unique_jobs)} duplicates/seen)")
    return unique_jobs, seen