# agent/applier.py — Apply logic with Railway/cloud detection

import os
import asyncio
from config import MAX_DAILY_APPLICATIONS, AUTO_APPLY_ENABLED
from agent.tracker import log_application

_applied_today = 0

def is_cloud_environment():
    """Detect if running on Railway or other cloud (no browser available)."""
    return os.environ.get("RAILWAY_ENVIRONMENT") is not None or \
           os.environ.get("RAILWAY_PROJECT_ID") is not None

async def apply_to_job(job: dict, resume_path: str) -> bool:
    global _applied_today

    if not AUTO_APPLY_ENABLED:
        return False

    if _applied_today >= MAX_DAILY_APPLICATIONS:
        print(f"[Applier] Daily limit reached.")
        return False

    # On Railway/cloud — no browser available, skip auto-apply
    if is_cloud_environment():
        print(f"[Applier] Cloud env detected — skipping browser apply for {job['title']}")
        return False

    apply_type = job.get("apply_type", "link")

    if apply_type == "easy_apply_linkedin":
        success = await _linkedin_easy_apply(job, resume_path)
    else:
        print(f"[Applier] Manual apply needed: {job['title']}")
        return False

    if success:
        _applied_today += 1
    return success

async def _linkedin_easy_apply(job: dict, resume_path: str) -> bool:
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                await page.goto(job["url"], timeout=15000)
                await page.wait_for_timeout(2000)
                easy_apply_btn = page.locator("button:has-text('Easy Apply')")
                if not await easy_apply_btn.is_visible():
                    return False
                await easy_apply_btn.click()
                await page.wait_for_timeout(1500)
                submit_btn = page.locator("button:has-text('Submit application')")
                if await submit_btn.is_visible():
                    await submit_btn.click()
                    await page.wait_for_timeout(2000)
                    print(f"[Applier] ✅ Applied to {job['title']} @ {job['company']}")
                    return True
            except Exception as e:
                print(f"[Applier] Error: {e}")
            finally:
                await browser.close()
    except ImportError:
        print("[Applier] Playwright not available")
    return False

def get_applied_today():
    return _applied_today