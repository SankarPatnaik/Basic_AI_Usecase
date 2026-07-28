.PHONY: install ingest run api test

install:
	python -m pip install -r requirements.txt

ingest:
	python ingest.py --reset

run:
	streamlit run streamlit_app.py

api:
	uvicorn api:app --reload --port 8000

test:
	pytest -q
