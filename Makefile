PYTHON=python

.PHONY: synthetic
synthetic:
	$(PYTHON) data_synthetic/generate_synthetic.py --seed 42

.PHONY: preprocess
preprocess:
	$(PYTHON) src/preprocess.py --input data_synthetic/region_daily.csv --output data_processed/region_daily.parquet

.PHONY: train
train:
	$(PYTHON) src/models/xgb_train.py
	$(PYTHON) src/explainers.py
	$(PYTHON) src/models/run_dlnm.py
	$(PYTHON) src/models/produce_policy_statement.py

.PHONY: viz
viz:
	$(PYTHON) src/viz.py

.PHONY: run-api
run-api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: run-dashboard
run-dashboard:
	streamlit run src/dashboard/app.py

.PHONY: test
test:
	pytest -v

.PHONY: all
all: synthetic preprocess train viz
