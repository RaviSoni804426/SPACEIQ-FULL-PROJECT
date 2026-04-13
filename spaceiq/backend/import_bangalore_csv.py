from __future__ import annotations

import argparse
import csv
from pathlib import Path

from sqlalchemy import func

from city_policy import normalize_bangalore_city
from database import SessionLocal, engine
from models import Base, Location, Unit


BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_IMPORT_FILE = BACKEND_DIR / "data" / "bangalore_locations.csv"
REQUIRED_COLUMNS = (
    "location_name",
    "area",
    "city",
    "address",
    "latitude",
    "longitude",
    "location_description",
    "location_amenities",
    "unit_name",
    "category",
    "capacity",
    "base_price",
    "unit_description",
    "unit_amenities",
)


def _clean_text(value: str | None) -> str | None:
    cleaned = (value or "").strip()
    return cleaned or None


def _required_text(row: dict[str, str], column: str, line_number: int) -> str:
    value = _clean_text(row.get(column))
    if value is None:
        raise ValueError(f"Line {line_number}: '{column}' is required.")
    return value


def _parse_float(value: str | None, column: str, line_number: int) -> float:
    cleaned = _clean_text(value)
    if cleaned is None:
        raise ValueError(f"Line {line_number}: '{column}' is required.")
    try:
        return float(cleaned)
    except ValueError as exc:
        raise ValueError(f"Line {line_number}: '{column}' must be a number.") from exc


def _parse_int(value: str | None, column: str, line_number: int) -> int:
    cleaned = _clean_text(value)
    if cleaned is None:
        raise ValueError(f"Line {line_number}: '{column}' is required.")
    try:
        return int(cleaned)
    except ValueError as exc:
        raise ValueError(f"Line {line_number}: '{column}' must be an integer.") from exc


def _load_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = tuple(reader.fieldnames or ())
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing_columns:
            missing = ", ".join(missing_columns)
            raise ValueError(f"CSV is missing required columns: {missing}")
        return list(reader)


def import_csv(csv_path: Path) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"File not found: {csv_path}")

    rows = _load_rows(csv_path)
    if not rows:
        raise ValueError("CSV has headers but no data rows.")

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    location_created = 0
    location_updated = 0
    unit_created = 0
    unit_updated = 0

    try:
        for line_number, row in enumerate(rows, start=2):
            if not any((row.get(column) or "").strip() for column in REQUIRED_COLUMNS):
                continue

            location_name = _required_text(row, "location_name", line_number)
            area = _required_text(row, "area", line_number)
            city = normalize_bangalore_city(_required_text(row, "city", line_number))
            address = _required_text(row, "address", line_number)
            latitude = _parse_float(row.get("latitude"), "latitude", line_number)
            longitude = _parse_float(row.get("longitude"), "longitude", line_number)
            location_description = _clean_text(row.get("location_description"))
            location_amenities = _clean_text(row.get("location_amenities"))

            unit_name = _required_text(row, "unit_name", line_number)
            category = _required_text(row, "category", line_number).lower()
            capacity = _parse_int(row.get("capacity"), "capacity", line_number)
            base_price = _parse_float(row.get("base_price"), "base_price", line_number)
            unit_description = _clean_text(row.get("unit_description"))
            unit_amenities = _clean_text(row.get("unit_amenities"))

            location = (
                db.query(Location)
                .filter(
                    func.lower(Location.name) == location_name.lower(),
                    func.lower(Location.address) == address.lower(),
                )
                .first()
            )
            if location is None:
                location = Location(
                    name=location_name,
                    area=area,
                    city=city,
                    address=address,
                    latitude=latitude,
                    longitude=longitude,
                    description=location_description,
                    amenities=location_amenities,
                )
                db.add(location)
                db.flush()
                location_created += 1
            else:
                location.area = area
                location.city = city
                location.latitude = latitude
                location.longitude = longitude
                location.description = location_description
                location.amenities = location_amenities
                location_updated += 1

            unit = (
                db.query(Unit)
                .filter(
                    Unit.location_id == location.id,
                    func.lower(Unit.name) == unit_name.lower(),
                    func.lower(Unit.category) == category,
                )
                .first()
            )
            if unit is None:
                unit = Unit(
                    location_id=location.id,
                    name=unit_name,
                    category=category,
                    capacity=capacity,
                    base_price=base_price,
                    description=unit_description,
                    amenities=unit_amenities,
                )
                db.add(unit)
                unit_created += 1
            else:
                unit.capacity = capacity
                unit.base_price = base_price
                unit.description = unit_description
                unit.amenities = unit_amenities
                unit.is_active = True
                unit_updated += 1

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"Imported from: {csv_path}")
    print(f"Locations created: {location_created}")
    print(f"Locations updated: {location_updated}")
    print(f"Units created: {unit_created}")
    print(f"Units updated: {unit_updated}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import real Bengaluru venue data into SpaceIQ.")
    parser.add_argument(
        "--file",
        default=str(DEFAULT_IMPORT_FILE),
        help="Path to the CSV file to import.",
    )
    args = parser.parse_args()
    import_csv(Path(args.file).resolve())


if __name__ == "__main__":
    main()
