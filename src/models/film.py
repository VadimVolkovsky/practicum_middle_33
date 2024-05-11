from datetime import datetime
from typing import Optional

import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class Film(BaseModel):
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
        model_validate_json = orjson.loads
        model_dump_json = orjson_dumps
