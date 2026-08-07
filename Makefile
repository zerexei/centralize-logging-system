up:
	docker compose up --build -d

fastapi:
	uv --directory server run fastapi dev
