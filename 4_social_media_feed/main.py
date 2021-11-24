import os
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_login.fastapi_login import LoginManager
from passlib.context import CryptContext
from pydantic import BaseModel

from db import users

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

manager = LoginManager(secret=SECRET_KEY, token_url="/login", use_cookie=True)
manager.cookie_name = "auth"

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@manager.user_loader()
def get_user_from_db(username: str):
    if username in users.keys():
        return UserDB(**users[username])


def get_hashed_password(plain_password):
    return password_context.hash(plain_password)


def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str):
    user = get_user_from_db(username=username)
    if not user:
        return None

    if not verify_password(
        plain_password=password, hashed_password=user.hashed_password
    ):
        return None

    return user


class Notification(BaseModel):
    author: str
    description: str


class User(BaseModel):
    name: str
    username: str
    email: str
    birthday: str
    friends: List[str]
    notifications: List[Notification]


class UserDB(User):
    hashed_password: str


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "FriendConnect - Home"}
    )


@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "title": "FriendConnect - Login",
            "invalid": True,
        },
    )
