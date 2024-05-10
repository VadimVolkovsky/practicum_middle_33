import logging
import os
from time import sleep
from typing import Optional

from elasticsearch.helpers import scan
from faker import Faker
from elasticsearch import Elasticsearch, helpers
import random

from pydantic import BaseModel, Field

from schemas.es_schemas import elastic_film_index_schema, elastic_genre_index_schema, elastic_person_index_schema
import core.config as config


FILMS_QTY = 100
PERSONS_QTY = 500
RATING_MIN = 1
RATING_MAX = 10
NUMBER_OF_DECIMALS = 1  # кол-во цифр после запятой в рейтинге фильма
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
    role: Optional[str]

    def dict(self, **kwargs):
        """"""
        obj_dict = super().dict(**kwargs)
        del obj_dict['role']
        return obj_dict


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


class ElasticDataGenerator:
    """Класс для генерации и загрузки данных в ElasticSearch"""
    persons: list[PersonSchema] = None
    genres: list[GenreSchema] = None
    items: list[FilmWorkSchema | GenreSchema | PersonSchema] = []

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
            self._get_genres_from_movies()
        elif self.es_index_name == 'persons':
            self._get_persons_from_movies()
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
            for _ in range(PERSONS_QTY)
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
        ) for _ in range(FILMS_QTY)]

    def _get_genres_from_movies(self):
        """Получает список из всех жанров, которые есть в добавленных фильмах"""
        items = []
        film_data = scan(self.elastic, index='movies', query={"query": {"match_all": {}}})
        for film in film_data:
            for genre in film['_source']['genre']:
                genre_obj = GenreSchema(**genre)
                if genre_obj not in self.items:
                    items.append(genre_obj)
        self.items = items

    def _get_persons_from_movies(self):
        """"""
        film_data = scan(self.elastic, index='movies', query={"query": {"match_all": {}}})
        for film in film_data:
            for roles, role in ROLES.items():
                for person in film['_source'][roles]:
                    person_obj = PersonSchema(**person)
                    if person_obj not in self.items:
                        self.items.append(person_obj)

    def _load_data_to_elastic(self):
        """Загрузка данных в эластик"""
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
        sleep(5)  # чтобы данные успели полностью загрузиться в эластик, и их можно было получать

        logger.info(f'{len(bulk_data)} objects were successfully loaded to index "{self.es_index_name}" ')


if __name__ == '__main__':
    indexes = {
        'movies': elastic_film_index_schema,
        'genres': elastic_genre_index_schema,
        'persons': elastic_person_index_schema,
    }
    for index_name, index_schema in indexes.items():
        fake_data_generator = ElasticDataGenerator(index_name, index_schema)
        fake_data_generator.exec()
