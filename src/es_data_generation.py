import logging
import os

from faker import Faker
from elasticsearch import Elasticsearch, helpers
import random

from pydantic import BaseModel, Field

from schemas.es_schemas import elastic_film_index_schema
import core.config as config


OBJECT_QTY = 100
RATING_MIN = 1
RATING_MAX = 10
NUMBER_OF_DECIMALS = 1
ROLES = {
    'directors': 'director',
    'actors': 'actor',
    'writers': 'writer'
}

logger = logging.getLogger(os.path.basename(__file__))
logger.setLevel(logging.INFO)


class PersonSchema(BaseModel):
    id: str
    name: str
    role: str


class GenreSchema(BaseModel):
    id: str
    name: str


class FilmWorkSchema(BaseModel):
    id: str
    imdb_rating: float
    genre: list[GenreSchema]
    title: str
    persons: list[PersonSchema] | None = Field(exclude=True)
    description: str | None = None

    def _filter_persons(self, role: str):
        if self.persons is not None:
            return [person for person in self.persons if person.role == role]

        return []

    def _get_persons_info(self, role: str):
        return [
            {'id': person.id, 'name': person.name}
            for person in self._filter_persons(role)
        ]

    def dict(self, **kwargs):
        """Трансформирует pydantic объекты в словарь, с распределением персоналий по ключам."""
        obj_dict = super().dict(**kwargs)

        for role_key, role_value in ROLES.items():
            obj_dict[role_key] = self._get_persons_info(role_value)

        return obj_dict


class FakeDataGenerator:
    """Класс для генерации и загрузки фейковых данных в ElasticSearch"""
    persons: list[PersonSchema] = None
    genres: list[GenreSchema] = None
    items: list[FilmWorkSchema] = None

    def __init__(self, es_index_name: str, es_index_schema: dict):
        self.es_index_name = es_index_name
        self.es_index_schema = es_index_schema
        self.elastic = Elasticsearch(host=config.ELASTIC_HOST, port=config.ELASTIC_PORT)
        self.fake = Faker()

    def exec(self):
        """Запуск процесса генерации и загрузки данных"""
        self._create_elastic_index()

        if self.es_index_name == 'movies':
            self._generate_persons()
            self._generate_genres()
            self._generate_films()
        elif self.es_index_name == 'genres':
            pass
        elif self.es_index_name == 'persons':
            pass

        self._load_data_to_elastic()

    def _create_elastic_index(self):
        """Создает индекс в эластике если он еще не создан"""
        logger.info(f'Check if index "{self.es_index_name}" exists...')

        if not self.elastic.indices.exists(index=self.es_index_name):
            self.elastic.indices.create(
                index=self.es_index_name,
                body=self.es_index_schema
            )
            logger.info(f'Elasticsearch index "{self.es_index_name}" created successfully')
        else:
            logger.info(f'Elasticsearch index "{self.es_index_name}" already exists')

    def _generate_persons(self):
        """Генерация персоналий"""
        logger.info('Generating persons...')

        self.persons = [
            PersonSchema(
                id=self.fake.uuid4(),
                name=self.fake.name(),
                role=random.choice(list(ROLES.values())))
            for _ in range(OBJECT_QTY)
        ]

    def _generate_genres(self):
        """Генерация жанров"""
        logger.info('Generating genres...')

        genres = ['Action', 'Western', 'Detective', 'Drama', 'Comedy', 'Melodrama', ]
        self.genres = [GenreSchema(id=self.fake.uuid4(), name=name) for name in genres]

    def _generate_films(self):
        """Генерация фильмов"""
        logger.info('Generating films...')

        self.items = [FilmWorkSchema(
            id=self.fake.uuid4(),
            imdb_rating=round(random.uniform(RATING_MIN, RATING_MAX), NUMBER_OF_DECIMALS),
            genre=random.sample(self.genres, k=random.randint(1, 3)),
            title=self.fake.bs().title(),
            persons=random.sample(self.persons, k=random.randint(5, 15)),
            description=self.fake.text(),
        ) for _ in range(OBJECT_QTY)]

    def _load_data_to_elastic(self):
        """Загрузка сгенерированных данных в эластик"""
        bulk_data = []

        logger.info('Preparing data for load...')

        for item in self.items:
            bulk_data.append({
                '_op_type': 'index',
                '_index': self.es_index_name,
                '_id': item.id,
                '_source': item.dict()
            })

        helpers.bulk(self.elastic, bulk_data)

        logger.info(f'{len(bulk_data)} objects were successfully loaded to index "{es_index_name}" ')


if __name__ == '__main__':
    indexes = {
        'movies': elastic_film_index_schema,
    }

    for es_index_name, es_index_schema in indexes.items():
        fake_data_generator = FakeDataGenerator(es_index_name, es_index_schema)
        fake_data_generator.exec()


# TODO индексы жанров и персон
