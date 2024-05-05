from faker import Faker
from elasticsearch import Elasticsearch, helpers
import random

from pydantic import BaseModel, Field

from schemas.es_schemas import elastic_film_index_schema
import core.config as config

ES_HOST = config.ELASTIC_HOST
ES_PORT = config.ELASTIC_PORT

OBJECT_QTY = 100
RATING_MIN = 1
RATING_MAX = 10
NUMBER_OF_DECIMALS = 1  # кол-во цифр после запятой для рейтинга фильма
ROLES = {
    'directors': 'director',
    'actors': 'actor',
    'writers': 'writer'
}
GENRES = ['Action', 'Western', 'Detective', 'Drama', 'Comedy', 'Melodrama', ]


class PersonSchema(BaseModel):
    id: str
    name: str
    role: str


class FilmWorkSchema(BaseModel):
    id: str
    imdb_rating: float
    genres: list[str]
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

    def _get_persons_names(self, role: str):
        return [person.name for person in self._filter_persons(role)]

    def dict(self, **kwargs):
        obj_dict = super().dict(**kwargs)
        for role_key, role_value in ROLES.items():
            obj_dict[role_key] = self._get_persons_info(role_value)
        return obj_dict


class FakeDataGenerator:
    """Класс для генерации и загрузки фейковых данных в ElasticSearch"""
    persons: list[PersonSchema] = None
    items: list[FilmWorkSchema] = None

    def __init__(self, es_index_name: str, es_index_schema: dict):
        self.es_index_name = es_index_name
        self.es_index_schema = es_index_schema
        self.elastic = Elasticsearch(host=ES_HOST, port=ES_PORT)
        self.fake = Faker()

    def exec(self):
        """Запуск процесса генерации и загрузки данных"""
        self._create_elastic_index()
        if self.es_index_name == 'movies':
            self._generate_persons()
            self._generate_films()
        elif self.es_index_name == 'genres':
            pass
        elif self.es_index_name == 'persons':
            pass
        self._load_data_to_elastic()

    def _create_elastic_index(self):
        """Создает индекс в эластике если он еще не создан"""
        if not self.elastic.indices.exists(index=self.es_index_name):
            self.elastic.indices.create(
                index=self.es_index_name,
                body=self.es_index_schema
            )
            print(f'Elasticsearch index "{self.es_index_name}" created successfully')
        else:
            print(f'Elasticsearch index "{self.es_index_name}" already exists')

    def _generate_persons(self):
        """Генерация персоналий"""
        self.persons = [
            PersonSchema(
                id=self.fake.uuid4(),
                name=self.fake.name(),
                role=random.choice(list(ROLES.values())))
            for _ in range(OBJECT_QTY)
        ]

    def _generate_films(self):
        """Генерация фильмов"""
        self.items = [FilmWorkSchema(
            id=self.fake.uuid4(),
            imdb_rating=round(random.uniform(RATING_MIN, RATING_MAX), NUMBER_OF_DECIMALS),
            genres=random.sample(GENRES, k=random.randint(1, 3)),  # TODO вынести жанры в отдельный метод и генерить их с uuid + поправить в схеме эластика
            title=self.fake.bs().title(),
            persons=random.sample(self.persons, k=random.randint(5, 15)),
            description=self.fake.text(),
        ) for _ in range(OBJECT_QTY)]

    def _load_data_to_elastic(self):
        """Загрузка сгенерированных данных в эластик"""
        bulk_data = []
        for item in self.items:
            bulk_data.append({
                '_op_type': 'index',
                '_index': self.es_index_name,
                '_id': item.id,
                '_source': item.dict()
            })

        helpers.bulk(self.elastic, bulk_data)
        print('Data were successfully loaded')


if __name__ == '__main__':
    indexes = {
        'movies': elastic_film_index_schema,
    }

    for es_index_name, es_index_schema in indexes.items():
        fake_data_generator = FakeDataGenerator(es_index_name, es_index_schema)
        fake_data_generator.exec()


# TODO индексы жанров и персон
