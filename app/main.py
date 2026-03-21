from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routes import analytics, insights, health
from app.services.db_service import db_service


def _now_iso() -> str:
      return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@asynccontextmanager
async def lifespan(_: FastAPI):
      db_service.init_pool()
      yield
      db_service.close_pool()

app = FastAPI(
        title="PromptLens API",
        version="1.0",
        lifespan=lifespan)

app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
      if isinstance(exc.detail, dict) and exc.detail.get("status") == "error":
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
      return JSONResponse(
            status_code=exc.status_code,
            content={
                  "timestamp": _now_iso(),
                  "status": "error",
                  "error": {
                        "code": "HTTP_ERROR",
                        "message": str(exc.detail),
                  },
            },
      )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
      return JSONResponse(
            status_code=400,
            content={
                  "timestamp": _now_iso(),
                  "status": "error",
                  "error": {
                        "code": "INVALID_PARAMETER",
                        "message": str(exc),
                  },
            },
      )

# Register routers
app.include_router(analytics.router)
app.include_router(insights.router)
app.include_router(health.router)