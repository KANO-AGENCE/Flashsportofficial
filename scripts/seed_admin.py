"""Create the initial SUPERADMIN user."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.security import hash_password
from app.db.database import SessionLocal
from app.models.auth import User


def seed():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == "admin@flashsport.fr").first()
        if existing:
            print("Admin user already exists")
            return

        user = User(
            email="admin@flashsport.fr",
            password_hash=hash_password("admin"),
            first_name="Admin",
            last_name="FlashSport",
            role="SUPERADMIN",
            modules=["TRI", "WEB", "MAILING"],
            is_active=True,
        )
        db.add(user)
        db.commit()
        print("SUPERADMIN created: admin@flashsport.fr / admin")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
