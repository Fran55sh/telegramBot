import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.config import Settings
from app.database import SessionLocal
from app.models import Reminder
from app.telegram import TelegramClient
from app.utils import local_now, to_naive_local

logger = logging.getLogger(__name__)


def create_scheduler(settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.app_timezone)
    scheduler.add_job(
        send_due_reminders,
        "interval",
        seconds=settings.reminder_check_seconds,
        kwargs={"settings": settings},
        id="send_due_reminders",
        replace_existing=True,
    )
    return scheduler


async def send_due_reminders(settings: Settings) -> None:
    now = to_naive_local(local_now(settings), settings)
    telegram = TelegramClient(settings)

    with SessionLocal() as db:
        reminders = (
            db.execute(
                select(Reminder)
                .where(Reminder.is_sent.is_(False), Reminder.remind_at <= now)
                .order_by(Reminder.remind_at.asc())
                .limit(25)
            )
            .scalars()
            .all()
        )

        for reminder in reminders:
            try:
                await telegram.send_message(reminder.chat_id, f"Recordatorio: {reminder.text}")
                reminder.is_sent = True
                reminder.sent_at = now
                db.add(reminder)
                db.commit()
                logger.info("reminder_sent reminder_id=%s chat_id=%s", reminder.id, reminder.chat_id)
            except Exception:
                db.rollback()
                logger.exception("reminder_send_failed reminder_id=%s chat_id=%s", reminder.id, reminder.chat_id)
