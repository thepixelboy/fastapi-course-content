import os
from datetime import timedelta

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_login.fastapi_login import LoginManager
from passlib.context import CryptContext
from sqlalchemy.orm import Session

import crud
import models
import schemas
from db import DBContext, SessionLocal, engine

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ACCESS_TOKEN_EXPIRES_MINUTES = 60

manager = LoginManager(SECRET_KEY, token_url="/login", use_cookie=True)
manager.cookie_name = "auth"
password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db():
    with DBContext() as db:
        yield db


def get_hashed_password(plain_password):
    return password_context.hash(plain_password)


def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)


@manager.user_loader()
def get_user(username: str, db: Session = None):
    if db is None:
        with DBContext() as db:
            return crud.get_user_by_username(db=db, username=username)
    return crud.get_user_by_username(db=db, username=username)


def authenticate_user(
    username: str, password: str, db: Session = Depends(get_db)
):
    user = crud.get_user_by_username(db=db, username=username)

    if not user:
        return None
    if not verify_password(
        plain_password=password, hashed_password=user.hashed_password
    ):
        return None

    return user


class NotAuthenticatedException(Exception):
    ...


def not_authenticated_exception_handler(request, exception):
    return RedirectResponse("/login")


manager.not_authenticated_exception = NotAuthenticatedException
app.add_exception_handler(
    NotAuthenticatedException, not_authenticated_exception_handler
)


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "Home"}
    )


@app.get("/tasks")
def get_tasks(
    db: Session = Depends(get_db), user: schemas.User = Depends(manager)
):
    return jsonable_encoder(user)


@app.get("/login")
def get_login(request: Request):
    return templates.TemplateResponse(
        "login.html", {"request": request, "title": "Login"}
    )


@app.post("/login")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        username=form_data.username, password=form_data.password, db=db
    )

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "title": "Login", "invalid": True},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTES)
    access_token = manager.create_access_token(
        data={"sub": user.username}, expires=access_token_expires
    )
    resp = RedirectResponse("/tasks", status_code=status.HTTP_302_FOUND)
    manager.set_cookie(resp, access_token)

    return resp


@app.get("/register")
def get_register(request: Request):
    return templates.TemplateResponse(
        "register.html", {"request": request, "title": "Register"}
    )


@app.post("/register")
def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    name: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    hashed_password = get_hashed_password(password)
    invalid = False
    if crud.get_user_by_username(db=db, username=username):
        invalid = True
    if crud.get_user_by_email(db=db, email=email):
        invalid = True

    if not invalid:
        crud.create_user(
            db=db,
            user=schemas.UserCreate(
                username=username,
                email=email,
                name=name,
                hashed_password=hashed_password,
            ),
        )
        response = RedirectResponse(
            "/login", status_code=status.HTTP_302_FOUND
        )
        return response
    else:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "title": "Register", "invalid": True},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
