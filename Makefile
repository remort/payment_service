.PHONY: help up down build logs restart clean migrate migrate-create shell

help:
	@echo "Available commands:"
	@echo "  make up          - Start all services"
	@echo "  make down        - Stop all services"
	@echo "  make build       - Rebuild images"
	@echo "  make logs        - Show logs"
	@echo "  make restart     - Restart services"
	@echo "  make clean       - Remove containers, volumes, and images"
	@echo "  make migrate     - Run database migrations"
	@echo "  make migrate-create msg='message' - Create new migration"
	@echo "  make shell       - Open Python shell in api container"
	@echo "  make db-shell    - Connect to PostgreSQL"
	@echo "  make rabbit-shell - List RabbitMQ queues"

up:
	docker-compose up -d
	@echo "Services started. API available at http://localhost:8000"
	@echo "RabbitMQ UI: http://localhost:15672 (guest/guest)"

down:
	docker-compose down

build:
	docker-compose build --no-cache

logs:
	docker-compose logs -f

restart:
	docker-compose restart

clean:
	docker-compose down -v
	docker system prune -f

migrate:
	docker-compose exec api alembic upgrade head

migrate-create:
	docker-compose exec api alembic revision --autogenerate -m "$(msg)"

shell:
	docker-compose exec api python

db-shell:
	docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}

rabbit-shell:
	docker-compose exec rabbitmq rabbitmqctl list_queues

status:
	docker-compose ps

test:
	./test_api.sh
