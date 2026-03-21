from collections import defaultdict
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.schemas.request_models import (
    LanguagePerformanceSortBy,
    ModelPerformanceSortBy,
    PromptFeatureSortBy,
    SortOrder,
    TopPromptsSortBy,
)
from app.services.db_service import DatabaseNotInitializedError, db_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _error_response(status_code: int, code: str, message: str) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={
            "timestamp": _now_iso(),
            "status": "error",
            "error": {"code": code, "message": message},
        },
    )


@router.get("/model-performance")
def model_performance(
    limit: int = Query(default=10, ge=1, le=100),
    sort_by: ModelPerformanceSortBy = Query(default=ModelPerformanceSortBy.avg_success),
    order: SortOrder = Query(default=SortOrder.desc),
):
    sort_column = {
        ModelPerformanceSortBy.avg_success: "avg_success",
        ModelPerformanceSortBy.attempts: "attempts",
        ModelPerformanceSortBy.median_success: "median_success",
    }[sort_by]

    sql = f"""
        SELECT
            model_name,
            attempts,
            avg_success,
            median_success
        FROM mv_model_performance_arena
        ORDER BY {sort_column} {order.value.upper()}, model_name ASC
        LIMIT %s
    """

    try:
        rows = db_service.fetch_all(sql, (limit,))
    except DatabaseNotInitializedError as exc:
        _error_response(503, "SERVICE_UNAVAILABLE", str(exc))
    except Exception as exc:
        _error_response(503, "DATABASE_ERROR", str(exc))

    data = []
    for idx, row in enumerate(rows, start=1):
        avg_success = float(row["avg_success"]) if row["avg_success"] is not None else 0.0
        median_success = float(row["median_success"]) if row["median_success"] is not None else 0.0
        data.append(
            {
                "model_name": row["model_name"],
                "attempts": int(row["attempts"]),
                "avg_success": avg_success,
                "median_success": median_success,
                "rank": idx,
                "success_rate_pct": round(avg_success * 100, 2),
            }
        )

    return {
        "timestamp": _now_iso(),
        "status": "success",
        "data": {
            "total_count": len(data),
            "data": data,
        },
    }


@router.get("/language-performance")
def language_performance(
    limit: int = Query(default=20, ge=1, le=200),
    sort_by: LanguagePerformanceSortBy = Query(default=LanguagePerformanceSortBy.success_rate),
    order: SortOrder = Query(default=SortOrder.desc),
):
    sort_column = {
        LanguagePerformanceSortBy.success_rate: "success_rate",
        LanguagePerformanceSortBy.prompts: "prompts",
        LanguagePerformanceSortBy.median_success: "median_success",
    }[sort_by]

    sql = f"""
        SELECT
            programming_lang,
            prompts,
            success_rate,
            median_success
        FROM mv_language_performance
        ORDER BY {sort_column} {order.value.upper()}, programming_lang ASC
        LIMIT %s
    """

    try:
        rows = db_service.fetch_all(sql, (limit,))
    except DatabaseNotInitializedError as exc:
        _error_response(503, "SERVICE_UNAVAILABLE", str(exc))
    except Exception as exc:
        _error_response(503, "DATABASE_ERROR", str(exc))

    data = []
    for row in rows:
        success_rate = float(row["success_rate"]) if row["success_rate"] is not None else 0.0
        if success_rate >= 0.75:
            difficulty = "easy"
        elif success_rate >= 0.5:
            difficulty = "medium"
        else:
            difficulty = "hard"

        data.append(
            {
                "programming_language": row["programming_lang"],
                "total_prompts": int(row["prompts"]),
                "success_rate": success_rate,
                "median_success": float(row["median_success"]) if row["median_success"] is not None else 0.0,
                "difficulty_level": difficulty,
            }
        )

    return {
        "timestamp": _now_iso(),
        "status": "success",
        "data": {
            "total_languages": len(data),
            "data": data,
        },
    }


