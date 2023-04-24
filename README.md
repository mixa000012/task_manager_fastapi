# Task manager Bot

 <a href="https://t.me/mixa000012"><img src="https://img.shields.io/badge/Telegram-💣%20@mixa000012"></a>

This is task manager bot that helps you to reach your goals!


## Used technology
* Python 3.10;
* aiogram 2.x (Telegram Bot framework);
* Docker and Docker Compose (containerization);
* PostgreSQL (database);
* SQLAlchemy (working with database from Python);
* Alembic (database migrations made easy);
* Docker images are built with buildx for both amd64 and arm64 architectures.

## Installation

Grab `docker-compose-example.yml`, rename it to `docker-compose.yml`

Create `.env` file and put it next to your `docker-compose.yml`, open
and fill the necessary data(API_TOKEN).

To init migrations in terminal:

```
alembic init migrations
```

Change `alembic.ini` and `env.py`
```
- `alembic.ini` in 63 line sqlalchemy.url = postgresql://postgres:postgres@db:5432/postgre (set your log:pass from db)
- in `env.py` need to change `target_metadata` to Base.metadata from myapp.models import Base
```

-  ```alembic revision --autogenerate -m "comment"```

Finally, start your bot with `docker compose -f docker-compose.yaml up -d` command.
