# Project Overview

This is a Django-based web application called **jRetireWise**. It is designed to help users plan for retirement by running different retirement scenarios and visualizing the results.

The application is built with the following technologies:

*   **Backend:** Django, Django REST Framework
*   **Frontend:** Django templates
*   **Database:** PostgreSQL
*   **Asynchronous Tasks:** Celery with Redis
*   **Authentication:** `django-allauth` for both local and social authentication
*   **API Documentation:** `drf-spectacular` for generating OpenAPI schemas
*   **Financial Calculations:** `numpy`, `pandas`, and `scipy`
*   **Testing:** `pytest` with `pytest-django`, `pytest-cov`, `pytest-mock`, `pytest-asyncio`, and `pytest-playwright`
*   **Containerization:** Docker and Docker Compose

The project is structured into several Django apps:

*   `authentication`: Handles user authentication and profiles.
*   `financial`: Manages user's financial data, such as assets, income, and expenses.
*   `scenarios`: The core of the application, where users can create and manage retirement scenarios.
*   `calculations`: Performs the financial calculations for the retirement scenarios.

# Building and Running

The project is designed to be run with Docker.

## Running the application

To run the application in a development environment, use Docker Compose:

```bash
docker-compose up
```

This will start the web server, database, and Celery worker. The application will be available at `http://localhost:8000`.

## Running tests

The project has a comprehensive test suite, including unit, integration, and end-to-end tests. The tests can be run using the provided script:

```bash
./run_tests.sh
```

To run the end-to-end tests, which use Playwright, you need to pass the `--e2e` flag:

```bash
./run_tests.sh --e2e
```

# Development Conventions

The project follows standard Django development conventions.

*   **Code Style:** The project uses `black` for code formatting and `isort` for import sorting. `flake8` is used for linting.
*   **Testing:** The project has a strong emphasis on testing. All new features should be accompanied by tests.
*   **API:** The project exposes a versioned REST API. The API is documented using the OpenAPI standard, and the documentation is available at `/api/docs/`.
*   **Asynchronous Tasks:** For long-running tasks, such as running retirement calculations, the project uses Celery. Tasks are defined in the `tasks.py` file of the relevant app.
