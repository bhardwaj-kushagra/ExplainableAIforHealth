PYTHON=python

.PHONY: synthetic
synthetic:
	$(PYTHON) data_synthetic/generate_synthetic.py --seed 42
