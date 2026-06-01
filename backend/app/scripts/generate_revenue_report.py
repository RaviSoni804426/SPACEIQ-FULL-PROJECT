from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.database import SessionLocal
from app.models import Booking, SearchEvent
from app.services.analytics import build_analytics_payload

PROJECT_ROOT = Path(__file__).resolve().parents[3]
REPORT_PATH = PROJECT_ROOT / "docs" / "REVENUE_ANALYSIS_REPORT.md"


def _render_table(rows: list[dict], headers: list[str]) -> str:
    if not rows:
        return "No data available.\n"

    header_line = "| " + " | ".join(headers) + " |"
    separator_line = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_lines = []
    for row in rows:
        body_lines.append("| " + " | ".join(str(row.get(header, "")) for header in headers) + " |")
    return "\n".join([header_line, separator_line, *body_lines]) + "\n"


async def generate_report() -> None:
    async with SessionLocal() as session:
        bookings_result = await session.execute(
            select(Booking)
            .options(selectinload(Booking.space), selectinload(Booking.review))
            .order_by(Booking.booking_date.asc())
        )
        bookings = list(bookings_result.scalars().all())
        search_events_count = await session.scalar(select(func.count(SearchEvent.id)))

    payload = build_analytics_payload(bookings, int(search_events_count or 0))
    overview = payload["overview"]
    segmentation = payload["segmentation"]
    nlp = payload["nlp"]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    content = [
        "# Revenue Analysis Report",
        "",
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## KPI Snapshot",
        "",
        f"- Total bookings: {overview['total_bookings']}",
        f"- Successful bookings: {overview['successful_bookings']}",
        f"- Total revenue: INR {overview['total_revenue']:.2f}",
        f"- Avg booking value: INR {overview['avg_booking_value']:.2f}",
        f"- Cancellation rate: {overview['cancellation_rate_pct']:.2f}%",
        f"- Repeat customer rate: {overview['repeat_customer_rate_pct']:.2f}%",
        f"- Search-to-booking conversion: {overview['search_to_booking_conversion_pct']:.2f}%",
        f"- Month-over-month growth: {overview['month_over_month_growth_pct']}%",
        f"- Projected next 30-day revenue: INR {overview['projected_next_30d_revenue']:.2f}",
        f"- Forecast confidence: {overview['forecast_confidence']}",
        "",
        "## Monthly Revenue",
        "",
        _render_table(payload["revenue"]["monthly"], ["month", "revenue", "bookings", "growth_pct"]),
        "",
        "## Revenue by Space Type",
        "",
        _render_table(segmentation["by_space_type"], ["segment", "revenue", "bookings", "share_pct"]),
        "",
        "## Revenue by Locality",
        "",
        _render_table(segmentation["by_locality"], ["segment", "revenue", "bookings", "share_pct"]),
        "",
        "## Customer Tiers",
        "",
        _render_table(
            segmentation["customer_tiers"],
            ["segment", "users", "revenue", "avg_recency_days", "avg_successful_bookings"],
        ),
        "",
        "## Review NLP",
        "",
        f"- Positive sentiment: {nlp['review_sentiment']['positive_pct']}%",
        f"- Neutral sentiment: {nlp['review_sentiment']['neutral_pct']}%",
        f"- Negative sentiment: {nlp['review_sentiment']['negative_pct']}%",
        f"- Review sample size: {nlp['review_sentiment']['sample_size']}",
        f"- Avg rating (reviews in analytics set): {nlp['review_sentiment']['average_rating']}",
        "",
        "## Strategic Recommendations",
        "",
        *[f"- {item}" for item in payload["recommendations"]],
        "",
    ]

    REPORT_PATH.write_text("\n".join(content), encoding="utf-8")
    print(f"Report written to {REPORT_PATH}")


if __name__ == "__main__":
    asyncio.run(generate_report())