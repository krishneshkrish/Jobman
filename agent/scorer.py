# agent/scorer.py — Strict scorer tuned for Krish's profile

import requests
import json
import re
import time
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL

RATE_LIMIT_DELAY = 2

# ── Candidate profile hardcoded for accurate scoring ───
CANDIDATE_PROFILE = """
- Name: Krishnesh
- Experience: ~1 year (Junior level)
- Current Role: Power Platform Developer at NeST Digital, Trivandrum
- Core Skills: Power Apps, Power Automate, Dataverse, Microsoft Teams, Power Platform
- Learning: Python, LangChain, RAG, LLM apps, AI agents, C#, ASP.NET Core
- Built: AI Tutor, AI Chatbot, J.A.R.V.I.S. (local LLM projects), RAG chatbot
- Location: Trivandrum, Kerala, India
- Target: India-based or Remote roles
- Preferred seniority: Junior / Entry-level (0-2 years experience required)
- NOT suitable for: Senior, Staff, Lead, Director, Manager roles
- NOT suitable for: Roles requiring 3+ years experience
- NOT suitable for: Non-tech roles (sales, copywriter, office assistant, etc.)
- NOT suitable for: Roles specific to Brazil, US-only, or requiring local presence outside India
"""

def load_resume():
    with open("data/resume.txt") as f:
        return f.read()

class RateLimitError(Exception):
    def __init__(self, msg, retry_after=30):
        super().__init__(msg)
        self.retry_after = retry_after

def call_openrouter(prompt: str) -> str:
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "X-Title": "JobAgent",
        },
        json={
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        },
        timeout=30,
    )
    if response.status_code == 429:
        retry_after = int(response.headers.get("Retry-After", 30))
        raise RateLimitError(f"Rate limited", retry_after)
    if response.status_code != 200:
        raise Exception(f"OpenRouter error {response.status_code}: {response.text}")
    return response.json()["choices"][0]["message"]["content"]

def score_job(job: dict, resume: str) -> dict:
    prompt = f"""
You are a strict career advisor. Evaluate if this job is a REALISTIC match for this candidate.

## CANDIDATE PROFILE
{CANDIDATE_PROFILE}

## CANDIDATE RESUME
{resume[:1500]}

## JOB POSTING
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Source: {job.get('source', 'unknown')}
Description: {job['description'][:1500]}

## STRICT SCORING RULES
Automatically score 0-20 (skip) if ANY of these are true:
- Job title contains: Senior, Staff, Lead, Director, Manager, Principal, Head, VP, C-level
- Requires 3+ years experience
- Non-tech role (sales, writing, design, HR, support, office work)
- Location is Brazil, Latin America, US-only, or requires physical presence outside India
- Skills mismatch is total (e.g. Ruby, iOS, Android, SAP when candidate has none)

Score 60-79 (notify) if:
- Good skill overlap but 1-2 gaps candidate can address
- India-based or remote role
- Junior/mid level appropriate

Score 80-100 (auto_apply) if:
- Strong match on skills (Power Platform OR AI/LLM/Python)
- India-based or open remote
- Junior level OR experience not strictly enforced
- Candidate has 80%+ of required skills

Return ONLY valid JSON, no markdown:
{{
  "score": <0-100>,
  "match_reasons": ["reason1"],
  "missing_skills": ["skill1"],
  "seniority_match": true/false,
  "location_match": true/false,
  "recommendation": "auto_apply" | "notify" | "skip",
  "one_liner": "why or why not"
}}
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            text = call_openrouter(prompt)
            text = re.sub(r"```json|```", "", text).strip()
            result = json.loads(text)

            job["score"]           = result.get("score", 0)
            job["match_reasons"]   = result.get("match_reasons", [])
            job["missing_skills"]  = result.get("missing_skills", [])
            job["seniority_match"] = result.get("seniority_match", False)
            job["location_match"]  = result.get("location_match", False)
            job["recommendation"]  = result.get("recommendation", "skip")
            job["one_liner"]       = result.get("one_liner", "")
            return job

        except RateLimitError as e:
            print(f"[Scorer] Rate limited. Waiting {e.retry_after}s...")
            time.sleep(e.retry_after)
        except json.JSONDecodeError:
            print(f"[Scorer] JSON parse error for {job['title']}, skipping")
            break
        except Exception as e:
            print(f"[Scorer] Error scoring {job['title']}: {e}")
            break

    job["score"]          = 0
    job["recommendation"] = "skip"
    job["one_liner"]      = "Scoring failed"
    return job

def score_all_jobs(jobs: list) -> dict:
    resume = load_resume()
    auto_apply, notify, skipped = [], [], []

    for i, job in enumerate(jobs):
        print(f"[Scorer] Scoring {i+1}/{len(jobs)}: {job['title']} @ {job['company']}")

        # Location pre-filter — skip bad locations before calling LLM
        loc_verdict = location_prefilter(job)
        if loc_verdict == "skip":
            print(f"[Scorer] Skipping (bad location: {job.get('location')})")
            job["score"] = 0
            job["recommendation"] = "skip"
            job["one_liner"] = f"Location {job.get('location')} not in your target areas"
            skipped.append(job)
            continue

        job = score_job(job, resume)

        if job["recommendation"] == "auto_apply":
            auto_apply.append(job)
        elif job["recommendation"] == "notify":
            notify.append(job)
        else:
            skipped.append(job)

        if i < len(jobs) - 1:
            time.sleep(RATE_LIMIT_DELAY)

    auto_apply.sort(key=lambda x: x["score"], reverse=True)
    notify.sort(key=lambda x: x["score"], reverse=True)

    print(f"[Scorer] Results → Auto: {len(auto_apply)}, Notify: {len(notify)}, Skip: {len(skipped)}")
    return {"auto_apply": auto_apply, "notify": notify, "skipped": skipped}


# ── Location pre-filter (runs BEFORE calling LLM) ──────
def location_prefilter(job: dict) -> str:
    """
    Returns 'skip', 'preferred', or 'acceptable'
    based on job location against config lists.
    Saves API calls by skipping bad locations early.
    """
    from config import SKIP_LOCATIONS, PREFERRED_LOCATIONS, ACCEPTABLE_LOCATIONS
    loc = (job.get("location") or "").lower()

    for bad in SKIP_LOCATIONS:
        if bad.lower() in loc:
            return "skip"

    for good in PREFERRED_LOCATIONS:
        if good.lower() in loc:
            return "preferred"

    for ok in ACCEPTABLE_LOCATIONS:
        if ok.lower() in loc:
            return "acceptable"

    # Unknown location — let LLM decide
    return "unknown"