from typing import Dict, List, Optional

from fastapi import Body, FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

from database import cars


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


@app.get("/cars", response_model=List[Dict[str, Car]])
def get_cars(number: Optional[str] = Query("10", max_length=3)):
    response = []
    for id, car in list(cars.items())[: int(number)]:
        to_add = {}
        to_add[id] = car
        response.append(to_add)

    return response


@app.get("/cars/{id}", response_model=Car)
def get_car_by_id(id: int = Path(..., ge=0, lt=1000)):
    car = cars.get(id)
    if not car:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find car by ID.",
        )

    return car


@app.post("/cars", status_code=status.HTTP_201_CREATED)
def add_cars(body_cars: List[Car], min_id: Optional[int] = Body(0)):
    if len(body_cars) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No cars to add."
        )

    min_id = len(cars.values()) + min_id
    for car in body_cars:
        while cars.get(min_id):
            min_id += 1
        cars[min_id] = car
        min_id += 1
