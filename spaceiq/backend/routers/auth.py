from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
import models, schemas
from auth import hash_password, verify_password, create_access_token, get_current_user, require_owner
from services.email_service import send_admin_request_notifications, send_admin_approval_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


@router.post("/register", response_model=schemas.TokenResponse)
def register(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    normalized_email = _normalize_email(req.email)
    if db.query(models.User).filter(func.lower(models.User.email) == normalized_email).first():
        raise HTTPException(400, "Email already registered")
    user = models.User(
        name=req.name,
        email=normalized_email,
        hashed_password=hash_password(req.password),
        phone=req.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.id})
    return {"access_token": token}


@router.post("/login", response_model=schemas.TokenResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    normalized_email = _normalize_email(req.email)
    user = db.query(models.User).filter(func.lower(models.User.email) == normalized_email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token = create_access_token({"sub": user.id})
    return {"access_token": token}


@router.post("/request-admin")
def request_admin(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """User requests admin access - triggers email to owner."""
    if user.role != "user":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Only normal users can request admin elevation")
    
    # Prevent duplicate requests
    if user.is_admin_requested:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="You already have a pending admin request")
    
    user.is_admin_requested = True
    db.add(user)
    db.commit()
    db.refresh(user)
    
    notifications = send_admin_request_notifications(user.name, user.email, user.id)
    if notifications["email_sent"] or notifications["whatsapp_sent"]:
        detail = "Admin request submitted. Owner notification has been sent."
    else:
        detail = "Admin request submitted. It is visible in the owner dashboard, but email and WhatsApp delivery are not configured yet."

    return {
        "detail": detail,
        "email_sent": notifications["email_sent"],
        "whatsapp_sent": notifications["whatsapp_sent"],
        "email_status": notifications["email_status"],
        "whatsapp_status": notifications["whatsapp_status"],
    }


@router.get("/pending-admin-requests")
def pending_admin_requests(_owner: models.User = Depends(require_owner), db: Session = Depends(get_db)):
    """Get all pending admin requests (owner only)."""
    pending = db.query(models.User).filter(models.User.is_admin_requested == True).all()
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in pending]


@router.post("/verify-admin/{user_id}")
def verify_admin(user_id: str, _owner: models.User = Depends(require_owner), db: Session = Depends(get_db)):
    """Approve admin request and send confirmation email."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.is_admin_requested:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pending request not found")
    
    user.role = "admin"
    user.is_admin_requested = False
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send approval email
    send_admin_approval_email(user.name, user.email)
    
    return {"detail": f"User {user.email} has been promoted to admin. Confirmation email sent."}


@router.post("/reject-admin/{user_id}")
def reject_admin(user_id: str, _owner: models.User = Depends(require_owner), db: Session = Depends(get_db)):
    """Reject admin request."""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.is_admin_requested:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pending request not found")
    
    user.is_admin_requested = False
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"detail": f"Admin request for {user.email} was rejected."}


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user
