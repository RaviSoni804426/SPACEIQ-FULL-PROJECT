from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from auth import get_current_user, require_admin
from city_policy import normalize_bangalore_city
from database import get_db
import models, schemas


router = APIRouter(prefix="/partners", tags=["partners"])


def _serialize_owner_application(row: models.OwnerApplication) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "business_name": row.business_name,
        "business_type": row.business_type,
        "city": row.city,
        "phone": row.phone,
        "message": row.message,
        "status": row.status,
        "review_note": row.review_note,
        "reviewed_by": row.reviewed_by,
        "reviewed_at": row.reviewed_at,
        "created_at": row.created_at,
    }


def _serialize_listing_submission(row: models.ListingSubmission) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "business_name": row.business_name,
        "business_type": row.business_type,
        "venue_name": row.venue_name,
        "category": row.category,
        "area": row.area,
        "city": row.city,
        "address": row.address,
        "description": row.description,
        "amenities": row.amenities,
        "capacity": row.capacity,
        "base_price": row.base_price,
        "status": row.status,
        "review_note": row.review_note,
        "reviewed_by": row.reviewed_by,
        "reviewed_at": row.reviewed_at,
        "approved_location_id": row.approved_location_id,
        "approved_unit_id": row.approved_unit_id,
        "created_at": row.created_at,
    }


@router.post("/owner-applications", response_model=schemas.OwnerApplicationOut)
def submit_owner_application(
    req: schemas.OwnerApplicationRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = (
        db.query(models.OwnerApplication)
        .filter(models.OwnerApplication.user_id == user.id, models.OwnerApplication.status == "pending")
        .first()
    )
    if existing:
        raise HTTPException(400, "You already have a pending partner access request.")

    try:
        city = normalize_bangalore_city(req.city)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    application = models.OwnerApplication(
        user_id=user.id,
        business_name=req.business_name.strip(),
        business_type=req.business_type.strip(),
        city=city,
        phone=req.phone or user.phone,
        message=req.message,
    )
    db.add(application)
    db.commit()
    db.refresh(application)
    return _serialize_owner_application(application)


@router.get("/owner-applications/my", response_model=list[schemas.OwnerApplicationOut])
def my_owner_applications(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.OwnerApplication)
        .filter(models.OwnerApplication.user_id == user.id)
        .order_by(models.OwnerApplication.created_at.desc())
        .all()
    )
    return [_serialize_owner_application(row) for row in rows]


@router.post("/listings", response_model=schemas.ListingSubmissionOut)
def submit_listing(
    req: schemas.ListingSubmissionRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        city = normalize_bangalore_city(req.city)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    submission = models.ListingSubmission(
        user_id=user.id,
        business_name=req.business_name.strip(),
        business_type=req.business_type.strip(),
        venue_name=req.venue_name.strip(),
        category=req.category.strip().lower(),
        area=req.area.strip(),
        city=city,
        address=req.address.strip(),
        description=req.description,
        amenities=req.amenities,
        capacity=max(int(req.capacity), 1),
        base_price=float(req.base_price),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return _serialize_listing_submission(submission)


@router.get("/listings/my", response_model=list[schemas.ListingSubmissionOut])
def my_listing_submissions(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.ListingSubmission)
        .filter(models.ListingSubmission.user_id == user.id)
        .order_by(models.ListingSubmission.created_at.desc())
        .all()
    )
    return [_serialize_listing_submission(row) for row in rows]


@router.get("/dashboard", response_model=schemas.PartnerDashboardOut)
def partner_dashboard(
    _admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return {
        "pending_owner_applications": db.query(models.OwnerApplication).filter(models.OwnerApplication.status == "pending").count(),
        "pending_listing_submissions": db.query(models.ListingSubmission).filter(models.ListingSubmission.status == "pending").count(),
        "approved_listings": db.query(models.ListingSubmission).filter(models.ListingSubmission.status == "approved").count(),
        "approved_partners": db.query(models.OwnerApplication).filter(models.OwnerApplication.status == "approved").count(),
    }


@router.get("/review/queue")
def review_queue(
    _admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    owner_rows = (
        db.query(models.OwnerApplication)
        .order_by(models.OwnerApplication.created_at.desc())
        .limit(20)
        .all()
    )
    listing_rows = (
        db.query(models.ListingSubmission)
        .order_by(models.ListingSubmission.created_at.desc())
        .limit(30)
        .all()
    )
    return {
        "owner_applications": [_serialize_owner_application(row) for row in owner_rows],
        "listing_submissions": [_serialize_listing_submission(row) for row in listing_rows],
    }


@router.post("/review/owner-application/{application_id}")
def review_owner_application(
    application_id: str,
    req: schemas.ReviewDecisionRequest,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    application = db.query(models.OwnerApplication).filter(models.OwnerApplication.id == application_id).first()
    if not application:
        raise HTTPException(404, "Partner application not found")
    if application.status != "pending":
        raise HTTPException(400, "This partner application has already been reviewed")

    action = req.action.strip().lower()
    if action not in {"approve", "reject"}:
        raise HTTPException(400, "Action must be approve or reject")

    application.status = "approved" if action == "approve" else "rejected"
    application.review_note = req.note
    application.reviewed_by = admin.id
    application.reviewed_at = datetime.utcnow()

    applicant = db.query(models.User).filter(models.User.id == application.user_id).first()
    if applicant and action == "approve":
        applicant.role = models.UserRole.admin
        applicant.is_admin_requested = False

    db.commit()
    return {
        "reviewed": True,
        "status": application.status,
        "user_id": application.user_id,
        "detail": "Partner access approved." if action == "approve" else "Partner access rejected.",
    }


@router.post("/review/listing/{submission_id}")
def review_listing_submission(
    submission_id: str,
    req: schemas.ReviewDecisionRequest,
    admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    submission = db.query(models.ListingSubmission).filter(models.ListingSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "Listing submission not found")
    if submission.status != "pending":
        raise HTTPException(400, "This listing submission has already been reviewed")

    action = req.action.strip().lower()
    if action not in {"approve", "reject"}:
        raise HTTPException(400, "Action must be approve or reject")

    submission.status = "approved" if action == "approve" else "rejected"
    submission.review_note = req.note
    submission.reviewed_by = admin.id
    submission.reviewed_at = datetime.utcnow()

    if action == "approve":
        location = models.Location(
            name=submission.venue_name,
            area=submission.area,
            city=submission.city,
            address=submission.address,
            description=submission.description or f"{submission.business_type.title()} listing submitted through SpaceIQ partner onboarding.",
            amenities=submission.amenities,
        )
        db.add(location)
        db.flush()

        unit = models.Unit(
            location_id=location.id,
            name=submission.venue_name,
            category=submission.category,
            capacity=submission.capacity,
            base_price=submission.base_price,
            description=submission.description,
            amenities=submission.amenities,
        )
        db.add(unit)
        db.flush()

        submission.approved_location_id = location.id
        submission.approved_unit_id = unit.id

    db.commit()
    return {
        "reviewed": True,
        "status": submission.status,
        "submission_id": submission.id,
        "approved_location_id": submission.approved_location_id,
        "approved_unit_id": submission.approved_unit_id,
        "detail": "Listing approved and published." if action == "approve" else "Listing rejected.",
    }
