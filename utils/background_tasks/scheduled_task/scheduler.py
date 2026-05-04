import zoneinfo
from datetime import datetime
from zoneinfo import ZoneInfo

from .daily_pray_reset import daily_pray_reset


from utils.background_tasks.scheduled_task.sched_helper import SchedulerManager
from utils.logs.pretty_log import pretty_log

NYC = zoneinfo.ZoneInfo("America/New_York")  # auto-handles EST/EDT

# 🛠️ Create a SchedulerManager instance with Asia/Manila timezone
scheduler_manager = SchedulerManager(timezone_str="Asia/Manila")


def format_next_run_manila(next_run_time):
    """
    Converts a timezone-aware datetime to Asia/Manila time and returns a readable string.
    """
    if next_run_time is None:
        return "No scheduled run time."
    # Convert to Manila timezone
    manila_tz = ZoneInfo("Asia/Manila")
    manila_time = next_run_time.astimezone(manila_tz)
    # Format as: Sunday, Nov 3, 2025 at 12:00 PM (Asia/Manila)
    return manila_time.strftime("%A, %b %d, %Y at %I:%M %p (Asia/Manila)")


# 🌈─────────────────────────────────────────────────────────────
# 💙 Scheduler Setup (setup_scheduler)
# 🌈─────────────────────────────────────────────────────────────
async def setup_scheduler(bot):

    # Start the scheduler
    scheduler_manager.start()


    # ✨─────────────────────────────────────────────────────────
    # 🤍 DAILY PRAY RESET — Every Midnight (NYC)
    # ✨─────────────────────────────────────────────────────────
    try:
        daily_pray_job = scheduler_manager.add_cron_job(
            func=daily_pray_reset,
            name="daily_pray_reset",
            hour=0,
            minute=0,
            timezone=NYC,  # Schedule based on NYC time (handles EST/EDT)
            args=[bot],
        )
        next_run = daily_pray_job.next_run_time
        pretty_log(
            "ready",
            f"✅ Scheduled 'daily_pray_reset' to run at {format_next_run_manila(next_run)}",
            label="SCHEDULER",
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to schedule 'daily_pray_reset': {e}",
            label="SCHEDULER",
        )