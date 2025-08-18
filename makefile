NET := $(shell docker inspect $$(docker compose -f infra/docker-compose.yml ps -q db) --format '{{range $$k,$$v := .NetworkSettings.Networks}}{{$$k}}{{end}}')

alembic-current:
	docker run --rm -it --network "$(NET)" -v "$$PWD":/work -w /work \
	  python:3.11-bullseye bash -lc '\
	    pip install -q alembic SQLAlchemy psycopg2-binary python-dotenv && \
	    alembic current'

alembic-upgrade:
	docker run --rm -it --network "$(NET)" -v "$$PWD":/work -w /work \
	  python:3.11-bullseye bash -lc '\
	    pip install -q alembic SQLAlchemy psycopg2-binary python-dotenv && \
	    alembic upgrade head'