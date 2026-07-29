.PHONY: generate test check

generate:
	python3 scripts/generate_site.py

test:
	python3 -m unittest discover -s tests -v

check:
	python3 scripts/generate_site.py --check
	python3 -m unittest discover -s tests -v
