from fastapi import APIRouter

from app.api.routes import categories, expenses, incomes, notes, reminders, reports

api_router = APIRouter(prefix="/api")
api_router.include_router(reports.router)
api_router.include_router(categories.router)
api_router.include_router(expenses.router)
api_router.include_router(incomes.router)
api_router.include_router(reminders.router)
api_router.include_router(notes.router)
