import uuid

from sqlalchemy.orm import Session

import models
import schemas


def get_user(db: Session, id: str):
    return db.query(models.User).filter(models.User.id == id).first()


def get_user_by_username(db: Session, username: str):
    return (
        db.query(models.User).filter(models.User.username == username).first()
    )


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, user: schemas.UserCreate):
    id = uuid.uuid4()
    while get_user(db=db, id=str(id)):
        id = uuid.uuid4()

    db_user = models.User(
        id=str(id),
        username=user.username,
        name=user.name,
        email=user.email,
        hashed_password=user.hashed_password,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


def get_tasks_by_user_id(
    db: Session, id: str, skip: int = 0, limit: int = 100
):
    return (
        db.query(models.Task)
        .filter(models.Task.user_id == id)
        .offset(skip)
        .limit(limit)
        .all()
    )
