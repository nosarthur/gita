.PHONY: dist test install clean twine

install:
	pip3 install -e .
test:
	pytest tests --cov=./gita $(TEST_ARGS) -n=auto -vv
dist:
	python3 setup.py sdist
twine:
	twine upload dist/*
clean:
	git clean -fdx
