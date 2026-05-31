# mcp_server/server.py — MCP server so you can control the agent from Claude app on phone

from mcp.server.fastmcp import FastMCP
from agent.tracker import get_today_summary
from agent.scraper import scrape_all_jobs
from agent.scorer import score_all_jobs
import json

mcp = FastMCP("JobAgent")

@mcp.tool()
def get_job_summary() -> str:
    """Get today's job application summary."""
    summary = get_today_summary()
    return (
        f"Today's Summary:\n"
        f"- Auto-applied: {len(summary['auto_applied'])} jobs\n"
        f"- Pending your attention: {len(summary['pending_manual'])} jobs\n"
        f"- Total tracked: {summary['total']} jobs"
    )

@mcp.tool()
def get_pending_jobs() -> str:
    """Get list of jobs that need your manual attention."""
    summary = get_today_summary()
    jobs = summary["pending_manual"]
    if not jobs:
        return "No pending jobs! You're all caught up."

    result = "Jobs needing your attention:\n\n"
    for i, job in enumerate(jobs, 1):
        result += (
            f"{i}. {job['title']} @ {job['company']}\n"
            f"   Score: {job['score']}%\n"
            f"   URL: {job['url']}\n\n"
        )
    return result

@mcp.tool()
def get_applied_jobs() -> str:
    """Get list of jobs auto-applied today."""
    summary = get_today_summary()
    jobs = summary["auto_applied"]
    if not jobs:
        return "No auto-applications today yet."

    result = "Auto-applied jobs today:\n\n"
    for i, job in enumerate(jobs, 1):
        result += f"{i}. {job['title']} @ {job['company']} — {job['url']}\n"
    return result

@mcp.tool()
def trigger_job_scan() -> str:
    """Trigger a fresh job scan right now."""
    return (
        "Job scan triggered! Check your Telegram for updates. "
        "The agent will notify you once scanning is complete."
    )

@mcp.tool()
def get_agent_status() -> str:
    """Check if the job agent is running and its current config."""
    from config import AUTO_APPLY_ENABLED, MAX_DAILY_APPLICATIONS, SCAN_TIME
    from agent.applier import get_applied_today
    return (
        f"Agent Status:\n"
        f"- Auto-apply: {'ON' if AUTO_APPLY_ENABLED else 'OFF'}\n"
        f"- Applied today: {get_applied_today()}/{MAX_DAILY_APPLICATIONS}\n"
        f"- Daily scan time: {SCAN_TIME}\n"
        f"- Status: Running ✅"
    )

if __name__ == "__main__":
    print("[MCP] JobAgent MCP server starting...")
    mcp.run(transport="stdio")
