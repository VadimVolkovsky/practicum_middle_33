DOCKER_COMPOSE:=docker-compose -f docker-compose.yml
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
