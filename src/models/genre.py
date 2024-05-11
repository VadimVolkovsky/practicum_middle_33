
import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class Genre(BaseModel):
    id: str
    name: str

    class Config:
        model_validate_json = orjson.loads
        model_dump_json = orjson_dumps
