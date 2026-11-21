from typing import Optional, List
from sqlalchemy.orm import Session

from backend.app.models.user import UserModel


class UserRepository:
    """Repository pattern for persistent UserModel queries and mutations."""
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[UserModel]:
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[UserModel]:
        if not email:
            return None
        normalized = email.strip().lower()
        return self.db.query(UserModel).filter(UserModel.email == normalized).first()

    def create(
        self,
        full_name: str,
        email: str,
        hashed_password: str,
        role: str = "Retail Investor & Decision Analyst"
    ) -> UserModel:
        user = UserModel(
            full_name=full_name.strip(),
            email=email.strip().lower(),
            hashed_password=hashed_password,
            role=role,
            is_active=True
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: UserModel) -> UserModel:
        self.db.commit()
        self.db.refresh(user)
        return user

    def count(self) -> int:
        return self.db.query(UserModel).count()

    def delete(self, user_id: str) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True
