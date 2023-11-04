# Pricing Services API

Pricing services (PS) is an API built on FastAPI that provides FIXME. ...

For more details see FIXME: Link to documentation

For API documentation see FIXME: Backstage link to api

## Code linting and env setup

- We use `ruff`, `black` and `mypy` to format/lint/check types together with `pre-commit`
- Before making changes make sure to install pre-commit hooks with `make setup-pre-commit`
- To run all formatters/linters manually run `make lint`
- To enter `venv` with all dependencies installed run `make env`

> **Note** There is also an option run the formatting scripts manually, they are found in `scripts` directory

## How to run

- We use docker images to run our apps in development and production
- First build the docker image with `make build`
- Run the docker image in a container with `make up` or use `make up-d` to run in the background
- To shut down the container run `make stop`
- To enter the running container with a bash prompt use `make bash`
- To access the local database run `make db`

## How to run tests

- We run tests in the app docker container
- To run tests use `make test` this will run `pytest -v tests/` in the app container
- To change testing flags use `make test TA="-vs"`
- Tests can also be run via the test script using `make test-script`

## DB Migrations

- If a new table is created, make sure to import it in `db/alembic.py`. It allows to use alembic autogenerate
  functionality
- When changes in database is done (for example creating a new table, add a new column), start an interactive session in
  the app container
    ```shell
    make bash
    ```
- Migrate the database to the latest version
    ```shell
    alembic upgrade head
    ```
- Then create a new migration (revision) by alembic inside the container
    ```shell
    alembic revision --autogenerate -m 'Your message'
    ```
- New automatically generated migration can be found in `alembic/versions`. Check it, update it if it is needed and do
  not forget to add it into git

> **Note**: A new file with the new migration is created by container so the owner of the file is usually root. For
> these reason it is necessary to change file owner
