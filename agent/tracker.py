# agent/tracker.py — Tracks all applications with tailored resume paths

import json
import os
from datetime import datetime

CACHE_FILE = "data/applied_jobs.json"

def log_application(job: dict, status: str = "applied", resume_path: str = None):
    seen = _load_cache()
    seen[job["id"]] = {
        "id": job["id"],
        "title": job["title"],
        "company": job["company"],
        "location": job.get("location", ""),
        "url": job["url"],
        "score": job.get("score", 0),
        "one_liner": job.get("one_liner", ""),
        "status": status,
        "resume_path": resume_path or "",   # ← tailored resume path stored here
        "applied_at": datetime.now().isoformat(),
    }
    _save_cache(seen)
    print(f"[Tracker] Logged: {job['title']} @ {job['company']} → {status}")

def get_today_summary():
    seen = _load_cache()
    today = datetime.now().date().isoformat()
    today_jobs = [
        v for v in seen.values()
        if v.get("applied_at", "").startswith(today)
    ]
    auto_applied    = [j for j in today_jobs if j["status"] == "auto_applied"]
    pending         = [j for j in today_jobs if j["status"] == "pending_manual"]
    return {
        "total": len(today_jobs),
        "auto_applied": auto_applied,
        "pending_manual": pending,
    }

def mark_as_applied(job_id: str):
    seen = _load_cache()
    if job_id in seen:
        seen[job_id]["status"] = "manually_applied"
        seen[job_id]["applied_at"] = datetime.now().isoformat()
        _save_cache(seen)

def _load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {}

def _save_cache(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)