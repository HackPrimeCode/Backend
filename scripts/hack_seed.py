"""Seed hackathons for local development."""

from datetime import datetime, timedelta, UTC

from sqlalchemy import select

from src.core.database import SessionLocal
from src.enums import HackathonStatus, HackPlace
from src.models.hackathon import Hackathon
from src.models.prizes import HackathonPrize


def seed_hackathons(db):
    now = datetime.now(UTC)

    hackathons_data = [
        {
            "title": "HackPrime Summer 2026",
            "description": "Главный летний хакатон платформы.",
            "status": HackathonStatus.REGISTRATION,
            "place": HackPlace.ONLINE,
            "min_team_size": 1,
            "max_team_size": 4,
            "max_participants": 1000,
            "start_date": now + timedelta(days=7),
            "end_date": now + timedelta(days=10),
            "topics": ["Python", "React", "ML"],
            "submission_requirements": [
                "Команда от 1 до 4 человек",
                "Регистрация до начала хакатона",
                "GitHub репозиторий",
            ],
            "prizes": [
                {"title": "1-е место", "reward": "300000"},
                {"title": "2-е место", "reward": "150000"},
                {"title": "3-е место", "reward": "50000"},
            ],
        },
        {
            "title": "AI Challenge 2026",
            "description": "Хакатон по искусственному интеллекту.",
            "status": HackathonStatus.IN_PROGRESS,
            "place": HackPlace.MOSCOW,
            "min_team_size": 1,
            "max_team_size": 5,
            "max_participants": 500,
            "start_date": now - timedelta(days=1),
            "end_date": now + timedelta(days=2),
            "topics": ["AI", "LLM", "Computer Vision"],
            "submission_requirements": [
                "Знание ML",
                "Рабочий прототип",
            ],
            "prizes": [
                {"title": "1-е место", "reward": "500000"},
                {"title": "2-е место", "reward": "200000"},
            ],
        },
        {
            "title": "GameDev Jam 2025",
            "description": "Хакатон по разработке игр.",
            "status": HackathonStatus.FINISHED,
            "place": HackPlace.SPB,
            "min_team_size": 1,
            "max_team_size": 4,
            "max_participants": 300,
            "start_date": now - timedelta(days=30),
            "end_date": now - timedelta(days=25),
            "topics": ["Unity", "Unreal", "Godot"],
            "submission_requirements": [
                "Рабочий билд",
                "Описание геймплея",
            ],
            "prizes": [
                {"title": "1-е место", "reward": "200000"},
                {"title": "2-е место", "reward": "100000"},
            ],
        },
        {
            "title": "CyberSecurity Cup",
            "description": "CTF соревнование по кибербезопасности.",
            "status": HackathonStatus.DRAFT,
            "place": HackPlace.ONLINE,
            "min_team_size": 1,
            "max_team_size": 3,
            "max_participants": 200,
            "start_date": now + timedelta(days=30),
            "end_date": now + timedelta(days=32),
            "topics": ["Security", "Crypto", "Reverse"],
            "submission_requirements": [
                "Регистрация обязательна",
            ],
            "prizes": [],
        },
    ]

    for data in hackathons_data:
        existing = db.scalar(
            select(Hackathon).where(Hackathon.title == data["title"])
        )

        if existing:
            continue

        hackathon = Hackathon(
            title=data["title"],
            description=data["description"],
            status=data["status"],
            place=data["place"],
            min_team_size=data["min_team_size"],
            max_team_size=data["max_team_size"],
            max_participants=data["max_participants"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            topics=data["topics"],
            submission_requirements=data["submission_requirements"],
        )

        db.add(hackathon)
        db.flush()

        for i, prize_data in enumerate(data["prizes"], start=1):
            prize = HackathonPrize(
                hackathon_id=hackathon.id,
                title=prize_data["title"],
                reward=prize_data["reward"],
            )
            db.add(prize)

    db.commit()
    print("Hackathons seeded successfully.")


def main():
    db = SessionLocal()
    try:
        seed_hackathons(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()