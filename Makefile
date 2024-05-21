DOCKER_COMPOSE:=docker compose
EXEC_CORE:=$(DOCKER_COMPOSE) exec api


# work with docker

build:
	export DOCKER_BUILDKIT=1 && docker build -f docker/Dockerfile -t async_api_image .

ps:
	$(DOCKER_COMPOSE) ps

up:
	$(DOCKER_COMPOSE) up

restart:
	$(DOCKER_COMPOSE) restart

down:
	$(DOCKER_COMPOSE) down

pull:
	$(DOCKER_COMPOSE) pull

shell:
	$(EXEC_CORE) bash

flake8:
	$(EXEC_CORE) flake8

generate_data:
	docker exec -it middle_practicum_api python es_data_generation.py

debug_tests:
	$(DOCKER_COMPOSE) -f docker-compose_tests.yml up