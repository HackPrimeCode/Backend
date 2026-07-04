"""Seed script for local development."""

from sqlalchemy import select

from src.core.database import SessionLocal
from src.core.security import hash_password
from src.enums import GlobalRole
from src.models.user import User

DEFAULT_PASSWORD = "password123"


def seed_users() -> None:
    db = SessionLocal()
    try:
        users = [
            User(
                email="admin@hackprime.com",
                name="Admin User",
                hashed_password=hash_password(DEFAULT_PASSWORD),
                tech_stack=["Python", "FastAPI"],
                global_role=GlobalRole.ADMIN,
            ),
            User(
                email="organizator@hackprime.com",
                name="Organizator User",
                hashed_password=hash_password(DEFAULT_PASSWORD),
                tech_stack=["Go", "Kubernetes"],
                global_role=GlobalRole.ORGANIZATOR,
            ),
            User(
                email="user@hackprime.com",
                name="Regular User",
                hashed_password=hash_password(DEFAULT_PASSWORD),
                tech_stack=["JavaScript", "React"],
                global_role=GlobalRole.USER,
            ),
        ]

        for user in users:
            existing = db.scalar(select(User).where(User.email == user.email))
            if existing is None:
                db.add(user)
            elif not existing.hashed_password or existing.hashed_password == "":
                existing.hashed_password = hash_password(DEFAULT_PASSWORD)

        db.commit()
        print("Seed users created successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_users()