"""
Announcement endpoints for the High School Management School API

Announcements are stored in the database and managed by signed-in teachers.
"""

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import Any, Dict, List, Optional

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementInput(BaseModel):
    """Payload for creating or updating an announcement."""
    message: str
    expiration_date: str
    start_date: Optional[str] = None

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message cannot be empty")
        return value.strip()

    @field_validator("expiration_date", "start_date")
    @classmethod
    def valid_date(cls, value: Optional[str]) -> Optional[str]:
        if value in (None, ""):
            return None
        try:
            date.fromisoformat(value)
        except ValueError:
            raise ValueError("Dates must be in YYYY-MM-DD format")
        return value


def require_teacher(teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Dependency that ensures the caller is a signed-in teacher."""
    if not teacher_username:
        raise HTTPException(
            status_code=401, detail="Authentication required for this action")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")

    return teacher


def serialize(announcement: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a Mongo announcement document into an API-friendly dict."""
    announcement = dict(announcement)
    announcement["id"] = str(announcement.pop("_id"))
    return announcement


@router.get("/active", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get announcements that are currently within their active date range"""
    today = date.today().isoformat()
    query = {
        "expiration_date": {"$gte": today},
        "$or": [{"start_date": None}, {"start_date": {"$lte": today}}]
    }

    announcements = [
        serialize(announcement)
        for announcement in announcements_collection.find(query).sort("expiration_date", 1)
    ]
    return announcements


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_all_announcements(teacher: Dict[str, Any] = Depends(require_teacher)) -> List[Dict[str, Any]]:
    """Get all announcements - requires teacher authentication"""
    announcements = [
        serialize(announcement)
        for announcement in announcements_collection.find().sort("expiration_date", 1)
    ]
    return announcements


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    payload: AnnouncementInput,
    teacher: Dict[str, Any] = Depends(require_teacher)
) -> Dict[str, Any]:
    """Create a new announcement - requires teacher authentication"""
    if payload.start_date and payload.start_date > payload.expiration_date:
        raise HTTPException(
            status_code=400, detail="Start date must be before expiration date")

    announcement = {
        "_id": uuid.uuid4().hex,
        "message": payload.message,
        "start_date": payload.start_date,
        "expiration_date": payload.expiration_date,
        "created_by": teacher["username"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    announcements_collection.insert_one(announcement)

    return serialize(announcement)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementInput,
    teacher: Dict[str, Any] = Depends(require_teacher)
) -> Dict[str, Any]:
    """Update an existing announcement - requires teacher authentication"""
    if payload.start_date and payload.start_date > payload.expiration_date:
        raise HTTPException(
            status_code=400, detail="Start date must be before expiration date")

    existing = announcements_collection.find_one({"_id": announcement_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")

    updates = {
        "message": payload.message,
        "start_date": payload.start_date,
        "expiration_date": payload.expiration_date
    }
    announcements_collection.update_one(
        {"_id": announcement_id}, {"$set": updates})

    updated = announcements_collection.find_one({"_id": announcement_id})
    return serialize(updated)


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    teacher: Dict[str, Any] = Depends(require_teacher)
) -> Dict[str, str]:
    """Delete an announcement - requires teacher authentication"""
    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
