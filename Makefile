# Tells Make that a target is a command/action to run, 
# rather than the name of an actual file on disk.
.PHONY: build up down restart fastapi

build:
	docker compose up --build -d

up:
	docker compose up -d

down:
	docker compose down

restart: down build

fastapi:
	uv --directory server run fastapi dev
