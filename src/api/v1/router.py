from fastapi import APIRouter

from src.api.v1.admin import hackathons as admin_hackathons
from src.api.v1 import auth, hackathons, tasks, teams, user

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth.router)
api_v1_router.include_router(admin_hackathons.router)
api_v1_router.include_router(hackathons.router)
api_v1_router.include_router(teams.router)
api_v1_router.include_router(tasks.router)
api_v1_router.include_router(user.router)
