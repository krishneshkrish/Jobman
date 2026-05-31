# agent/applier.py — Playwright handles Easy Apply jobs automatically

from playwright.async_api import async_playwright
import asyncio
from config import MAX_DAILY_APPLICATIONS, AUTO_APPLY_ENABLED
from agent.tracker import log_application

# Daily counter (resets when agent restarts / new day)
_applied_today = 0

async def apply_to_job(job: dict, resume_path: str) -> bool:
    """
    Attempts to auto-apply to a job.
    Returns True if applied, False if needs manual attention.
    """
    global _applied_today

    if not AUTO_APPLY_ENABLED:
        print(f"[Applier] Auto-apply disabled, skipping {job['title']}")
        return False

    if _applied_today >= MAX_DAILY_APPLICATIONS:
        print(f"[Applier] Daily limit ({MAX_DAILY_APPLICATIONS}) reached, stopping.")
        return False

    apply_type = job.get("apply_type", "link")

    # Only attempt auto-apply for known Easy Apply patterns
    if apply_type == "easy_apply_linkedin":
        success = await _linkedin_easy_apply(job, resume_path)
    elif apply_type == "email_apply":
        success = await _email_apply(job, resume_path)
    else:
        # Unknown portal — flag for manual
        print(f"[Applier] Manual apply needed: {job['title']}")
        return False

    if success:
        _applied_today += 1
        log_application(job, status="auto_applied")

    return success

async def _linkedin_easy_apply(job: dict, resume_path: str) -> bool:
    """LinkedIn Easy Apply automation."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(job["url"], timeout=15000)
            await page.wait_for_timeout(2000)

            # Look for Easy Apply button
            easy_apply_btn = page.locator("button:has-text('Easy Apply')")
            if not await easy_apply_btn.is_visible():
                print(f"[Applier] No Easy Apply button found for {job['title']}")
                return False

            await easy_apply_btn.click()
            await page.wait_for_timeout(1500)

            # Handle multi-step form (basic)
            # Step 1: Contact info (usually pre-filled if logged in)
            next_btn = page.locator("button:has-text('Next')")
            if await next_btn.is_visible():
                await next_btn.click()
                await page.wait_for_timeout(1000)

            # Step 2: Resume upload if prompted
            resume_upload = page.locator("input[type='file']")
            if await resume_upload.is_visible():
                await resume_upload.set_input_files(resume_path)
                await page.wait_for_timeout(1000)

            # Final submit
            submit_btn = page.locator("button:has-text('Submit application')")
            if await submit_btn.is_visible():
                await submit_btn.click()
                await page.wait_for_timeout(2000)
                print(f"[Applier] ✅ Applied to {job['title']} @ {job['company']}")
                return True

        except Exception as e:
            print(f"[Applier] Error applying to {job['title']}: {e}")
        finally:
            await browser.close()

    return False

async def _email_apply(job: dict, resume_path: str) -> bool:
    """Apply via email — compose and send."""
    # Implement with Gmail API or smtplib
    # For now, flag as manual
    print(f"[Applier] Email apply not yet automated: {job['title']}")
    return False

def get_applied_today():
    return _applied_today
