import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_login.fastapi_login import LoginManager
from sqlalchemy.orm import Session

import models
from db import DBContext, SessionLocal, engine

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
ACCESS_TOKEN_EXPIRES_MINUTES = 60

manager = LoginManager(SECRET_KEY, token_url="/login", use_cookie=True)
manager.cookie_name = "auth"

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def get_db():
    with DBContext() as db:
        yield db


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "Home"}
    )


@app.get("/tasks")
def get_tasks(db: Session = Depends(get_db)):
    return jsonable_encoder(db.query(models.Task).first())


@app.get("/login")
def get_login(request: Request):
    return templates.TemplateResponse(
        "login.html", {"request": request, "title": "Login"}
    )
