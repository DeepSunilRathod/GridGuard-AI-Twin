from fastapi import APIRouter

router = APIRouter(
    prefix="/api/notifications",
    tags=["Notifications"],
)