@router.get("/prompt-features")
def prompt_features(
    limit: int = Query(default=8, ge=1, le=20),
    min_samples: int = Query(default=10, ge=1),
    sort_by: PromptFeatureSortBy = Query(default=PromptFeatureSortBy.avg_success),
    order: SortOrder = Query(default=SortOrder.desc),
):
    sort_column = {
        PromptFeatureSortBy.avg_success: "avg_success",
        PromptFeatureSortBy.cnt: "cnt",
        PromptFeatureSortBy.median_success: "median_success",
    }[sort_by]

    sql = f"""
        SELECT
            contains_examples,
            contains_code,
            contains_constraints,
            cnt,
            avg_success,
            median_success
        FROM mv_prompt_feature_impact
        WHERE cnt >= %s
        ORDER BY {sort_column} {order.value.upper()}, cnt DESC
        LIMIT %s
    """

    try:
        rows = db_service.fetch_all(sql, (min_samples, limit))
    except DatabaseNotInitializedError as exc:
        _error_response(503, "SERVICE_UNAVAILABLE", str(exc))
    except Exception as exc:
        _error_response(503, "DATABASE_ERROR", str(exc))

    data = []
    if not rows:
        insights = {"best_combination": None, "worst_combination": None, "confidence": "low"}
    else:
        ranked = sorted(rows, key=lambda x: float(x["avg_success"]), reverse=True)
        best = ranked[0]
        worst = ranked[-1]

        def describe(row: dict) -> str:
            labels = []
            if row["contains_examples"]:
                labels.append("examples")
            if row["contains_code"]:
                labels.append("code")
            if row["contains_constraints"]:
                labels.append("constraints")
            return " + ".join(labels) if labels else "no features"

        insights = {
            "best_combination": describe(best),
            "worst_combination": describe(worst),
            "confidence": "medium" if int(best["cnt"]) >= 100 else "low",
        }

    for row in rows:
        ex = bool(row["contains_examples"])
        co = bool(row["contains_code"])
        cn = bool(row["contains_constraints"])
        combo_id = f"{'EX' if ex else 'NE'}_{'CO' if co else 'NC'}_{'CT' if cn else 'NT'}"
        data.append(
            {
                "features": {
                    "contains_examples": ex,
                    "contains_code": co,
                    "contains_constraints": cn,
                },
                "sample_count": int(row["cnt"]),
                "avg_success": float(row["avg_success"]) if row["avg_success"] is not None else 0.0,
                "median_success": float(row["median_success"]) if row["median_success"] is not None else 0.0,
                "feature_combination_id": combo_id,
            }
        )

    return {
        "timestamp": _now_iso(),
        "status": "success",
        "data": {
            "data": data,
            "insights": insights,
        },
    }


@router.get("/top-prompts")
def top_prompts(
    limit: int = Query(default=10, ge=1, le=100),
    min_uses: int = Query(default=5, ge=1),
    sort_by: TopPromptsSortBy = Query(default=TopPromptsSortBy.avg_success),
    order: SortOrder = Query(default=SortOrder.desc),
):
    sort_column = {
        TopPromptsSortBy.avg_success: "avg_success",
        TopPromptsSortBy.uses: "uses",
        TopPromptsSortBy.median_success: "median_success",
    }[sort_by]

    sql = f"""
        SELECT
            prompt_hash,
            prompt_text,
            uses,
            avg_success,
            median_success
        FROM mv_top_prompt_templates
        WHERE uses >= %s
        ORDER BY {sort_column} {order.value.upper()}, uses DESC
        LIMIT %s
    """

    total_sql = "SELECT COUNT(*) AS total_count FROM mv_top_prompt_templates WHERE uses >= %s"

    try:
        rows = db_service.fetch_all(sql, (min_uses, limit))
        total = db_service.fetch_one(total_sql, (min_uses,)) or {"total_count": 0}
    except DatabaseNotInitializedError as exc:
        _error_response(503, "SERVICE_UNAVAILABLE", str(exc))
    except Exception as exc:
        _error_response(503, "DATABASE_ERROR", str(exc))

    top_templates = []
    for idx, row in enumerate(rows, start=1):
        avg_success = float(row["avg_success"]) if row["avg_success"] is not None else 0.0
        prompt_text = row["prompt_text"] or ""
        top_templates.append(
            {
                "prompt_hash": row["prompt_hash"],
                "prompt_preview": prompt_text[:160],
                "full_prompt_available": bool(prompt_text),
                "usage_count": int(row["uses"]),
                "avg_success": avg_success,
                "median_success": float(row["median_success"]) if row["median_success"] is not None else 0.0,
                "success_rate_pct": round(avg_success * 100, 2),
                "rank": idx,
            }
        )

    return {
        "timestamp": _now_iso(),
        "status": "success",
        "data": {
            "total_templates": int(total["total_count"]),
            "top_templates": top_templates,
        },
    }


