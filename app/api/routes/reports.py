from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import ApiUser, db_session, get_api_user
from app.api.schemas import (
    ActivityOut,
    CategoryBreakdownOut,
    DashboardOut,
    MeOut,
    MonthlyReportOut,
    ReminderOut,
)
from app.config import Settings, get_settings
from app.services import reports as report_service
from app.utils import local_now

router = APIRouter(tags=["reports"])


@router.get("/me", response_model=MeOut)
def get_me(
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
    settings: Settings = Depends(get_settings),
) -> MeOut:
    chat_id = user.chat_id
    pending = report_service.pending_reminder_count(db, settings, chat_id)
    return MeOut(
        chat_id=chat_id,
        display_name=f"Usuario {chat_id}",
        initials=str(chat_id)[-2:],
        pending_reminder_count=pending,
    )


@router.get("/reports/dashboard", response_model=DashboardOut)
def dashboard(
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
    settings: Settings = Depends(get_settings),
) -> DashboardOut:
    summary = report_service.dashboard_summary(db, settings, user.chat_id)
    return DashboardOut(
        balance=summary["balance"],
        total_incomes=summary["total_incomes"],
        total_expenses=summary["total_expenses"],
        expenses_by_category=[
            CategoryBreakdownOut(
                slug=item.slug,
                label=item.label,
                amount=item.amount,
                percent=item.percent,
            )
            for item in summary["expenses_by_category"]
        ],
        upcoming_reminders=[ReminderOut.model_validate(r) for r in summary["upcoming_reminders"]],
        recent_activity=[
            ActivityOut(
                id=item.id,
                kind=item.kind,
                title=item.title,
                subtitle=item.subtitle,
                amount=item.amount,
                date=item.date,
                created_at=item.created_at,
            )
            for item in summary["recent_activity"]
        ],
        pending_reminder_count=summary["pending_reminder_count"],
    )


@router.get("/reports/monthly", response_model=MonthlyReportOut)
def monthly_report(
    user: ApiUser = Depends(get_api_user),
    db: Session = Depends(db_session),
    settings: Settings = Depends(get_settings),
    year: int | None = None,
    month: int | None = None,
) -> MonthlyReportOut:
    today = local_now(settings).date()
    y = year or today.year
    m = month or today.month
    report = report_service.monthly_report(db, user.chat_id, y, m)
    return MonthlyReportOut(
        year=report["year"],
        month=report["month"],
        total_incomes=report["total_incomes"],
        total_expenses=report["total_expenses"],
        balance=report["balance"],
        expenses_by_category=[
            CategoryBreakdownOut(
                slug=item.slug,
                label=item.label,
                amount=item.amount,
                percent=item.percent,
            )
            for item in report["expenses_by_category"]
        ],
    )
