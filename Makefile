PYTHON ?= python3

.PHONY: check frontend-check backend-check format

check: frontend-check backend-check

frontend-check:
	npm run lint --prefix frontend
	npm run format:check --prefix frontend
	npm test --prefix frontend
	npm run build --prefix frontend

backend-check:
	$(PYTHON) -m ruff check backend/app backend/tests backend/maintenance backend/create_admin.py
	$(PYTHON) -m black --check --config backend/pyproject.toml backend/app backend/tests backend/maintenance backend/create_admin.py
	$(PYTHON) -m unittest discover -s backend/tests -q

format:
	npm run format --prefix frontend
	$(PYTHON) -m black --config backend/pyproject.toml backend/app backend/tests backend/maintenance backend/create_admin.py
