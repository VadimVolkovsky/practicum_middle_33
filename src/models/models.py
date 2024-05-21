from datetime import datetime

import orjson
from pydantic import BaseModel

from constants import OptStrType, ListDictType


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class BaseCommonModel(BaseModel):
    id: str

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class BaseNameModel(BaseCommonModel):
    name: str


class Film(BaseModel):
    id: str
    title: str
    imdb_rating: float | None = None

    genre: ListDictType | None = None
    description: OptStrType = None

    directors: ListDictType | None = None
    actors: ListDictType | None = None
    writers: ListDictType | None = None

    file_path: OptStrType = None
    creation_date: datetime | None = None


class Person(BaseNameModel):
    pass


class Genre(BaseNameModel):
    pass
