FROM python:3.11-slim as dependencies

RUN \
    apt-get update -y && \
    apt-get install -y curl gcc python3-dev && \
    apt-get clean

RUN \
    curl -sSL https://install.python-poetry.org \
    | POETRY_HOME=/opt/poetry POETRY_VERSION=1.6.1 python3 -
ENV PATH="/opt/poetry/bin:$PATH"

RUN poetry config virtualenvs.in-project true


RUN mkdir /usr/src/app
WORKDIR /usr/src/app

COPY pyproject.toml poetry.lock* ./

RUN poetry install --only main --no-root


FROM python:3.11-slim as production

# Update system packages and install vim
RUN \
    apt-get update -y && \
    apt-get install -y vim && \
    apt-get clean

COPY --from=dependencies /usr/src/app /usr/src/app

WORKDIR /usr/src/app

# Create system user `app` and use it for executing python app
RUN useradd --uid 1000 --user-group --no-create-home app
RUN chown -R app:app /usr/src/app

USER app

# Include python app into PATH
ENV VIRTUAL_ENV=/usr/src/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH=/usr/src/app

ENV PYTHONUNBUFFERED=1

# Copy files
COPY alembic.ini alembic.ini
COPY alembic alembic
COPY app app
COPY scripts/run-api.sh ./scripts/
COPY README.md README.md

EXPOSE 5000


FROM python:3.11-slim as development

# Update system packages and install netcat, vim, curl and ipython
RUN \
    apt-get update -y && \
    apt-get install -y netcat-openbsd vim curl gcc python3-dev && \
    apt-get clean

COPY --from=dependencies /opt/poetry /opt/poetry
COPY --from=dependencies /usr/src/app /usr/src/app

WORKDIR /usr/src/app

# Include python app into PATH
ENV VIRTUAL_ENV=/usr/src/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV PYTHONPATH=/usr/src/app

# Include poetry into PATH
ENV PATH="/opt/poetry/bin:$PATH"

# Install development python packages
RUN poetry install --no-root

COPY --from=production /usr/src/app /usr/src/app

COPY scripts scripts
COPY tests tests

EXPOSE 5000
