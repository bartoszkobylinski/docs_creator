PROJECT_DIR ?= ../ZipTie

install:
	poetry install
scan: 
	poetry run fastdoc scan $(PROJECT_DIR) --out report.json

dashboard:
	streamlit run scripts/streamlit_app.py