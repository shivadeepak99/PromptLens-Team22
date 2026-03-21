from datetime import datetime, timezone

from fastapi import APIRouter

from app.services.db_service import db_service

router = APIRouter()


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

@router.get("/health")
def health_check():
    try:
        db_service.fetch_one("SELECT 1 AS ok")
        return {
            "timestamp": _now_iso(),
            "status": "success",
            "data": {"service": "healthy", "database": "connected"},
        }
    except Exception as exc:
        return {
            "timestamp": _now_iso(),
            "status": "error",
            "error": {"code": "DATABASE_ERROR", "message": str(exc)},
        }