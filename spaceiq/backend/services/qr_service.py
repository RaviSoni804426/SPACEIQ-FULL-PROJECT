import qrcode
import uuid
import io
import base64
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
import models


def generate_qr_token(booking_id: str) -> str:
    """Generate a unique token for the QR code."""
    return f"SIQR-{uuid.uuid4().hex.upper()[:16]}-{booking_id[:8].upper()}"


def generate_qr_image_b64(token: str) -> str:
    """Generate QR code image and return as base64 string."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def validate_qr(token: str, db: Session) -> dict:
    """Validate a QR token at entry — used by venue staff."""
    qr_record = db.query(models.QRCode).filter(models.QRCode.token == token).first()
    if not qr_record:
        raise HTTPException(404, "Invalid QR code")
    if qr_record.is_used:
        raise HTTPException(409, "QR code already used")
    if qr_record.expires_at < datetime.utcnow():
        raise HTTPException(410, "QR code expired")

    # Mark as used
    qr_record.is_used = True
    db.commit()

    booking = qr_record.booking
    return {
        "valid": True,
        "booking_id": booking.id,
        "user_name": booking.user.name,
        "unit_name": booking.unit.name,
        "start_time": booking.start_time.isoformat(),
        "end_time": booking.end_time.isoformat(),
    }
