from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, require_admin
from services.qr_service import generate_qr_image_b64, validate_qr
import models

router = APIRouter(prefix="/qr", tags=["qr"])


@router.get("/{booking_id}/image")
def get_qr_image(
    booking_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    qr_record = db.query(models.QRCode).filter(
        models.QRCode.booking_id == booking_id
    ).first()
    if not qr_record:
        from fastapi import HTTPException
        raise HTTPException(404, "QR code not found")

    img_b64 = generate_qr_image_b64(qr_record.token)
    return {"qr_image_b64": img_b64, "token": qr_record.token}


@router.post("/validate/{token}")
def validate(
    token: str,
    _admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return validate_qr(token, db)
