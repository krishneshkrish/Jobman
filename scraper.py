# agent/scraper.py — Job discovery from multiple free sources

import feedparser
import requests
import json
import os
from datetime import datetime, timedelta
from config import JOB_KEYWORDS, JOB_LOCATIONS

CACHE_FILE = "data/applied_jobs.json"

def load_seen_jobs():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}

def save_seen_jobs(seen):
    with open(CACHE_FILE, "w") as f:
        json.dump(seen, f, indent=2)

# ── Source 1: Remotive (Remote jobs, RSS) ──────────────
def fetch_remotive_jobs():
    jobs = []
    for keyword in JOB_KEYWORDS[:3]:  # Limit to avoid rate limiting
        url = f"https://remotive.com/api/remote-jobs?search={keyword.replace(' ', '%20')}&limit=10"
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
                    "apply_type": "link",   # Needs manual apply
                    "source": "Remotive",
                    "posted": job.get("publication_date", ""),
                })
        except Exception as e:
            print(f"[Remotive] Error: {e}")
    return jobs

# ── Source 2: Adzuna API (Free tier available) ──────────
def fetch_adzuna_jobs():
    # Sign up free at developer.adzuna.com
    APP_ID  = "54a8721f"
    APP_KEY = "d967612e8b57bab0fa7e6df29df3b8e0"
    jobs = []

    for keyword in JOB_KEYWORDS[:2]:
        url = (
            f"https://api.adzuna.com/v1/api/jobs/in/search/1"
            f"?app_id={APP_ID}&app_key={APP_KEY}"
            f"&what={keyword.replace(' ', '%20')}"
            f"&where=India&results_per_page=10"
        )
        try:
            res = requests.get(url, timeout=10)
            data = res.json()
            for job in data.get("results", []):
                jobs.append({
                    "id": f"adzuna_{job['id']}",
                    "title": job["title"],
                    "company": job["company"]["display_name"],
                    "location": job["location"]["display_name"],
                    "description": job.get("description", ""),
                    "url": job["redirect_url"],
                    "apply_type": "link",
                    "source": "Adzuna",
                    "posted": job.get("created", ""),
                })
        except Exception as e:
            print(f"[Adzuna] Error: {e}")
    return jobs

# ── Source 3: LinkedIn RSS (Public feed, no login needed) ─
def fetch_linkedin_rss():
    jobs = []
    for keyword in JOB_KEYWORDS[:2]:
        kw = keyword.replace(" ", "%20")
        # LinkedIn public job RSS (may need updating if they change it)
        url = f"https://www.linkedin.com/jobs/search/?keywords={kw}&location=India&f_TPR=r86400"
        # Note: LinkedIn doesn't have a clean RSS. Use jobicy or similar as fallback.
        pass
    return jobs

# ── Source 4: Jobicy RSS (Good for remote) ─────────────
def fetch_jobicy_rss():
    jobs = []
    url = "https://jobicy.com/?feed=job_feed&job_categories=dev&job_types=full-time"
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:20]:
            jobs.append({
                "id": f"jobicy_{entry.get('id', entry.link)}",
                "title": entry.title,
                "company": entry.get("author", "Unknown"),
                "location": "Remote",
                "description": entry.get("summary", ""),
                "url": entry.link,
                "apply_type": "link",
                "source": "Jobicy",
                "posted": entry.get("published", ""),
            })
    except Exception as e:
        print(f"[Jobicy] Error: {e}")
    return jobs

# ── Main scraper function ───────────────────────────────
def scrape_all_jobs():
    print("[Scraper] Starting job discovery...")
    seen = load_seen_jobs()
    all_jobs = []

    # Fetch from all sources
    sources = [
        fetch_remotive_jobs,
        fetch_adzuna_jobs,
        fetch_jobicy_rss,
    ]

    for fetch_fn in sources:
        jobs = fetch_fn()
        print(f"[Scraper] {fetch_fn.__name__}: {len(jobs)} jobs found")
        all_jobs.extend(jobs)

    # Deduplicate against already seen/applied
    new_jobs = [j for j in all_jobs if j["id"] not in seen]
    print(f"[Scraper] {len(new_jobs)} new jobs (filtered {len(all_jobs) - len(new_jobs)} seen)")

    return new_jobs, seen