@router.get("/model-performance-timeline")
def model_performance_timeline(
    model_name: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    start_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
):
    if (start_date and not end_date) or (end_date and not start_date):
        _error_response(400, "INVALID_PARAMETER", "start_date and end_date must be provided together")

    filters = []
    params: list = []

    if start_date and end_date:
        filters.append("day BETWEEN %s::date AND %s::date")
        params.extend([start_date, end_date])
    else:
        since = (datetime.now(tz=timezone.utc) - timedelta(days=days)).date().isoformat()
        filters.append("day >= %s::date")
        params.append(since)

    if model_name:
        filters.append("model_name = %s")
        params.append(model_name)

    where_clause = " AND ".join(filters)

    sql = f"""
        SELECT
            day,
            model_name,
            attempts,
            avg_success,
            median_success
        FROM mv_daily_model_success
        WHERE {where_clause}
        ORDER BY day ASC, model_name ASC
    """

    try:
        rows = db_service.fetch_all(sql, tuple(params))
    except DatabaseNotInitializedError as exc:
        _error_response(503, "SERVICE_UNAVAILABLE", str(exc))
    except Exception as exc:
        _error_response(503, "DATABASE_ERROR", str(exc))

    grouped: dict[str, list[dict]] = defaultdict(list)
    models: set[str] = set()
    for row in rows:
        day_str = row["day"].isoformat()
        model = row["model_name"]
        models.add(model)
        grouped[day_str].append(
            {
                "model_name": model,
                "attempts": int(row["attempts"]),
                "avg_success": float(row["avg_success"]) if row["avg_success"] is not None else 0.0,
                "median_success": float(row["median_success"]) if row["median_success"] is not None else 0.0,
            }
        )

    ordered_days = sorted(grouped.keys())
    timeline = [{"date": day, "series": grouped[day]} for day in ordered_days]

    return {
        "timestamp": _now_iso(),
        "status": "success",
        "data": {
            "models": sorted(models),
            "date_range": {
                "start": ordered_days[0] if ordered_days else None,
                "end": ordered_days[-1] if ordered_days else None,
            },
            "data": timeline,
        },
    }

@router.post('/admin/refresh-views')
def refresh_views():
    """WebHook to refresh all MatViews after ETL completes."""
    try:
        views = [
            'mv_model_performance_arena', 
            'mv_language_performance', 
            'mv_prompt_feature_impact', 
            'mv_top_prompt_templates', 
            'mv_daily_model_success'
        ]
        with db_service.get_conn() as conn:
            with conn.cursor() as cur:
                for v in views:
                    cur.execute(f"REFRESH MATERIALIZED VIEW {v};")
            conn.commit()
        return {'timestamp': _now_iso(), 'status': 'success', 'data': {'message': 'Materialized views refreshed'}}
    except Exception as exc:
        _error_response(500, 'REFRESH_ERROR', str(exc))

@router.get('/clusters')
def get_prompt_clusters():
    # Example logic or pull from db if we exported to DB, but KMeans clusters predict via ML Service natively per prompt.
    return {'status': 'success', 'data': 'Clusters loaded natively in ML service.'}
@router.post('/admin/refresh-views')
def refresh_views():
    try:
        views = ['mv_model_performance_arena', 'mv_language_performance', 'mv_prompt_feature_impact', 'mv_top_prompt_templates', 'mv_daily_model_success']
        with db_service.get_conn() as conn:
            with conn.cursor() as cur:
                for v in views:
                    cur.execute(f'REFRESH MATERIALIZED VIEW {v}')
            conn.commit()
        return {'status': 'success', 'message': 'All materialized views refreshed perfectly.'}
    except Exception as e:
        _error_response(500, 'REFRESH_ERROR', str(e))

