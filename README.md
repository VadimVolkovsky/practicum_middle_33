# **Репозиторий для командной работы (Миддл-Практикум - Когорта 33)**


### Инструкция по развертыванию

#### Создание контейнеров

```shell script
make build
```

#### Запуск

```shell script
make up
```

#### Заливка тестовых данных в ElasticSearch
```shell script
make generate_data
```

#### Тестирование

Для запуска тестирования в контейнерах необходимо выполнить следующие шаги:

...

Для локального дебага тестов необходимо выполнить следующие шаги:
- Активировать настройки для локального дебага тестов в src/tests/functional/settings.py
- Закомментить сервис "tests" в файле docker-compose_tests.yml
- Пересобрать контейнеры командой make build
- Запустить сервис командой make debug_tests
- Выставить брейкпоинты на необходимые тесты и запустить тесты локально


### Документация

- http://127.0.0.1:80/api/openapi

### Авторы
- [Di-Nov](https://github.com/Di-Nov)
- [ykolpakov](https://github.com/ykolpakov)
- [VadimVolkovsky](https://github.com/VadimVolkovsky)


### Другое
- python 3.12
