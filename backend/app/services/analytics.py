from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd

from app.models import Booking

REVENUE_STATUSES = {"confirmed", "completed"}

POSITIVE_WORDS = {
    "amazing",
    "awesome",
    "best",
    "clean",
    "comfortable",
    "easy",
    "excellent",
    "friendly",
    "good",
    "great",
    "helpful",
    "love",
    "perfect",
    "quick",
    "smooth",
    "spacious",
    "supportive",
    "value",
}

NEGATIVE_WORDS = {
    "bad",
    "crowded",
    "delay",
    "dirty",
    "expensive",
    "hard",
    "issue",
    "late",
    "noisy",
    "poor",
    "problem",
    "slow",
    "small",
    "terrible",
    "worst",
}

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "i",
    "in",
    "is",
    "it",
    "my",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "very",
    "was",
    "we",
    "with",
}

TOPIC_KEYWORDS = {
    "pricing": {"price", "value", "cost", "expensive", "cheap", "pricing"},
    "facility": {"clean", "ac", "parking", "wifi", "seating", "room", "court", "studio"},
    "experience": {"friendly", "staff", "service", "support", "booking", "smooth", "quick"},
    "location": {"location", "locality", "metro", "traffic", "access"},
}


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value)


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 2)


def _build_base_dataframe(bookings: list[Booking]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for booking in bookings:
        status_value = booking.status.value if hasattr(booking.status, "value") else str(booking.status)
        rows.append(
            {
                "booking_id": str(booking.id),
                "user_id": str(booking.user_id),
                "space_id": str(booking.space_id),
                "space_type": booking.space.type.value if booking.space and booking.space.type else "unknown",
                "locality": booking.space.locality if booking.space and booking.space.locality else "unknown",
                "status": status_value,
                "total_amount": _to_float(booking.total_amount),
                "booking_date": pd.to_datetime(booking.booking_date),
                "created_at": pd.to_datetime(booking.created_at),
            }
        )

    if not rows:
        return pd.DataFrame(
            columns=[
                "booking_id",
                "user_id",
                "space_id",
                "space_type",
                "locality",
                "status",
                "total_amount",
                "booking_date",
                "created_at",
                "is_revenue",
            ]
        )

    df = pd.DataFrame(rows)
    df["is_revenue"] = df["status"].isin(REVENUE_STATUSES)
    return df


def _daily_revenue_frame(confirmed_df: pd.DataFrame) -> pd.DataFrame:
    if confirmed_df.empty:
        return pd.DataFrame(columns=["booking_date", "revenue", "bookings"])

    daily = (
        confirmed_df.groupby("booking_date", as_index=False)
        .agg(revenue=("total_amount", "sum"), bookings=("booking_id", "count"))
        .sort_values("booking_date")
    )

    min_date = daily["booking_date"].min()
    max_date = daily["booking_date"].max()
    full_range = pd.date_range(min_date, max_date, freq="D")

    return (
        daily.set_index("booking_date")
        .reindex(full_range, fill_value=0)
        .rename_axis("booking_date")
        .reset_index()
    )


def _linear_regression(y_values: list[float]) -> tuple[float, float, float]:
    n = len(y_values)
    if n == 0:
        return 0.0, 0.0, 0.0
    if n == 1:
        return 0.0, y_values[0], max(y_values[0] * 0.25, 1.0)

    t_values = list(range(n))
    t_mean = sum(t_values) / n
    y_mean = sum(y_values) / n

    var_t = sum((t - t_mean) ** 2 for t in t_values)
    if var_t == 0:
        slope = 0.0
    else:
        cov_ty = sum((t - t_mean) * (y - y_mean) for t, y in zip(t_values, y_values, strict=False))
        slope = cov_ty / var_t

    intercept = y_mean - slope * t_mean
    residuals = [y - (intercept + slope * t) for t, y in zip(t_values, y_values, strict=False)]
    residual_std = math.sqrt(sum(r**2 for r in residuals) / n)
    return slope, intercept, residual_std


def _forecast_revenue(daily_df: pd.DataFrame, horizon_days: int = 14) -> tuple[list[dict[str, Any]], str]:
    if daily_df.empty:
        today = date.today()
        default = [
            {
                "date": (today + timedelta(days=i)).isoformat(),
                "predicted_revenue": 0.0,
                "lower": 0.0,
                "upper": 0.0,
            }
            for i in range(1, horizon_days + 1)
        ]
        return default, "low"

    y_values = [float(value) for value in daily_df["revenue"].tolist()]
    n = len(y_values)
    slope, intercept, residual_std = _linear_regression(y_values)

    average_revenue = max(sum(y_values) / max(n, 1), 1.0)
    residual_band = max(residual_std, average_revenue * (0.2 if n >= 30 else 0.35))

    weekday_df = daily_df.copy()
    weekday_df["weekday"] = weekday_df["booking_date"].dt.weekday
    weekday_avg = weekday_df.groupby("weekday")["revenue"].mean().to_dict()
    weekday_factor = {
        weekday: min(max((value / average_revenue) if average_revenue else 1.0, 0.65), 1.4)
        for weekday, value in weekday_avg.items()
    }

    last_date = daily_df["booking_date"].max().date()
    forecasts: list[dict[str, Any]] = []

    for step in range(1, horizon_days + 1):
        index_value = n - 1 + step
        trend_value = intercept + slope * index_value
        future_date = last_date + timedelta(days=step)
        seasonal = weekday_factor.get(future_date.weekday(), 1.0)

        predicted = max(0.0, trend_value * seasonal)
        if n < 10:
            predicted = (predicted * 0.5) + (average_revenue * 0.5)

        lower = max(0.0, predicted - residual_band)
        upper = predicted + residual_band

        forecasts.append(
            {
                "date": future_date.isoformat(),
                "predicted_revenue": round(predicted, 2),
                "lower": round(lower, 2),
                "upper": round(upper, 2),
            }
        )

    variability = residual_std / average_revenue if average_revenue else 1.0
    if n >= 90 and variability <= 0.7:
        confidence = "high"
    elif n >= 30 and variability <= 1.1:
        confidence = "medium"
    else:
        confidence = "low"

    return forecasts, confidence


def _monthly_revenue_frame(confirmed_df: pd.DataFrame) -> pd.DataFrame:
    if confirmed_df.empty:
        return pd.DataFrame(columns=["month", "revenue", "bookings", "growth_pct"])

    monthly = (
        confirmed_df.assign(month=confirmed_df["booking_date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)
        .agg(revenue=("total_amount", "sum"), bookings=("booking_id", "count"))
        .sort_values("month")
    )

    growth_values = [None]
    for i in range(1, len(monthly)):
        previous = float(monthly.iloc[i - 1]["revenue"])
        current = float(monthly.iloc[i]["revenue"])
        if previous <= 0:
            growth_values.append(None)
        else:
            growth_values.append(round(((current - previous) / previous) * 100, 2))
    monthly["growth_pct"] = growth_values
    return monthly


def _tier_for_user(recency_days: int, frequency: int, revenue: float) -> str:
    if frequency >= 8 and recency_days <= 30:
        return "champions"
    if frequency >= 4 and recency_days <= 60:
        return "loyal"
    if recency_days > 90 and frequency <= 2:
        return "dormant"
    if recency_days > 60:
        return "at_risk"
    if revenue >= 5000:
        return "high_value"
    return "new"


def _customer_segments(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []

    today = pd.Timestamp(date.today())
    stats = (
        df.groupby("user_id", as_index=False)
        .agg(
            total_bookings=("booking_id", "count"),
            successful_bookings=("is_revenue", "sum"),
            revenue=("total_amount", lambda values: float(values[df.loc[values.index, "is_revenue"]].sum())),
            last_booking=("booking_date", "max"),
        )
    )

    stats["recency_days"] = (today - stats["last_booking"]).dt.days
    stats["tier"] = stats.apply(
        lambda row: _tier_for_user(int(row["recency_days"]), int(row["successful_bookings"]), float(row["revenue"])),
        axis=1,
    )

    grouped = (
        stats.groupby("tier", as_index=False)
        .agg(
            users=("user_id", "count"),
            revenue=("revenue", "sum"),
            avg_recency_days=("recency_days", "mean"),
            avg_successful_bookings=("successful_bookings", "mean"),
        )
        .sort_values(["revenue", "users"], ascending=False)
    )

    return [
        {
            "segment": row["tier"],
            "users": int(row["users"]),
            "revenue": round(float(row["revenue"]), 2),
            "avg_recency_days": round(float(row["avg_recency_days"]), 1),
            "avg_successful_bookings": round(float(row["avg_successful_bookings"]), 2),
        }
        for _, row in grouped.iterrows()
    ]


def _segment_by_dimension(df: pd.DataFrame, dimension: str, total_revenue: float, limit: int | None = None) -> list[dict[str, Any]]:
    if df.empty:
        return []

    grouped = (
        df.groupby(dimension, as_index=False)
        .agg(revenue=("total_amount", "sum"), bookings=("booking_id", "count"))
        .sort_values("revenue", ascending=False)
    )

    if limit is not None:
        grouped = grouped.head(limit)

    label_key = "segment"
    return [
        {
            label_key: str(row[dimension]),
            "revenue": round(float(row["revenue"]), 2),
            "bookings": int(row["bookings"]),
            "share_pct": _safe_pct(float(row["revenue"]), total_revenue),
        }
        for _, row in grouped.iterrows()
    ]


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[a-zA-Z]+", text.lower())]


def _review_nlp(bookings: list[Booking]) -> dict[str, Any]:
    comments: list[str] = []
    ratings: list[int] = []

    for booking in bookings:
        if booking.review and booking.review.comment:
            comments.append(booking.review.comment)
            ratings.append(int(booking.review.rating))

    if not comments:
        return {
            "review_sentiment": {
                "positive_pct": 0.0,
                "neutral_pct": 0.0,
                "negative_pct": 0.0,
                "sample_size": 0,
                "average_rating": 0.0,
            },
            "top_keywords": [],
            "topic_breakdown": [],
        }

    sentiment_counter: Counter[str] = Counter()
    keyword_counter: Counter[str] = Counter()
    topic_counter: defaultdict[str, int] = defaultdict(int)

    for comment in comments:
        tokens = _tokenize(comment)
        positive_hits = sum(1 for token in tokens if token in POSITIVE_WORDS)
        negative_hits = sum(1 for token in tokens if token in NEGATIVE_WORDS)

        if positive_hits > negative_hits:
            sentiment_counter["positive"] += 1
        elif negative_hits > positive_hits:
            sentiment_counter["negative"] += 1
        else:
            sentiment_counter["neutral"] += 1

        for token in tokens:
            if len(token) < 3 or token in STOPWORDS:
                continue
            keyword_counter[token] += 1
            for topic, topic_words in TOPIC_KEYWORDS.items():
                if token in topic_words:
                    topic_counter[topic] += 1

    sample_size = len(comments)
    top_keywords = [
        {"keyword": keyword, "count": count}
        for keyword, count in keyword_counter.most_common(12)
    ]

    topic_breakdown = [
        {"topic": topic, "mentions": mentions}
        for topic, mentions in sorted(topic_counter.items(), key=lambda item: item[1], reverse=True)
    ]

    return {
        "review_sentiment": {
            "positive_pct": _safe_pct(sentiment_counter["positive"], sample_size),
            "neutral_pct": _safe_pct(sentiment_counter["neutral"], sample_size),
            "negative_pct": _safe_pct(sentiment_counter["negative"], sample_size),
            "sample_size": sample_size,
            "average_rating": round(sum(ratings) / max(len(ratings), 1), 2),
        },
        "top_keywords": top_keywords,
        "topic_breakdown": topic_breakdown,
    }


def _recommendations(kpis: dict[str, Any], segments: dict[str, Any]) -> list[str]:
    recommendations: list[str] = []

    if kpis["cancellation_rate_pct"] >= 15:
        recommendations.append("Cancellation rate is elevated. Add reminders and flexible rescheduling to recover revenue.")

    locality_segments = segments.get("by_locality", [])
    if locality_segments:
        top_locality = locality_segments[0]
        if top_locality["share_pct"] >= 35:
            recommendations.append(
                f"Revenue is concentrated in {top_locality['segment']}. Target adjacent localities to reduce concentration risk."
            )

    customer_tiers = segments.get("customer_tiers", [])
    at_risk = next((row for row in customer_tiers if row["segment"] == "at_risk"), None)
    if at_risk and at_risk["users"] > 0:
        recommendations.append("Run retention campaigns for at-risk users with return discounts and loyalty points.")

    if kpis["repeat_customer_rate_pct"] < 40:
        recommendations.append("Repeat customer rate is low. Introduce subscription packs for frequent users.")

    if not recommendations:
        recommendations.append("Performance is healthy. Next step is experimenting with dynamic pricing by demand windows.")

    return recommendations


def build_analytics_payload(bookings: list[Booking], search_events_count: int) -> dict[str, Any]:
    df = _build_base_dataframe(bookings)

    if df.empty:
        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "overview": {
                "total_bookings": 0,
                "successful_bookings": 0,
                "total_revenue": 0.0,
                "avg_booking_value": 0.0,
                "cancellation_rate_pct": 0.0,
                "repeat_customer_rate_pct": 0.0,
                "search_to_booking_conversion_pct": 0.0,
                "month_over_month_growth_pct": None,
                "projected_next_30d_revenue": 0.0,
                "forecast_confidence": "low",
            },
            "revenue": {
                "daily": [],
                "monthly": [],
                "forecast_next_14_days": [],
            },
            "segmentation": {
                "by_space_type": [],
                "by_locality": [],
                "customer_tiers": [],
            },
            "nlp": _review_nlp(bookings),
            "recommendations": ["Generate demo bookings to unlock AI analytics insights."],
        }

    confirmed_df = df[df["is_revenue"]].copy()
    cancelled_count = int((df["status"] == "cancelled").sum())
    successful_count = len(confirmed_df)

    total_revenue = round(float(confirmed_df["total_amount"].sum()), 2) if successful_count else 0.0
    avg_booking_value = round(float(confirmed_df["total_amount"].mean()), 2) if successful_count else 0.0

    customer_revenue = confirmed_df.groupby("user_id").size() if not confirmed_df.empty else pd.Series(dtype="int64")
    repeat_users = int((customer_revenue >= 2).sum()) if not customer_revenue.empty else 0
    active_users = int((customer_revenue >= 1).sum()) if not customer_revenue.empty else 0

    daily_df = _daily_revenue_frame(confirmed_df)
    forecast_14, confidence = _forecast_revenue(daily_df, horizon_days=14)
    forecast_30, _ = _forecast_revenue(daily_df, horizon_days=30)
    projected_next_30d_revenue = round(sum(item["predicted_revenue"] for item in forecast_30), 2)

    monthly_df = _monthly_revenue_frame(confirmed_df)
    month_over_month_growth = None
    if len(monthly_df) >= 2:
        month_over_month_growth = monthly_df.iloc[-1]["growth_pct"]

    search_to_booking_conversion = _safe_pct(successful_count, search_events_count) if search_events_count > 0 else 0.0

    overview = {
        "total_bookings": int(len(df)),
        "successful_bookings": successful_count,
        "total_revenue": total_revenue,
        "avg_booking_value": avg_booking_value,
        "cancellation_rate_pct": _safe_pct(cancelled_count, len(df)),
        "repeat_customer_rate_pct": _safe_pct(repeat_users, active_users),
        "search_to_booking_conversion_pct": search_to_booking_conversion,
        "month_over_month_growth_pct": month_over_month_growth,
        "projected_next_30d_revenue": projected_next_30d_revenue,
        "forecast_confidence": confidence,
    }

    revenue = {
        "daily": [
            {
                "date": row["booking_date"].date().isoformat(),
                "revenue": round(float(row["revenue"]), 2),
                "bookings": int(row["bookings"]),
            }
            for _, row in daily_df.iterrows()
        ],
        "monthly": [
            {
                "month": str(row["month"]),
                "revenue": round(float(row["revenue"]), 2),
                "bookings": int(row["bookings"]),
                "growth_pct": float(row["growth_pct"]) if row["growth_pct"] is not None and not pd.isna(row["growth_pct"]) else None,
            }
            for _, row in monthly_df.iterrows()
        ],
        "forecast_next_14_days": forecast_14,
    }

    by_space_type = _segment_by_dimension(confirmed_df, "space_type", total_revenue)
    by_locality = _segment_by_dimension(confirmed_df, "locality", total_revenue, limit=8)
    customer_tiers = _customer_segments(df)

    segmentation = {
        "by_space_type": by_space_type,
        "by_locality": by_locality,
        "customer_tiers": customer_tiers,
    }

    nlp = _review_nlp(bookings)

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "overview": overview,
        "revenue": revenue,
        "segmentation": segmentation,
        "nlp": nlp,
        "recommendations": _recommendations(overview, segmentation),
    }