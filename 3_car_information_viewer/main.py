from typing import Dict, List, Optional

from fastapi import (
    Body,
    FastAPI,
    Form,
    HTTPException,
    Path,
    Query,
    Request,
    status,
)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.responses import HTMLResponse
from starlette.status import HTTP_400_BAD_REQUEST

from database import cars

templates = Jinja2Templates(directory="templates")


class Car(BaseModel):
    make: Optional[str]
    model: Optional[str]
    year: Optional[int] = Field(..., ge=1970, lt=2022)
    price: Optional[float]
    engine: Optional[str] = "V4"
    autonomous: Optional[bool]
    sold: Optional[List[str]]


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=RedirectResponse)
def root(request: Request):
    return RedirectResponse(url="/cars")


@app.get("/cars", response_class=HTMLResponse)
def get_cars(
    request: Request, number: Optional[str] = Query("10", max_length=3)
):
    response = []
    for id, car in list(cars.items())[: int(number)]:
        response.append((id, car))

    return templates.TemplateResponse(
        "index.html", {"request": request, "cars": response, "title": "Home"}
    )


@app.get("/cars/{id}", response_class=HTMLResponse)
def get_car_by_id(request: Request, id: int = Path(..., ge=0, lt=1000)):
    car = cars.get(id)
    response = templates.TemplateResponse(
        "search.html",
        {"request": request, "car": car, "id": id, "title": "Search Car"},
    )
    if not car:
        response.status_code = status.HTTP_404_NOT_FOUND

    return response


@app.get("/create", response_class=HTMLResponse)
def create_car(request: Request):
    return templates.TemplateResponse(
        "create.html", {"request": request, "title": "Create Car"}
    )


@app.post("/search", response_class=RedirectResponse)
def search_cars(id: str = Form(...)):
    return RedirectResponse("/cars/" + id, status_code=302)


@app.post("/cars", status_code=status.HTTP_201_CREATED)
def add_cars(
    make: Optional[str] = Form(...),
    model: Optional[str] = Form(...),
    year: Optional[str] = Form(...),
    price: Optional[float] = Form(...),
    engine: Optional[str] = Form(...),
    autonomous: Optional[bool] = Form(...),
    sold: Optional[List[str]] = Form(None),
    min_id: Optional[int] = Body(0),
):
    body_cars = [
        Car(
            make=make,
            model=model,
            year=year,
            price=price,
            engine=engine,
            autonomous=autonomous,
            sold=sold,
        )
    ]
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

    return RedirectResponse(url="/cars", status_code=302)


@app.put("/cars/{id}", response_model=Dict[str, Car])
def update_car(id: int, car: Car = Body(...)):
    stored = cars.get(id)
    if not stored:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find car with the given ID.",
        )

    stored = Car(**stored)
    new = car.dict(exclude_unset=True)
    new = stored.copy(update=new)
    cars[id] = jsonable_encoder(new)
    response = {}
    response[id] = cars[id]

    return response


@app.delete("/cars/{id}")
def delete_car(id: int):
    if not cars.get(id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not find car with the given ID",
        )

    del cars[id]
