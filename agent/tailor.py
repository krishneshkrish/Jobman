# agent/tailor.py — OpenRouter rewrites your resume for each job

import requests
import os
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL

def load_resume():
    with open("data/resume.txt") as f:
        return f.read()

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
            "temperature": 0.3,
        },
        timeout=60,
    )
    if response.status_code != 200:
        raise Exception(f"OpenRouter error {response.status_code}: {response.text}")
    return response.json()["choices"][0]["message"]["content"]

def tailor_resume(job: dict) -> str:
    resume = load_resume()

    prompt = f"""
You are an expert resume writer. Tailor the candidate's resume for this specific job.

## BASE RESUME
{resume}

## TARGET JOB
Title: {job['title']}
Company: {job['company']}
Description: {job['description'][:2000]}

## RULES
1. Keep all facts TRUE — do not invent experience or skills
2. Rewrite bullet points to mirror the job description's language and keywords
3. Adjust the professional summary to directly address this role
4. Highlight skills from the JD that the candidate has
5. Keep it to 1 page worth of content
6. Return ONLY the tailored resume text, no explanation
"""

    try:
        return call_openrouter(prompt).strip()
    except Exception as e:
        print(f"[Tailor] Error tailoring for {job['title']}: {e}")
        return load_resume()

def tailor_and_save(job: dict) -> str:
    tailored = tailor_resume(job)
    safe_name = f"{job['title']}_{job['company']}".replace(" ", "_").replace("/", "-")[:50]
    path = f"data/tailored_{safe_name}.txt"

    with open(path, "w") as f:
        f.write(f"TAILORED FOR: {job['title']} @ {job['company']}\n")
        f.write(f"JOB URL: {job['url']}\n")
        f.write(f"MATCH SCORE: {job.get('score', 'N/A')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(tailored)

    print(f"[Tailor] Saved → {path}")
    return path