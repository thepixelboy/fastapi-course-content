import os
from datetime import datetime, timedelta
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_login.fastapi_login import LoginManager
from passlib.context import CryptContext
from pydantic import BaseModel

from db import users

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ACCESS_TOKEN_EXPIRES_MINUTES = 60

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
        },
    )


@app.post("/login")
def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = authenticate_user(
        username=form_data.username, password=form_data.password
    )
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "title": "FriendConnect - Login",
                "invalid": True,
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    access_token = manager.create_access_token(
        data={"sub": user.username}, expires=access_token_expires
    )
    response_method = RedirectResponse(
        "/home", status_code=status.HTTP_302_FOUND
    )
    manager.set_cookie(response_method, access_token)

    return response_method


class NotAuthenticatedException(Exception):
    ...


def not_authenticated_exception_handler(request, exception):
    return RedirectResponse("/login")


manager.not_authenticated_exception = NotAuthenticatedException
app.add_exception_handler(
    NotAuthenticatedException, not_authenticated_exception_handler
)


@app.get("/home")
def home(user: User = Depends(manager)):
    return user
