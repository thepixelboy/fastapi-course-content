from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel


class Car(BaseModel):
    make: str
    model: str
    year: int
    price: float
    engine: Optional[str] = "V4"
    autonomous: bool
    sold: List[str]


app = FastAPI()


@app.get("/")
def root():
    return {"Welcome to": "your first API in FastAPI!", "This is": "so cool!"}
