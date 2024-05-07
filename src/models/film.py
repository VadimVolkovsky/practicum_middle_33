import uuid
from datetime import datetime
from typing import Optional

import orjson
from pydantic import BaseModel

from models.genre import Genre
from models.person import Person


def orjson_dumps(v, *, default):
    # orjson.dumps возвращает bytes, а pydantic требует unicode, поэтому декодируем
    return orjson.dumps(v, default=default).decode()


class Film(BaseModel):
    id: uuid.UUID
    imdb_rating: Optional[float]
    genre: list[Genre]
    title: str
    description: str
    directors: list[Person]
    actors: list[Person]
    writers: list[Person]
    file_path: str
    creation_date: datetime

    class Config:
        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps
