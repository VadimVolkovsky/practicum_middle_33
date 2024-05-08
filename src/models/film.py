from datetime import datetime
from typing import Optional

import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    # orjson.dumps возвращает bytes, а pydantic требует unicode, поэтому декодируем
    return orjson.dumps(v, default=default).decode()


class Film(BaseModel):
    # id: str
    # imdb_rating: Optional[float]
    # genre: Optional[list[Genre]]
    # title: str
    # description: Optional[str]
    # directors: Optional[list[Person]]
    # actors: Optional[list[Person]]
    # writers: Optional[list[Person]]
    # file_path: Optional[str]
    # creation_date: Optional[datetime]

    id: str
    title: str
    imdb_rating: Optional[float]

    genre: Optional[list[dict[str, str]]]
    description: Optional[str]

    directors: Optional[list[dict[str, str]]]
    actors: Optional[list[dict[str, str]]]
    writers: Optional[list[dict[str, str]]]

    file_path: Optional[str]
    creation_date: Optional[datetime]

    class Config:
        # Заменяем стандартную работу с json на более быструю
        json_loads = orjson.loads
        json_dumps = orjson_dumps
