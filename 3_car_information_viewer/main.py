from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field


class Car(BaseModel):
    make: str
    model: str
    year: int = Field(..., ge=1970, lt=2022)
    price: float
    engine: Optional[str] = "V4"
    autonomous: bool
    sold: List[str]


app = FastAPI()


@app.get("/")
def root():
    return {"Welcome to": "your first API in FastAPI!", "This is": "so cool!"}
